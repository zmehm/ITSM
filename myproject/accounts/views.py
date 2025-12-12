from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model
from django.db import IntegrityError 
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.utils import timezone
from django.db.models import Q # Added for better query handling

# --- Local Imports ---
# NOTE: Removed ResolutionForm import as it is no longer used in the simplified workflow
from .forms import EmployeeRegistrationForm, ProfileCompletionForm, IncidentForm, FeedbackForm
from .models import Category, SubCategory, Incident, TicketFeedback 
User = get_user_model() 

# --- UTILITY FUNCTION FOR ROLE CHECKING ---
def role_required(role):
    """Decorator to restrict view access based on user role."""
    def decorator(view_func):
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Check if the user's role matches the required role
            if not hasattr(request.user, 'role') or request.user.role != role:
                messages.error(request, "Access denied. You do not have permission to view this page.")
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


# =====================================================================
# 1. AUTHENTICATION & UTILITY VIEWS
# =====================================================================

def register_employee(request):
    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save() 
                user.role = 'USER' 
                user.save()
                login(request, user)
                messages.success(request, "Registration successful. You are now logged in.")
                return redirect('home')
            except IntegrityError:
                messages.error(request, "Registration failed due to a database constraint.")
            except Exception:
                messages.error(request, "An unexpected error occurred during registration.")
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

def logout_view(request):
    logout(request)
    return redirect('login_view')

def password_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(request=request)
            messages.success(request, "Password reset instructions sent to your email.")
            return redirect('login_view')
        else:
            messages.error(request, "Please enter a valid email address.")
    else:
        form = PasswordResetForm()
    return render(request, 'accounts/password_reset.html', {'form': form})

# Utility for AJAX
def get_subcategories(request, category_id):
    subcategories = SubCategory.objects.filter(category_id=category_id, active=True).values('id', 'name')
    data = {subcat['id']: subcat['name'] for subcat in subcategories}
    return JsonResponse(data)


# =====================================================================
# 2. ROLE-BASED LANDING PAGE (CENTRAL HOME ROUTER)
# =====================================================================

@login_required
def home(request):
    # Profile Completion Check
    if not request.user.EmpID or not request.user.Dept or not request.user.Grade or not request.user.Discipline:
        if request.method == 'POST':
            form = ProfileCompletionForm(request.POST, instance=request.user) 
            if form.is_valid():
                form.save()
                messages.success(request, "Profile completed successfully! You now have full access.")
                return redirect('home') 
            else:
                messages.error(request, "Please correct the errors in the profile form.")
        else:
            form = ProfileCompletionForm(instance=request.user)
        
        messages.info(request, "Please complete your mandatory profile information to access the portal.")
        return render(request, 'accounts/home.html', {'form': form, 'profile_incomplete': True})

    # Role-based Redirect
    if request.user.role == 'ADMIN':
        return redirect('admin_dashboard')
    elif request.user.role == 'IT_SUPPORT':
        return redirect('support_dashboard')
    else: 
        return redirect('user_dashboard')


# =====================================================================
# 3. ROLE-SPECIFIC DASHBOARDS
# =====================================================================

@login_required
@role_required('USER')
def user_dashboard(request):
    incidents = Incident.objects.filter(empID=request.user).order_by('-created_on', '-created_time')
    awaiting_feedback = incidents.filter(status='AWAITING_FEEDBACK')
    
    return render(request, 'accounts/user_dashboard.html', {
        'incidents': incidents,
        'awaiting_feedback': awaiting_feedback,
    })


