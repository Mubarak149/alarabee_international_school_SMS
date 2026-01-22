from django import views
from django.urls import path
from .views import *


urlpatterns = [
    path("dashboard", admin_dashboard, name="admin_dashboard"),
    path("admins/", manage_admins, name="manage_admins"),
    path("students/", manage_students, name="manage_students"),
    path("teachers/", manage_teachers, name="manage_teachers"),
    path("classes/", manage_classes, name="manage_classes"),
    path("subjects/", manage_subjects, name="manage_subjects"),
    path('system-settings/', system_settings, name='system_settings'),
    path('score-types/', manage_score_types, name='manage_score_types'),
    path('teacher-subjects/', manage_teacher_subjects, name='manage_teacher_subjects'),
    path('terms/', manage_terms, name='manage_terms'),
    path('admin/academic-years/', manage_academic_years, name='manage_academic_years'),
    path("profile/", admin_profile, name="admin_profile"),
    path('teacher/<int:teacher_id>/bank-details/', manage_bank_details, name='manage_bank_details'),
    path("check-student-id/", check_student_id, name="check_student_id")
]

