from django.db import models

# Create your models here.
class Student(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    parent = models.ForeignKey('Parent', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.student_id}"
    
class Parent(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    phone_number = models.CharField(max_length=15)
    address = models.TextField()


    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.phone_number}"