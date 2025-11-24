from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth import logout
from django.middleware.csrf import get_token

from .models import (
    VerificationDocument,
    DoctorProfile, Abonnement, PatientProfile
)
from .serializers import (
    DoctorRegisterSerializer, AnalyseSerializer,
    PatientListSerializer
)

from authentication import CookieTokenAuthentication


# ============================================
# CONFIGURATION DES COOKIES
# ============================================
COOKIE_SETTINGS = {
    'httponly': False,  # Must be False for middleware to read it
    'secure': True,
    'samesite': 'None',
    'domain': None,  # Important: None pour Render
    'path': '/',
    'max_age': 60 * 60 * 24 * 7  # 7 jours
}


class RegisterView(APIView):
    permission_classes = []
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        raw = request.data

        documents = []
        i = 0
        while f'documents.{i}.doc_type' in raw:
            documents.append({
                'doc_type': raw[f'documents.{i}.doc_type'],
                'document': raw[f'documents.{i}.document'],
            })
            i += 1

        payload = dict(raw)
        clean_payload = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in payload.items()}
        clean_payload['documents'] = documents

        serializer = DoctorRegisterSerializer(data=clean_payload)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "Registration successful. Please wait for admin approval."}, status=201)

        return Response(serializer.errors, status=400)


class CustomLoginView(ObtainAuthToken):
    """
    Vue de login unifiée avec gestion correcte des cookies
    """
    permission_classes = []

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.validated_data['user']
        
        # Check if user is active
        if not user.is_active:
            return Response({
                "error": "Account is deactivated. Please contact support."
            }, status=status.HTTP_403_FORBIDDEN)
        
        # For doctors, check if their profile is approved
        if user.role == 'doctor':
            try:
                doctor_profile = user.doctor_profile
                if not doctor_profile.is_approved:
                    return Response({
                        "error": "Account not yet approved by the administrator."
                    }, status=status.HTTP_403_FORBIDDEN)
            except DoctorProfile.DoesNotExist:
                return Response({
                    "error": "Doctor profile not found. Please contact support."
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Get or create token
        token, created = Token.objects.get_or_create(user=user)
        
        # Prepare response data (sans le token pour plus de sécurité)
        response_data = {
            "user_id": user.pk,
            "email": user.email,
            "full_name": f"{user.first_name} {user.last_name}",
            "role": user.role,
        }
        
        # Add approval status for doctors
        if user.role == 'doctor':
            try:
                response_data["is_approved"] = user.doctor_profile.is_approved
                response_data["verification_status"] = user.doctor_profile.verification_status
            except DoctorProfile.DoesNotExist:
                response_data["is_approved"] = False
                response_data["verification_status"] = "pending"
        
        # Create response
        response = Response(response_data, status=status.HTTP_200_OK)
        
        # Set auth token cookie
        response.set_cookie(
            key="auth_token",
            value=token.key,
            **COOKIE_SETTINGS
        )
        
        # Set CSRF token cookie
        response.set_cookie(
            key='csrftoken',
            value=get_token(request),
            **{**COOKIE_SETTINGS, 'httponly': False}  # CSRF must be readable by JS
        )
        
        return response


class CheckAuthView(APIView):
    """
    Endpoint pour vérifier l'authentification
    Utilisé par le frontend au chargement de l'app
    """
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        response_data = {
            "authenticated": True,  # Changed from "is_authenticated" for consistency
            "user_id": user.pk,
            "email": user.email,
            "full_name": f"{user.first_name} {user.last_name}",
            "role": user.role,
        }
        
        # Add approval status based on user role
        if user.role == 'doctor':
            try:
                doctor_profile = user.doctor_profile
                response_data["is_approved"] = doctor_profile.is_approved
                response_data["verification_status"] = doctor_profile.verification_status
            except DoctorProfile.DoesNotExist:
                response_data["is_approved"] = False
                response_data["verification_status"] = "pending"
        else:
            response_data["is_approved"] = True
            response_data["verification_status"] = "approved"
        
        return Response(response_data)


class CheckSubscriptionView(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            
            if user.role != 'doctor':
                return JsonResponse({
                    "error": "Access denied",
                    "message": "This endpoint is only available for doctors"
                }, status=403)
            
            try:
                doctor_profile = DoctorProfile.objects.get(user=user)
            except DoctorProfile.DoesNotExist:
                return JsonResponse({
                    "error": "Doctor profile not found",
                    "message": "Please complete your doctor profile"
                }, status=404)
            
            has_subscription = Abonnement.objects.filter(
                doctor=doctor_profile,
                statut="active"
            ).exists()
            
            response_data = {
                "name": f"Dr. {user.first_name} {user.last_name}",
                "email": user.email,
                "hasSubscription": has_subscription
            }
            
            return JsonResponse(response_data)
        
        except Exception as e:
            return JsonResponse({
                "error": "Failed to fetch user data",
                "details": str(e)
            }, status=500)


class DoctorProfileView(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        try:
            doctor_profile = DoctorProfile.objects.get(user=user)
            
            current_subscription = Abonnement.objects.filter(
                doctor=doctor_profile,
                date_debut__lte=timezone.now().date(),
                date_fin__gte=timezone.now().date(),
                statut="active"
            ).first()
            
            documents = VerificationDocument.objects.filter(doctor=doctor_profile)
            document_status = {
                "total_documents": documents.count(),
                "approved_documents": documents.filter(status="approved").count(),
                "pending_documents": documents.filter(status="pending").count(),
                "rejected_documents": documents.filter(status="rejected").count(),
            }
            
            subscription_history = Abonnement.objects.filter(
                doctor=doctor_profile
            ).order_by('-date_debut')[:5].values(
                'type', 'date_debut', 'date_fin', 'statut', 'prix'
            )
            
            response_data = {
                "user": {
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "full_name": f"{user.first_name} {user.last_name}".strip(),
                    "email": user.email,
                    "phone": user.phone,
                    "date_of_birth": user.date_of_birth,
                    "address": user.address,
                    "gender": user.gender,
                    "role": user.role,
                },
                "doctor": {
                    "speciality": doctor_profile.speciality,
                    "numero_ordre": doctor_profile.numero_ordre,
                    "grade": doctor_profile.grade,
                    "experience": doctor_profile.experience,
                    "hopital": doctor_profile.hopital,
                    "is_approved": doctor_profile.is_approved,
                    "verification_status": doctor_profile.verification_status,
                },
                "subscription": {
                    "current_type": current_subscription.type if current_subscription else "FreeTrial",
                    "current_status": current_subscription.statut if current_subscription else "inactive",
                    "start_date": current_subscription.date_debut if current_subscription else None,
                    "end_date": current_subscription.date_fin if current_subscription else None,
                    "price": float(current_subscription.prix) if current_subscription else 0.0,
                    "payment_method": current_subscription.mode_paiement if current_subscription else None,
                } if current_subscription else {
                    "current_type": "FreeTrial",
                    "current_status": "inactive",
                    "start_date": None,
                    "end_date": None,
                    "price": 0.0,
                    "payment_method": None,
                },
                "verification": document_status,
                "subscription_history": list(subscription_history),
                "statistics": {
                    "total_patients": doctor_profile.patients.count(),
                    "total_analyses": doctor_profile.analyses.count(),
                    "recent_analyses": doctor_profile.analyses.filter(
                        date__gte=timezone.now().date() - timezone.timedelta(days=30)
                    ).count(),
                }
            }
            
            return Response(response_data)
            
        except DoctorProfile.DoesNotExist:
            return Response({
                "error": "Doctor profile not found",
                "user": {
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "full_name": f"{user.first_name} {user.last_name}".strip(),
                    "email": user.email,
                    "phone": user.phone,
                    "date_of_birth": user.date_of_birth,
                    "address": user.address,
                    "gender": user.gender,
                    "role": user.role,
                }
            }, status=404)


class DoctorProfileUpdateView(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        
        try:
            doctor_profile = DoctorProfile.objects.get(user=user)
            
            user_fields = ['first_name', 'last_name', 'phone', 'date_of_birth', 'address', 'gender']
            for field in user_fields:
                if field in request.data:
                    setattr(user, field, request.data[field])
            
            doctor_fields = ['speciality', 'numero_ordre', 'grade', 'experience', 'hopital']
            for field in doctor_fields:
                if field in request.data:
                    setattr(doctor_profile, field, request.data[field])
            
            user.save()
            doctor_profile.save()
            
            return Response({
                "message": "Profile updated successfully",
                "user": {
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "phone": user.phone,
                    "date_of_birth": user.date_of_birth,
                    "address": user.address,
                    "gender": user.gender,
                },
                "doctor": {
                    "speciality": doctor_profile.speciality,
                    "numero_ordre": doctor_profile.numero_ordre,
                    "grade": doctor_profile.grade,
                    "experience": doctor_profile.experience,
                    "hopital": doctor_profile.hopital,
                }
            })
            
        except DoctorProfile.DoesNotExist:
            return Response({"error": "Doctor profile not found"}, status=404)


class EnhancedLogoutView(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Delete the auth token from database
            if hasattr(request.user, 'auth_token'):
                request.user.auth_token.delete()
            
            # Clear Django session
            logout(request)
            
            response = Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
            
            # Clear all auth-related cookies
            cookies_to_clear = ['auth_token', 'sessionid', 'csrftoken']
            
            for cookie_name in cookies_to_clear:
                response.delete_cookie(
                    cookie_name,
                    path="/",
                    domain=None,  # Important: doit correspondre au domain du set_cookie
                    samesite='None'
                )
            
            return response
        except Exception as e:
            print(f"Logout error: {e}")
            return Response({"error": "Error during logout"}, status=status.HTTP_400_BAD_REQUEST)


class DoctorPatientsView(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "doctor" or not request.user.doctor_profile.is_approved:
            return Response({"error": "Only approved doctors can view their patients."}, status=403)

        patients = request.user.doctor_profile.patients.all()
        serializer = PatientListSerializer(patients, many=True)
        return Response(serializer.data, status=200)


class PatientAnalysesView(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, patient_id):
        try:
            patient = PatientProfile.objects.get(id=patient_id, doctor=request.user.doctor_profile)
        except PatientProfile.DoesNotExist:
            return Response({"error": "Patient not found"}, status=404)

        analyses = patient.analyses.all().order_by("-date")
        serializer = AnalyseSerializer(analyses, many=True)
        return Response(serializer.data, status=200)