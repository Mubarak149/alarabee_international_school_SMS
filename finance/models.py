from django.db import models
from django.db import models
from django.db.models import Sum
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.student} - {self.get_sponsorship_type_display()}"
    
    @property
    def display_type(self):
        """Get human-readable sponsorship type"""
        return dict(self.SPONSORSHIP_TYPE).get(self.sponsorship_type, self.sponsorship_type.title())
    
    @property
    def current_class_name(self):
        """Get student's current class name"""
        return self.student.current_class_name


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

    def recalculate(self):
        """
        Sync invoice amounts & status from payments.
        """
        total_paid = self.payments.filter(
            status='completed'
        ).aggregate(
            total=Sum('amount_paid')
        )['total'] or 0

        self.amount_due = self.total_amount - total_paid

        if total_paid <= 0:
            self.status = 'unpaid'
        elif total_paid < self.total_amount:
            self.status = 'partial'
        else:
            self.status = 'paid'

        self.save(update_fields=['amount_due', 'status'])
    
    
    def __str__(self):
        return f"Invoice {self.id} - {self.student}"
    
    class Meta:
        unique_together = ('student', 'academic_year', 'term')

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    fee_type = models.ForeignKey(FeeType, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

# Update your Payment model in finance/models.py
class Payment(models.Model):
    METHOD = [
        ('cash', 'Cash'),
        ('transfer', 'Bank Transfer'),
        ('pos', 'POS'),
        ('online', 'Online'),
        ('cheque', 'Cheque'),
        ('mobile', 'Mobile Money'),
    ]
    
    STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField()
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=METHOD)
    status = models.CharField(max_length=20, choices=STATUS, default='completed')
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-payment_date', '-created_at']
    
    def __str__(self):
        return f"Payment {self.id} - {self.student}"

    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Always resync invoice after saving payment
        self.invoice.recalculate()


    
    @property
    def payment_method_icon(self):
        """Return icon for payment method"""
        icons = {
            'cash': 'fa-money-bill-wave',
            'transfer': 'fa-university',
            'pos': 'fa-credit-card',
            'online': 'fa-globe',
            'cheque': 'fa-file-invoice',
            'mobile': 'fa-mobile-alt',
        }
        return icons.get(self.payment_method, 'fa-money-check')
    
    @property
    def status_color(self):
        """Return color for status"""
        colors = {
            'completed': 'success',
            'pending': 'warning',
            'failed': 'danger',
            'refunded': 'secondary',
        }
        return colors.get(self.status, 'info')