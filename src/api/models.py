from django.db import models
from django.contrib.auth.models import AbstractUser

# --------------------
# USER DE BASE (PERSONNE + LOGIN)
# --------------------
class CustomUser(AbstractUser):
    ROLES = (
        ('doctor', 'Doctor'),
        ('admin', 'Admin'),
        ('patient', 'Patient'),
        ('researcher', 'Researcher'),
    )
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLES)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.email} ({self.role})"


# --------------------
# DOCTOR
# --------------------
class DoctorProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="doctor_profile")
    speciality = models.CharField(max_length=100)
    numero_ordre = models.CharField(max_length=50)
    grade = models.CharField(max_length=50)
    experience = models.TextField(blank=True, null=True)
    hopital = models.CharField(max_length=100, blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="pending"
    )

    def check_approval_status(self):
        """Check if all documents are approved and update status accordingly"""
        documents = self.documents.all()
        
        if not documents.exists():
            # No documents uploaded yet
            self.is_approved = False
            self.verification_status = "pending"
            self.save()
            return False
            
        if all(doc.status == "approved" for doc in documents):
            # All documents approved
            self.is_approved = True
            self.verification_status = "approved"
            self.save()
            return True
        elif any(doc.status == "rejected" for doc in documents):
            # At least one document rejected
            self.is_approved = False
            self.verification_status = "rejected"
            self.save()
            return False
        else:
            # Some documents still pending
            self.is_approved = False
            self.verification_status = "pending"
            self.save()
            return False
    
    def __str__(self):
        return f"Doctor {self.user.first_name} {self.user.last_name}"

    

# --------------------
# PATIENT
# --------------------
class PatientProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="patient_profile")
    num_dossier = models.CharField(max_length=50, unique=True)
    # Chaque patient est suivi par UN médecin (mais un médecin peut avoir plusieurs patients)
    doctor = models.ForeignKey(
        "DoctorProfile",
        on_delete=models.CASCADE,
        related_name="patients",
        null=True,
    )

    def __str__(self):
        return f"Patient {self.user.first_name} {self.user.last_name}"


# --------------------
# VERIFICATION DOCUMENT
# --------------------
class VerificationDocument(models.Model):
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name="documents")
    document = models.FileField(upload_to="verification_documents/")
    doc_type = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[('pending','Pending'),('approved','Approved'),('rejected','Rejected')],
        default='pending'
    )
    comment = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        limit_choices_to={'role':'admin'}, related_name="reviewed_docs"
    )

    def __str__(self):
        return f"Doc {self.id} for {self.doctor.user.email} - {self.status}"


# --------------------
# ANALYSE
# --------------------

class Analyse(models.Model):
    ANALYSE_TYPES = [
        ("MRI", "IRM"),
        ("BIOMARKER", "Biomarkers"),
        ("COMBINED_ALZ", "MRI + Biomarkers"),
        ("DATSCAN","DaTscan"),
        ("COMBINED_PARK","DaTscan + Biomarkers"),
        ("CLINICAL_DATA", "Clinical data"),

        
    ]

    patient = models.ForeignKey(
        "PatientProfile",
        on_delete=models.CASCADE,
        related_name="analyses"
    )
    doctor = models.ForeignKey(
        "DoctorProfile",
        on_delete=models.CASCADE,
        related_name="analyses",
        null=True
    )

    date = models.DateField(auto_now_add=True)
    type_analyse = models.CharField(max_length=20, choices=ANALYSE_TYPES, default="MRI")
    maladie = models.CharField(max_length=100, default="Alzheimer")

    # --- IRM ---
    irm_original = models.ImageField(upload_to="irm/", blank=True, null=True)
    heatmap_img = models.ImageField(upload_to="heatmaps/", blank=True, null=True)

    # --- Biomarqueurs ---
    biomarkers = models.JSONField(blank=True, null=True)

    # --- Résultats IA ---
    result = models.CharField(max_length=50, blank=True, null=True)
    confidence = models.FloatField(blank=True, null=True)
    probabilities = models.JSONField(blank=True, null=True)  # {AD: xx, CN: xx, ...}

    # --- Diagnostic & Rapport ---
    diagnostic = models.TextField(blank=True, null=True)  # résumé IA
    rapport = models.FileField(upload_to="rapports/", blank=True, null=True)

    # --- Notes du médecin ---
    doctor_notes = models.TextField(blank=True, null=True)

    # --- Visualisations XAI ---
    xai_biomarkers = models.ImageField(upload_to="xai_biomarkers/", blank=True, null=True)
    # --- Valeurs SHAP en JSON
    shap_values = models.JSONField(blank=True, null=True)


    def __str__(self):
        return f"{self.get_type_analyse_display()} - {self.maladie} ({self.result})"

