from django.contrib import admin
from students.models import StudentProfile, StudentClass
from .models import AdminProfile
# Register your models here.
admin.site.register(StudentProfile)
admin.site.register(StudentClass)
admin.site.register(AdminProfile)
