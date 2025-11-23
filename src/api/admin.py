# api/admin.py
from django.contrib import admin
from .models import CustomUser, VerificationDocument, DoctorProfile , Abonnement, Paiement
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
 
from django.contrib.auth.admin import UserAdmin

import logging
logger = logging.getLogger(__name__)

# Action personnalisée pour activer les abonnements
def activate_subscription(modeladmin, request, queryset):
    queryset.update(statut='active')
activate_subscription.short_description = "Activer les abonnements sélectionnés"

# Action personnalisée pour expirer les abonnements
def expire_subscription(modeladmin, request, queryset):
    queryset.update(statut='expired')
expire_subscription.short_description = "Marquer comme expiré"

# Action personnalisée pour suspendre les abonnements
def suspend_subscription(modeladmin, request, queryset):
    queryset.update(statut='suspended')
suspend_subscription.short_description = "Suspendre les abonnements"

# Filtre personnalisé pour le statut d'abonnement
class SubscriptionStatusFilter(admin.SimpleListFilter):
    title = 'Statut personnalisé'
    parameter_name = 'custom_status'
    
    def lookups(self, request, model_admin):
        return (
            ('active', 'Actifs'),
            ('expired', 'Expirés'),
            ('no_end_date', 'Sans date de fin'),
        )
    
    def queryset(self, request, queryset):
        from django.utils import timezone
        from django.db.models import Q
        
        if self.value() == 'active':
            return queryset.filter(statut='active')
        elif self.value() == 'expired':
            return queryset.filter(Q(statut='expired') | Q(date_fin__lt=timezone.now().date()))
        elif self.value() == 'no_end_date':
            return queryset.filter(date_fin__isnull=True)
        return queryset

# Admin pour le modèle Abonnement
@admin.register(Abonnement)
class AbonnementAdmin(admin.ModelAdmin):
    list_display = ('doctor_name', 'type', 'statut', 'date_debut', 'date_fin', 'prix', 'days_remaining')
    list_filter = (SubscriptionStatusFilter, 'type', 'statut', 'date_debut')
    search_fields = ('doctor__user__first_name', 'doctor__user__last_name', 'doctor__user__email')
    list_editable = ('statut', 'type', 'prix')
    date_hierarchy = 'date_debut'
    actions = [activate_subscription, expire_subscription, suspend_subscription]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('doctor__user')
    
    def doctor_name(self, obj):
        return f"Dr. {obj.doctor.user.get_full_name() or obj.doctor.user.email}"
    doctor_name.short_description = 'Médecin'
    doctor_name.admin_order_field = 'doctor__user__last_name'
    
    def days_remaining(self, obj):
        if obj.date_fin:
            remaining = (obj.date_fin - timezone.now().date()).days
            if remaining > 0:
                return f"{remaining} jours"
            elif remaining == 0:
                return "Aujourd'hui"
            else:
                return f"Expiré ({abs(remaining)} jours)"
        return "Pas de date fin"
    days_remaining.short_description = 'Jours restants'
    
    fieldsets = (
        ('Informations Médecin', {
            'fields': ('doctor',)
        }),
        ('Détails Abonnement', {
            'fields': ('type', 'statut', 'prix', 'mode_paiement')
        }),
        ('Période', {
            'fields': ('date_debut', 'date_fin')
        }),
    )

# Admin pour le modèle Paiement
@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('abonnement_display', 'montant', 'date_paiement', 'statut', 'mode_paiement', 'reference_trans')
    list_filter = ('statut', 'mode_paiement', 'date_paiement')
    search_fields = ('abonnement__doctor__user__first_name', 'abonnement__doctor__user__last_name', 'reference_trans')
    
    def abonnement_display(self, obj):
        return f"{obj.abonnement.doctor.user.get_full_name()} - {obj.abonnement.type}"
    abonnement_display.short_description = 'Abonnement'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('abonnement__doctor__user')


