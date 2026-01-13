from django.urls import path
from .views import *

urlpatterns = [
    path("teachers/dashboard", teacher_dashboard, name="teacher_dashboard"),
    path("teachers/classes", teacher_classes, name="teacher_classes"),
    path("teachers/add_score", teacher_classes, name="add_score"),
    path("teachers/bulk_upload", teacher_classes, name="bulk_upload"),
    path("teachers/profile", teacher_classes, name="teacher_profile"),

    path('dashboard/', teacher_dashboard, name='teacher_dashboard'),
    path('save-scores/', save_student_scores, name='save_student_scores'),
]


