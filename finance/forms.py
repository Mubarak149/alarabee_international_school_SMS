from django import forms
from .models import FeeStructure, FeeType, Payment


class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = [
            "fee_type",
            "school_class",
            "academic_year",
            "term",
            "amount",
        ]

        widgets = {
            "fee_type": forms.Select(attrs={"class": "form-select"}),
            "school_class": forms.Select(attrs={"class": "form-select"}),
            "academic_year": forms.Select(attrs={"class": "form-select"}),
            "term": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01",
                }
            ),
        }

class FeeTypeForm(forms.ModelForm):
    class Meta:
        model = FeeType
        fields = ["name", "description", "is_recurring"]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g Tuition, Hostel"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Optional description"
            }),
            "is_recurring": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }

class PaymentsForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = [
            "invoice",
            "student",
            "payment_date",
            "amount_paid",
            "payment_method",
            "status",
            "notes",
        ]

        widgets = {
            "invoice": forms.Select(attrs={"class": "form-select"}),
            "student": forms.Select(attrs={"class": "form-select"}),
            "payment_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "amount_paid": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
            "payment_method": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }



class RecordPaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount_paid', 'payment_method', 'notes']
        
    def __init__(self, *args, **kwargs):
        self.invoice = kwargs.pop('invoice', None)
        super().__init__(*args, **kwargs)
        
        # Set initial values
        if self.invoice:
            self.fields['amount_paid'].widget.attrs.update({
                'max': self.invoice.amount_due,
                'min': '0.01',
                'step': '0.01'
            })
            
    def clean_amount_paid(self):
        amount_paid = self.cleaned_data['amount_paid']
        if self.invoice and amount_paid > self.invoice.amount_due:
            raise forms.ValidationError(
                f"Amount cannot exceed due amount: ${self.invoice.amount_due:.2f}"
            )
        return amount_paid
    
    amount_paid = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter payment amount'
        })
    )
    
    payment_method = forms.ChoiceField(
        choices=Payment.METHOD,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Optional notes about payment'
        })
    )