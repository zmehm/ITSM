from django import forms
from django.contrib.auth import get_user_model
from .models import Employee

User = get_user_model()

# --- Existing EmployeeRegistrationForm (Left unchanged) ---
class EmployeeRegistrationForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'EmpID', 'EmpName', 'DoB', 'Gender', 'Dept', 'Grade', 
            'Discipline', 'Floor', 'Active', 'Phone'
        ]

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['EmpID'],
            # Note: You should update this to a proper password setup later
            password=self.cleaned_data['EmpID'] 
        )
        # Manually sync user fields from Employee form during registration
        user.email = self.cleaned_data.get('Email', '') 
        user.phone_number = self.cleaned_data.get('Phone', '')
        # Add other user fields if they were on the registration form
        user.save() 

        employee = super().save(commit=False)
        employee.user = user
        if commit:
            employee.save()
        return employee
# -----------------------------------------------------------


# --- MODIFIED ProfileCompletionForm for Autofill and Saving Personal Details ---
class ProfileCompletionForm(forms.ModelForm):
    # 1. Add CustomUser fields (First Name, Last Name) to the form 
    # so they can be rendered and validated.
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    
    class Meta:
        model = Employee
        # We need to include fields that hold personal info (DoB, Gender, Email, Phone) 
        # plus the required profile fields (Dept, Grade, Discipline, Floor, Active)
        fields = [
            'Email', 'Phone', 'DoB', 'Gender',  # Personal Employee fields
            'Dept', 'Grade', 'Discipline', 'Floor', 'Active' # Profile fields
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Access the linked CustomUser instance
        if self.instance and self.instance.pk:
            user = self.instance.user
            
            # 2. INITIALIZE fields using data from the CustomUser instance
            
            # --- Personal Fields (from CustomUser) ---
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            
            # --- Employee Fields that mirror CustomUser data ---
            
            # If the Employee Email is empty, pull it from the CustomUser model
            if not self.instance.Email and user.email:
                self.fields['Email'].initial = user.email

            # If the Employee Phone is empty, pull it from the CustomUser model
            if not self.instance.Phone and user.phone_number:
                self.fields['Phone'].initial = user.phone_number
            
            # If the Employee DoB is empty, pull it from the CustomUser model's date_of_birth
            if not self.instance.DoB and user.date_of_birth:
                self.fields['DoB'].initial = user.date_of_birth

            # Note: Other fields like Dept, Grade, etc., are automatically initialized 
            # with existing Employee data by ModelForm.

    def save(self, commit=True):
        # 3. Save the form data back to the linked CustomUser instance
        
        # Save the Employee instance first
        employee = super().save(commit=False)
        
        if self.instance and self.instance.pk:
            user = self.instance.user
            
            # Update CustomUser fields
            user.first_name = self.cleaned_data.get('first_name', '')
            user.last_name = self.cleaned_data.get('last_name', '')
            # Assuming you don't want to change username/primary email here, 
            # but if you did, you would update user.email and user.phone_number here too
            
            if commit:
                user.save()
                employee.save()
        
        return employee