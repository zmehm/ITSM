# accounts/urls.py

from django.urls import path
from django.views.generic import RedirectView
from . import views 

urlpatterns = [
    # AUTHENTICATION PATHS (Standardized Names)
    # The URL paths are defined here
    path('login/', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout_view'),
    path('register/', views.register_employee, name='register_employee'),
    path('password_reset/', views.password_reset, name='password_reset'),

    # APPLICATION PATHS
    path('home/', views.home, name='home'), 
    
    # ITSM Modules
    path('incident_management/', views.create_incident, name='create_incident'), 
    path('incident_list/', views.incident_management, name='incident_list'), 
    path('problem_management/', views.problem_management, name='problem_management'), 
    path('change_management/', views.change_management, name='change_management'), 
    path('service_requests/', views.service_requests, name='service_requests'), 
    
    # API ENDPOINT FOR AJAX DROPDOWN
    path('api/subcategories/<int:category_id>/', views.get_subcategories, name='get_subcategories'),
]