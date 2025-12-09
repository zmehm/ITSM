from django import forms
from django.contrib.auth import get_user_model
from .models import Employee
from .models import Incident, Category, SubCategory

User = get_user_model()

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
            password=self.cleaned_data['EmpID'] 
        )
        user.email = self.cleaned_data.get('Email', '') 
        user.phone_number = self.cleaned_data.get('Phone', '')
        user.save() 

        employee = super().save(commit=False)
        employee.user = user
        if commit:
            employee.save()
        return employee

class ProfileCompletionForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    
    class Meta:
        model = Employee
        fields = [
            'Email', 'Phone', 'DoB', 'Gender', 
            'Dept', 'Grade', 'Discipline', 'Floor', 'Active'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            user = self.instance.user
            
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            
            if not self.instance.Email and user.email:
                self.fields['Email'].initial = user.email

            if not self.instance.Phone and user.phone_number:
                self.fields['Phone'].initial = user.phone_number
            
            if not self.instance.DoB and user.date_of_birth:
                self.fields['DoB'].initial = user.date_of_birth

    def save(self, commit=True):
        employee = super().save(commit=False)
        
        if self.instance and self.instance.pk:
            user = self.instance.user
            
            user.first_name = self.cleaned_data.get('first_name', '')
            user.last_name = self.cleaned_data.get('last_name', '')
            
            if commit:
                user.save()
                employee.save()
        
        return employee


class IncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = [
            'subsidiary', 'catID', 'subcatID', 'description', 'file_upload', 'impact', 'state'
        ]

    # Dynamically load subcategories based on selected category
    def __init__(self, *args, **kwargs):
        super(IncidentForm, self).__init__(*args, **kwargs)
        self.fields['subcatID'].queryset = SubCategory.objects.none()  # Initially no subcategories

        if 'catID' in self.data:
            try:
                category_id = int(self.data.get('catID'))
                self.fields['subcatID'].queryset = SubCategory.objects.filter(category_id=category_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['subcatID'].queryset = self.instance.catID.subcategory_set.all()