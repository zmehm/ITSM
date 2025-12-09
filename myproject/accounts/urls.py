from django.contrib import admin
from django.urls import path
from accounts import views  # Import your views module

urlpatterns = [
    # API ENDPOINT FOR AJAX DROPDOWN (Only with category_id)
    path('api/subcategories/<int:category_id>/', views.get_subcategories, name='get_subcategories'),

    # AUTHENTICATION PATHS
    path('admin/', admin.site.urls),  # Admin URL
    path('login/', views.login_view, name='login'),  # Login view
    path('logout/', views.logout_view, name='logout'),  # Logout view
    path('register/', views.register_employee, name='register_employee'),  # Registration view
    path('password_reset/', views.password_reset, name='password_reset'),  # Password Reset

    # APPLICATION PATHS
    path('home/', views.home, name='home'),  # Home page (with profile completion alert)
    path('incident_management/', views.create_incident, name='incident_management'),  # Incident Creation View (kept as is)
    path('incident_list/', views.incident_management, name='incident_list'),  # Assuming this is your list view
    path('problem_management/', views.problem_management, name='problem_management'),  # Problem Management
    path('change_management/', views.change_management, name='change_management'),  # Change Management
    path('service_requests/', views.service_requests, name='service_requests'),  # Service Requests
]
