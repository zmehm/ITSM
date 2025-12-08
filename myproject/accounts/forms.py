from django import forms
from django.contrib.auth import get_user_model  # Use get_user_model() to ensure compatibility with CustomUser
from .models import Employee

class EmployeeRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    
    class Meta:
        model = Employee
        fields = [
            'EmpID', 'EmpName', 'DoB', 'Gender', 'Dept', 'Grade', 
            'Discipline', 'Floor', 'Active'
        ]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Password and Confirm Password do not match.")
        
        return cleaned_data

    def save(self, commit=True):
        # Create or get the CustomUser instance
        User = get_user_model()  # This ensures compatibility with CustomUser
        user = User.objects.create_user(
            username=self.cleaned_data['username'], 
            password=self.cleaned_data['password']
        )
        
        # Create the employee instance and link to the CustomUser
        employee = super().save(commit=False)
        employee.user = user
        if commit:
            employee.save()
        return employee
