from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes

from django.http import JsonResponse, FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth import logout
from django.middleware.csrf import get_token
from django.core.files.base import ContentFile

from .models import (
    CustomUser, VerificationDocument, Analyse,
    DoctorProfile, Abonnement, PatientProfile
)
from .serializers import (
    DoctorRegisterSerializer, PatientSerializer,
    PatientProfileSerializer, AnalyseSerializer,
    PatientListSerializer
)

from authentication import CookieTokenAuthentication

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.utils import ImageReader

from datetime import datetime, date
import json
import os

"""___________________________________________________________________________________
                                Registration
   ___________________________________________________________________________________
"""


class RegisterView(APIView):
    permission_classes = []
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        raw = request.data  # still a QueryDict

        # build list of documents from dotted keys:
        documents = []
        i = 0
        while f'documents.{i}.doc_type' in raw:
            documents.append({
                'doc_type': raw[f'documents.{i}.doc_type'],
                'document': raw[f'documents.{i}.document'],
            })
            i += 1

        # build a normal dict with everything else + documents
        payload = dict(raw)  # copies keys: values lists
        # flatten the single-value lists
        clean_payload = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in payload.items()}
        clean_payload['documents'] = documents  # our real list of dicts

        serializer = DoctorRegisterSerializer(data=clean_payload)
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "Registration successful. Please wait for admin approval."}, status=201)

        return Response(serializer.errors, status=400)

class CustomLoginView_1(ObtainAuthToken):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
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
            
            # For other roles (admin, patient, researcher), allow login without approval check
            # or add specific checks if needed
            
            token, created = Token.objects.get_or_create(user=user)
            
            # Prepare response data
            response_data = {
                "token": token.key,
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
            
            return Response(response_data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from django.middleware.csrf import get_token
from django.http import HttpResponse

class CustomLoginView_2(ObtainAuthToken):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
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
            
            token, created = Token.objects.get_or_create(user=user)
            
            # Prepare response data (SANS le token)
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
            
            # Créer la réponse
            response = Response(response_data)
            
            # Définir le cookie HttpOnly sécurisé
            response.set_cookie(
                key='auth_token',
                value=token.key,
                httponly=True,  # Empêche l'accès JavaScript
                secure=True,    # HTTPS seulement en production
                samesite="None",  # Protection CSRF
                domain=".neurev.com", 
                max_age=86400,  # 24 heures
                path='/',
            )
            
            # Ajouter aussi un cookie CSRF si nécessaire
            response.set_cookie(
                key='csrftoken',
                value=get_token(request),
                secure=True,
                domain=".neurev.com", 
                samesite='Lax',
                max_age=86400,
            )
            
            return response
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class CheckAuthView(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Prepare basic response
        response_data = {
            "is_authenticated": True,
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
            # For non-doctor roles, they are automatically "approved"
            response_data["is_approved"] = True
            response_data["verification_status"] = "approved"
        
        return Response(response_data)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_auth(request):
    user = request.user
    response_data = {
        "authenticated": True,
        "user_id": user.pk,
        "email": user.email,
        "full_name": f"{user.first_name} {user.last_name}",
        "role": user.role,
    }
    
    if user.role == 'doctor':
        try:
            response_data["is_approved"] = user.doctor_profile.is_approved
            response_data["verification_status"] = user.doctor_profile.verification_status
        except DoctorProfile.DoesNotExist:
            response_data["is_approved"] = False
            response_data["verification_status"] = "pending"
    
    return Response(response_data)

    
class CheckSubscriptionView(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
      try:
        user = request.user
        
        # Check if user is a doctor
        if user.role != 'doctor':
            return JsonResponse({
                "error": "Access denied",
                "message": "This endpoint is only available for doctors"
            }, status=403)
        
        # Try to get the doctor's profile
        try:
            doctor_profile = DoctorProfile.objects.get(user=user)
        except DoctorProfile.DoesNotExist:
            return JsonResponse({
                "error": "Doctor profile not found",
                "message": "Please complete your doctor profile"
            }, status=404)
        
        # Check if doctor has ANY subscription (regardless of dates)
        has_subscription = Abonnement.objects.filter(
            doctor=doctor_profile,
            statut="active"  # Only check if status is active
        ).exists()
        
        # Prepare response data
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


from django.utils import timezone

class DoctorProfileView(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        try:
            doctor_profile = DoctorProfile.objects.get(user=user)
            
            # Get current subscription
            current_subscription = Abonnement.objects.filter(
                doctor=doctor_profile,
                date_debut__lte=timezone.now().date(),
                date_fin__gte=timezone.now().date(),
                statut="active"
            ).first()
            
            # Get verification documents status
            documents = VerificationDocument.objects.filter(doctor=doctor_profile)
            document_status = {
                "total_documents": documents.count(),
                "approved_documents": documents.filter(status="approved").count(),
                "pending_documents": documents.filter(status="pending").count(),
                "rejected_documents": documents.filter(status="rejected").count(),
            }
            
            # Get subscription history
            subscription_history = Abonnement.objects.filter(
                doctor=doctor_profile
            ).order_by('-date_debut')[:5].values(
                'type', 'date_debut', 'date_fin', 'statut', 'prix'
            )
            
            response_data = {
                # User basic info
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
                
                # Doctor professional info
                "doctor": {
                    "speciality": doctor_profile.speciality,
                    "numero_ordre": doctor_profile.numero_ordre,
                    "grade": doctor_profile.grade,
                    "experience": doctor_profile.experience,
                    "hopital": doctor_profile.hopital,
                    "is_approved": doctor_profile.is_approved,
                    "verification_status": doctor_profile.verification_status,
                },
                
                # Subscription info
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
                
                # Verification documents
                "verification": document_status,
                
                # Subscription history
                "subscription_history": list(subscription_history),
                
                # Statistics (optional)
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
            
            # Update user info
            user_fields = ['first_name', 'last_name', 'phone', 'date_of_birth', 'address', 'gender']
            for field in user_fields:
                if field in request.data:
                    setattr(user, field, request.data[field])
            
            # Update doctor profile info
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


from django.contrib.auth import logout
from django.middleware.csrf import get_token

class EnhancedLogoutView(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Delete the auth token
            if hasattr(request.user, 'auth_token'):
                request.user.auth_token.delete()
            
            # Clear Django session (important!)
            logout(request)
            
            response = Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
            
            # Clear  cookies explicitly
            cookies_to_clear = ['auth_token', 'sessionid', 'csrftoken']
            
            for cookie_name in cookies_to_clear:
                response.delete_cookie(cookie_name , path="/")
            
            return response
        except Exception as e:
            print(f"Logout error: {e}")
            return Response({"error": "Error during logout"}, status=status.HTTP_400_BAD_REQUEST)
 

class DoctorPatientsView(APIView):
    authentication_classes = [CookieTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Only doctors can list their patients
        if request.user.role != "doctor" or not request.user.doctor_profile.is_approved:
            return Response({"error": "Only approved doctors can view their patients."}, status=403)

        # thanks to related_name="patients"
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

