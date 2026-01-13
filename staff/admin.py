from django.contrib import admin
from .models import TeacherBankDetails, TeacherProfile, TeacherSubject
admin.site.register(TeacherProfile)
admin.site.register(TeacherSubject)
admin.site.register(TeacherBankDetails)
# Register your models here.
