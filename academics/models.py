# Create your models here.
# academics/models.py
from django.db import models


class SchoolClass(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
class ClassSubject(models.Model):
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('school_class', 'subject')

    def __str__(self):
        return f"{self.school_class} - {self.subject}"


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

class Term(models.Model):
    TERM_CHOICES = [
        ('1st', 'First Term'),
        ('2nd', 'Second Term'),
        ('3rd', 'Third Term'),
    ]
    name = models.CharField(max_length=3, choices=TERM_CHOICES)

    def __str__(self):
        return self.name


class ScoreType(models.Model):
    name = models.CharField(max_length=20)  # 1stCA, 2ndCA, Exam

    def __str__(self):
        return self.name
    