# --------------------
# ABONNEMENT
# --------------------
class Abonnement(models.Model):
    TYPES = [('FreeTrial','Free Trial'),('Normal','Normal'),('Premium','Premium'),('PayPerScan','Pay Per Scan')]
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name="abonnements")
    type = models.CharField(max_length=20, choices=TYPES)
    mode_paiement = models.CharField(max_length=50)
    date_debut = models.DateField()
    date_fin = models.DateField(blank=True, null=True)
    statut = models.CharField(max_length=20, default="active")
    prix = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.type} - {self.doctor.user.email}"


# --------------------
# PAIEMENT
# --------------------
class Paiement(models.Model):
    abonnement = models.ForeignKey(Abonnement, on_delete=models.CASCADE, related_name="paiements")
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_paiement = models.DateTimeField(auto_now_add=True)
    mode_paiement = models.CharField(max_length=50)
    statut = models.CharField(max_length=20, default="en_attente")
    reference_trans = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"Paiement {self.id} - {self.montant}€"





























"""______________________________________________________________________________________
                                        Signals
__________________________________________________________________________________________"""




# models.py - Add at the bottom of the file
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse

# models.py - ajoutez cette fonction AVANT le signal

def send_email_to_doctor(subject, template_name, context, to_email):
    """
    Fonction utilitaire pour envoyer des emails avec templates en dur
    """
    try:
        # Templates en dur pour éviter les problèmes de chemin
        templates = {
            'emails/document_approved.html': f"""
            <!DOCTYPE html>
            <html><body>
                <h2>Document Approuvé</h2>
                <p>Cher Dr. {context.get('doctor_name', '')},</p>
                <p>Votre document <strong>{context.get('document_type', '')}</strong> a été approuvé.</p>
                {f"<p><strong>Commentaire:</strong> {context.get('comment', '')}</p>" if context.get('comment') else ""}
            </body></html>
            """,
            
            'emails/document_rejected.html': f"""
            <!DOCTYPE html>
            <html><body>
                <h2>Document Rejeté</h2>
                <p>Cher Dr. {context.get('doctor_name', '')},</p>
                <p>Votre document <strong>{context.get('document_type', '')}</strong> a été rejeté.</p>
                {f"<p><strong>Commentaire:</strong> {context.get('comment', '')}</p>" if context.get('comment') else ""}
                <p>Veuillez uploader un nouveau document.</p>
            </body></html>
            """,
            
            'emails/doctor_fully_approved.html': f"""
            <!DOCTYPE html>
            <html><body>
                <h2>Félicitations ! Compte Activé</h2>
                <p>Cher Dr. {context.get('doctor_name', '')},</p>
                <p>Votre compte Neurevia est maintenant <strong>entièrement approuvé</strong> !</p>
                <p>Connectez-vous : <a href="{context.get('login_url', '')}">{context.get('login_url', '')}</a></p>
            </body></html>
            """,
            
            'emails/document_comment.html': f"""
            <!DOCTYPE html>
            <html><body>
                <h2>Nouveau Commentaire</h2>
                <p>Cher Dr. {context.get('doctor_name', '')},</p>
                <p>Un commentaire a été ajouté à votre document <strong>{context.get('document_type', '')}</strong> (Status: {context.get('status', '')}).</p>
                <p><strong>Commentaire:</strong> {context.get('comment', '')}</p>
            </body></html>
            """
        }
        
        # Récupérer le template en dur
        html_content = templates.get(template_name, f"<p>Email: {subject}</p>")
        text_content = strip_tags(html_content)
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email]
        )
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send()
        print(f"✅ Email envoyé à {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur envoi email: {e}")
        return False
    

