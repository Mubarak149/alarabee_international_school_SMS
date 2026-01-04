from django.db import models

# Create your models here.
class StudentProfile(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    parent_name = models.CharField(max_length=100)
    parent_contact = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.student_id}"
    
