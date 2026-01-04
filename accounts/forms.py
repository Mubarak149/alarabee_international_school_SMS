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
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'dob': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }
