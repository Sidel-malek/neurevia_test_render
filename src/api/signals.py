from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import VerificationDocument, DoctorProfile

def update_doctor_status(doctor: DoctorProfile):
    docs = doctor.documents.all()

    if not docs.exists():
        doctor.is_approved = False
        doctor.verification_status = "pending"
    elif all(doc.status == "approved" for doc in docs):
        doctor.is_approved = True
        doctor.verification_status = "approved"
    elif any(doc.status == "rejected" for doc in docs):
        doctor.is_approved = False
        doctor.verification_status = "rejected"
    else:
        doctor.is_approved = False
        doctor.verification_status = "pending"

    doctor.save()


@receiver(post_save, sender=VerificationDocument)
@receiver(post_delete, sender=VerificationDocument)
def update_doctor_on_document_change(sender, instance, **kwargs):
    update_doctor_status(instance.doctor)
