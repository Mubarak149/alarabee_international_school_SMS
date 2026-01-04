from django.urls import path
from .views import *

urlpatterns = [
    path("dashboard", admin_panel, name="admin_panel"),
    path("students/", manage_students, name="manage_students"),
    path("teachers/", manage_teachers, name="manage_teachers"),
    path("classes/", manage_classes, name="manage_classes"),
    path("subjects/", manage_subjects, name="manage_subjects"),
    path("profile/", admin_profile, name="admin_profile"),
]

