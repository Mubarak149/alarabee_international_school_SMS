# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User
from django import forms

class StudentUserForm(forms.ModelForm):
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


class TeacherUserForm(forms.ModelForm):
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        }),
        required=True
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'dob', 'address', 'gender']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username/Teacher ID'
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
                'placeholder': 'Email'
            }),
            'password': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Password'
            }),
            'dob': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Address'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'staff'
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class UserEditForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(
            attrs={'placeholder': 'Leave empty to keep old password'}
        )
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'gender',
            'dob',
            'address',

        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'dob': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)

        # 🔁 Keep username in sync with email
        if user.email:
            user.username = user.email

        # 🔐 Handle password change
        password = self.cleaned_data.get('password')
        if password:
            print("password changed to:", password)
            user.set_password(password)

        if commit:
            user.save()
        return user

        