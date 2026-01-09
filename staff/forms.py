# forms.py - Updated teacher forms
from .models import TeacherProfile, TeacherBankDetails, TeacherSubject
from accounts.models import User
from academics.models import Subject
from django import forms


class TeacherProfileForm(forms.ModelForm):
    class Meta:
        model = TeacherProfile
        fields = ['qualification', 'contact', 'nin', 'status']
        widgets = {
            'qualification': forms.Select(attrs={
                'class': 'form-control'
            }),
            'contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number'
            }),
            'nin': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'National ID Number'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

# forms.py
class TeacherSubjectForm(forms.ModelForm):
    
    class Meta:
        model = TeacherSubject
        fields = ['teacher', 'subject', 'academic_year', 'class_assigned']
        widgets = {
            'teacher': forms.Select(attrs={
                'class': 'form-control'
            }),
            'subject': forms.Select(attrs={
                'class': 'form-control'
            }),
            'academic_year': forms.Select(attrs={
                'class': 'form-control'
            }),
            'class_assigned': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize the label for the teacher field
        self.fields['teacher'].label_from_instance = lambda obj: f"{obj.user.get_full_name()} (ID: {obj.user.id})"
        
        # Optional: Filter only active teachers
        self.fields['teacher'].queryset = TeacherProfile.objects.select_related('user').filter(
            status='active'
        ).order_by('user__first_name', 'user__last_name')
class TeacherBankDetailsForm(forms.ModelForm):

    class Meta:
        model = TeacherBankDetails
        fields = ['bank_name', 'account_number', 'account_name']
        widgets = {
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bank Name'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Account Number'
            }),
            'account_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Account Name'
            }),
        }

class TeacherProfileEditForm(forms.ModelForm):
    class Meta:
        model = TeacherProfile
        fields = [
            'qualification',
            'contact',
            'nin',
            'status',
            'subjects',
        ]
        widgets = {
            'subjects': forms.CheckboxSelectMultiple(),
            'qualification': forms.Select(attrs={
                'class': 'form-control'
            }),
            'contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number'
            }),
            'nin': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'National ID Number'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
class TeacherBankEditForm(forms.ModelForm):
    class Meta:
        model = TeacherBankDetails
        fields = [
            'bank_name',
            'account_number',
            'account_name',
        ]
        widgets = {
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bank Name'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Account Number'
            }),
            'account_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Account Name'
            }),
        }
