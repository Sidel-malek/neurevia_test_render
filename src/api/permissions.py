# backend/api/permissions.py
from rest_framework.permissions import BasePermission

class IsApprovedUser(BasePermission):
    """
    Autorise uniquement les utilisateurs approuvés
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.doctor_profile.is_approved
        )