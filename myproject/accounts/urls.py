from django.urls import path
from . import views 

urlpatterns = [
    # --- 1. AUTHENTICATION & UTILITY PATHS ---
    path('login/', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout_view'),
    path('register/', views.register_employee, name='register_employee'),
    path('password_reset/', views.password_reset, name='password_reset'),
    path('api/subcategories/<int:category_id>/', views.get_subcategories, name='get_subcategories'),

    # --- 2. ROLE-BASED DASHBOARDS ---
    path('home/', views.home, name='home'), 
    path('dashboard/user/', views.user_dashboard, name='user_dashboard'),
    path('dashboard/support/', views.support_dashboard, name='support_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),

    # --- 3. INCIDENT MODULES ---
    path('incident/create/', views.create_incident, name='create_incident'), 
    path('incident/my_list/', views.incident_list_view, name='incident_list'), 
    path('incident/<int:incident_id>/detail/', views.incident_detail_view, name='incident_detail'), 

    # --- 4. CORE WORKFLOW ---
    path('incident/<int:incident_id>/take/', views.take_incident, name='take_incident'),
    path('incident/<int:incident_id>/resolve/', views.resolve_incident, name='resolve_incident'),
    path('incident/<int:incident_id>/feedback/', views.submit_feedback, name='submit_feedback'),

    # --- 5. ITSM MODULES (Unique Names) ---
    path('problem_management/', views.problem_management, name='problem_management'), 
    path('change_management/', views.change_management, name='change_management'), 
    path('service_requests/', views.service_requests, name='service_requests'), 
    path('sla_management/', views.sla_management, name='sla_management'),
    path('asset_management/', views.asset_management, name='asset_management'),

    # --- 6. QUEUES ---
    path('tickets/unassigned/', views.unassigned_queue_view, name='unassigned_queue'),
    path('tickets/my-active/', views.my_active_tickets_view, name='my_active_tickets'),
    path('tickets/feedback/', views.feedback_queue_view, name='feedback_queue'),

    # --- 7. ADMIN & OVERSIGHT ---
    path('vendors/', views.vendor_management, name='vendor_management'),
    path('security/', views.security_center, name='security_center'),
    path('backups/', views.backup_management, name='backup_management'),
    path('audit/', views.audit_trail, name='audit_trail'),
    path('tracker/incidents/', views.incident_tracker, name='incident_tracker'),
    path('tracker/technicians/', views.tech_tracking, name='tech_tracking'),
    path('oversight/support/', views.support_oversight, name='support_oversight'), # Renamed slightly to avoid conflict
    path('incident/tracking/', views.incident_tracking_view, name='incident_tracking'),
    path('login-monitor/', views.login_monitor_dashboard, name='login_monitor'),
    path('login-monitor/', views.login_monitor_dashboard, name='login_monitor'),
    path('profile/', views.profile_view, name='profile_view'),
    path('chatbot-api/', views.flashbot_logic, name='chatbot_api'),
    path('admin-approvals/', views.admin_approval_monitor, name='admin_approval_monitor'),
    path('approve-user/<int:user_id>/', views.approve_user, name='approve_user'),
]