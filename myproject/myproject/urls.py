from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView  # For redirecting
from accounts import views  # Import the views from your accounts app

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Redirect root to login page
    path('', RedirectView.as_view(url='/login/', permanent=False)),  # You can change permanent=True in production
    
    # URL mappings for different views
    path('login/', views.login_view, name='login'),
    path('home/', views.home, name='home'),
    path('register/', views.register_employee, name='register_employee'),
    path('incident_management/', views.incident_management, name='incident_management'),
    path('problem_management/', views.problem_management, name='problem_management'),
    path('change_management/', views.change_management, name='change_management'),
    path('service_requests/', views.service_requests, name='service_requests'),
    path('password_reset/', views.password_reset, name='password_reset'),
]
