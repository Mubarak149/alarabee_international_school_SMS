from django.db import models
from accounts.models import User

# models.py - Add to existing models
class TeacherProfile(models.Model):
    TEACHER_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_leave', 'On Leave'),
        ('retired', 'Retired'),
    ]
    
    QUALIFICATION_CHOICES = [
        ('phd', 'PhD'),
        ('masters', 'Masters'),
        ('bachelors', 'Bachelors'),
        ('diploma', 'Diploma'),
        ('other', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    qualification = models.CharField(max_length=20, choices=QUALIFICATION_CHOICES)
    contact = models.CharField(max_length=20, blank=True)
    nin = models.CharField(max_length=50, blank=True, unique=True)  # National Identification Number
    status = models.CharField(max_length=20, choices=TEACHER_STATUS, default='active')
    subjects = models.ManyToManyField('academics.Subject', related_name='teachers', blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.subjects})"
    
    @property
    def is_active(self):
        return self.status == 'active'

class TeacherSubject(models.Model):
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.CASCADE, related_name='subject_assignments')
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE)
    academic_year = models.ForeignKey('academics.AcademicYear', on_delete=models.CASCADE)
    class_assigned = models.ForeignKey('academics.SchoolClass', on_delete=models.CASCADE, related_name='teacher_assignments')
    
    class Meta:
        unique_together = ['teacher', 'subject', 'academic_year', 'class_assigned']
        ordering = ['academic_year', 'class_assigned']
    
    def __str__(self):
        return f"{self.teacher.user.get_full_name()} - {self.subject.name} ({self.class_assigned.name})"
    
class TeacherBankDetails(models.Model):
    teacher = models.OneToOneField(TeacherProfile, on_delete=models.CASCADE, related_name='bank_details')
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=50)
    account_name = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.teacher.user.get_full_name()} - {self.bank_name}"