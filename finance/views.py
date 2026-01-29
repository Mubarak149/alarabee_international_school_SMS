# finance/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q, Avg, Prefetch
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db import models, transaction
from datetime import datetime, timedelta
from decimal import Decimal
import json
from django.http import JsonResponse

from .models import Sponsorship, FeeType, FeeStructure, Invoice, InvoiceItem, Payment
from .forms import FeeStructureForm, FeeTypeForm, PaymentsForm, RecordPaymentForm
from .utils import apply_sponsorship

from finance.models import Sponsorship  # Assuming you have a Sponsorship model

from students.models import StudentProfile, StudentClass
from academics.models import SchoolClass, AcademicYear, Term
from accounts.models import User

@login_required
def finance_dashboard(request):
    """Finance dashboard with key metrics and overview"""
    
    # Current academic year and term
    current_year = AcademicYear.objects.filter(is_active=True).first()
    terms = Term.objects.all()
    
    # Summary statistics
    total_students = StudentProfile.objects.count()
    total_invoices = Invoice.objects.count()
    
    # Revenue statistics
    total_revenue = Payment.objects.aggregate(total=Sum('amount_paid'))['total'] or 0
    current_month_revenue = Payment.objects.filter(
        payment_date__month=timezone.now().month,
        payment_date__year=timezone.now().year
    ).aggregate(total=Sum('amount_paid'))['total'] or 0
    
    # Invoice status summary
    invoice_status = Invoice.objects.values('status').annotate(
        count=Count('id'),
        total_amount=Sum('total_amount'),
        total_due=Sum('amount_due')
    )
    
    # Sponsorship summary
    sponsorship_summary = Sponsorship.objects.values('sponsorship_type').annotate(
        count=Count('id')
    )
    
    # Recent payments
    recent_payments = Payment.objects.select_related(
        'invoice', 'invoice__student',
    ).order_by('-payment_date')[:10]
    
    # Outstanding invoices
    outstanding_invoices = Invoice.objects.filter(
        status__in=['unpaid', 'partial']
    ).order_by('-amount_due')[:10]
    
    # Chart data
    monthly_revenue = []
    for i in range(6, -1, -1):
        month = timezone.now() - timedelta(days=30*i)
        month_revenue = Payment.objects.filter(
            payment_date__month=month.month,
            payment_date__year=month.year
        ).aggregate(total=Sum('amount_paid'))['total'] or 0
        monthly_revenue.append({
            'month': month.strftime('%b'),
            'revenue': float(month_revenue)
        })
    
    context = {
        'current_year': current_year,
        'terms': terms,
        'total_students': total_students,
        'total_invoices': total_invoices,
        'total_revenue': total_revenue,
        'current_month_revenue': current_month_revenue,
        'invoice_status': invoice_status,
        'sponsorship_summary': sponsorship_summary,
        'recent_payments': recent_payments,
        'outstanding_invoices': outstanding_invoices,
        'monthly_revenue': json.dumps(monthly_revenue),
        'pending_invoices': Invoice.objects.filter(status='unpaid').count(),
    }
    
    return render(request, 'finance/finance_dashboard.html', context)

