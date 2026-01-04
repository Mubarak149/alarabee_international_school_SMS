from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('student', 'Student'),
        ('staff', 'Staff'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    dob = models.DateField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    