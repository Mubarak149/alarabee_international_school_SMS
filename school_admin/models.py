from django.db import models
from accounts.models import User
# Create your models here.

class AdminProfile(models.Model):
    Qualifications = [
        ('BEd', 'Bachelor of Education'),
        ('MEd', 'Master of Education'),
        ('PhD', 'Doctor of Philosophy in Education'),
        ('Other', 'Other'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    nin = models.CharField(max_length=20, blank=True, null=True)  # National Identification Number
    qualification = models.CharField(max_length=10, choices=Qualifications, blank=True, null=True)

    def __str__(self):
        return f"Admin Profile: {self.user.username}"
    