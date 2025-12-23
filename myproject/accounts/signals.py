from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import LoginMonitor, Incident, SLAManagement,Vendor, SecurityManagement, BackupManagement, AuditManagement,ProblemManagement, ProblemCase
from django.db.models.signals import pre_save

# --- UTILITY: GET CLIENT IP ADDRESS ---
def get_client_ip(request):
    """Extracts the IP address from the request metadata."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# =====================================================================
# 1. LOGIN MONITOR SIGNALS (Session Tracking)
# =====================================================================

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Triggers on login to record the hardware and network identifiers.
    Captures the IP address and User-Agent (representing MAC/Hardware).
    """
    # Note: Browsers do not expose the literal MAC address; 
    # capturing the User-Agent is the standard web-safe alternative.
    hardware_info = request.META.get('HTTP_USER_AGENT', 'Unknown Device')
    
    LoginMonitor.objects.create(
        login_by=user.email, # Identifies the user
        ip_address=get_client_ip(request), # Records IP
        mac_address=hardware_info[:200], # Records Device ID
        session_key=request.session.session_key
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """
    Updates the monitor entry with the logout date and time when the session ends.
    """
    now = timezone.now()
    # Find the latest session for this user using their unique session key
    record = LoginMonitor.objects.filter(
        login_by=user.email, 
        session_key=request.session.session_key
    ).last()
    
    if record:
        record.logout_date = now.date() # Records Logout Date
        record.logout_time = now.time() # Records Logout Time
        record.save()


# =====================================================================
# 2. SLA MANAGEMENT SIGNALS (Incident Automation)
# =====================================================================

@receiver(post_save, sender=Incident)
def auto_create_incident_sla(sender, instance, created, **kwargs):
    """
    Automatically generates an SLA record when a new Incident is created.
    Sets initial due dates for Response and Resolution.
    """
    if created:
        # Define your standard SLA thresholds (e.g., 4 hours for Response, 48 hours for Resolution)
        # Dates are captured as required by your schema.
        SLAManagement.objects.create(
            incident=instance,
            response_due=(timezone.now() + timedelta(hours=4)).date(), #
            resolution_due=(timezone.now() + timedelta(days=2)).date(), #
            sla_status='Active' #
        )

@receiver(pre_save, sender=Vendor)
@receiver(pre_save, sender=SecurityManagement)
def track_admin_changes(sender, instance, **kwargs):
    """
    Automatically captures the 'Before' and 'After' values of Admin records
    to populate the AuditManagement trail.
    """
    if instance.pk:  # Only track updates to existing records
        try:
            old_obj = sender.objects.get(pk=instance.pk)
            # Example: Tracking status changes
            if old_obj.status != instance.status:
                AuditManagement.objects.create(
                    performed_by="System Admin",  # In a real app, track request.user
                    action_type=f"Update {sender.__name__}",
                    old_value=f"Status: {old_obj.status}",
                    new_value=f"Status: {instance.status}"
                )
        except sender.DoesNotExist:
            pass



@receiver(post_save, sender=Incident)
def evaluate_problem_policy(sender, instance, created, **kwargs):
    # Only run logic for new incidents with a mapped Root Cause
    if created and instance.subcatID and instance.subcatID.rc_cat:
        user = instance.empID
        sub_name = instance.subcatID.name
        rc_cat_obj = instance.subcatID.rc_cat

        # --- A. DEFINE METRIC PERIODS (Based on your table) ---
        if any(x in sub_name for x in ["Battery", "Crash", "Connectivity"]):
            days = 7
        elif any(x in sub_name for x in ["Profile", "Vendor"]):
            days = 90
        else:
            days = 30 # Standard for Hardware, Config, Resources, Lockouts
            
        start_date = timezone.now().date() - timedelta(days=days)

        # --- B. COUNT HISTORICAL INCIDENTS FOR THIS USER ---
        incident_count = Incident.objects.filter(
            empID=user,
            subcatID=instance.subcatID,
            created_on__gte=start_date
        ).count()

        # --- C. DEFINE THRESHOLD LOGIC (Your Table Policy) ---
        severity = None
        
        # 1. Hardware/Battery/Connectivity/Resource/Lockout (≥10 is Major)
        if any(x in sub_name for x in ["Hardware", "Battery", "Connectivity Drop", "Resource", "Account Lockout"]):
            if incident_count >= 10: severity = 'Major Issue'
            elif 6 <= incident_count <= 9: severity = 'Moderate Issue'
            elif 3 <= incident_count <= 5: severity = 'Minor Issue'

        # 2. Component Failure/Performance/Connectivity Fix (≥12 is Major)
        elif any(x in sub_name for x in ["Component", "Application Crash", "Connectivity Fix", "Performance"]):
            if incident_count >= 12: severity = 'Major Issue'
            elif 8 <= incident_count <= 11: severity = 'Moderate Issue'
            elif 4 <= incident_count <= 7: severity = 'Minor Issue' # Note: 5-7 for Crash/Fix

        # 3. Profile Corruption / Config Change (≥5 is Major)
        elif any(x in sub_name for x in ["Profile", "Configuration"]):
            if incident_count >= 5: severity = 'Major Issue'
            elif 3 <= incident_count <= 4: severity = 'Moderate Issue'
            elif incident_count == 2: severity = 'Minor Issue'

        # 4. Vendor Glitch (≥6 is Major)
        elif "Vendor" in sub_name:
            if incident_count >= 6: severity = 'Major Issue'
            elif 4 <= incident_count <= 5: severity = 'Moderate Issue'
            elif 2 <= incident_count <= 3: severity = 'Minor Issue'

        # --- D. TAKE ACTION ---
        if severity:
            # Create the Problem Record
            ProblemManagement.objects.get_or_create(
                description=f"{severity}: {sub_name} threshold reached (Count: {incident_count})",
                root_cause_catID=rc_cat_obj,
                defaults={
                    'status': 'open',
                    'known_issue': True,
                    'created_by': instance.created_by
                }
            )

            # Update the ProblemCase Tracking table
            ProblemCase.objects.filter(rc_catID=rc_cat_obj).update(
                freq_count=incident_count,
                active=True,
                detected_on=timezone.now().date()
            )
