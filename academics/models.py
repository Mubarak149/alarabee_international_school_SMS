from django.db import models

# Create your models here.
# academics/models.py
class SchoolClass(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
class AcademicYear(models.Model):
    year = models.CharField(max_length=15)  # 2023-2024

    def __str__(self):
        return self.year
