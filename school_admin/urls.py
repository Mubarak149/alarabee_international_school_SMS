from django.urls import path
from .views import *

urlpatterns = [
    path("dashboard", admin_panel, name="admin_panel"),
    path("students/", manage_students, name="manage_students"),
    path("teachers/", manage_teachers, name="manage_teachers"),
    path("classes/", manage_classes, name="manage_classes"),
    path("subjects/", manage_subjects, name="manage_subjects"),
    path('admin/academic-years/', manage_academic_years, name='manage_academic_years'),
    path("profile/", admin_profile, name="admin_profile"),
    path('teacher/<int:teacher_id>/', view_teacher, name='view_teacher'),
    path('teacher/<int:teacher_id>/bank-details/', manage_bank_details, name='manage_bank_details'),
]

