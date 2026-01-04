from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('student', 'Student'),
        ('staff', 'Staff'),
    )
    GENDER_CHOICES = (
        ('M', 'Male'),  
        ('F', ' Female'),  
        ('O', 'Other'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    dob = models.DateField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)

    def __str__(self):
        return self.username
    

# class BankDetails(models.Model):
#     staff = models.OneToOneField(User, on_delete=models.CASCADE)
#     bank_name = models.CharField(max_length=100)
#     account_number = models.CharField(max_length=30)

#     def __str__(self):
#         return f"Bank Details for {self.staff.username}"
