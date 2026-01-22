from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('invoices/', views.student_invoices, name='student_invoice'),
    path('academic-scores/', views.student_academic_scores, name='student_academic_scores'),
    path('invoice/<int:invoice_id>/download/', views.download_invoice_pdf, name='download_invoice_pdf'),
    path('report-card/<int:academic_year_id>/<int:term_id>/download/', 
         views.download_report_card_pdf, name='download_report_card_pdf'),
]
# End of file students/urls.py