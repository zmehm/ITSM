# myproject/urls.py
from django.contrib import admin
from django.urls import path
from accounts import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.login_view, name='login'),
    path('home/', views.home, name='home'),
    path('register/', views.register_employee, name='register_employee'),
    path('incident_management/', views.incident_management, name='incident_management'),
    path('problem_management/', views.problem_management, name='problem_management'),
    path('change_management/', views.change_management, name='change_management'),
    path('service_requests/', views.service_requests, name='service_requests'),
    path('password_reset/', views.password_reset, name='password_reset'),
]
