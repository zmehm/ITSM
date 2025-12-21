from django.urls import path
from django.views.generic import RedirectView
from . import views 

urlpatterns = [
    # --- 1. AUTHENTICATION & UTILITY PATHS ---
    path('login/', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout_view'),
    path('register/', views.register_employee, name='register_employee'),
    path('password_reset/', views.password_reset, name='password_reset'),

    # API ENDPOINT FOR AJAX DROPDOWN
    path('api/subcategories/<int:category_id>/', views.get_subcategories, name='get_subcategories'),

    # --- 2. ROLE-BASED DASHBOARDS ---
    path('home/', views.home, name='home'), 
    path('dashboard/user/', views.user_dashboard, name='user_dashboard'),
    path('dashboard/support/', views.support_dashboard, name='support_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),


    # --- 3. INCIDENT MODULES (ITSM) ---
    
    # User path to create a new incident
    path('incident/create/', views.create_incident, name='create_incident'), 
    
    # User path to LIST all their incidents (Assuming you create a dedicated view for this)
    # NOTE: You will need to create the view: views.incident_list_view
    path('incident/my_list/', views.incident_list_view, name='incident_list'), 
    
    # Detail view for a specific incident (Assumes you rename incident_management to incident_detail_view)
    # NOTE: You will need to create the view: views.incident_detail_view
    path('incident/<int:incident_id>/detail/', views.incident_detail_view, name='incident_detail'), 


    # --- 4. CORE WORKFLOW PATHS (IT Support & Feedback) ---

    path('incident/<int:incident_id>/take/', views.take_incident, name='take_incident'),
    path('incident/<int:incident_id>/resolve/', views.resolve_incident, name='resolve_incident'),
    path('incident/<int:incident_id>/feedback/', views.submit_feedback, name='submit_feedback'),


    # --- 5. STUB PATHS (Remaining ITSM Modules) ---
    path('problem_management/', views.problem_management, name='problem_management'), 
    path('change_management/', views.change_management, name='change_management'), 
    path('service_requests/', views.service_requests, name='service_requests'), 

    path('tickets/unassigned/', views.unassigned_queue_view, name='unassigned_queue'),
    path('tickets/my-active/', views.my_active_tickets_view, name='my_active_tickets'),
    path('tickets/feedback/', views.feedback_queue_view, name='feedback_queue'),

    path('sla_management/', views.sla_management, name='sla_management'),
    path('asset_management/', views.asset_management, name='asset_management'),
    path('problem-management/', views.problem_management, name='problem_management'),
    path('change-management/', views.change_management, name='change_management'),
]