from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model
from django.db import IntegrityError 
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import never_cache
from django.utils import timezone
from django.db.models import Q 
from datetime import timedelta

# --- Email and Template Imports ---
from django.template.loader import render_to_string 
from django.core.mail import EmailMessage

# --- Local Imports ---
from .forms import (
    EmployeeRegistrationForm, ProfileCompletionForm, 
    IncidentForm, FeedbackForm, ServiceRequestForm
)
from .models import (
    Category, SubCategory, Incident, TicketFeedback, 
    IncidentTracking, ServiceRequest, SLAManagement, Asset,
    ProblemManagement, ProblemCase, RootCauseCat, RcSubcat,Vendor, SecurityManagement, BackupManagement, AuditManagement
)

User = get_user_model() 

# =====================================================================
# 0. UTILITY FUNCTIONS & ROLE CHECK
# =====================================================================

def format_ticket_count(count, limit=1000):
    if count >= limit:
        return f"{limit:,.0f}+"
    return str(count)

def role_required(role):
    def decorator(view_func):
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'role') or request.user.role != role:
                messages.error(request, "Access denied. You do not have permission to view this page.")
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def is_support(user):
    return user.is_authenticated and user.role == 'IT_SUPPORT'

def get_subcategories(request, category_id):
    subcategories = SubCategory.objects.filter(category_id=category_id, active=True).values('id', 'name')
    data = {subcat['id']: subcat['name'] for subcat in subcategories}
    return JsonResponse(data)


# =====================================================================
# 1. AUTHENTICATION & GLOBAL VIEWS
# =====================================================================

def register_employee(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save() 
                login(request, user)
                messages.success(request, f"Registration successful! Your Employee ID is {user.EmpID}.")
                return redirect('home')
            except IntegrityError:
                messages.error(request, "Registration failed due to a database constraint.")
            except Exception as e:
                messages.error(request, f"An unexpected error occurred: {str(e)}")
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = EmployeeRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username_email = request.POST.get('username_email')
        password = request.POST.get('password')
        user = authenticate(request, username=username_email, password=password)
        if user is not None and user.is_active:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'accounts/login.html')

@never_cache 
def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "You have been logged out successfully.")
    return redirect('login_view')

def password_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(request=request)
            messages.success(request, "Password reset instructions sent.")
            return redirect('login_view')
    else:
        form = PasswordResetForm()
    return render(request, 'accounts/password_reset.html', {'form': form})


# =====================================================================
# 2. ROLE-BASED LANDING PAGE (CENTRAL HOME ROUTER)
# =====================================================================

@login_required
def home(request):
    if not request.user.Dept or not request.user.Grade or not request.user.Subsidiary:
        if request.method == 'POST':
            form = ProfileCompletionForm(request.POST, instance=request.user) 
            if form.is_valid():
                form.save()
                messages.success(request, "Profile completed successfully!")
                return redirect('home') 
        else:
            form = ProfileCompletionForm(instance=request.user)
        messages.info(request, "Please complete your mandatory profile information.")
        return render(request, 'accounts/home.html', {'form': form, 'profile_incomplete': True})

    if request.user.role == 'ADMIN':
        return redirect('admin_dashboard')
    elif request.user.role == 'IT_SUPPORT':
        return redirect('support_dashboard')
    else: 
        return redirect('user_dashboard')


# =====================================================================
# 3. DASHBOARDS
# =====================================================================

@login_required
@role_required('USER')
def user_dashboard(request):
    incidents = Incident.objects.filter(empID=request.user).order_by('-created_on', '-created_time')
    awaiting_feedback = incidents.filter(status='AWAITING_FEEDBACK')
    open_active_count = incidents.exclude(status__in=['CLOSED', 'AWAITING_FEEDBACK']).count()
    return render(request, 'accounts/user_dashboard.html', {
        'incidents': incidents,
        'awaiting_feedback': awaiting_feedback,
        'open_active_count': open_active_count, 
    })

