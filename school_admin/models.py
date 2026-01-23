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
    System-wide settings (single row only)
    """

    # ======================
    # SCHOOL INFORMATION
    # ======================
    school_name = models.CharField(max_length=200, default="Our School")
    school_logo = models.ImageField(
        upload_to="school/logo/",
        null=True,
        blank=True
    )
    school_email = models.EmailField(
        max_length=100,
        blank=True,
        null=True
    )
    school_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )
    school_address = models.TextField(
        blank=True,
        null=True
    )

    # ======================
    # DEFAULT STUDENT SETTINGS
    # ======================
    default_student_password = models.CharField(
        max_length=100,
        default="Password123"
    )

    STUDENT_ID_CHOICES = [
        ('auto', 'Automatic Generation'),
        ('manual', 'Manual Input'),
    ]
    student_id_option = models.CharField(
        max_length=10,
        choices=STUDENT_ID_CHOICES,
        default='auto'
    )

    student_id_prefix = models.CharField(
        max_length=10,
        default="STU"
    )

    def __str__(self):
        return f"System Settings - {self.school_name}"

    def save(self, *args, **kwargs):
        if SystemSettings.objects.exists() and not self.pk:
            existing = SystemSettings.objects.first()
            for field in self._meta.fields:
                setattr(existing, field.name, getattr(self, field.name))
            existing.save()
            return existing
        return super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        settings, _ = cls.objects.get_or_create(id=1)
        return settings
