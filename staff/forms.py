# forms.py - Updated teacher forms
from .models import TeacherProfile, TeacherBankDetails, TeacherSubject
from accounts.models import User
from academics.models import Subject
from django import forms


class TeacherUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'dob', 'address', 'gender']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'dob': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
        }

class TeacherProfileForm(forms.ModelForm):
    class Meta:
        model = TeacherProfile
        fields = ['qualification', 'contact', 'nin', 'status']
        widgets = {
            'qualification': forms.Select(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'nin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'National ID Number'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class TeacherBankDetailsForm(forms.ModelForm):
    class Meta:
        model = TeacherBankDetails
        fields = ['bank_name', 'account_number', 'account_name']
        widgets = {
            'bank_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bank Name'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Account Number'}),
            'account_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Account Holder Name'}),
        }

class TeacherSubjectAssignmentForm(forms.ModelForm):
    class Meta:
        model = TeacherSubject
        fields = ['subject', 'academic_year', 'class_assigned']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
            'class_assigned': forms.Select(attrs={'class': 'form-control'}),
        }

class TeacherSubjectMultipleForm(forms.Form):
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False
    )