# students/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import StudentProfile, StudentClass

class StudentProfileForm(forms.ModelForm):
    student_id = forms.CharField(required=False)
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
                'placeholder': 'Student ID',
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

class StudentClassForm(forms.ModelForm):
    class Meta:
        model = StudentClass
        fields = [
            'school_class',
            'academic_year',
        ]
        widgets = {
            'school_class': forms.Select(attrs={'class': 'form-select'}),
            'academic_year': forms.Select(attrs={'class': 'form-select'}),
        }
