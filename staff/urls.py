from django.urls import path
from .views import *

urlpatterns = [
    path("teachers/dashboard", teachers_dashboard, name="teachers_dashboard"),
    path("teachers/classes", teacher_classes, name="teacher_classes"),
]

