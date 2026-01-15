from django.db import models

# Create your models here.
# finance/models.py
from django.db import models
from students.models import StudentProfile

class Sponsorship(models.Model):
    SPONSORSHIP_TYPE = [
        ('none', 'No Scholarship'),
        ('full', 'Full Scholarship'),
        ('partial', 'Partial Scholarship'),
        ('other', 'Other / Unknown'),
    ]

    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE)
    sponsorship_type = models.CharField(
        max_length=20,
        choices=SPONSORSHIP_TYPE,
        default='none'
    )
    
    sponsor_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Government, NGO, Parent, Company, etc"
    )

    percentage_covered = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Used only for partial scholarship (e.g. 50%)"
    )

    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.student} - {self.get_sponsorship_type_display()}"

class FeeType(models.Model):
    name = models.CharField(max_length=100)  # Tuition, Hostel, Exam, Uniform
    description = models.TextField(blank=True)
    is_recurring = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class FeeStructure(models.Model):
    fee_type = models.ForeignKey(FeeType, on_delete=models.CASCADE)
    school_class = models.ForeignKey('academics.SchoolClass', on_delete=models.CASCADE)
    academic_year = models.ForeignKey('academics.AcademicYear', on_delete=models.CASCADE)
    term = models.ForeignKey('academics.Term', on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('fee_type', 'school_class', 'academic_year', 'term')

class Invoice(models.Model):
    STATUS = [
        ('unpaid', 'Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    academic_year = models.ForeignKey('academics.AcademicYear', on_delete=models.CASCADE)
    term = models.ForeignKey('academics.Term', on_delete=models.CASCADE)

    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(max_length=20, choices=STATUS, default='unpaid')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice {self.id} - {self.student}"

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    fee_type = models.ForeignKey(FeeType, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

class Payment(models.Model):
    METHOD = [
        ('cash', 'Cash'),
        ('transfer', 'Bank Transfer'),
        ('pos', 'POS'),
        ('online', 'Online'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=METHOD)
    reference = models.CharField(max_length=100, blank=True)

    received_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True
    )

    payment_date = models.DateTimeField(auto_now_add=True)
