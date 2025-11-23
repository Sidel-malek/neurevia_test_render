# api/serializers.py
from rest_framework import serializers
from .models import CustomUser, VerificationDocument , DoctorProfile , PatientProfile

class VerificationDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationDocument
        fields = ['doc_type', 'document']


class DoctorRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirmPassword = serializers.CharField(write_only=True)
    documents = VerificationDocumentSerializer(many=True, write_only=True)

    speciality = serializers.CharField(write_only=True)
    grade = serializers.CharField(write_only=True)
    numero_ordre = serializers.CharField(write_only=True)
    experience = serializers.CharField(write_only=True, required=False, allow_blank=True)  # Add this
    hopital = serializers.CharField(write_only=True, required=False, allow_blank=True)    # Add this

    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email',
            'password', 'confirmPassword',
            'phone', 'date_of_birth', 'gender',
            'speciality', 'grade', 'numero_ordre', 'experience', 'hopital',  # Add experience and hopital
            'documents',
        ]

    def validate(self, data):
        if data['password'] != data['confirmPassword']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        documents_data = validated_data.pop('documents', [])
        validated_data.pop('confirmPassword')

        # Extract all the doctor-specific fields
        speciality = validated_data.pop('speciality')
        grade = validated_data.pop('grade')
        numero_ordre = validated_data.pop('numero_ordre')
        experience = validated_data.pop('experience', '')  # Use get with default
        hopital = validated_data.pop('hopital', '')        # Use get with default

        # Create the user
        user = CustomUser.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            phone=validated_data.get('phone'),
            date_of_birth=validated_data.get('date_of_birth'),
            gender=validated_data.get('gender'),
            address=validated_data.get('address'),
            role="doctor"
        )

        # Create the doctor profile with the extracted values
        doctor_profile = DoctorProfile.objects.create(
            user=user,
            speciality=speciality,        # Use the extracted value
            numero_ordre=numero_ordre,    # Use the extracted value
            grade=grade,                  # Use the extracted value
            experience=experience,        # Use the extracted value
            hopital=hopital,              # Use the extracted value
            is_approved=False,
            verification_status="pending"
        )

        # Create verification documents
        for doc in documents_data:
            VerificationDocument.objects.create(
                doctor=doctor_profile,
                doc_type=doc['doc_type'],
                document=doc['document'],
            )

        return doctor_profile



class PatientSerializer(serializers.ModelSerializer):
    num_dossier = serializers.SerializerMethodField()
    patient_id = serializers.SerializerMethodField()


    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "date_of_birth",
            "gender",
            "address",
            "num_dossier",  # now works
            "patient_id",
        ]

    def get_num_dossier(self, obj):
        try:
            return obj.patient_profile.num_dossier
        except PatientProfile.DoesNotExist:
            return None
    def get_patient_id(self, obj):
        try:
           return obj.patient_profile.id
        except PatientProfile.DoesNotExist:
           return None

    def create(self, validated_data):
        request = self.context.get("request")
        doctor = getattr(request.user, "doctor_profile", None)

        # Create patient user
        user = CustomUser.objects.create(
            email=validated_data["email"],
            username=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            phone=validated_data.get("phone"),
            date_of_birth=validated_data.get("date_of_birth"),
            gender=validated_data.get("gender"),
            address=validated_data.get("address"),
            role="patient",
        )

        # Create patient profile with num_dossier
        PatientProfile.objects.create(
            user=user,
            num_dossier=f"DOS-{user.id}",
            doctor=doctor,
        )

        return user  # serializer will now also include num_dossier


# serializers.py
class PatientListSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    email = serializers.EmailField(source="user.email")
    phone = serializers.CharField(source="user.phone")
    date_of_birth = serializers.DateField(source="user.date_of_birth")
    gender = serializers.CharField(source="user.gender")
    address = serializers.CharField(source="user.address")
    primary_condition = serializers.SerializerMethodField()
    last_visit_date = serializers.SerializerMethodField()

    class Meta:
        model = PatientProfile
        fields = [
            "id",           # PatientProfile ID
            "num_dossier",
            "first_name",
            "last_name",
            "email",
            "phone",
            "date_of_birth",
            "gender",
            "address",
            "primary_condition",
            "last_visit_date"
        ]

    def get_primary_condition(self, obj):
        # Obtenir la condition principale à partir de la dernière analyse
        last_analysis = obj.analyses.order_by('-date').first()
        return last_analysis.maladie if last_analysis else "Not diagnosed"

    def get_last_visit_date(self, obj):
        # Obtenir la date de la dernière visite (dernière analyse)
        last_analysis = obj.analyses.order_by('-date').first()
        return last_analysis.date if last_analysis else None


# serializers.py

from .models import Analyse

class AnalyseSerializer(serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(queryset=PatientProfile.objects.all())
    
    class Meta:
        model = Analyse
        fields = '__all__'
        extra_kwargs = {
            'irm_original': {'required': False},
            'heatmap_img': {'required': False},
            'rapport': {'required': False},
            'probabilities': {'required': False},
        }


class PatientProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    date_of_birth = serializers.DateField(source='user.date_of_birth')
    gender = serializers.CharField(source='user.gender')
    
    class Meta:
        model = PatientProfile
        fields = ['id', 'first_name', 'last_name', 'date_of_birth', 'gender', 'num_dossier']
