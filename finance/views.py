# finance/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json
from django.http import JsonResponse

from .models import Sponsorship, FeeType, FeeStructure, Invoice, InvoiceItem, Payment
from .forms import FeeStructureForm, FeeTypeForm

from students.models import StudentProfile
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
        'invoice', 'invoice__student', 'received_by'
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
    
    if status_filter != 'all':
        invoices = invoices.filter(status=status_filter)
    
    if class_filter != 'all':
        invoices = invoices.filter(student__current_class_id=class_filter)
    
    if search_query:
        invoices = invoices.filter(
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(student__admission_number__icontains=search_query)
        )
    
    # Order by creation date (newest first)
    invoices = invoices.order_by('-created_at')
    
    # Pagination
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


# finance/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from academics.models import SchoolClass, AcademicYear, Term
from .models import FeeType, FeeStructure, Invoice
from .forms import FeeTypeForm, FeeStructureForm

@login_required
def fee_management(request):
    # Fee Type CRUD
    fee_types = FeeType.objects.all().order_by('name')
    fee_type_form = FeeTypeForm()
    
    # Fee Structure data
    fee_structures = FeeStructure.objects.select_related(
        'fee_type', 'school_class', 'academic_year', 'term'
    ).order_by('school_class__name', 'academic_year__year', 'term__name')
    
    fee_structure_form = FeeStructureForm()
    
    # Get filter values
    class_filter = request.GET.get('class', 'all')
    academic_year_filter = request.GET.get('academic_year', 'all')
    term_filter = request.GET.get('term', 'all')
    
    # Handle POST requests for CRUD operations
    if request.method == "POST":
        action = request.POST.get("action")
        
        # ➕ CREATE Fee Type
        if action == "add_fee_type":
            fee_type_form = FeeTypeForm(request.POST)
            if fee_type_form.is_valid():
                fee_type = fee_type_form.save()
                messages.success(request, f"Fee type '{fee_type.name}' added successfully")
                return redirect("fee_management")
        
        # ✏️ UPDATE Fee Type
        elif action == "edit_fee_type":
            fee_type_id = request.POST.get("fee_type_id")
            fee_type = get_object_or_404(FeeType, id=fee_type_id)
            form = FeeTypeForm(request.POST, instance=fee_type)
            if form.is_valid():
                form.save()
                messages.success(request, f"Fee type updated successfully")
                return redirect("fee_management")
        
        # 🗑 DELETE Fee Type
        elif action == "delete_fee_type":
            fee_type_id = request.POST.get("fee_type_id")
            fee_type = get_object_or_404(FeeType, id=fee_type_id)
            fee_type_name = fee_type.name
            fee_type.delete()
            messages.success(request, f"Fee type '{fee_type_name}' deleted successfully")
            return redirect("fee_management")
        
        # ➕ CREATE Fee Structure
        elif action == "add_fee_structure":
            fee_structure_form = FeeStructureForm(request.POST)
            if fee_structure_form.is_valid():
                fee_structure = fee_structure_form.save()
                messages.success(request, f"Fee structure for {fee_structure.fee_type.name} added successfully")
                return redirect("fee_management")
        
        # ✏️ UPDATE Fee Structure
        elif action == "edit_fee_structure":
            fee_structure_id = request.POST.get("fee_structure_id")
            fee_structure = get_object_or_404(FeeStructure, id=fee_structure_id)
            form = FeeStructureForm(request.POST, instance=fee_structure)
            if form.is_valid():
                form.save()
                messages.success(request, f"Fee structure updated successfully")
                return redirect("fee_management")
        
        # 🗑 DELETE Fee Structure
        elif action == "delete_fee_structure":
            fee_structure_id = request.POST.get("fee_structure_id")
            fee_structure = get_object_or_404(FeeStructure, id=fee_structure_id)
            fee_structure.delete()
            messages.success(request, f"Fee structure deleted successfully")
            return redirect("fee_management")
    
    # Apply filters
    if class_filter != 'all':
        fee_structures = fee_structures.filter(school_class__name=class_filter)
    if academic_year_filter != 'all':
        fee_structures = fee_structures.filter(academic_year__year=academic_year_filter)
    if term_filter != 'all':
        fee_structures = fee_structures.filter(term__name=term_filter)
    
    # Get active academic year
    try:
        current_year = AcademicYear.objects.get(is_active=True)
    except AcademicYear.DoesNotExist:
        current_year = None
    
    # Group fee structures for display
    grouped_fees = {}
    for fee in fee_structures:
        key = (fee.school_class.name, fee.academic_year.year)
        if key not in grouped_fees:
            grouped_fees[key] = []
        grouped_fees[key].append(fee)
    
    # Calculate total for each group
    group_totals = {}
    for key, fees in grouped_fees.items():
        group_totals[key] = sum(fee.amount for fee in fees)
    
    context = {
        "fee_types": fee_types,
        "fee_type_form": fee_type_form,
        "fee_structures": fee_structures,
        "grouped_fees": grouped_fees,
        "group_totals": group_totals,
        "fee_structure_form": fee_structure_form,
        "class_filter": class_filter,
        "academic_year_filter": academic_year_filter,
        "term_filter": term_filter,
        "classes": SchoolClass.objects.all().order_by('name'),
        "academic_years": AcademicYear.objects.all().order_by('-year'),
        "terms": Term.objects.all(),
        "current_year": current_year.year if current_year else "Not Set",
        "pending_invoices": Invoice.objects.filter(status="unpaid").count(),
    }
    
    return render(request, "finance/fee_management.html", context)