# Admin personnalisé pour CustomUser
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'phone', 'date_of_birth', 'gender')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
        ('Adresse', {'fields': ('address',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'role'),
        }),
    )

# Enregistrer CustomUser avec l'admin personnalisé (sans unregister)
admin.site.register(CustomUser, CustomUserAdmin)

# Personnalisation du titre de l'admin
admin.site.site_header = "Administration MedicalAI"
admin.site.site_title = "MedicalAI Admin"
admin.site.index_title = "Gestion de la plateforme MedicalAI"






from .models import PatientProfile, Analyse


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "doctor_display")
    search_fields = ("user__first_name", "user__last_name", "user__email")
    list_filter = ("doctor",)
    
    def full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    full_name.short_description = "Nom complet"
    
    def email(self, obj):
        return obj.user.email
    email.short_description = "Email"
    
    def doctor_display(self, obj):
        return f"Dr. {obj.doctor.user.get_full_name()}" if obj.doctor else "—"
    doctor_display.short_description = "Médecin"


@admin.register(Analyse)
class AnalyseAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "maladie", "type_analyse", "result", "confidence", "date", "rapport_link")
    list_filter = ("maladie", "type_analyse", "date")
    search_fields = ("patient__user__first_name", "patient__user__last_name", "patient__user__email", "result")
    date_hierarchy = "date"
    
    def rapport_link(self, obj):
        if obj.rapport:
            return format_html('<a href="{}" target="_blank">📄 Voir PDF</a>', obj.rapport.url)
        return "—"
    rapport_link.short_description = "Rapport"



class VerificationDocumentInline(admin.TabularInline):
    model = VerificationDocument
    extra = 0
    fields = ("document", "doc_type", "status", "comment", "reviewed_by", "uploaded_at")
    readonly_fields = ("uploaded_at",)



# admin.py - Update the DoctorProfileAdmin
@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'speciality', 'is_approved', 'verification_status', 
                   'documents_status', 'abonnements_count')
    list_filter = ('is_approved', 'verification_status', 'speciality')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    readonly_fields = ('is_approved', 'verification_status', 'documents_status_display')
    inlines = [VerificationDocumentInline]
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def documents_status(self, obj):
        docs = obj.documents.all()
        if not docs.exists():
            return "No documents"
        
        approved = sum(1 for d in docs if d.status == 'approved')
        pending = sum(1 for d in docs if d.status == 'pending')
        rejected = sum(1 for d in docs if d.status == 'rejected')
        
        return f"{approved}✓ {pending}⏳ {rejected}✗"
    documents_status.short_description = 'Documents Status'
    
    def documents_status_display(self, obj):
        docs = obj.documents.all()
        if not docs.exists():
            return "No documents uploaded"
        
        status_html = "<ul>"
        for doc in docs:
            status_icon = "⏳" if doc.status == "pending" else "✓" if doc.status == "approved" else "✗"
            status_html += f'<li>{status_icon} {doc.doc_type or "Document"}: {doc.get_status_display()}</li>'
        status_html += "</ul>"
        
        return format_html(status_html)
    documents_status_display.short_description = "Documents Details"
    
    def abonnements_count(self, obj):
        count = obj.abonnements.count()
        url = reverse('admin:api_abonnement_changelist') + f'?doctor__id__exact={obj.id}'
        return format_html('<a href="{}">{} abonnement(s)</a>', url, count)
    abonnements_count.short_description = 'Abonnements'
    
    fieldsets = (
        (None, {
            'fields': ('user', 'speciality', 'numero_ordre', 'grade', 'experience', 'hopital')
        }),
        ('Verification Status', {
            'fields': ('is_approved', 'verification_status', 'documents_status_display')
        }),
    )