@login_required
def student_invoices(request):
    """View and manage student invoices"""
    
    invoices = Invoice.objects.select_related(
        'student', 'student__user', 'academic_year', 'term'
    ).all()
    
    # Apply filters
    status_filter = request.GET.get('status', 'all')
    class_filter = request.GET.get('class', 'all')
    search_query = request.GET.get('search', '')
    print(class_filter)
    
    if status_filter != 'all':
        invoices = invoices.filter(status=status_filter)
    
    if class_filter != 'all':
        invoices = invoices.filter(
            student__class_records__school_class__name=class_filter,
            student__class_records__is_current=True
        ).distinct()
    
    if search_query:
        invoices = invoices.filter(
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(student__admission_number__icontains=search_query)
        )
    
    invoices = invoices.order_by('-created_at')
    
    paginator = Paginator(invoices, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    classes = SchoolClass.objects.all()
    
    context = {
        'invoices': page_obj,
        'classes': classes,
        'status_filter': status_filter,
        'class_filter': class_filter,
        'search_query': search_query,
        'pending_invoices': Invoice.objects.filter(status='unpaid').count(),
    }
    
    return render(request, 'finance/student_invoices.html', context)


@login_required
def invoice_detail(request, invoice_id):
    """View invoice details"""
    invoice = get_object_or_404(
        Invoice.objects.select_related(
            'student', 'student__user', 'academic_year', 'term'
        ).prefetch_related('items', 'payments'),
        id=invoice_id
    )
    
    context = {
        'invoice': invoice,
        'pending_invoices': Invoice.objects.filter(status='unpaid').count(),
    }
    
    return render(request, 'finance/invoice_detail.html', context)

@login_required
def record_payment(request, invoice_id):
    """Record a payment for an invoice"""
    if request.method == 'POST':
        invoice = get_object_or_404(Invoice, id=invoice_id)
        amount_paid = Decimal(request.POST.get('amount_paid'))
        payment_method = request.POST.get('payment_method')
        reference = request.POST.get('reference', '')
        
        if amount_paid > invoice.amount_due:
            messages.error(request, 'Payment amount cannot exceed amount due')
            return redirect('invoice_detail', invoice_id=invoice_id)
        
        # Create payment
        payment = Payment.objects.create(
            invoice=invoice,
            amount_paid=amount_paid,
            payment_method=payment_method,
            reference=reference,
            received_by=request.user
        )
        
        # Update invoice
        invoice.amount_due -= amount_paid
        if invoice.amount_due == 0:
            invoice.status = 'paid'
        elif invoice.amount_due < invoice.total_amount:
            invoice.status = 'partial'
        invoice.save()
        
        messages.success(request, f'Payment of ${amount_paid} recorded successfully')
        return redirect('invoice_detail', invoice_id=invoice_id)
    
    return redirect('student_invoices')

@login_required
def generate_invoice(request, student_id):
    """Generate invoice for a student"""
    if request.method == 'POST':
        student = get_object_or_404(StudentProfile, id=student_id)
        academic_year_id = request.POST.get('academic_year')
        term_id = request.POST.get('term')
        
        academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
        term = get_object_or_404(Term, id=term_id) if term_id else None
        
        # Get fee structure for student's class
        fee_items = FeeStructure.objects.filter(
            school_class=student.current_class,
            academic_year=academic_year,
            term=term if term else None
        )
        
        if not fee_items.exists():
            messages.error(request, 'No fee structure found for this class')
            return redirect('student_invoices')
        
        # Calculate total amount
        total_amount = sum(item.amount for item in fee_items)
        
        # Apply sponsorship discount if any
        sponsorship = Sponsorship.objects.filter(student=student).first()
        amount_due = total_amount
        
        if sponsorship and sponsorship.sponsorship_type in ['full', 'partial']:
            if sponsorship.sponsorship_type == 'full':
                amount_due = Decimal('0.00')
            elif sponsorship.sponsorship_type == 'partial' and sponsorship.percentage_covered:
                discount = total_amount * (Decimal(sponsorship.percentage_covered) / Decimal('100'))
                amount_due = total_amount - discount
        
        # Create invoice
        invoice = Invoice.objects.create(
            student=student,
            academic_year=academic_year,
            term=term,
            total_amount=total_amount,
            amount_due=amount_due,
            status='unpaid' if amount_due > 0 else 'paid'
        )
        
        # Create invoice items
        for fee_item in fee_items:
            InvoiceItem.objects.create(
                invoice=invoice,
                fee_type=fee_item.fee_type,
                amount=fee_item.amount
            )
        
        messages.success(request, f'Invoice generated for {student.user.get_full_name()}')
        return redirect('invoice_detail', invoice_id=invoice.id)
    
    return redirect('student_invoices')

# @login_required
# def fee_management(request):
#     # Fee Type CRUD
#     fee_types = FeeType.objects.all().order_by('name')
#     fee_type_form = FeeTypeForm()
    
#     # Fee Structure data
#     fee_structures = FeeStructure.objects.select_related(
#         'fee_type', 'school_class', 'academic_year', 'term'
#     ).order_by('school_class__name', 'academic_year__year', 'term__name')
    
#     fee_structure_form = FeeStructureForm()
    
#     # Get filter values
#     class_filter = request.GET.get('class', 'all')
#     academic_year_filter = request.GET.get('academic_year', 'all')
#     term_filter = request.GET.get('term', 'all')
    
#     # Handle POST requests for CRUD operations
#     if request.method == "POST":
#         action = request.POST.get("action")
        
#         # ➕ CREATE Fee Type
#         if action == "add_fee_type":
#             fee_type_form = FeeTypeForm(request.POST)
#             if fee_type_form.is_valid():
#                 fee_type = fee_type_form.save()
#                 messages.success(request, f"Fee type '{fee_type.name}' added successfully")
#                 return redirect("fee_management")
        
#         # ✏️ UPDATE Fee Type
#         elif action == "edit_fee_type":
#             fee_type_id = request.POST.get("fee_type_id")
#             fee_type = get_object_or_404(FeeType, id=fee_type_id)
#             form = FeeTypeForm(request.POST, instance=fee_type)
#             if form.is_valid():
#                 form.save()
#                 messages.success(request, f"Fee type updated successfully")
#                 return redirect("fee_management")
        
#         # 🗑 DELETE Fee Type
#         elif action == "delete_fee_type":
#             fee_type_id = request.POST.get("fee_type_id")
#             fee_type = get_object_or_404(FeeType, id=fee_type_id)
#             fee_type_name = fee_type.name
#             fee_type.delete()
#             messages.success(request, f"Fee type '{fee_type_name}' deleted successfully")
#             return redirect("fee_management")
        
#         # ➕ CREATE Fee Structure
#         elif action == "add_fee_structure":
#             fee_structure_form = FeeStructureForm(request.POST)
#             if fee_structure_form.is_valid():
#                 fee_structure = fee_structure_form.save()
#                 messages.success(request, f"Fee structure for {fee_structure.fee_type.name} added successfully")
#                 return redirect("fee_management")
        
#         # ✏️ UPDATE Fee Structure
#         elif action == "edit_fee_structure":
#             fee_structure_id = request.POST.get("fee_structure_id")
#             fee_structure = get_object_or_404(FeeStructure, id=fee_structure_id)
#             form = FeeStructureForm(request.POST, instance=fee_structure)
#             if form.is_valid():
#                 form.save()
#                 messages.success(request, f"Fee structure updated successfully")
#                 return redirect("fee_management")
        
#         # 🗑 DELETE Fee Structure
#         elif action == "delete_fee_structure":
#             fee_structure_id = request.POST.get("fee_structure_id")
#             fee_structure = get_object_or_404(FeeStructure, id=fee_structure_id)
#             fee_structure.delete()
#             messages.success(request, f"Fee structure deleted successfully")
#             return redirect("fee_management")
    
#     # Apply filters
#     if class_filter != 'all':
#         fee_structures = fee_structures.filter(school_class__name=class_filter)
#     if academic_year_filter != 'all':
#         fee_structures = fee_structures.filter(academic_year__year=academic_year_filter)
#     if term_filter != 'all':
#         fee_structures = fee_structures.filter(term__name=term_filter)
    
#     # Get active academic year
#     try:
#         current_year = AcademicYear.objects.get(is_active=True)
#     except AcademicYear.DoesNotExist:
#         current_year = None
    
#     # Group fee structures for display
#     grouped_fees = {}
#     for fee in fee_structures:
#         key = (fee.school_class.name, fee.academic_year.year)
#         if key not in grouped_fees:
#             grouped_fees[key] = []
#         grouped_fees[key].append(fee)
    
#     # Calculate total for each group
#     group_totals = {}
#     for key, fees in grouped_fees.items():
#         group_totals[key] = sum(fee.amount for fee in fees)
    
#     context = {
#         "fee_types": fee_types,
#         "fee_type_form": fee_type_form,
#         "fee_structures": fee_structures,
#         "grouped_fees": grouped_fees,
#         "group_totals": group_totals,
#         "fee_structure_form": fee_structure_form,
#         "class_filter": class_filter,
#         "academic_year_filter": academic_year_filter,
#         "term_filter": term_filter,
#         "classes": SchoolClass.objects.all().order_by('name'),
#         "academic_years": AcademicYear.objects.all().order_by('-year'),
#         "terms": Term.objects.all(),
#         "current_year": current_year.year if current_year else "Not Set",
#         "pending_invoices": Invoice.objects.filter(status="unpaid").count(),
#     }
    
#     return render(request, "finance/fee_management.html", context)



def sponsorship_management(request):
    # Handle form submissions
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create':
            return create_sponsorship(request)
        elif action == 'update':
            return update_sponsorship(request)
        elif action == 'delete':
            return delete_sponsorship(request)
    
    # Handle GET requests - show main page
    search_query = request.GET.get('search', '')
    type_filter = request.GET.get('type', 'all')
    class_filter = request.GET.get('class', '')
    view_mode = request.GET.get('view', 'sponsorships')  # 'sponsorships' or 'students'
    
    # Get filters for the page
    context = get_sponsorship_context(
        search_query=search_query,
        type_filter=type_filter,
        class_filter=class_filter,
        view_mode=view_mode
    )
    
    return render(request, 'finance/sponsorship_management.html', context)

def get_sponsorship_context(search_query='', type_filter='all', class_filter='', view_mode='sponsorships'):
    """Helper function to get context data for the sponsorship page"""
    
    # Get all classes for filter dropdown
    classes = SchoolClass.objects.all().order_by('name')
    
    # Get all sponsorships with student info
    sponsorships = Sponsorship.objects.select_related(
        'student', 
        'student__user'
    ).all()
    
    # Filter sponsorships by type
    if type_filter != 'all':
        sponsorships = sponsorships.filter(sponsorship_type=type_filter)
    
    # Filter sponsorships by class
    if class_filter:
        sponsorships = sponsorships.filter(
            student__class_records__school_class__id=class_filter,
            student__class_records__is_current=True
        )
    
    # Filter sponsorships by search query
    if search_query:
        sponsorships = sponsorships.filter(
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(student__student_id__icontains=search_query) |
            Q(sponsor_name__icontains=search_query)
        )
    
    # Prepare sponsorships data for template
    sponsorship_list = []
    for sponsorship in sponsorships:
        # Get current class using the property
        current_class_name = sponsorship.student.current_class_name
        
        sponsorship_data = {
            'id': sponsorship.id,
            'student': sponsorship.student,
            'sponsorship_type': sponsorship.sponsorship_type,
            'sponsor_name': sponsorship.sponsor_name,
            'percentage_covered': sponsorship.percentage_covered,
            'notes': sponsorship.notes,
            'created_at': sponsorship.created_at,
            'updated_at': sponsorship.updated_at,
            'current_class_name': current_class_name,
            'current_class_id': None,  # We'll get this if needed
        }
        sponsorship_list.append(sponsorship_data)
    
    # Get students without sponsorship for assignment
    students_without = StudentProfile.objects.filter(
        sponsorship__isnull=True
    ).select_related('user').prefetch_related('class_records')
    
    # Filter students by class if selected
    if class_filter:
        students_without = students_without.filter(
            class_records__school_class__id=class_filter,
            class_records__is_current=True
        )
    
    # Filter students by search
    if search_query:
        students_without = students_without.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(student_id__icontains=search_query)
        )
    
    # Prepare students data for template
    student_list = []
    for student in students_without:
        # Get current class using the property
        current_class_name = student.current_class_name
        
        student_data = {
            'id': student.id,
            'user': student.user,
            'student_id': student.student_id,
            'parent_name': student.parent_name,
            'parent_contact': student.parent_contact,
            'current_class_name': current_class_name,
        }
        student_list.append(student_data)
    
    # Calculate counts
    full_count = Sponsorship.objects.filter(sponsorship_type='full').count()
    partial_count = Sponsorship.objects.filter(sponsorship_type='partial').count()
    none_count = Sponsorship.objects.filter(sponsorship_type='none').count()
    other_count = Sponsorship.objects.filter(sponsorship_type='other').count()
    total_students = StudentProfile.objects.count()
    sponsored_count = Sponsorship.objects.count()
    
    # Get available classes for filter display
    available_classes = dict(
        StudentClass.objects.filter(is_current=True)
        .select_related('school_class')
        .values_list('school_class__id', 'school_class__name')
        .distinct()
    )
    
    return {
        'sponsorships': sponsorship_list,
        'students_without': student_list,
        'full_count': full_count,
        'partial_count': partial_count,
        'none_count': none_count,
        'other_count': other_count,
        'total_students': total_students,
        'sponsored_count': sponsored_count,
        'type_filter': type_filter,
        'class_filter': class_filter,
        'search_query': search_query,
        'view_mode': view_mode,
        'classes': classes,
        'available_classes': available_classes,
    }

