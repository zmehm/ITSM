from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from accounts import views  # Import the views from your accounts app

urlpatterns = [
    # 1. API ENDPOINT FIX: This path is needed for the {% url 'get_subcategories' 0 %} tag to resolve.
    path('api/subcategories/<int:category_id>/', views.get_subcategories, name='get_subcategories'),
    
    # 2. INCIDENT LIST (Assuming this was an intentional path in your app)
    path('incident_list/', views.incident_management, name='incident_list'),
    
    # --- Existing Project Paths ---
    path('admin/', admin.site.urls),
    
    # Redirect root to login page
    path('', RedirectView.as_view(url='/login/', permanent=False)), 
    
    # URL mappings for different views
    path('login/', views.login_view, name='login'),
    path('home/', views.home, name='home'),
    path('register/', views.register_employee, name='register_employee'),
    
    # Incident creation view (Ensure this view is for creating incidents)
    path('incident_management/', views.create_incident, name='incident_management'),
    
    path('problem_management/', views.problem_management, name='problem_management'),
    path('change_management/', views.change_management, name='change_management'),
    path('service_requests/', views.service_requests, name='service_requests'),
    path('password_reset/', views.password_reset, name='password_reset'),
]
