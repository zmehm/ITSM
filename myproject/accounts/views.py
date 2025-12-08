from django.shortcuts import render, redirect
from .forms import EmployeeRegistrationForm  # Import the new Employee form
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model  # Use get_user_model() for CustomUser
from .models import Employee  # Import the Employee model
from django.contrib.auth.decorators import login_required
from .models import Category, SubCategory, Incident


# Incident Creation View
@login_required
def create_incident(request):
    categories = Category.objects.all()
    subcategories = SubCategory.objects.all()

    if request.method == "POST":
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        subcategory_id = request.POST.get('subcategory')
        impact = request.POST.get('impact')
        priority = request.POST.get('priority')
        file_upload = request.FILES.get('file_upload')  # Get the uploaded file

        category = Category.objects.get(id=category_id)
        subcategory = SubCategory.objects.get(id=subcategory_id)

        # Ensure the user has an associated Employee object before creating the incident
        try:
            employee = request.user.employee
        except Employee.DoesNotExist:
            messages.error(request, "No employee record found for this user.")
            return redirect('incident_management')  # Redirect to incident management if error

        # Create the new incident
        incident = Incident(
            description=description,
            catID=category,
            subcatID=subcategory,
            impact=impact,
            priority=priority,
            file_upload=file_upload,  # Save the uploaded file
            created_by=request.user,
            empID=employee,
        )
        incident.save()

        return redirect('incident_list')  # Redirect to the list of incidents

    return render(request, 'incident_management.html', {
        'categories': categories,
        'subcategories': subcategories
    })


# Home view
@login_required
def home(request):
    return render(request, 'accounts/home.html')


# Incident Management View
@login_required
def incident_management(request):
    return render(request, 'accounts/incident_management.html')


# Problem Management View
@login_required
def problem_management(request):
    return render(request, 'accounts/problem_management.html')


# Change Management View
@login_required
def change_management(request):
    return render(request, 'accounts/change_management.html')


# Service Requests View
@login_required
def service_requests(request):
    return render(request, 'accounts/service_requests.html')


# Registration view for Employee
def register_employee(request):
    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST)
        if form.is_valid():
            # The form.save() method creates both the User and Employee instance
            user = form.save()  # The `form.save()` method will create the user and handle password hashing
            
            # Login the user automatically after registration
            login(request, user)

            messages.success(request, "Employee registered successfully.")
            return redirect('home')  # Redirect to the home page or another page you prefer
        else:
            print(form.errors)  # Print any validation errors for debugging
    else:
        form = EmployeeRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


# Login view (handle username or email)
def login_view(request):
    # If the user is already authenticated, redirect to the home page
    if request.user.is_authenticated:
        return redirect('home')  # Redirect to the homepage or dashboard
    
    if request.method == 'POST':
        # Get the username/email and password from the POST request
        username_email = request.POST.get('username_email')
        password = request.POST.get('password')
        
        # Authenticate the user by checking if it's a valid username or email
        User = get_user_model()  # Use the custom user model
        try:
            # Try to authenticate by username first
            user = authenticate(request, username=username_email, password=password)
            # If authentication fails with username, try with email
            if user is None:
                user = authenticate(request, email=username_email, password=password)
        except Exception as e:
            user = None  # Handle any exceptions, e.g., if email field is missing in the User model

        # If user is authenticated and is active, log them in and redirect
        if user is not None and user.is_active:
            login(request, user)
            return redirect('home')  # Redirect to the homepage or dashboard
        
        # If login fails, show an error message
        else:
            messages.error(request, 'Invalid username or password. Please try again.')

    # Render the login page if it's not a POST request or if login fails
    return render(request, 'accounts/login.html')


# Password reset view
def password_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(request=request)
            return redirect('password_reset_done')
    else:
        form = PasswordResetForm()
    return render(request, 'accounts/password_reset.html', {'form': form})
