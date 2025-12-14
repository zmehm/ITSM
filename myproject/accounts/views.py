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

# --- Email and Template Imports ---
from django.template.loader import render_to_string 
from django.core.mail import EmailMessage
# ----------------------------------

# --- Local Imports ---
from .forms import EmployeeRegistrationForm, ProfileCompletionForm, IncidentForm, FeedbackForm
from .models import Category, SubCategory, Incident, TicketFeedback 
User = get_user_model() 

# =====================================================================
# 0. UTILITY FUNCTIONS & ROLE CHECK (DEFINED FIRST TO AVOID NAMEERROR)
# =====================================================================

def format_ticket_count(count, limit=1000):
    """Formats the count: '1000+' for large numbers, otherwise the exact count."""
    if count >= limit:
        # Use f-string formatting for thousands separator
        return f"{limit:,.0f}+"
    return str(count)


def role_required(role):
    """Decorator to restrict view access based on user role."""
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
    """Helper function to check if user is IT Support."""
    return user.is_authenticated and user.role == 'IT_SUPPORT'

# Utility for AJAX
def get_subcategories(request, category_id):
    """Returns subcategories for a given category ID as JSON (for AJAX)."""
    subcategories = SubCategory.objects.filter(category_id=category_id, active=True).values('id', 'name')
    data = {subcat['id']: subcat['name'] for subcat in subcategories}
    return JsonResponse(data)


# =====================================================================
# 1. AUTHENTICATION & GLOBAL VIEWS
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


# =====================================================================
# 2. ROLE-BASED LANDING PAGE (CENTRAL HOME ROUTER)
# =====================================================================

@login_required
def home(request):
    # Profile Completion Check (Logic kept concise)
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
# 3. ROLE-SPECIFIC DASHBOARDS (Metric Hubs)
# =====================================================================

@login_required
@role_required('USER')
def user_dashboard(request):
    incidents = Incident.objects.filter(empID=request.user).order_by('-created_on', '-created_time')
    awaiting_feedback = incidents.filter(status='AWAITING_FEEDBACK')
    
    # Calculate Open/Active Count in the View
    open_active_count = incidents.exclude(status__in=['CLOSED', 'AWAITING_FEEDBACK']).count()

    return render(request, 'accounts/user_dashboard.html', {
        'incidents': incidents,
        'awaiting_feedback': awaiting_feedback,
        'open_active_count': open_active_count, 
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
        # Pass the raw lists for the detailed tables later
        'my_tickets': my_tickets,
        'unassigned_tickets': unassigned_tickets,
        'feedback_tickets': feedback_tickets,
        
        # Pass the formatted count strings for the dashboard cards (NEW)
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

    context = {
        'total_incidents': total_incidents,
        'closed_count': closed_count,
        'resolved_count': resolved_count,
        'csat_score': round(csat_score, 2),
        'all_incidents': Incident.objects.all().select_related('empID', 'assigned_to').order_by('-created_on'),
    }
    return render(request, 'accounts/admin_dashboard.html', context)


# =====================================================================
# 4. DEDICATED SUPPORT QUEUE VIEWS (New: Separate Pages)
# =====================================================================

@login_required
@user_passes_test(is_support)
def unassigned_queue_view(request):
    """Dedicated view for Unassigned tickets (NEW/REOPENED)."""
    tickets = Incident.objects.filter(assigned_to__isnull=True, status__in=['NEW', 'REOPENED']).order_by('-priority', 'created_on')
    context = {
        'tickets': tickets,
        'queue_name': 'Unassigned Triage Queue',
        'queue_color': 'danger',
        'queue_icon': 'fa-fire',
        'is_support_view': True,
        'ticket_count_formatted': format_ticket_count(tickets.count()), # UPDATED
    }
    return render(request, 'accounts/dedicated_queue.html', context)

@login_required
@user_passes_test(is_support)
def my_active_tickets_view(request):
    """Dedicated view for tickets assigned to the current support agent (IN_PROGRESS/PENDING_INFO)."""
    tickets = Incident.objects.filter(assigned_to=request.user).exclude(status__in=['AWAITING_FEEDBACK', 'CLOSED']).order_by('-priority', 'created_on')
    context = {
        'tickets': tickets,
        'queue_name': 'My Active Workload',
        'queue_color': 'primary',
        'queue_icon': 'fa-helmet-safety',
        'is_support_view': True,
        'is_my_tickets_view': True,
        'ticket_count_formatted': format_ticket_count(tickets.count()), # UPDATED
    }
    return render(request, 'accounts/dedicated_queue.html', context)

@login_required
@user_passes_test(is_support)
def feedback_queue_view(request):
    """Dedicated view for tickets awaiting user confirmation (AWAITING_FEEDBACK)."""
    tickets = Incident.objects.filter(status='AWAITING_FEEDBACK').order_by('created_on')
    context = {
        'tickets': tickets,
        'queue_name': 'Awaiting User Feedback',
        'queue_color': 'warning', # Using Bootstrap's 'warning' class for the yellow/brown look
        'queue_icon': 'fa-hourglass-half',
        'is_support_view': True,
        'is_feedback_queue': True,
        'ticket_count_formatted': format_ticket_count(tickets.count()), # UPDATED
    }
    return render(request, 'accounts/dedicated_queue.html', context)


# =====================================================================
# 5. INCIDENT WORKFLOW VIEWS (CRUD & Status Changes)
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
    Handles IT Support marking a ticket as resolved, updates the status to 
    AWAITING_FEEDBACK, and sends an email notification to the user.
    """
    
    incident = get_object_or_404(Incident, id=incident_id, assigned_to=request.user)

    if request.method == 'POST':
        
        current_time_aware = timezone.now()
        
        # Resolution Logic
        incident.status = 'AWAITING_FEEDBACK'
        incident.resolved_at = current_time_aware 
        incident.resolved_date = current_time_aware.date() 
        incident.save()
        
        # ------------------- EMAIL NOTIFICATION LOGIC -------------------
        try:
            context = {
                'incident': incident,
                'request': request, 
            }
            
            email_content = render_to_string('accounts/email/incident_resolved_notification.html', context)
            
            email = EmailMessage(
                subject=f"✅ Incident Resolved: {incident.incident_number} - {incident.description[:40]}...",
                body=email_content,
                to=[incident.empID.email], # Sends to the user who reported the incident
            )
            email.content_subtype = "html" 
            email.send()
            
            messages.success(request, f"Incident {incident.incident_number} marked as resolved. Notification email sent to user.")
            
        except Exception as e:
            # Fallback for email failure 
            print(f"Error sending resolution email for {incident.incident_number}: {e}")
            messages.warning(request, f"Incident resolved, but failed to send email notification to user. Error: {e}")
        # ------------------- END EMAIL NOTIFICATION LOGIC -------------------
        
        return redirect('support_dashboard')

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

# =====================================================================
# 6. STUB VIEWS (For Sidebar Navigation)
# =====================================================================

@login_required
def problem_management(request):
    return render(request, 'accounts/problem_management.html')

@login_required
def change_management(request):
    return render(request, 'accounts/change_management.html')

@login_required
def service_requests(request):
    return render(request, 'accounts/service_requests.html')