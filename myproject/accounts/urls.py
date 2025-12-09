from django.contrib import admin
from django.urls import path
from accounts import views # Import your views module

urlpatterns = [
 path('admin/', admin.site.urls), # Admin URL
 path('login/', views.login_view, name='login'), # Login view
 path('logout/', views.logout_view, name='logout'), # <-- ADDED LOGOUT URL
 path('home/', views.home, name='home'), # Home page (with profile completion alert)
 path('register/', views.register_employee, name='register_employee'), # Registration view
 path('incident_management/', views.incident_management, name='incident_management'), # Incident Management
 path('problem_management/', views.problem_management, name='problem_management'), # Problem Management
 path('change_management/', views.change_management, name='change_management'), # Change Management
 path('service_requests/', views.service_requests, name='service_requests'), # Service Requests
 path('password_reset/', views.password_reset, name='password_reset'),# Password Reset
]