from django.urls import path
from .views import *

urlpatterns = [
    path("teachers/dashboard", teacher_dashboard, name="teacher_dashboard"),

    path('dashboard/', teacher_dashboard, name='teacher_dashboard'),
    path('save-scores/', save_student_scores, name='save_student_scores'),
    # Add these URLs:
    path('teachers/profile/', teacher_profile, name='teacher_profile'),
    path('teachers/classes/', teacher_assigned_classes, name='teacher_classes'),
    path('teachers/reports/', teacher_reports, name='teacher_reports'),
    path('teachers/profile/update/', update_teacher_profile, name='update_teacher_profile'),
    path('teachers/profile/bank/update/', update_bank_details, name='update_bank_details'),
]