@admin.register(VerificationDocument)
class VerificationDocumentAdmin(admin.ModelAdmin):
    list_display = ['doctor_info', 'doc_type', 'status_badge', 'uploaded_at', 'reviewed_by_info', 'document_link']
    list_filter = ['status', 'doc_type', 'uploaded_at']
    search_fields = ['doctor__user__email', 'doctor__user__first_name', 'doctor__user__last_name']
    readonly_fields = ['uploaded_at', 'document_preview', 'doctor', 'document', 'doc_type', 'reviewed_by']
    actions = ['approve_documents', 'reject_documents']

    # Doctor info
    def doctor_info(self, obj):
        return f"Dr. {obj.doctor.user.first_name} {obj.doctor.user.last_name} ({obj.doctor.user.email})"
    doctor_info.short_description = "Doctor"

    # Status badge
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'approved': 'green', 
            'rejected': 'red'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 12px;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )
    status_badge.short_description = "Status"

    # Reviewed by info
    def reviewed_by_info(self, obj):
        return obj.reviewed_by.email if obj.reviewed_by else "Not reviewed"
    reviewed_by_info.short_description = "Reviewed By"

    # Document link
    def document_link(self, obj):
        if obj.document:
            return format_html('<a href="{}" target="_blank">📄 View</a>', obj.document.url)
        return "No document"
    document_link.short_description = "Document"

    # Preview
    def document_preview(self, obj):
        if obj.document:
            return format_html(
                '<a href="{}" target="_blank">📋 Download/View</a><br>'
                '<iframe src="{}" width="100%" height="500px" style="border:1px solid #ccc;"></iframe>',
                obj.document.url, obj.document.url
            )
        return "No document"
    document_preview.short_description = "Document Preview"

     # ---- Admin actions ----
    def approve_documents(self, request, queryset):
        for doc in queryset:
            doc.status = 'approved'
            doc.reviewed_by = request.user
            doc.save()  # This will trigger the signal and send email
        self.message_user(request, "Selected documents have been approved. Emails sent to doctors.")
    
    def reject_documents(self, request, queryset):
        for doc in queryset:
            doc.status = 'rejected'
            doc.reviewed_by = request.user
            if not doc.comment:
                doc.comment = "Document rejected. Please upload a valid document."
            doc.save()  # This will trigger the signal and send email
        self.message_user(request, "Selected documents have been rejected. Emails sent to doctors.")
    
    # Allow changing documents to trigger status updates
    def has_change_permission(self, request, obj=None):
        return True
    
    # ---- NOUVELLE MÉTHODE AJOUTÉE ----
    def save_model(self, request, obj, form, change):
        """
        Surcharge la méthode save pour s'assurer que les emails sont envoyés
        quand on modifie manuellement dans l'admin
        """
        # Sauvegarder d'abord l'objet
        super().save_model(request, obj, form, change)
        
        # Forcer la vérification du statut du docteur
        obj.doctor.check_approval_status()
        
        # Envoyer l'email si le statut a changé
        if change and 'status' in form.changed_data:
            self.send_status_email(obj, form.cleaned_data['status'])
    
    def send_status_email(self, document, new_status):
        """
        Envoyer manuellement l'email de changement de statut
        """
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        from django.conf import settings
        
        doctor = document.doctor
        doctor_email = doctor.user.email
        doctor_name = f"{doctor.user.first_name} {doctor.user.last_name}"
        
        # Déterminer le template en fonction du statut
        if new_status == 'approved':
            subject = "Votre document a été approuvé - Neurevia"
            template_name = "emails/document_approved.html"
        elif new_status == 'rejected':
            subject = "Votre document a été rejeté - Neurevia"
            template_name = "emails/document_rejected.html"
        else:
            return
        
        # Construire le contexte
        context = {
            'doctor_name': doctor_name,
            'document_type': document.doc_type or "Document de vérification",
            'comment': document.comment
        }
        
        try:
            # Render HTML content
            html_content = render_to_string(template_name, context)
            text_content = strip_tags(html_content)
            
            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[doctor_email]
            )
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            email.send()
            print(f"✅ Email envoyé à {doctor_email}")
        except Exception as e:
            print(f"❌ Erreur envoi email: {e}")
    
    # ---- FIN DE LA NOUVELLE MÉTHODE ----