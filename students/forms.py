# students/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import StudentProfile

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            'student_id',
            'parent_name',
            'parent_contact',
        ]
        widgets = {
            'student_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Student ID'
            }),
            'parent_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Parent/Guardian Name'
            }),
            'parent_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Parent Contact'
            }),
        }
