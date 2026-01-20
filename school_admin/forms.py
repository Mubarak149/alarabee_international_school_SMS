from django import forms
from .models import AdminProfile, SystemSettings

class AdminProfileForm(forms.ModelForm):
    class Meta:
        model = AdminProfile
        fields = ['qualification', 'contact_number', 'nin']
        widgets = {
            'qualification': forms.Select(attrs={
                'class': 'form-control'
            }),
            'contact_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number'
            }),
            'nin': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'National ID Number'
            }),
        }


class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = ['school_name', 'default_student_password', 'student_id_option', 'student_id_prefix']
        
        widgets = {
            'school_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter school name'
            }),
            'default_student_password': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter default password for students'
            }),
            'student_id_option': forms.Select(attrs={
                'class': 'form-select'
            }),
            'student_id_prefix': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., STU'
            }),
        }