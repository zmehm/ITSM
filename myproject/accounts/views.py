from django.shortcuts import render, redirect
from .forms import EmployeeRegistrationForm, ProfileCompletionForm
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model
from .models import Employee, Category, SubCategory, Incident
from django.contrib.auth.decorators import login_required
from .decorators import profile_required  # <-- NEW IMPORT
from django.contrib.auth import logout
# Home view (handles profile completion form)
def home(request):
    # Ensure the user is authenticated, otherwise redirect them to login
    if not request.user.is_authenticated:
        return redirect('login_view') # Assuming you have a login URL name 'login_view'

    try:
        employee = request.user.employee 
    except Employee.DoesNotExist:
        # Note: A new user should technically be handled by the signal, 
        # but this remains a robust check for existing users.
        employee = Employee.objects.create(user=request.user)

    if not employee.Dept or not employee.Grade or not employee.Discipline:
        if request.method == 'POST':
            form = ProfileCompletionForm(request.POST, instance=employee) 
            if form.is_valid():
                form.save()
                messages.success(request, "Profile completed successfully!")
                return redirect('home')
            else:
                messages.error(request, "Please correct the errors in the form.")
        else:
            form = ProfileCompletionForm(instance=employee)

        return render(request, 'accounts/home.html', {'form': form}) 

    return render(request, 'accounts/home.html')

# Incident creation view
@login_required
@profile_required  # <-- Applied
def create_incident(request):
    categories = Category.objects.all()
    subcategories = SubCategory.objects.all()

    if request.method == "POST":
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        subcategory_id = request.POST.get('subcategory')
        impact = request.POST.get('impact')
        priority = request.POST.get('priority')
        file_upload = request.FILES.get('file_upload')

        category = Category.objects.get(id=category_id)
        subcategory = SubCategory.objects.get(id=subcategory_id)

        try:
            employee = request.user.employee
        except Employee.DoesNotExist:
            messages.error(request, "No employee record found for this user.")
            return redirect('incident_management') # This part is less critical now due to @profile_required

        incident = Incident(
            description=description,
            catID=category,
            subcatID=subcategory,
            impact=impact,
            priority=priority,
            file_upload=file_upload,
            created_by=request.user,
            empID=employee,
        )
        incident.save()
        return redirect('incident_list') # Assuming 'incident_list' is the correct URL name

    return render(request, 'incident_management.html', {
        'categories': categories,
        'subcategories': subcategories
    })

# Incident management view
@login_required
@profile_required  # <-- Applied
def incident_management(request):
    incidents = Incident.objects.filter(created_by=request.user) 
    return render(request, 'accounts/incident_management.html', {'incidents': incidents})

# Problem management view
@login_required
@profile_required  # <-- Applied
def problem_management(request):
    return render(request, 'accounts/problem_management.html')

# Change management view
@login_required
@profile_required  # <-- Applied
def change_management(request):
    return render(request, 'accounts/change_management.html')

# Service requests view
@login_required
@profile_required  # <-- Applied
def service_requests(request):
    return render(request, 'accounts/service_requests.html')

# Registration view for Employee
def register_employee(request):
    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Employee registered successfully.")
            return redirect('home')
        else:
            print(form.errors)
    else:
        form = EmployeeRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})

# Login view for handling both username/email login
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username_email = request.POST.get('username_email')
        password = request.POST.get('password')
        
        User = get_user_model()
        try:
            user = authenticate(request, username=username_email, password=password)
            if user is None:
                user = authenticate(request, email=username_email, password=password)
        except Exception as e:
            user = None

        if user is not None and user.is_active:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    # Redirect to the login page or a simple thank you page
    return redirect('login_view')



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