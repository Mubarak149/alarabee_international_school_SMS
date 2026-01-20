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
    

class SystemSettings(models.Model):
    """
    Simple system settings model with only essential fields
    """
    # School Information
    school_name = models.CharField(max_length=200, default="Our School")
    
    # Default Student Password
    default_student_password = models.CharField(max_length=100, default="Password123")
    
    # Student ID Options
    STUDENT_ID_CHOICES = [
        ('auto', 'Automatic Generation'),
        ('manual', 'Manual Input'),
    ]
    student_id_option = models.CharField(
        max_length=10,
        choices=STUDENT_ID_CHOICES,
        default='auto'
    )
    
    # Student ID Prefix for automatic generation
    student_id_prefix = models.CharField(max_length=10, default="STU")
    
    def __str__(self):
        return f"System Settings - {self.school_name}"
    
    def save(self, *args, **kwargs):
        # Make sure only one settings instance exists
        if SystemSettings.objects.exists() and not self.pk:
            # If a settings instance already exists, update it instead of creating new
            existing = SystemSettings.objects.first()
            existing.school_name = self.school_name
            existing.default_student_password = self.default_student_password
            existing.student_id_option = self.student_id_option
            existing.student_id_prefix = self.student_id_prefix
            existing.save()
            return existing
        return super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get or create the system settings instance"""
        settings, created = cls.objects.get_or_create(
            id=1,
            defaults={
                'school_name': 'Our School',
                'default_student_password': 'Password123',
                'student_id_option': 'auto',
                'student_id_prefix': 'STU'
            }
        )
        return settings