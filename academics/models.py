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
    
# models.py
class AcademicYear(models.Model):
    year = models.CharField(max_length=15)  # 2023-2024
    is_active = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.year

    class Meta:
        ordering = ['-year']  # Show latest years first
