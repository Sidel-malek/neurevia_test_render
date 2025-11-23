# api/__init__.py
default_app_config = 'api.apps.ApiConfig'

# Import signals to ensure they're registered
from django.db.models.signals import post_save
from .models import update_doctor_status_on_document_change, VerificationDocument

# Connect the signal
post_save.connect(update_doctor_status_on_document_change, sender=VerificationDocument)