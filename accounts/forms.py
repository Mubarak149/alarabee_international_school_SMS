# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class StudentUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'dob',
            'address',
        ]
        fields = ['username', 'first_name', 'last_name', 'email', 'dob', 'address']
        widgets = {
             'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Student ID (will be auto-generated)'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email address'
            }),
            'dob': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }
