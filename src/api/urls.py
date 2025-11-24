# backend/api/urls.py
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from .views import (
    # Auth & Doctor
    RegisterView, CustomLoginView_2,CheckAuthView,CheckSubscriptionView, EnhancedLogoutView , CheckAuthView
)

urlpatterns = [
    # === Auth & Profiles ===
    path("register/", RegisterView.as_view(), name="register"),
    path('login/', CustomLoginView_2.as_view(), name='login'),
    path('logout/', EnhancedLogoutView.as_view(), name='logout'),
    path('check-auth/', CheckAuthView.as_view(), name='check-auth'),
    #path('check-auth/', check_auth, name='check-auth'),
  
    path("check-subscription/", CheckSubscriptionView.as_view(), name="check-subscription"),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