@login_required
@role_required('IT_SUPPORT')
def support_dashboard(request):
    
    unassigned_tickets = Incident.objects.filter(
        status__in=['NEW', 'REOPENED'], 
        assigned_to__isnull=True
    ).order_by('priority')
    
    my_tickets = Incident.objects.filter(
        assigned_to=request.user
    ).exclude(status__in=['AWAITING_FEEDBACK', 'CLOSED'])

    feedback_tickets = Incident.objects.filter(status='AWAITING_FEEDBACK')

    context = {
        'my_tickets': my_tickets,
        'unassigned_tickets': unassigned_tickets,
        'feedback_tickets': feedback_tickets,
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

    context = {
        'total_incidents': total_incidents,
        'closed_count': closed_count,
        'resolved_count': resolved_count,
        'csat_score': round(csat_score, 2),
        # Ensure we use correct related name for empID/reported_by based on your model
        'all_incidents': Incident.objects.all().select_related('empID', 'assigned_to').order_by('-created_on'),
    }
    return render(request, 'accounts/admin_dashboard.html', context)


# =====================================================================
# 4. INCIDENT WORKFLOW VIEWS
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
            
            messages.success(request, f"Incident created successfully! Tracking Number: {incident.incident_number}")
            return redirect('user_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
            
    else:
        form = IncidentForm()

    return render(request, 'accounts/incident_management.html', {'form': form})


@login_required
@role_required('IT_SUPPORT')
def take_incident(request, incident_id):
    incident = get_object_or_404(Incident, id=incident_id)

    if incident.status in ['NEW', 'REOPENED'] and incident.assigned_to is None:
        incident.assigned_to = request.user
        incident.status = 'IN_PROGRESS'
        incident.save()
        messages.success(request, f"Incident {incident.incident_number} assigned to you and is now In Progress.")
    else:
        messages.warning(request, "This incident is not available for assignment or is already in progress.")

    return redirect('support_dashboard')


@login_required
@role_required('IT_SUPPORT')
def resolve_incident(request, incident_id):
    """
    Handles IT Support marking a ticket as resolved (form-less confirmation). 
    Captures date/time and sets the status to AWAITING_FEEDBACK.
    """
    
    incident = get_object_or_404(Incident, id=incident_id, assigned_to=request.user)

    if request.method == 'POST':
        
        # Resolution Logic (No form required)
        incident.status = 'AWAITING_FEEDBACK'
        incident.resolved_on = timezone.now().date()
        incident.resolved_time = timezone.now().time()
        incident.save()
        
        messages.success(request, f"Incident {incident.incident_number} marked as resolved. Awaiting user feedback.")
        return redirect('support_dashboard')

    # Renders the confirmation template
    return render(request, 'accounts/incident_detail_support.html', {'incident': incident})


@login_required
def incident_list_view(request):
    """View to see a list of all incidents reported by the current user."""
    incidents = Incident.objects.filter(empID=request.user).order_by('-created_on', '-created_time')
    return render(request, 'accounts/incident_list.html', {'incidents': incidents})


@login_required
def incident_detail_view(request, incident_id):
    """View to see a single incident detail."""
    incident = get_object_or_404(Incident, id=incident_id)
    
    # Permission check: Only reported_by, assigned_to, or Admin can view detail
    is_authorized = (incident.empID == request.user) or \
                    (incident.assigned_to == request.user) or \
                    (request.user.role == 'ADMIN')
    
    if not is_authorized:
        messages.error(request, "You are not authorized to view this incident.")
        return redirect('home')

    return render(request, 'accounts/incident_detail.html', {'incident': incident})


@login_required
@role_required('USER')
def submit_feedback(request, incident_id):
    """Handles the user satisfaction feedback loop (CLOSED or REOPENED)."""
    ticket = get_object_or_404(Incident, id=incident_id, empID=request.user)

    if ticket.status != 'AWAITING_FEEDBACK':
        messages.warning(request, "This incident is not awaiting feedback.")
        return redirect('user_dashboard') 

    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            # CRITICAL: Comparison must be against the string 'True' from the form submission
            is_satisfied = form.cleaned_data['is_satisfied'] == 'True' 
            
            # 1. Create the Feedback Record
            TicketFeedback.objects.create(
                ticket=ticket,
                is_satisfied=is_satisfied,
                comments=form.cleaned_data['comments'],
                provided_by=request.user
            )

            # 2. Update the Incident Status
            if is_satisfied:
                ticket.status = 'CLOSED'
                messages.success(request, f"Incident {ticket.incident_number} closed successfully. Thank you for your feedback.")
            else:
                ticket.status = 'REOPENED'
                ticket.assigned_to = None # Reset assignment
                messages.info(request, f"Incident {ticket.incident_number} reopened and returned to the queue.")
            
            # 3. CRITICAL: Save the status change to the database
            ticket.save() 
            return redirect('user_dashboard') 
    else:
        form = FeedbackForm()
    
    return render(request, 'accounts/incident_detail_feedback.html', {'ticket': ticket, 'form': form})

# Remaining stub views 
@login_required
def problem_management(request):
    return render(request, 'accounts/problem_management.html')

@login_required
def change_management(request):
    return render(request, 'accounts/change_management.html')

@login_required
def service_requests(request):
    return render(request, 'accounts/service_requests.html')