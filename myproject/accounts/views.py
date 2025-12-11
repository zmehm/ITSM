from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model
from django.db import IntegrityError 
from django.http import JsonResponse
from .forms import EmployeeRegistrationForm, ProfileCompletionForm, IncidentForm
from .models import Category, SubCategory, Incident 
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

User = get_user_model()

def register_employee(request):
    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST)
        
        if form.is_valid():
            try:
                user = form.save() 
                login(request, user)
                messages.success(request, "Registration successful. You are now logged in.")
                return redirect('home')
            
            except IntegrityError as e:
                messages.error(request, "Registration failed due to a database constraint.")
            except Exception as e:
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


@login_required
def home(request):
    user = request.user
    
    if not user.EmpID or not user.Dept or not user.Grade or not user.Discipline:
        messages.info(request, "Please complete your mandatory profile information to access the portal.")
        
        if request.method == 'POST':
            form = ProfileCompletionForm(request.POST, instance=user) 
            if form.is_valid():
                form.save()
                messages.success(request, "Profile completed successfully! You now have full access.")
                return redirect('home')
            else:
                messages.error(request, "Please correct the errors in the profile form.")
        else:
            form = ProfileCompletionForm(instance=user)

        return render(request, 'accounts/home.html', {'form': form, 'profile_incomplete': True}) 

    return render(request, 'accounts/home.html', {'profile_incomplete': False})


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
            
            incident.save()
            
            messages.success(request, f"Incident created successfully! Tracking Number: {incident.incident_number}")
            return redirect('incident_list')
        else:
            messages.error(request, "Please correct the errors below.")
            
    else:
        form = IncidentForm()

    return render(request, 'accounts/incident_management.html', {
        'form': form,
    })


@login_required
def incident_management(request):
    incidents = Incident.objects.filter(created_by=request.user).order_by('-created_on', '-created_time')
    return render(request, 'accounts/incident_list.html', {'incidents': incidents})


@login_required
def problem_management(request):
    return render(request, 'accounts/problem_management.html')


@login_required
def change_management(request):
    return render(request, 'accounts/change_management.html')


@login_required
def service_requests(request):
    return render(request, 'accounts/service_requests.html')


def get_subcategories(request, category_id):
    subcategories = SubCategory.objects.filter(category_id=category_id, active=True).values('id', 'name')
    data = {subcat['id']: subcat['name'] for subcat in subcategories}
    return JsonResponse(data)