@receiver(post_save, sender=VerificationDocument)
def update_doctor_status_on_document_change(sender, instance, created, **kwargs):
    """Update doctor approval status when a document is saved and send email"""
    
    print(f"📨 Signal déclenché pour document {instance.id}, créé: {created}")
    
    # Skip if this is a new creation (not an update)
    if created:
        print("➡️ Nouveau document, skip email")
        return
    
    # Get the previous state to check if status changed
    try:
        old_instance = VerificationDocument.objects.get(pk=instance.pk)
        status_changed = old_instance.status != instance.status
        comment_changed = old_instance.comment != instance.comment
        print(f"🔄 Status changé: {status_changed}, Comment changé: {comment_changed}")
    except VerificationDocument.DoesNotExist:
        status_changed = True
        comment_changed = True
        print("⚠️ Document précédent non trouvé")
    
    # Update doctor status
    doctor = instance.doctor
    previous_approved_status = doctor.is_approved
    doctor.check_approval_status()
    
    print(f"👨‍⚕️ Docteur {doctor.user.email}, précédemment approuvé: {previous_approved_status}, maintenant: {doctor.is_approved}")
    
    # Send email notifications based on changes
    doctor_email = doctor.user.email
    doctor_name = f"{doctor.user.first_name} {doctor.user.last_name}"
    
    # Send email if status changed to approved
    if status_changed and instance.status == 'approved':
        print("✅ Envoi email d'approbation")
        send_email_to_doctor(
            subject="Votre document a été approuvé - Neurevia",
            template_name="emails/document_approved.html",
            context={
                'doctor_name': doctor_name,
                'document_type': instance.doc_type or "Document de vérification",
                'comment': instance.comment
            },
            to_email=doctor_email
        )
    
    # Send email if status changed to rejected
    elif status_changed and instance.status == 'rejected':
        print("❌ Envoi email de rejet")
        send_email_to_doctor(
            subject="Votre document a été rejeté - Neurevia",
            template_name="emails/document_rejected.html",
            context={
                'doctor_name': doctor_name,
                'document_type': instance.doc_type or "Document de vérification",
                'comment': instance.comment
            },
            to_email=doctor_email
        )
    
    # Send email if comment was added/changed (without status change)
    elif comment_changed and instance.comment and not status_changed:
        print("💬 Envoi email de commentaire")
        status_display = "Approuvé" if instance.status == 'approved' else "Rejeté" if instance.status == 'rejected' else "En attente"
        
        send_email_to_doctor(
            subject=f"Commentaire ajouté à votre document {status_display} - Neurevia",
            template_name="emails/document_comment.html",
            context={
                'doctor_name': doctor_name,
                'document_type': instance.doc_type or "Document de vérification",
                'status': status_display,
                'comment': instance.comment
            },
            to_email=doctor_email
        )
    
    # Send congratulatory email if doctor just became fully approved
    if not previous_approved_status and doctor.is_approved:
        print("🎉 Envoi email de félicitations pour approbation complète")
        login_url = f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/auth"
        send_email_to_doctor(
        subject="Félicitations ! Votre compte Neurevia est entièrement approuvé",
        template_name="emails/doctor_fully_approved.html",  # ← NOM COURT!
        context={
            'doctor_name': doctor_name,
            'login_url': login_url
        },
        to_email=doctor_email
    )
        