@login_required
@role_required('IT_SUPPORT')
def support_dashboard(request):
    unassigned_tickets = Incident.objects.filter(status__in=['NEW', 'REOPENED'], assigned_to__isnull=True).order_by('priority')
    my_tickets = Incident.objects.filter(assigned_to=request.user).exclude(status__in=['AWAITING_FEEDBACK', 'CLOSED'])
    feedback_tickets = Incident.objects.filter(status='AWAITING_FEEDBACK')
    pending_requests = ServiceRequest.objects.filter(status='OPEN').order_by('-created_at')

    context = {
        'my_tickets': my_tickets,
        'unassigned_tickets': unassigned_tickets,
        'feedback_tickets': feedback_tickets,
        'pending_requests': pending_requests,
        'unassigned_count_formatted': format_ticket_count(unassigned_tickets.count()),
        'my_tickets_count_formatted': format_ticket_count(my_tickets.count()),
        'feedback_count_formatted': format_ticket_count(feedback_tickets.count()),
    }
    return render(request, 'accounts/support_dashboard.html', context)

@login_required
@role_required('ADMIN')
def admin_dashboard(request):
    """
    Administrator Power Panel: Consolidates ITSM metrics, Vendor tracking, 
    Security monitoring, Backup schedules, and System Audits.
    """
    # 1. --- Core Incident Metrics ---
    total_incidents = Incident.objects.count()
    closed_count = Incident.objects.filter(status='CLOSED').count()
    resolved_count = Incident.objects.filter(status='AWAITING_FEEDBACK').count()
    
    # 2. --- CSAT / Feedback Logic ---
    satisfied_feedback_count = TicketFeedback.objects.filter(is_satisfied=True).count()
    total_feedback_count = TicketFeedback.objects.count()
    csat_score = (satisfied_feedback_count / total_feedback_count * 100) if total_feedback_count > 0 else 0
    
    # 3. --- NEW: Vendor Management ---
    # Monitor contracts expiring within 30 days
    expiry_threshold = timezone.now().date() + timedelta(days=30)
    expiring_vendors = Vendor.objects.filter(
        contract_expiry__lte=expiry_threshold, 
        status='Active'
    ).order_by('contract_expiry')
    
    # 4. --- NEW: Security Management ---
    # Track active threats that require admin attention
    active_threats = SecurityManagement.objects.filter(
        status='Detected'
    ).select_related('affected_asset', 'assigned_admin').order_by('-severity')
    
    # 5. --- NEW: Backup Management ---
    # Monitor upcoming and overdue data backup tasks
    backup_status = BackupManagement.objects.all().select_related('target_asset').order_by('next_schedule')
    
    # 6. --- NEW: Audit Management ---
    # Display the most recent 10 administrative actions for the log
    recent_audits = AuditManagement.objects.all().order_by('-timestamp')[:10]
    
    context = {
        'total_incidents': total_incidents,
        'closed_count': closed_count,
        'resolved_count': resolved_count,
        'csat_score': round(csat_score, 2),
        'all_incidents': Incident.objects.all().select_related('empID', 'assigned_to').order_by('-created_on')[:10],
        
        # Admin Module Context
        'expiring_vendors': expiring_vendors,
        'active_threats': active_threats,
        'backup_status': backup_status,
        'recent_audits': recent_audits,
    }
    return render(request, 'accounts/admin_dashboard.html', context)

# =====================================================================
# 4. INCIDENT WORKFLOW & TRACKING AUTOMATION
# =====================================================================

@login_required
@never_cache
def create_incident(request):
    user = request.user
    if request.method == "POST":
        form = IncidentForm(request.POST, request.FILES)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.created_by = user
            incident.empID = user 
            incident.status = 'NEW'
            incident.save()
            
            IncidentTracking.objects.create(
                incident=incident,
                status=incident.status,
                assigned_to="Unassigned",
                created_by=user
            )
            
            messages.success(request, f"Incident created! Tracking started for {incident.incident_number}")
            return redirect('user_dashboard')
    else:
        form = IncidentForm()
    return render(request, 'accounts/incident_management.html', {'form': form})

