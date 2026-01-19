from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('invoice/pdf/<int:invoice_id>/', views.generate_invoice_pdf, name='generate_invoice_pdf'),
    path('report-card/pdf/<int:academic_year_id>/<int:term_id>/', views.generate_report_card_pdf, name='generate_report_card_pdf'),
]
# End of file students/urls.py