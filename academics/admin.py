from django.contrib import admin
from .models import SchoolClass, Subject, ClassSubject, AcademicYear, Term, ScoreType
# Register your models here.
admin.site.register(SchoolClass)
admin.site.register(Subject)
admin.site.register(ClassSubject)
admin.site.register(AcademicYear)
admin.site.register(Term)
admin.site.register(ScoreType)
