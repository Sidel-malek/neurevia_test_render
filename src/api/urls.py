# backend/api/urls.py
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from .views import (
    # Auth & Doctor
    RegisterView, CustomLoginView_2,CheckSubscriptionView, EnhancedLogoutView , CheckAuthView,
    DoctorProfileView, DoctorProfileUpdateView, PatientCreateView , DoctorPatientsView , get_patient_details,
)

urlpatterns = [
    # === Auth & Profiles ===
    path("register/", RegisterView.as_view(), name="register"),
    path('login/', CustomLoginView_2.as_view(), name='login'),
    path('logout/', EnhancedLogoutView.as_view(), name='logout'),
    path('check-auth/', CheckAuthView.as_view(), name='check-auth'),
    #path('check-auth/', check_auth, name='check-auth'),
  
    path("check-subscription/", CheckSubscriptionView.as_view(), name="check-subscription"),
     path("check-subscription/", CheckSubscriptionView.as_view(), name="check-subscription"),
    path('profile/', DoctorProfileView.as_view(), name='doctor-profile'),
    path('profile/update/', DoctorProfileUpdateView.as_view(), name='doctor-profile-update'),

    # === Patients ===
    path("patient/", PatientCreateView.as_view(), name="create-patient"),
    path("doctor/patients/", DoctorPatientsView.as_view(), name="doctor-patients"),
    path("patients/<int:patient_id>/", get_patient_details, name="patient-details"),


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
