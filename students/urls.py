from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('report-cards/', views.student_report_cards, name='report_cards'),
    path('subject/', views.student_subject, name='student_subject'),
    path('profile/', views.student_subject, name='profile'),
    path('setting/', views.student_subject, name='settings'),
]
# End of file students/urls.py