def create_sponsorship(request):
    """Handle sponsorship creation"""
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student')
            sponsorship_type = request.POST.get('sponsorship_type')
            sponsor_name = request.POST.get('sponsor_name', '')
            percentage_covered = request.POST.get('percentage_covered')
            notes = request.POST.get('notes', '')
            
            student = get_object_or_404(StudentProfile, id=student_id)
            
            # Validate percentage for partial scholarships
            if sponsorship_type == 'partial' and not percentage_covered:
                messages.error(request, 'Percentage covered is required for partial scholarships')
                return redirect('sponsorship_management')
            
            # Create sponsorship
            Sponsorship.objects.create(
                student=student,
                sponsorship_type=sponsorship_type,
                sponsor_name=sponsor_name if sponsorship_type != 'none' else '',
                percentage_covered=percentage_covered if sponsorship_type == 'partial' else None,
                notes=notes,
            )
            
            messages.success(request, f'Sponsorship created for {student.user.get_full_name()}!')
        except Exception as e:
            messages.error(request, f'Error creating sponsorship: {str(e)}')
    
    return redirect('sponsorship_management')

def update_sponsorship(request):
    """Handle sponsorship update"""
    if request.method == 'POST':
        try:
            sponsorship_id = request.POST.get('sponsorship_id')
            sponsorship = get_object_or_404(Sponsorship, id=sponsorship_id)
            
            sponsorship.sponsorship_type = request.POST.get('sponsorship_type')
            sponsorship.sponsor_name = request.POST.get('sponsor_name', '')
            
            percentage_covered = request.POST.get('percentage_covered')
            sponsorship.percentage_covered = percentage_covered if sponsorship.sponsorship_type == 'partial' else None
            
            sponsorship.notes = request.POST.get('notes', '')
            sponsorship.save()
            
            messages.success(request, 'Sponsorship updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating sponsorship: {str(e)}')
    
    return redirect('sponsorship_management')