@login_required
def sponsorship_management(request):
    """Manage student sponsorships"""
    
    sponsorships = Sponsorship.objects.select_related(
        'student', 'student__user', 'student__current_class'
    ).all()
    
    students = StudentProfile.objects.select_related('user', 'current_class').all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_sponsorship':
            student_id = request.POST.get('student')
            sponsorship_type = request.POST.get('sponsorship_type')
            sponsor_name = request.POST.get('sponsor_name')
            percentage_covered = request.POST.get('percentage_covered')
            notes = request.POST.get('notes')
            
            student = get_object_or_404(StudentProfile, id=student_id)
            
            sponsorship, created = Sponsorship.objects.update_or_create(
                student=student,
                defaults={
                    'sponsorship_type': sponsorship_type,
                    'sponsor_name': sponsor_name,
                    'percentage_covered': percentage_covered if percentage_covered else None,
                    'notes': notes,
                }
            )
            
            message = 'updated' if not created else 'added'
            messages.success(request, f'Sponsorship {message} successfully')
            
        elif action == 'delete_sponsorship':
            sponsorship_id = request.POST.get('sponsorship_id')
            sponsorship = get_object_or_404(Sponsorship, id=sponsorship_id)
            sponsorship.delete()
            messages.success(request, 'Sponsorship deleted successfully')
    
    # Group sponsorships by type for summary
    sponsorship_summary = sponsorships.values('sponsorship_type').annotate(
        count=Count('id')
    )
    
    context = {
        'sponsorships': sponsorships,
        'students': students,
        'sponsorship_summary': sponsorship_summary,
        'SPONSORSHIP_TYPES': Sponsorship.SPONSORSHIP_TYPE,
        'pending_invoices': Invoice.objects.filter(status='unpaid').count(),
    }
    
    return render(request, 'finance/sponsorship_management.html', context)

@login_required
def finance_reports(request):
    """Generate financial reports"""
    
    # Get report parameters
    report_type = request.GET.get('report_type', 'revenue')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    class_id = request.GET.get('class', 'all')
    
    # Default date range (last 30 days)
    if not start_date:
        start_date = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = timezone.now().strftime('%Y-%m-%d')
    
    # Convert to datetime
    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Base queryset for payments
    payments = Payment.objects.filter(
        payment_date__date__gte=start_datetime,
        payment_date__date__lte=end_datetime
    ).select_related('invoice', 'invoice__student')
    
    if class_id != 'all':
        payments = payments.filter(invoice__student__current_class_id=class_id)
    
    # Generate report data based on type
    report_data = {}
    
    if report_type == 'revenue':
        # Daily revenue breakdown
        daily_revenue = []
        current_date = start_datetime
        while current_date <= end_datetime:
            day_revenue = payments.filter(
                payment_date__date=current_date
            ).aggregate(total=Sum('amount_paid'))['total'] or 0
            
            daily_revenue.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'revenue': float(day_revenue),
                'count': payments.filter(payment_date__date=current_date).count()
            })
            current_date += timedelta(days=1)
        
        report_data['daily_revenue'] = daily_revenue
        
    elif report_type == 'payment_methods':
        # Payment method breakdown
        method_breakdown = payments.values('payment_method').annotate(
            total=Sum('amount_paid'),
            count=Count('id')
        )
        report_data['method_breakdown'] = list(method_breakdown)
        
    elif report_type == 'class_performance':
        # Revenue by class
        class_performance = payments.values(
            'invoice__student__current_class__name'
        ).annotate(
            total=Sum('amount_paid'),
            count=Count('id')
        ).order_by('-total')
        report_data['class_performance'] = list(class_performance)
    
    # Summary statistics
    total_revenue = payments.aggregate(total=Sum('amount_paid'))['total'] or 0
    total_payments = payments.count()
    average_payment = total_revenue / total_payments if total_payments > 0 else 0
    
    classes = SchoolClass.objects.all()
    
    context = {
        'report_type': report_type,
        'start_date': start_date,
        'end_date': end_date,
        'class_id': class_id,
        'report_data': report_data,
        'total_revenue': total_revenue,
        'total_payments': total_payments,
        'average_payment': average_payment,
        'classes': classes,
        'pending_invoices': Invoice.objects.filter(status='unpaid').count(),
    }
    
    return render(request, 'finance/finance_reports.html', context)

@login_required
def get_student_info(request):
    """AJAX endpoint to get student information"""
    student_id = request.GET.get('student_id')
    
    if student_id:
        try:
            student = StudentProfile.objects.get(id=student_id)
            sponsorship = Sponsorship.objects.filter(student=student).first()
            
            data = {
                'name': student.user.get_full_name(),
                'admission_number': student.admission_number,
                'class_name': student.current_class.name if student.current_class else 'N/A',
                'has_sponsorship': sponsorship is not None,
                'sponsorship_type': sponsorship.sponsorship_type if sponsorship else 'none',
                'percentage_covered': sponsorship.percentage_covered if sponsorship else 0,
            }
            return JsonResponse(data)
        except StudentProfile.DoesNotExist:
            return JsonResponse({'error': 'Student not found'}, status=404)
    
    return JsonResponse({'error': 'No student ID provided'}, status=400)

@login_required
def delete_fee_structure(request, structure_id):
    """Delete fee structure"""
    if request.method == 'POST':
        fee_structure = get_object_or_404(FeeStructure, id=structure_id)
        fee_structure.delete()
        messages.success(request, 'Fee structure deleted successfully')
    
    return redirect('fee_management')

@login_required
def delete_fee_type(request, type_id):
    """Delete fee type"""
    if request.method == 'POST':
        fee_type = get_object_or_404(FeeType, id=type_id)
        fee_type.delete()
        messages.success(request, 'Fee type deleted successfully')
    
    return redirect('fee_management')