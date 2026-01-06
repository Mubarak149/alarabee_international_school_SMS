from django.contrib import admin
from students.models import StudentProfile, StudentClass

# Register your models here.
admin.site.register(StudentProfile)
admin.site.register(StudentClass)
