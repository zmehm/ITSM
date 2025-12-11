# myproject/urls.py (FINAL CORRECTED VERSION)

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from accounts import views 

# CRITICAL IMPORTS for serving media files in development
from django.conf import settings
from django.conf.urls.static import static 

urlpatterns = [
    # API ENDPOINT
    path('api/subcategories/<int:category_id>/', views.get_subcategories, name='get_subcategories'),
    
    # --- Project Core Paths ---
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/login/', permanent=False)), 
    
    # --- Accounts App Paths ---
    path('login/', views.login_view, name='login_view'), # Renamed for clarity if you need a specific name
    path('logout/', views.logout_view, name='logout_view'), # Added logout path for completeness
    path('home/', views.home, name='home'),
    path('register/', views.register_employee, name='register_employee'),
    path('password_reset/', views.password_reset, name='password_reset'),
    
    # --- ITSM Paths ---
    path('incident_management/', views.create_incident, name='create_incident'), # Renamed for clarity
    path('incident_list/', views.incident_management, name='incident_list'), 
    path('problem_management/', views.problem_management, name='problem_management'),
    path('change_management/', views.change_management, name='change_management'),
    path('service_requests/', views.service_requests, name='service_requests'),
]

# CRITICAL FIX: Only serve media files if DEBUG is True (development)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)