@login_required
@role_required('IT_SUPPORT')
def resolve_incident(request, incident_id):
    incident = get_object_or_404(Incident, id=incident_id, assigned_to=request.user)
    if request.method == 'POST':
        current_time = timezone.now()
        incident.status = 'AWAITING_FEEDBACK'
        incident.resolved_at = current_time 
        incident.resolved_date = current_time.date() 
        incident.save()
        
        tracking = getattr(incident, 'tracking', None)
        if tracking:
            tracking.status = 'AWAITING_FEEDBACK'
            tracking.assigned_to = request.user.get_full_name() or request.user.email
            tracking.resolved_on = current_time.date()
            tracking.resolved_time = current_time.time()
            tracking.save() 
        
        messages.success(request, f"Incident {incident.incident_number} resolved. Metrics recorded.")
        return redirect('support_dashboard')
    return render(request, 'accounts/incident_detail_support.html', {'incident': incident})

@login_required
@role_required('USER')
def submit_feedback(request, incident_id):
    ticket = get_object_or_404(Incident, id=incident_id, empID=request.user)
    if ticket.status != 'AWAITING_FEEDBACK':
        return redirect('user_dashboard') 
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            is_satisfied = form.cleaned_data['is_satisfied'] == 'True' 
            TicketFeedback.objects.create(
                ticket=ticket, is_satisfied=is_satisfied,
                comments=form.cleaned_data['comments'], provided_by=request.user
            )
            
            tracking = getattr(ticket, 'tracking', None)
            if tracking:
                tracking.feedback_action = is_satisfied
                tracking.status = 'CLOSED' if is_satisfied else 'REOPENED'
                tracking.save()

            ticket.status = 'CLOSED' if is_satisfied else 'REOPENED'
            if not is_satisfied: ticket.assigned_to = None
            ticket.save() 
            return redirect('user_dashboard') 
    else:
        form = FeedbackForm()
    return render(request, 'accounts/incident_detail_feedback.html', {'ticket': ticket, 'form': form})

# =====================================================================
# 5. SUPPORT QUEUES & MISC
# =====================================================================

@login_required
@user_passes_test(is_support)
def unassigned_queue_view(request):
    tickets = Incident.objects.filter(assigned_to__isnull=True, status__in=['NEW', 'REOPENED']).order_by('-priority', 'created_on')
    return render(request, 'accounts/dedicated_queue.html', {
        'tickets': tickets, 'queue_name': 'Unassigned Triage Queue', 'queue_color': 'danger',
        'queue_icon': 'fa-fire', 'is_support_view': True, 'ticket_count_formatted': format_ticket_count(tickets.count())
    })

@login_required
@user_passes_test(is_support)
def my_active_tickets_view(request):
    tickets = Incident.objects.filter(assigned_to=request.user).exclude(status__in=['AWAITING_FEEDBACK', 'CLOSED']).order_by('-priority', 'created_on')
    return render(request, 'accounts/dedicated_queue.html', {
        'tickets': tickets, 'queue_name': 'My Active Workload', 'queue_color': 'primary',
        'queue_icon': 'fa-helmet-safety', 'is_support_view': True, 'is_my_tickets_view': True,
        'ticket_count_formatted': format_ticket_count(tickets.count())
    })

@login_required
@user_passes_test(is_support)
def feedback_queue_view(request):
    tickets = Incident.objects.filter(status='AWAITING_FEEDBACK').order_by('created_on')
    return render(request, 'accounts/dedicated_queue.html', {
        'tickets': tickets, 'queue_name': 'Awaiting User Feedback', 'queue_color': 'warning',
        'queue_icon': 'fa-hourglass-half', 'is_support_view': True, 'is_feedback_queue': True,
        'ticket_count_formatted': format_ticket_count(tickets.count())
    })

@login_required
@role_required('IT_SUPPORT')
def take_incident(request, incident_id):
    incident = get_object_or_404(Incident, id=incident_id)
    if incident.status in ['NEW', 'REOPENED'] and incident.assigned_to is None:
        incident.assigned_to = request.user
        incident.status = 'IN_PROGRESS'
        incident.save()
        
        tracking = getattr(incident, 'tracking', None)
        if tracking:
            tracking.status = 'IN_PROGRESS'
            tracking.assigned_to = request.user.get_full_name() or request.user.email
            tracking.save()
            
        messages.success(request, f"Incident {incident.incident_number} assigned to you.")
    return redirect('support_dashboard')