def delete_sponsorship(request):
    """Handle sponsorship deletion"""
    if request.method == 'POST':
        try:
            sponsorship_id = request.POST.get('sponsorship_id')
            sponsorship = get_object_or_404(Sponsorship, id=sponsorship_id)
            student_name = f"{sponsorship.student.user.first_name} {sponsorship.student.user.last_name}"
            sponsorship.delete()
            
            messages.success(request, f'Sponsorship for {student_name} deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting sponsorship: {str(e)}')
    
    return redirect('sponsorship_management')

def get_student_info(request, student_id):
    """AJAX endpoint to get student info for modal"""
    if request.method == 'GET':
        try:
            student = get_object_or_404(StudentProfile, id=student_id)
            
            data = {
                'id': student.id,
                'name': student.user.get_full_name(),
                'student_id': student.student_id,
                'class_name': student.current_class_name,
                'parent_name': student.parent_name,
                'parent_contact': student.parent_contact,
            }
            
            return JsonResponse({'success': True, 'student': data})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def payment_management(request):
    """Single page payment management with all CRUD operations"""
    
    # Handle POST requests (Create, Update, Delete)
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create':
            return create_payment(request)
        elif action == 'update':
            return update_payment(request)
        elif action == 'delete':
            return delete_payment(request)
    
    # Handle GET requests - show main page with filters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    method_filter = request.GET.get('method', 'all')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    view_mode = request.GET.get('view', 'list')  # 'list' or 'form'
    payment_id = request.GET.get('payment_id', '')
    
    # Get selected payment for editing
    selected_payment = None
    if payment_id:
        try:
            selected_payment = get_object_or_404(Payment, id=payment_id)
            view_mode = 'form'
        except:
            pass
    
    # Get all payments
    payments = Payment.objects.select_related(
        'invoice', 'student', 'student__user'
    ).all()
    
    # Apply filters
    if status_filter != 'all':
        payments = payments.filter(status=status_filter)
    
    if method_filter != 'all':
        payments = payments.filter(payment_method=method_filter)
    
    if search_query:
        payments = payments.filter(
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(student__student_id__icontains=search_query)
        )
    
    # Date filters
    if date_from:
        try:
            date_from_obj = datetime.datetime.strptime(date_from, '%Y-%m-%d').date()
            payments = payments.filter(payment_date__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.datetime.strptime(date_to, '%Y-%m-%d').date()
            payments = payments.filter(payment_date__lte=date_to_obj)
        except ValueError:
            pass
    
    # Calculate totals
    totals = payments.aggregate(
        total_amount=Sum('amount_paid'),
        count=Count('id'),
        avg_amount=Avg('amount_paid')
    )
    
    # Get invoices for dropdown
    invoices = Invoice.objects.filter(
        status__in=['unpaid', 'partial']
    ).select_related('student', 'student__user').order_by('-created_at')
    
    # Get payment statistics by method
    by_method = payments.values('payment_method').annotate(
        total=Sum('amount_paid'),
        count=Count('id')
    ).order_by('-total')
    
    # Get today's date for default
    today = timezone.now().date()
    
    # Initialize form with or without instance
    if selected_payment:
        payments_form = PaymentsForm(instance=selected_payment)
    else:
        payments_form = PaymentsForm(initial={'payment_date': today, 'status': 'completed'})
    
    # Pagination
    paginator = Paginator(payments, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    fees = FeeStructure.objects.all()
    total_fee = sum(fee.amount for fee in fees)

    context = {
        "fees": fees,
        "total_fee": total_fee,
        "total_fee": total_fee,
        'payments_form': payments_form,
        'payments': page_obj,
        'invoices': invoices,
        'selected_payment': selected_payment,
        'total_amount': totals['total_amount'] or 0,
        'total_count': totals['count'] or 0,
        'avg_amount': totals['avg_amount'] or 0,
        'search_query': search_query,
        'status_filter': status_filter,
        'method_filter': method_filter,
        'date_from': date_from,
        'date_to': date_to,
        'view_mode': view_mode,
        'payment_id': payment_id,
        'today': today,
        'by_method': by_method,
        'page_obj': page_obj,
        'payments': page_obj,
    }
    
    return render(request, 'finance/payment_management.html', context)

def create_payment(request):
    """Handle payment creation"""
    if request.method == 'POST':
        try:
            form = PaymentsForm(request.POST)
            if form.is_valid():
                payment = form.save(commit=False)
                # Auto-update invoice status will be handled in Payment.save() method
                payment.save()
                
                messages.success(request, f'Payment of ₦{payment.amount_paid:,.2f} recorded successfully!')
                
                # Check if "Save & New" was clicked
                if 'save_and_new' in request.POST:
                    return redirect('payment_management?view=form')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
                        
        except Exception as e:
            messages.error(request, f'Error creating payment: {str(e)}')
    
    return redirect('payment_management')

def update_payment(request):
    """Handle payment update"""
    if request.method == 'POST':
        try:
            payment_id = request.POST.get('payment_id')
            payment = get_object_or_404(Payment, id=payment_id)
            
            form = PaymentsForm(request.POST, instance=payment)
            if form.is_valid():
                form.save()
                messages.success(request, 'Payment updated successfully!')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
            
        except Exception as e:
            messages.error(request, f'Error updating payment: {str(e)}')
    
    return redirect('payment_management')

def delete_payment(request):
    """Handle payment deletion"""
    if request.method == 'POST':
        try:
            payment_id = request.POST.get('payment_id')
            payment = get_object_or_404(Payment, id=payment_id)
            student_name = f"{payment.student.user.get_full_name()}"
            amount = payment.amount_paid
            
            # Store invoice reference before deletion
            invoice = payment.invoice
            
            # Delete payment
            payment.delete()
            
            # Update invoice status after deletion
            invoice.refresh_from_db()
            total_paid = invoice.payments.filter(status='completed').aggregate(
                total=Sum('amount_paid')
            )['total'] or 0
            
            invoice.amount_paid = total_paid
            invoice.amount_due = invoice.total_amount - total_paid
            
            if total_paid >= invoice.total_amount:
                invoice.status = 'paid'
            elif total_paid > 0:
                invoice.status = 'partial'
            else:
                invoice.status = 'unpaid'
            
            invoice.save()
            
            messages.success(request, f'Payment of ₦{amount:,.2f} for {student_name} deleted successfully!')
            
        except Exception as e:
            messages.error(request, f'Error deleting payment: {str(e)}')
    
    return redirect('payment_management')


def record_payment(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if request.method == 'POST':
        form = RecordPaymentForm(request.POST, invoice=invoice)
        
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.student = invoice.student
            payment.payment_date = timezone.now().date()
            payment.save()
            
            messages.success(request, f'Payment of ${payment.amount_paid:.2f} recorded successfully!')
            return redirect('invoice_detail', invoice_id=invoice.id)
    else:
        form = RecordPaymentForm(invoice=invoice)
    
    # Use your existing view or create a specific one
    context = {
        'invoice': invoice,
        'form': form,
    }
    return render(request, 'finance/record_payment.html', context)
@login_required


def get_invoice_info(request, invoice_id):
    """AJAX endpoint to get invoice info"""
    if request.method == 'GET':
        try:
            invoice = get_object_or_404(Invoice, id=invoice_id)
            
            # Calculate sponsorship discount if any
            discount = 0
            try:
                sponsorship = Sponsorship.objects.get(student=invoice.student)
                if sponsorship.sponsorship_type == 'full':
                    discount = float(invoice.total_amount)
                elif sponsorship.sponsorship_type == 'partial' and sponsorship.percentage_covered:
                    discount = (float(invoice.total_amount) * sponsorship.percentage_covered) / 100
            except Sponsorship.DoesNotExist:
                pass
            
            data = {
                'student_name': invoice.student.user.get_full_name(),
                'student_id': invoice.student.student_id,
                'total_amount': float(invoice.total_amount),
                'amount_paid': float(invoice.amount_paid),
                'amount_due': float(invoice.amount_due),
                'discount': discount,
                'payable_amount': float(invoice.total_amount - discount),
                'status': invoice.status,
                'academic_year': str(invoice.academic_year),
                'term': str(invoice.term),
            }
            
            return JsonResponse({'success': True, 'invoice': data})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def payment_receipt(request, payment_id):
    """Generate payment receipt"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    context = {
        'payment': payment,
        'today': timezone.now().date(),
    }
    
    return render(request, 'finance/payment_receipt.html', context)



@login_required
def fee_management(request):
    """Fee management view with invoice generation"""
    
    # Handle POST requests
    if request.method == 'POST':
        print("Handling POST request...", request.POST)
        action = request.POST.get('action')

        if action == 'generate_invoice':
            return generate_invoices(request)
        elif action == 'add_fee_type':
            return add_fee_type(request)
        elif action == 'edit_fee_type':
            return edit_fee_type(request)
        elif action == 'delete_fee_type':
            return delete_fee_type(request)
        elif action == 'add_fee_structure':
            return add_fee_structure(request)
        elif action == 'edit_fee_structure':
            return edit_fee_structure(request)
        elif action == 'delete_fee_structure':
            return delete_fee_structure(request)

    
    # Handle GET requests
    class_filter = request.GET.get('class', 'all')
    academic_year_filter = request.GET.get('academic_year', 'all')
    term_filter = request.GET.get('term', 'all')
    
    # Get current academic year
    current_year = AcademicYear.objects.filter(is_active=True).first()

    # Get all fee types
    fee_types = FeeType.objects.all().order_by('name')
    
    # Get all classes
    classes = SchoolClass.objects.all().order_by('name')
    
    # Get all academic years
    academic_years = AcademicYear.objects.all().order_by('-year')
    
    # Get all terms
    terms = Term.objects.all()
    
    # Get all fee structures with filters
    fee_structures = FeeStructure.objects.select_related(
        'fee_type', 'school_class', 'academic_year', 'term'
    ).all()
    
    # Apply filters
    if class_filter != 'all':
        fee_structures = fee_structures.filter(school_class__name=class_filter)
    
    if academic_year_filter != 'all':
        fee_structures = fee_structures.filter(academic_year__year=academic_year_filter)
    
    if term_filter != 'all':
        fee_structures = fee_structures.filter(term__name=term_filter)
    
    # Group fee structures by class and academic year
    grouped_fees = {}
    for fee in fee_structures:
        key = (fee.school_class.name, fee.academic_year.year)
        grouped_fees.setdefault(key, []).append(fee)
    
    # Get all students with their current class and sponsorship info
    students_in_class = StudentProfile.objects.select_related(
        'user', 'sponsorship'
    ).prefetch_related(
        Prefetch(
            'class_records',
            queryset=StudentClass.objects.filter(is_current=True).select_related('school_class'),
            to_attr='current_classes'
        )
    ).filter(is_active=True).order_by('user__last_name')
    
    # Calculate estimated total for each class
    estimated_totals = {}
    for key, fees in grouped_fees.items():
        class_name = key[0]
        # Count students in this class by checking their current_classes
        student_count = 0
        for student in students_in_class:
            for class_record in student.current_classes:
                if class_record.school_class.name == class_name:
                    student_count += 1
                    break
        
        total_fees = sum(fee.amount for fee in fees)
        estimated_totals[key] = student_count * total_fees
    
    # Forms
    fee_type_form = FeeTypeForm()
    fee_structure_form = FeeStructureForm()
    
    context = {
        'fee_types': fee_types,
        'fee_type_form': fee_type_form,
        'fee_structure_form': fee_structure_form,
        'grouped_fees': grouped_fees,
        'classes': classes,
        'academic_years': academic_years,
        'terms': terms,
        'class_filter': class_filter,
        'academic_year_filter': academic_year_filter,
        'term_filter': term_filter,
        'current_year': current_year,
        'students_in_class': students_in_class,
        'estimated_total': sum(estimated_totals.values()) if estimated_totals else 0,
    }
    
    return render(request, 'finance/fee_management.html', context)



def generate_invoices(request):
    """Generate invoices for all students in a class considering sponsorship"""
    if request.method != 'POST':
        return redirect('fee_management')

    try:
        school_class_id = request.POST.get('school_class_id')
        academic_year_id = request.POST.get('academic_year_id')
        term_id = request.POST.get('term_id')
        skip_existing = request.POST.get('skip_existing') == 'on'
        apply_sponsorship = request.POST.get('apply_sponsorship') == 'on'

        # Get the class, academic year, and term
        school_class = get_object_or_404(SchoolClass, id=school_class_id)
        academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
        term = get_object_or_404(Term, id=term_id)

        # Get all fee structures for this class, academic year, and term
        fee_structures = FeeStructure.objects.filter(
            school_class=school_class,
            academic_year=academic_year,
            term=term
        )

        if not fee_structures.exists():
            messages.error(
                request,
                f'No fee structure found for {school_class.name} in {academic_year.year} - {term.name}'
            )
            return redirect('fee_management')

        # Get all active students in this class
        student_class_records = StudentClass.objects.filter(
            school_class=school_class,
            academic_year=academic_year,
            is_current=True
        ).select_related('student', 'student__user', 'student__sponsorship')

        if not student_class_records.exists():
            messages.error(request, f'No active students found in {school_class.name}')
            return redirect('fee_management')

        created_count = 0
        skipped_count = 0
        errors = []

        for student_class in student_class_records:
            student = student_class.student

            try:
                # Skip if invoice already exists
                if skip_existing and Invoice.objects.filter(
                    student=student,
                    academic_year=academic_year,
                    term=term
                ).exists():
                    skipped_count += 1
                    continue

                total_amount = Decimal('0.00')
                invoice_items = []

                # Calculate fees per fee structure
                for fee_structure in fee_structures:
                    fee_amount = fee_structure.amount

                    if apply_sponsorship and hasattr(student, 'sponsorship'):
                        sponsorship = student.sponsorship
                        if sponsorship.sponsorship_type == 'full':
                            fee_amount = Decimal('0.00')
                        elif sponsorship.sponsorship_type == 'partial' and sponsorship.percentage_covered:
                            discount = Decimal(sponsorship.percentage_covered) / Decimal('100')
                            fee_amount = fee_amount * (Decimal('1') - discount)

                    total_amount += fee_amount
                    invoice_items.append({
                        'fee_type': fee_structure.fee_type,
                        'amount': fee_amount
                    })

                # Create invoice
                invoice = Invoice.objects.create(
                    student=student,
                    academic_year=academic_year,
                    term=term,
                    total_amount=total_amount,
                    amount_due=total_amount,
                    status='unpaid'
                )

                # Create invoice items
                for item_data in invoice_items:
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        fee_type=item_data['fee_type'],
                        amount=item_data['amount']
                    )

                # Add notes about sponsorship
                if apply_sponsorship and hasattr(student, 'sponsorship'):
                    sponsorship = student.sponsorship
                    invoice.notes = f"Sponsorship: {sponsorship.get_sponsorship_type_display()}"
                    if sponsorship.sponsorship_type == 'partial' and sponsorship.percentage_covered:
                        invoice.notes += f" ({sponsorship.percentage_covered}% covered)"
                    invoice.save()

                created_count += 1

            except Exception as e:
                errors.append(f"{student.user.get_full_name()}: {str(e)}")

        # Show success messages
        if created_count > 0:
            msg = f'Successfully created {created_count} invoices for {school_class.name} ({academic_year.year} - {term.name})'
            if skipped_count > 0:
                msg += f', skipped {skipped_count} existing invoices'
            messages.success(request, msg)

        if errors:
            err_msg = f'Errors occurred while creating invoices:<br>' + '<br>'.join(errors[:5])
            if len(errors) > 5:
                err_msg += f'<br>... and {len(errors) - 5} more errors'
            messages.error(request, err_msg)

    except Exception as e:
        messages.error(request, f'Error generating invoices: {str(e)}')

    return redirect('fee_management')


def add_fee_type(request):
    """Add new fee type"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            is_recurring = request.POST.get('is_recurring') == 'on'
            
            if not name:
                messages.error(request, 'Fee type name is required')
                return redirect('fee_management')
            
            FeeType.objects.create(
                name=name,
                description=description,
                is_recurring=is_recurring
            )
            
            messages.success(request, f'Fee type "{name}" created successfully!')
            
        except Exception as e:
            messages.error(request, f'Error creating fee type: {str(e)}')
    
    return redirect('fee_management')

def edit_fee_type(request):
    """Edit existing fee type"""
    if request.method == 'POST':
        try:
            fee_type_id = request.POST.get('fee_type_id')
            fee_type = get_object_or_404(FeeType, id=fee_type_id)
            
            fee_type.name = request.POST.get('name')
            fee_type.description = request.POST.get('description', '')
            fee_type.is_recurring = request.POST.get('is_recurring') == 'on'
            fee_type.save()
            
            messages.success(request, f'Fee type "{fee_type.name}" updated successfully!')
            
        except Exception as e:
            messages.error(request, f'Error updating fee type: {str(e)}')
    
    return redirect('fee_management')

def delete_fee_type(request):
    """Delete fee type"""
    if request.method == 'POST':
        try:
            fee_type_id = request.POST.get('fee_type_id')
            fee_type = get_object_or_404(FeeType, id=fee_type_id)
            
            # Check if fee type is used in any fee structure
            if FeeStructure.objects.filter(fee_type=fee_type).exists():
                messages.error(request, f'Cannot delete "{fee_type.name}" because it is used in fee structures')
                return redirect('fee_management')
            
            fee_type_name = fee_type.name
            fee_type.delete()
            
            messages.success(request, f'Fee type "{fee_type_name}" deleted successfully!')
            
        except Exception as e:
            messages.error(request, f'Error deleting fee type: {str(e)}')
    
    return redirect('fee_management')

def add_fee_structure(request):
    """Add new fee structure"""
    if request.method == 'POST':
        form = FeeStructureForm(request.POST)
        if form.is_valid():
            try:
                fee_structure = form.save()
                messages.success(request, 'Fee structure added successfully!')
            except Exception as e:
                messages.error(request, f'Error adding fee structure: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    
    return redirect('fee_management')

def edit_fee_structure(request):
    """Edit existing fee structure"""
    if request.method == 'POST':
        try:
            fee_structure_id = request.POST.get('fee_structure_id')
            fee_structure = get_object_or_404(FeeStructure, id=fee_structure_id)
            
            fee_structure.fee_type_id = request.POST.get('fee_type')
            fee_structure.school_class_id = request.POST.get('school_class')
            fee_structure.academic_year_id = request.POST.get('academic_year')
            fee_structure.term_id = request.POST.get('term')
            fee_structure.amount = request.POST.get('amount')
            fee_structure.save()
            
            messages.success(request, 'Fee structure updated successfully!')
            
        except Exception as e:
            messages.error(request, f'Error updating fee structure: {str(e)}')
    
    return redirect('fee_management')

def delete_fee_structure(request):
    """Delete fee structure"""
    if request.method == 'POST':
        try:
            fee_structure_id = request.POST.get('fee_structure_id')
            fee_structure = get_object_or_404(FeeStructure, id=fee_structure_id)
            
            fee_structure.delete()
            
            messages.success(request, 'Fee structure deleted successfully!')
            
        except Exception as e:
            messages.error(request, f'Error deleting fee structure: {str(e)}')
    
    return redirect('fee_management')

@login_required
def delete_fee_type(request, type_id):
    """Delete fee type"""
    if request.method == 'POST':
        fee_type = get_object_or_404(FeeType, id=type_id)
        fee_type.delete()
        messages.success(request, 'Fee type deleted successfully')
    
    return redirect('fee_management')


@login_required
def term_invoices(request, class_id, term_id, academic_year_id):
    """
    View for displaying invoices for a specific class, term, and academic year.
    """
    # Get the objects
    school_class = get_object_or_404(SchoolClass, id=class_id)
    term = get_object_or_404(Term, id=term_id)
    academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
    
    # Get students in this class
    students = StudentProfile.objects.filter(
        class_records__school_class=school_class,
        class_records__is_current=True,
        is_active=True
    ).select_related('user').distinct()


    
    # Get fee structure for this class, term, and academic year
    fee_structures = FeeStructure.objects.filter(
        school_class=school_class,
        term=term,
        academic_year=academic_year
    ).select_related('fee_type')
    
    # Get invoices for this term and class
    invoices = Invoice.objects.filter(
        student__class_records__school_class=school_class,
        student__class_records__is_current=True,
        term=term,
        academic_year=academic_year
    ).select_related('student__user').prefetch_related('payments').distinct()


    
    # Apply search filter
    search_query = request.GET.get('search', '')
    if search_query:
        invoices = invoices.filter(
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(student__student_id__icontains=search_query)
        )
    
    # Apply status filter
    status_filter = request.GET.get('status', '')
    if status_filter and status_filter != 'all':
        invoices = invoices.filter(status=status_filter)
    
    # Calculate statistics
    total_invoices = invoices.count()
    total_amount = invoices.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    total_paid = sum(
        invoice.total_amount - invoice.amount_due 
        for invoice in invoices
    )
    total_due = total_amount - total_paid
    
    # Get counts by status
    status_counts = invoices.values('status').annotate(count=Count('id'))
    unpaid_count = next((item['count'] for item in status_counts if item['status'] == 'unpaid'), 0)
    partial_count = next((item['count'] for item in status_counts if item['status'] == 'partial'), 0)
    paid_count = next((item['count'] for item in status_counts if item['status'] == 'paid'), 0)
    
    # Pagination
    paginator = Paginator(invoices, 25)  # Show 25 invoices per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'school_class': school_class,
        'term': term,
        'academic_year': academic_year,
        'students': students,
        'fee_structures': fee_structures,
        'page_obj': page_obj,
        'total_invoices': total_invoices,
        'total_amount': total_amount,
        'total_paid': total_paid,
        'total_due': total_due,
        'unpaid_count': unpaid_count,
        'partial_count': partial_count,
        'paid_count': paid_count,
        'search_query': search_query,
    }
    
    return render(request, 'finance/term_invoices.html', context)

@login_required
def generate_term_invoices(request):
    """
    View to generate invoices for all students in a class for a specific term.
    """
    if request.method == 'POST':
        school_class_id = request.POST.get('school_class_id')
        term_id = request.POST.get('term_id')
        academic_year_id = request.POST.get('academic_year_id')
        
        school_class = get_object_or_404(SchoolClass, id=school_class_id)
        term = get_object_or_404(Term, id=term_id)
        academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
        
        # Get fee structure
        fee_structures = FeeStructure.objects.filter(
            school_class=school_class,
            term=term,
            academic_year=academic_year
        )
        
        if not fee_structures.exists():
            messages.error(request, 'No fee structure found for this class, term, and academic year.')
            return redirect('term_invoices', school_class_id, term_id, academic_year_id)
        
        # Get all active students in the class
        students = StudentProfile.objects.filter(
            current_class=school_class,
            is_active=True
        )
        
        skip_existing = request.POST.get('skip_existing') == 'on'
        apply_sponsorship = request.POST.get('apply_sponsorship') == 'on'
        send_notifications = request.POST.get('send_notifications') == 'on'
        
        created_invoices = 0
        skipped_invoices = 0
        
        for student in students:
            # Check if invoice already exists
            existing_invoice = Invoice.objects.filter(
                student=student,
                term=term,
                academic_year=academic_year
            ).exists()
            
            if skip_existing and existing_invoice:
                skipped_invoices += 1
                continue
            
            # Calculate total amount from fee structure
            total_amount = sum(fee.amount for fee in fee_structures)
            
            # Apply sponsorship discount if applicable
            if apply_sponsorship:
                try:
                    sponsorship = student.sponsorship
                    if sponsorship.sponsorship_type == 'full':
                        total_amount = Decimal('0')
                    elif sponsorship.sponsorship_type == 'partial' and sponsorship.percentage_covered:
                        discount = total_amount * (Decimal(sponsorship.percentage_covered) / Decimal('100'))
                        total_amount = total_amount - discount
                except Sponsorship.DoesNotExist:
                    pass  # No sponsorship, use full amount
            
            # Create invoice
            invoice = Invoice.objects.create(
                student=student,
                term=term,
                academic_year=academic_year,
                total_amount=total_amount,
                amount_due=total_amount,
                status='unpaid'
            )
            
            # Create invoice items
            for fee_structure in fee_structures:
                invoice.items.create(
                    fee_type=fee_structure.fee_type,
                    amount=fee_structure.amount
                )
            
            created_invoices += 1
            
            # TODO: Send notification if requested
            # if send_notifications:
            #     send_invoice_notification(invoice)
        
        messages.success(
            request, 
            f'Successfully generated {created_invoices} invoices. {skipped_invoices} invoices were skipped.'
        )
        
        return redirect('term_invoices', school_class_id, term_id, academic_year_id)
    
    return redirect('fee_management')

@login_required
def record_payment(request, invoice_id):
    """
    View to record a payment for an invoice.
    """
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if request.method == 'POST':
        amount_paid = Decimal(request.POST.get('amount_paid'))
        payment_method = request.POST.get('payment_method')
        payment_date = request.POST.get('payment_date')
        notes = request.POST.get('notes', '')
        
        # Validate amount
        if amount_paid <= 0:
            messages.error(request, 'Payment amount must be greater than 0.')
        elif amount_paid > invoice.amount_due:
            messages.error(request, f'Payment amount cannot exceed amount due (₦{invoice.amount_due:,.2f}).')
        else:
            # Create payment
            payment = Payment.objects.create(
                invoice=invoice,
                student=invoice.student,
                payment_date=payment_date,
                amount_paid=amount_paid,
                payment_method=payment_method,
                notes=notes,
                status='completed'
            )
            
            messages.success(request, f'Payment of ₦{amount_paid:,.2f} recorded successfully.')
            
            # Recalculate invoice status
            invoice.recalculate()
    
    return redirect('invoice_detail', invoice_id=invoice_id)

@login_required
def invoice_detail(request, invoice_id):
    """
    View for individual invoice detail page.
    """
    invoice = get_object_or_404(
        Invoice.objects.select_related(
            'student__user',  # student info
            'term',
            'academic_year',
        ).prefetch_related(
            'student__studentscore_set',  # if you want their scores
            'items',                      # invoice items
            'payments',                    # payment history
        ),
        id=invoice_id
    )


    
    # Get sponsorship info if exists
    # Get sponsorship info if exists
    try:
        sponsorship = invoice.student.sponsorship
    except Sponsorship.DoesNotExist:
        sponsorship = None

    
    # Get payment history
    payments = invoice.payments.all().order_by('-payment_date')
    
    # Calculate total paid
    total_paid = sum(payment.amount_paid for payment in payments)
    
    # Update invoice status if needed
    if total_paid >= invoice.total_amount:
        invoice.status = 'paid'
    elif total_paid > 0:
        invoice.status = 'partial'
    else:
        invoice.status = 'unpaid'
    invoice.save()
    
    context = {
        'invoice': invoice,
        'sponsorship': sponsorship,
        'payments': payments,
        'total_paid': total_paid,
    }
    
    return render(request, 'finance/invoice_detail.html', context)


@login_required
def send_reminder(request, invoice_id):
    """Send payment reminder for invoice"""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    # Logic to send reminder email/SMS
    # You can integrate with email sending service
    
    messages.success(request, f"Payment reminder sent for Invoice #{invoice.invoice_number}")
    return redirect('invoice_detail', invoice_id=invoice.id)

@login_required
def update_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    # Handle your form here
    if request.method == 'POST':
        # process form
        pass
    
    context = {'invoice': invoice}
    return render(request, 'finance/update_invoice.html', context)


@login_required
def delete_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if request.method == 'POST':
        invoice.delete()
        messages.success(request, "Invoice deleted successfully.")
        return redirect('term_invoices', class_id=invoice.student.class_records.first().school_class.id, 
                        term_id=invoice.term.id, 
                        academic_year_id=invoice.academic_year.id)
    
    context = {'invoice': invoice}
    return render(request, 'finance/confirm_delete_invoice.html', context)
