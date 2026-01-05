from django import forms
from .models import SchoolClass, AcademicYear
import re

# forms.py
class SchoolClassForm(forms.ModelForm):
    class Meta:
        model = SchoolClass
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter class name'
            })
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Class name is required')
        
        # Normalize the name to title case with special handling
        normalized_name = self.normalize_class_name(name)
        return normalized_name
    
    def normalize_class_name(self, name):
        """
        Normalize class name to proper title case.
        Examples:
        - "primary 1a" -> "Primary 1A"
        - "ss 1a" -> "SS 1A"
        - "jss 1a" -> "JSS 1A"
        - "grade 1 section a" -> "Grade 1 Section A"
        """
        # Common education level abbreviations that should stay uppercase
        education_levels = ['SS', 'JSS', 'SSS', 'PRY', 'NURSERY', 'KG', 'PRE', 'GRADE']
        
        # Split into words
        words = name.upper().split()
        normalized_words = []
        
        for i, word in enumerate(words):
            # Check if word is an education level abbreviation
            if word in education_levels:
                normalized_words.append(word)
            # Check if word contains numbers (like "1A", "2B", etc.)
            elif any(char.isdigit() for char in word):
                # Keep the format as is but ensure letters after numbers are uppercase
                normalized_word = ''
                for char in word:
                    if char.isalpha():
                        normalized_word += char.upper()
                    else:
                        normalized_word += char
                normalized_words.append(normalized_word)
            else:
                # Capitalize first letter, rest lowercase
                normalized_words.append(word.capitalize())
        
        return ' '.join(normalized_words)
    

class AcademicYearForm(forms.ModelForm):
    class Meta:
        model = AcademicYear
        fields = ['year', 'start_date', 'end_date', 'is_active']
        widgets = {
            'year': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2023-2024',
                'required': True
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_year(self):
        year = self.cleaned_data.get('year', '').strip()
        
        # Validate format
        if not re.match(r'^\d{4}-\d{4}$', year):
            raise forms.ValidationError('Academic year must be in format: YYYY-YYYY (e.g., 2023-2024)')
        
        # Check if start year is less than end year
        start_year, end_year = map(int, year.split('-'))
        if end_year != start_year + 1:
            raise forms.ValidationError('Academic year should be sequential (e.g., 2023-2024)')
        
        # Check for duplicate (case-insensitive)
        if self.instance.pk:  # Editing existing record
            if AcademicYear.objects.filter(year__iexact=year).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError(f'Academic year "{year}" already exists')
        else:  # Creating new record
            if AcademicYear.objects.filter(year__iexact=year).exists():
                raise forms.ValidationError(f'Academic year "{year}" already exists')
        
        return year
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        year = cleaned_data.get('year')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise forms.ValidationError('End date must be after start date')
            
            # Optional: Validate dates match the academic year
            if year:
                start_year = int(year.split('-')[0])
                if start_date.year != start_year:
                    self.add_error('start_date', 
                        f'Start date should be in {start_year} for academic year {year}')
        
        return cleaned_data