# accounts/decorators.py

from django.shortcuts import redirect
from django.contrib import messages
from .models import Employee  # Assuming Employee is imported from .models

def profile_required(view_func):
    def wrapper_func(request, *args, **kwargs):
        # Ensure the employee object exists (same logic as the home view)
        try:
            employee = request.user.employee
        except Employee.DoesNotExist:
            employee = Employee.objects.create(user=request.user)
            
        # Check if any of the mandatory fields are empty
        if not employee.Dept or not employee.Grade or not employee.Discipline:
            messages.warning(request, "Please complete your employee profile before accessing other sections.")
            # Redirect to the 'home' view (where the form is shown)
            return redirect('home')
        
        # If the profile is complete, proceed to the requested view
        return view_func(request, *args, **kwargs)
        
    return wrapper_func