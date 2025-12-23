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
from django.core.mail import send_mail

# --- Email and Template Imports ---
from django.template.loader import render_to_string 
from django.core.mail import EmailMessage

# --- Local Imports ---
from .forms import (
    EmployeeRegistrationForm, ProfileCompletionForm, 
    IncidentForm, FeedbackForm, ServiceRequestForm,UserProfileForm
)
from .models import (
    Category, SubCategory, Incident, TicketFeedback, 
    IncidentTracking, ServiceRequest, SLAManagement, Asset,
    ProblemManagement, ProblemCase, RootCauseCat, RcSubcat, Vendor, 
    SecurityManagement, BackupManagement, AuditManagement,LoginMonitor
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
    subcategories = SubCategory.objects.filter(
        category_id=category_id, 
        active=True
    ).values('id', 'name')
    return JsonResponse(list(subcategories), safe=False)

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
# 2. ROLE-BASED LANDING PAGE
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
    total_incidents = Incident.objects.count()
    closed_count = Incident.objects.filter(status='CLOSED').count()
    resolved_count = Incident.objects.filter(status='AWAITING_FEEDBACK').count()
    
    satisfied_feedback_count = TicketFeedback.objects.filter(is_satisfied=True).count()
    total_feedback_count = TicketFeedback.objects.count()
    csat_score = (satisfied_feedback_count / total_feedback_count * 100) if total_feedback_count > 0 else 0
    
    expiry_threshold = timezone.now().date() + timedelta(days=30)
    expiring_vendors = Vendor.objects.filter(contract_expiry__lte=expiry_threshold, status='Active').order_by('contract_expiry')
    active_threats = SecurityManagement.objects.filter(status='Detected').select_related('affected_asset', 'assigned_admin').order_by('-severity')
    backup_status = BackupManagement.objects.all().select_related('target_asset').order_by('next_schedule')
    recent_audits = AuditManagement.objects.all().order_by('-timestamp')[:10]
    
    context = {
        'total_incidents': total_incidents,
        'closed_count': closed_count,
        'resolved_count': resolved_count,
        'csat_score': round(csat_score, 2),
        'all_incidents': Incident.objects.all().select_related('empID', 'assigned_to').order_by('-created_on')[:10],
        'expiring_vendors': expiring_vendors,
        'active_threats': active_threats,
        'backup_status': backup_status,
        'recent_audits': recent_audits,
    }
    return render(request, 'accounts/admin_dashboard.html', context)

# =====================================================================
# 4. INCIDENT WORKFLOW & AUTOMATION ENGINE
# =====================================================================

def check_threshold_and_categorize(incident):
    user = incident.empID
    subcat = incident.subcatID
    
    if not subcat or not subcat.rc_cat:
        return

    sub_name = subcat.name
    
    if any(x in sub_name for x in ["Battery", "Application Crash", "Connectivity", "Routers", "Switches", "Access Points", "Network Cables"]):
        lookback = 7
    elif any(x in sub_name for x in ["Profile", "Vendor"]):
        lookback = 90
    else:
        lookback = 30

    start_date = timezone.now().date() - timedelta(days=lookback)
    incident_count = Incident.objects.filter(
        empID=user,
        subcatID=subcat,
        created_on__gte=start_date
    ).count()

    severity = None
    if any(x in sub_name for x in ["Routers", "Switches", "Access Points", "Network Cables", "Connectivity Drop", "Hardware", "Monitor", "Keyboard", "Mouse", "Laptop", "Desktop"]):
        if incident_count >= 10: severity = "Major Issue"
        elif 6 <= incident_count <= 9: severity = "Moderate Issue"
        elif 3 <= incident_count <= 5: severity = "Minor Issue"
    elif any(x in sub_name for x in ["Profile", "Configuration", "Vendor", "Encryption", "Firewalls", "Security"]):
        if incident_count >= 5: severity = "Major Issue"
        elif 3 <= incident_count <= 4: severity = "Moderate Issue"

    if severity:
     user_full_name = f"{user.first_name} {user.last_name}"
    
    problem, created = ProblemManagement.objects.get_or_create(
        root_cause_catID=subcat.rc_cat,
        description__icontains=user_full_name,
        status='open',
        defaults={
            # We put the count at the VERY END so HTML can find it easily
            'description': f"{severity} - {user_full_name} | {incident_count}",
            'known_issue': False  # This fixes the KEDB "YES" issue
        }
    )

    if not created:
        # Update existing record with the new count
        problem.description = f"{severity} - {user_full_name} | {incident_count}"
        problem.save()
@login_required
@never_cache
def create_incident(request):
    user = request.user
    if request.method == "POST":
        form = IncidentForm(request.POST, request.FILES)
        
        # Manually construction with restored field names
        incident = Incident(
            subsidiary_id=request.POST.get('subsidiary'),
            catID_id=request.POST.get('catID'),
            subcatID_id=request.POST.get('subcatID'),
            description=request.POST.get('description'),
            priority=request.POST.get('priority'),
            impact_id=request.POST.get('catID'), # Satisfy NOT NULL constraint
            file_upload=request.FILES.get('file_upload'), 
            empID=user,
            created_by=user,
            status='NEW'
        )

        try:
            incident.save()
            check_threshold_and_categorize(incident)
            
            IncidentTracking.objects.create(
                incident=incident,
                status=incident.status,
                assigned_to="Unassigned",
                created_by=user
            )
            
            messages.success(request, "Incident created successfully!")
            return redirect('user_dashboard')
        except Exception as e:
            messages.error(request, f"Error saving incident: {str(e)}")
            return render(request, 'accounts/incident_management.html', {'form': form})
    else:
        form = IncidentForm()
    return render(request, 'accounts/incident_management.html', {'form': form})

# =====================================================================
# 5. RESOLUTION & FEEDBACK
# =====================================================================

@login_required
@role_required('IT_SUPPORT')
def resolve_incident(request, incident_id):
    incident = get_object_or_404(Incident, id=incident_id)
    if request.method == 'POST':
        incident.status = 'RESOLVED'
        incident.resolved_at = timezone.now()
        incident.resolution_notes = request.POST.get('resolution_notes', 'No notes provided.')
        incident.save()
        return redirect('support_dashboard')

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
            ticket.status = 'CLOSED' if is_satisfied else 'REOPENED'
            ticket.save() 
            return redirect('user_dashboard') 
    else:
        form = FeedbackForm()
    return render(request, 'accounts/incident_detail_feedback.html', {'ticket': ticket, 'form': form})

# =====================================================================
# 6. QUEUES, TRACKING & ASSETS
# =====================================================================

@login_required
@user_passes_test(is_support)
def unassigned_queue_view(request):
    tickets = Incident.objects.filter(assigned_to__isnull=True, status__in=['NEW', 'REOPENED']).order_by('-priority', 'created_on')
    return render(request, 'accounts/dedicated_queue.html', {'tickets': tickets, 'queue_name': 'Unassigned Triage Queue', 'ticket_count_formatted': format_ticket_count(tickets.count())})

@login_required
@user_passes_test(is_support)
def my_active_tickets_view(request):
    tickets = Incident.objects.filter(assigned_to=request.user).exclude(status__in=['AWAITING_FEEDBACK', 'CLOSED']).order_by('-priority', 'created_on')
    return render(request, 'accounts/dedicated_queue.html', {'tickets': tickets, 'queue_name': 'My Active Workload', 'ticket_count_formatted': format_ticket_count(tickets.count())})

@login_required
@user_passes_test(is_support)
def feedback_queue_view(request):
    tickets = Incident.objects.filter(status='AWAITING_FEEDBACK').order_by('created_on')
    return render(request, 'accounts/dedicated_queue.html', {'tickets': tickets, 'queue_name': 'Awaiting User Feedback', 'ticket_count_formatted': format_ticket_count(tickets.count())})

@login_required
@role_required('IT_SUPPORT')
def take_incident(request, incident_id):
    incident = get_object_or_404(Incident, id=incident_id)
    if incident.status in ['NEW', 'REOPENED'] and incident.assigned_to is None:
        incident.assigned_to = request.user
        incident.status = 'IN_PROGRESS'
        incident.save()
        messages.success(request, f"Incident {incident.incident_number} assigned to you.")
    return redirect('support_dashboard')

@login_required
def incident_list_view(request):
    incidents = Incident.objects.filter(empID=request.user).order_by('-created_on')
    return render(request, 'accounts/incident_list.html', {'incidents': incidents})

@login_required
def incident_detail_view(request, incident_id):
    incident = get_object_or_404(Incident, id=incident_id)
    return render(request, 'accounts/incident_detail.html', {'incident': incident})

@login_required
def service_requests(request):
    if request.method == "POST":
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.empID = request.user 
            req.save()
            return redirect('user_dashboard')
    else:
        form = ServiceRequestForm()
    return render(request, 'accounts/service_requests.html', {'form': form})

@login_required
@role_required('IT_SUPPORT')
def problem_management(request):
    problems = ProblemManagement.objects.all().select_related('root_cause_catID').order_by('-created_on')
    problem_cases = ProblemCase.objects.all().order_by('-freq_count')
    return render(request, 'accounts/problem_management.html', {'problems': problems, 'problem_cases': problem_cases})

@login_required
@role_required('IT_SUPPORT')
def sla_management(request):
    sla_records = SLAManagement.objects.all().select_related('incident').order_by('resolution_due')
    return render(request, 'accounts/sla_management.html', {'sla_records': sla_records})

@login_required
@role_required('IT_SUPPORT')
def asset_management(request):
    assets = Asset.objects.all().select_related('category', 'custodian').order_by('-last_audit_date')
    return render(request, 'accounts/asset_management.html', {'assets': assets})

# --- Placeholder Views ---
@login_required
def change_management(request): return render(request, 'accounts/change_management.html')
@login_required
def vendor_management(request): return render(request, 'accounts/vendor_management.html')
@login_required
def security_center(request): return render(request, 'accounts/security_center.html')
@login_required
def backup_management(request): return render(request, 'accounts/backup_management.html')
@login_required
def audit_trail(request): return render(request, 'accounts/audit_trail.html')

@login_required
def incident_tracker(request):
    all_tracked_incidents = Incident.objects.all().order_by('-created_on')
    context = {'all_tracked_incidents': all_tracked_incidents}
    return render(request, 'accounts/incident_tracker.html', context)

@login_required
def tech_tracking(request): return render(request, 'accounts/tech_tracking.html')

@login_required
def support_oversight(request):
    if request.user.role != 'ADMIN': return redirect('home')
    active_problems = ProblemManagement.objects.exclude(status='close')
    context = {'active_problems': active_problems}
    return render(request, 'accounts/support_oversight.html', context)

@login_required
def incident_tracking_view(request):
    tracking_records = IncidentTracking.objects.filter(incident__empID=request.user).select_related('incident').order_by('-created_on')
    return render(request, 'accounts/incident_tracking.html', {'tracking_records': tracking_records})



@user_passes_test(lambda u: u.is_staff)
def login_monitor_dashboard(request):
    # Fetch all records from your existing model
    logs = LoginMonitor.objects.all().order_by('-login_date', '-login_time')
    return render(request, 'accounts/login_monitor.html', {'logs': logs})


def profile_view(request):
    if request.method == 'POST':
        # instance=request.user tells Django to update the CURRENT user
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('profile_view')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'accounts/profile.html', {'form': form})