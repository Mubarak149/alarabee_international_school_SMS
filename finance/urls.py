from django.urls import path
from . import views


urlpatterns = [
    # Dashboard
    path('dashboard/', views.finance_dashboard, name='finance_dashboard'),
    
    # Invoices
    path('invoices/', views.student_invoices, name='student_invoices'),
    path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:invoice_id>/payment/', views.record_payment, name='record_payment'),
    path('invoices/generate/<int:student_id>/', views.generate_invoice, name='generate_invoice'),
    
    # Fee Management
    path('fee-management/', views.fee_management, name='fee_management'),
    path('fee-structure/delete/<int:structure_id>/', views.delete_fee_structure, name='delete_fee_structure'),
    path('fee-type/delete/<int:type_id>/', views.delete_fee_type, name='delete_fee_type'),
    
    # Sponsorship
    path('sponsorships/', views.sponsorship_management, name='sponsorship_management'),
    
    # Reports
    path('reports/', views.finance_reports, name='finance_reports'),
    
    # AJAX endpoints
    path('ajax/student-info/', views.get_student_info, name='get_student_info'),
]