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
    
    #payments
    path('payments/', views.payment_management, name='payment_management'),
    path('payments/receipt/<int:payment_id>/', views.payment_receipt, name='payment_receipt'),
    path('payments/get-invoice-info/<int:invoice_id>/', views.get_invoice_info, name='get_invoice_info'),

    path('term-invoices/<int:class_id>/<int:term_id>/<int:academic_year_id>/', views.term_invoices, name='term_invoices'),

    path('generate-term-invoices/', views.generate_term_invoices, name='generate_term_invoices'),
    path('term-invoices/send-reminder/<int:invoice_id>/', views.send_reminder, name='send_reminder'),
    path('print-term-invoices/<int:invoice_id>/', views.print_invoice, name='print_invoice'),
    path('invoices/<int:invoice_id>/edit/', views.update_invoice, name='update_invoice'),
    path('invoices/<int:invoice_id>/delete/', views.delete_invoice, name='delete_invoice'),
]