@login_required
def incident_list_view(request):
    incidents = Incident.objects.filter(empID=request.user).order_by('-created_on', '-created_time')
    return render(request, 'accounts/incident_list.html', {'incidents': incidents})

@login_required
def incident_detail_view(request, incident_id):
    incident = get_object_or_404(Incident, id=incident_id)
    is_authorized = (incident.empID == request.user) or (incident.assigned_to == request.user) or (request.user.role == 'ADMIN')
    if not is_authorized:
        messages.error(request, "Unauthorized access.")
        return redirect('home')
    return render(request, 'accounts/incident_detail.html', {'incident': incident})

@login_required
def service_requests(request):
    if request.method == "POST":
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.empID = request.user 
            req.save()
            messages.success(request, "Service Request submitted successfully!")
            return redirect('user_dashboard')
    else:
        form = ServiceRequestForm()
    return render(request, 'accounts/service_requests.html', {'form': form})

# =====================================================================
# 6. PROBLEM, SLA & ASSET MANAGEMENT
# =====================================================================

@login_required
@role_required('IT_SUPPORT')
def problem_management(request):
    """Monitor recurring problem cases and root causes"""
    problems = ProblemManagement.objects.all().select_related('root_cause_catID', 'assigned_to').order_by('-created_on')
    problem_cases = ProblemCase.objects.all().order_by('-freq_count')
    return render(request, 'accounts/problem_management.html', {
        'problems': problems,
        'problem_cases': problem_cases
    })

@login_required
@role_required('IT_SUPPORT')
def sla_management(request):
    """View to monitor restoration delays and SLA compliance"""
    sla_records = SLAManagement.objects.all().select_related('incident').order_by('resolution_due')
    return render(request, 'accounts/sla_management.html', {'sla_records': sla_records})

@login_required
@role_required('IT_SUPPORT')
def asset_management(request):
    """View to track hardware and software assets"""
    assets = Asset.objects.all().select_related('category', 'custodian').order_by('-last_audit_date')
    return render(request, 'accounts/asset_management.html', {'assets': assets})

@login_required
def change_management(request): 
    return render(request, 'accounts/change_management.html')
    


@login_required
def vendor_management(request):
    # logic for vendor management will go here
    return render(request, 'accounts/vendor_management.html')

@login_required
def security_center(request):
    # logic for security threats will go here
    return render(request, 'accounts/security_center.html')

@login_required
def backup_management(request):
    # logic for backup compliance will go here
    return render(request, 'accounts/backup_management.html')

@login_required
def audit_trail(request):
    # logic for audit logs will go here
    return render(request, 'accounts/audit_trail.html')


@login_required
def incident_tracker(request):
    # Use 'created_on' instead of 'created_at'
    all_tracked_incidents = Incident.objects.all().order_by('-created_on', '-created_time')

    # Logic for "Aging": use 'created_on'
    threshold = timezone.now().date() - timedelta(days=1)
    aging_incidents = Incident.objects.filter(created_on__lt=threshold).exclude(status='CLOSED')

    # Logic for "Reopened"
    reopened_incidents = Incident.objects.filter(status='REOPENED')

    context = {
        'all_tracked_incidents': all_tracked_incidents,
        'aging_incidents': aging_incidents,
        'reopened_incidents': reopened_incidents,
    }
    return render(request, 'accounts/incident_tracker.html', context)
@login_required
def tech_tracking(request):
    """
    Monitor support technician workload and efficiency.
    """
    # Logic to calculate tech metrics will go here
    return render(request, 'accounts/tech_tracking.html')


@login_required
def support_oversight(request):
    if request.user.role != 'ADMIN':
        return redirect('home')

    # Monitor existing models
    active_problems = ProblemManagement.objects.exclude(status='close')
    pending_requests = ServiceRequest.objects.filter(status='OPEN')
    sla_breaches = SLAManagement.objects.filter(sla_status='Breached')
    
    today = timezone.now().date()
    critical_assets = Asset.objects.filter(warranty_expiry__lte=today + timedelta(days=30))

    context = {
        'active_problems': active_problems,
        'pending_requests': pending_requests,
        'sla_breaches': sla_breaches,
        'critical_assets': critical_assets,
    }
    return render(request, 'accounts/support_oversight.html', context)