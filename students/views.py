from io import BytesIO
from collections import defaultdict

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Avg, Q, Sum
from django.conf import settings

from .models import StudentProfile, StudentScore, StudentClass
from school_admin.models import SystemSettings
from finance.models import Invoice, Sponsorship
from academics.models import AcademicYear, Term, ScoreType
from staff.models import TeacherSubject
# PDF Generation imports
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER

from .utils import *


@login_required
def student_dashboard(request):
    try:
        student = StudentProfile.objects.get(id=2)  # For testing
    except:
        student = StudentProfile.objects.first()
    academic_session = AcademicYear.objects.filter(is_active=True).first()
    current_term = academic_session.terms.filter(is_current=True).first() if academic_session else None
    
    # Calculate scores for all terms in current academic year
    term_scores = []
    current_term_average = None
    current_term_rank = None
    if academic_session:
        terms = academic_session.terms.all()
        for term in terms:
            # Get average score for this term
            avg_result = StudentScore.objects.filter(
                student=student,
                academic_session=academic_session,
                term=term
            ).aggregate(avg_score=Avg('score'))
            
            average_score = avg_result['avg_score']
            if average_score is not None:
                average_score = round(average_score, 2)
            
            # Get class rank for this term
            rank = student.class_rank(academic_session, term)
            
            # Get class size for this term
            current_class_record = student.class_records.filter(is_current=True).first()
            class_size = None
            if current_class_record:
                class_size = StudentClass.objects.filter(
                    school_class=current_class_record.school_class,
                    academic_year=academic_session,
                    is_current=True
                ).count()
            
            # Get subject scores for this term
            subject_scores = StudentScore.objects.filter(
                student=student,
                academic_session=academic_session,
                term=term
            ).select_related('subject').values('subject__name').annotate(
                avg_score=Avg('score')
            ).order_by('-avg_score')
            
            # Format subject scores
            formatted_subject_scores = [
                {
                    'subject': score['subject__name'],
                    'score': round(score['avg_score'], 2) if score['avg_score'] else None
                }
                for score in subject_scores
            ]
            term_scores.append({
                'term': term,
                'academic_year': academic_session,
                'average_score': average_score,
                'rank': rank,
                'class_size': class_size,
                'subject_scores': formatted_subject_scores,
            })
            
            # Store current term data separately
            if term.is_current:
                current_term_average = average_score
                current_term_rank = rank
    
    # Get invoices organized by term
    all_invoices_by_term = []
    recent_invoices = []
    
    if academic_session:
        terms = academic_session.terms.all()
        
        for term in terms:
            invoice = Invoice.objects.filter(
                student=student,
                academic_year=academic_session,
                term=term
            ).first()
            
            if invoice:
                payments = invoice.payments.filter(status='completed').order_by('-payment_date')
                recent_invoices.append(invoice)
                
                all_invoices_by_term.append({
                    'term': term,
                    'invoice': invoice,
                    'payments': payments
                })
            else:
                all_invoices_by_term.append({
                    'term': term,
                    'invoice': None,
                    'payments': []
                })
    
    # Get current invoice for dashboard
    current_invoice = None
    if academic_session and current_term:
        current_invoice = Invoice.objects.filter(
            student=student,
            academic_year=academic_session,
            term=current_term
        ).first()
    
    # Get sponsorship info
    sponsorship = Sponsorship.objects.filter(student=student).first()
    
    context = {
        "student": student,
        "academic_session": academic_session,
        "current_term": current_term,
        "current_term_average": current_term_average,
        "current_term_rank": current_term_rank,
        "class_size": StudentClass.objects.filter(
            school_class=student.class_records.filter(is_current=True).first().school_class,
            academic_year=academic_session,
            is_current=True
        ).count() if academic_session else None,
        "current_invoice": current_invoice,
        "term_scores": term_scores,
        "all_invoices_by_term": all_invoices_by_term,
        "recent_invoices": recent_invoices[:3],  # Last 3 invoices
        "sponsorship": sponsorship,
    }
    
    return render(request, "student/student_dashboard.html", context)


@login_required
def student_invoices(request):
    """Dedicated invoices page"""
    student = get_object_or_404(StudentProfile, id=2)
    
    # Get filter parameters
    year_filter = request.GET.get('year', 'all')
    term_filter = request.GET.get('term', 'all')
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')
    
    # Get all academic years the student has been in
    academic_years = AcademicYear.objects.filter(
        studentclass__student=student
    ).distinct().order_by('-year')
    
    # Get current academic year
    current_academic_year = AcademicYear.objects.filter(is_active=True).first()
    
    # Get all invoices with related data
    invoices = Invoice.objects.filter(
        student=student
    ).select_related(
        'academic_year', 'term'
    ).prefetch_related(
        'items', 'payments'
    ).order_by('-academic_year__year', 'term__name')
    
    # Apply filters
    if search_query:
        invoices = invoices.filter(
            Q(id__icontains=search_query) |
            Q(term__name__icontains=search_query) |
            Q(academic_year__year__icontains=search_query)
        )
    
    if year_filter == 'current':
        if current_academic_year:
            invoices = invoices.filter(academic_year=current_academic_year)
    elif year_filter not in ['all', 'older']:
        invoices = invoices.filter(academic_year__year__icontains=year_filter)
    elif year_filter == 'older':
        # Get invoices from previous years
        if current_academic_year:
            invoices = invoices.exclude(academic_year=current_academic_year)
    
    if term_filter != 'all':
        invoices = invoices.filter(term__name__icontains=term_filter)
    
    if status_filter != 'all':
        invoices = invoices.filter(status=status_filter)
    
    # Group invoices by academic year
    invoices_by_year = {}
    for invoice in invoices:
        year_name = invoice.academic_year.year  # Changed from .name to .year
        if year_name not in invoices_by_year:
            invoices_by_year[year_name] = []
        invoices_by_year[year_name].append(invoice)
    
    # Get current invoice for download button
    current_invoice = None
    if current_academic_year:
        current_term = Term.objects.filter(is_current=True).first()
        if current_term:
            current_invoice = invoices.filter(
                academic_year=current_academic_year,
                term=current_term
            ).first()
    
    # Get all years for filter dropdown
    years_list = AcademicYear.objects.values_list('year', flat=True).distinct().order_by('-year')
    
    context = {
        'student': student,
        'invoices': invoices,
        'invoices_by_year': invoices_by_year,
        'academic_years': academic_years,
        'current_academic_year': current_academic_year,
        'current_invoice': current_invoice,
        'year_filter': year_filter,
        'term_filter': term_filter,
        'status_filter': status_filter,
        'search_query': search_query,
        'years': list(years_list),  # Use actual years from database
    }
    
    return render(request, 'student/invoices.html', context)

@login_required
def student_academic_scores(request):
    """Dedicated academic scores page"""
    student = get_object_or_404(StudentProfile, id=2)
    
    # Get filter parameters
    year_filter = request.GET.get('year', 'all')
    term_filter = request.GET.get('term', 'all')
    subject_filter = request.GET.get('subject', 'all')
    search_query = request.GET.get('search', '')
    
    # Get all academic years the student has been in
    academic_years = AcademicYear.objects.filter(
        studentclass__student=student
    ).distinct().order_by('-year')
    
    # Get current academic year
    current_academic_year = AcademicYear.objects.filter(is_active=True).first()
    
    # Get all scores
    scores = StudentScore.objects.filter(
        student=student
    ).select_related(
        'academic_session', 'term', 'subject', 'score_type'
    ).order_by('-academic_session__year', 'term__name', 'subject__name')
    
    grouped_scores = {}
    for s in scores:
        subject_name = s.subject.name
        if subject_name not in grouped_scores:
            grouped_scores[subject_name] = {"subject": subject_name, "scores": []}
        grouped_scores[subject_name]["scores"].append({
            "type": s.score_type.name,
            "score": s.score
        })

    # Apply filters
    if search_query:
        scores = scores.filter(
            Q(subject__name__icontains=search_query) |
            Q(term__name__icontains=search_query) |
            Q(academic_session__year__icontains=search_query)
        )
    if year_filter == 'current' and current_academic_year:
        scores = scores.filter(academic_session=current_academic_year)
    elif year_filter not in ['all', 'older']:
        scores = scores.filter(academic_session__year__icontains=year_filter)
    elif year_filter == 'older' and current_academic_year:
        scores = scores.exclude(academic_session=current_academic_year)
    if term_filter != 'all':
        scores = scores.filter(term__name__icontains=term_filter)
    if subject_filter != 'all':
        scores = scores.filter(subject__name__icontains=subject_filter)
    
    # Group scores by academic year and term
    scores_by_term = {}
    for score in scores:
        year_name = score.academic_session.year
        term_name = score.term.name
        key = f"{year_name} - {term_name} Term"
        
        if key not in scores_by_term:
            scores_by_term[key] = {
                'academic_year': score.academic_session,
                'term': score.term,
                'scores': [],
                'subjects': set(),
                'subject_table': defaultdict(lambda: {"1st CA": 0, "2nd CA": 0, "Exam": 0, "total": 0})
            }
        
        # Populate scores and subject table
        subject_name = score.subject.name
        score_type = score.score_type.name
        score_value = float(score.score)
        
        scores_by_term[key]['subject_table'][subject_name][score_type] = score_value
        scores_by_term[key]['subject_table'][subject_name]["total"] += score_value
        scores_by_term[key]['scores'].append(score_value)
        scores_by_term[key]['subjects'].add(subject_name)

    first_term_data = None
    if scores_by_term:
        first_term_data = next(iter(scores_by_term.values()))

        # Calculate averages and ranks
        for term_data in scores_by_term.values():
            scores_list = term_data['scores']
            if scores_list:
                total_score = sum(scores_list)  # Already floats
                term_data['average_score'] = round(total_score / len(scores_list), 2)
                
                # Rank
                term_data['rank'] = student.class_rank(
                    term_data['academic_year'],
                    term_data['term']
                )
                
                # Class size
                term_class = student.class_records.filter(
                    academic_year=term_data['academic_year']
                ).first()
                if term_class and term_class.school_class:
                    term_data['class_size'] = StudentProfile.objects.filter(
                        class_records__school_class=term_class.school_class,
                        class_records__academic_year=term_data['academic_year']
                    ).distinct().count()
                else:
                    term_data['class_size'] = 0
            else:
                term_data['average_score'] = None
                term_data['rank'] = None
                term_data['class_size'] = 0

            term_data['subjects'] = sorted(term_data['subjects'])

        # Subjects for filter
        all_subjects = TeacherSubject.objects.filter(
            class_assigned=student.current_class
        ).values_list('subject__name', flat=True).distinct().order_by('subject__name')

        # All terms
        terms = Term.objects.filter(studentscore__student=student).distinct().order_by('name')

        # Current term scores for download button
        current_term_scores = None
        if current_academic_year:
            current_term = Term.objects.filter(is_current=True).first()
            if current_term:
                current_scores = scores.filter(
                    academic_session=current_academic_year,
                    term=current_term
                )
                if current_scores.exists():
                    current_term_scores = {
                        'academic_year': current_academic_year,
                        'term': current_term,
                        'scores': current_scores,
                    }

        # Prepare data for template
        years_list = AcademicYear.objects.values_list('year', flat=True).distinct().order_by('-year')
        subject_scores = list(grouped_scores.values())
        score_types = ScoreType.objects.all().order_by("id")

        subject_data = {}
        for subject_name, scores_dict in first_term_data['subject_table'].items():
            subject_data[subject_name] = {
                "scores": scores_dict,  # includes all score types + total
                "total": scores_dict.get("total", 0)
            }

        context = {
            'student': student,
            "score_types": score_types,
            "subject_rows": subject_data,
            'scores_by_term': scores_by_term,
            "subject_scores": subject_scores,
            'academic_years': academic_years,
            'current_academic_year': current_academic_year,
            'current_term_scores': current_term_scores,
            'all_subjects': all_subjects,
            'terms': terms,
            'year_filter': year_filter,
            'term_filter': term_filter,
            'subject_filter': subject_filter,
            'search_query': search_query,
            'years': list(years_list),
        }

        return render(request, 'student/academic_scores.html', context)


@login_required
def download_invoice_pdf(request, invoice_id):
    """Generate PDF for a specific invoice"""
    invoice = get_object_or_404(Invoice, id=invoice_id, student__id=2)
    
    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.id}_{invoice.term.name}_{invoice.academic_year.year}.pdf"'
    
    # Create the PDF object
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=72)
    
    # Container for PDF elements
    elements = []
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Roboto-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#34495E'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Roboto-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        fontName='Roboto'
    )
    
    bold_style = ParagraphStyle(
        'CustomBold',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        fontName='Roboto-Bold'
    )
    
    # Title
    elements.append(Paragraph("INVOICE RECEIPT", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # School information
    school_info = [
        ["SCHOOL MANAGEMENT SYSTEM", "", "", ""],
        ["123 Education Street", "Phone: +123-456-7890", "", ""],
        ["Academic City", "Email: info@school.edu", "", ""],
        ["", "Website: www.school.edu", "", ""],
    ]
    
    school_table = Table(school_info, colWidths=[3*inch, 3*inch, 1.5*inch, 1.5*inch])
    school_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (0, 0), 'Roboto-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 14),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#2980B9')),
        ('BOTTOMPADDING', (0, 0), (0, 0), 10),
        ('TOPPADDING', (0, 0), (0, 0), 10),
    ]))
    elements.append(school_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Invoice header
    invoice_header = [
        ["Invoice Details", "", "Student Information", ""],
        ["Invoice No:", f"INV-{invoice.id:06d}", "Name:", invoice.student.full_name],
        ["Date Issued:", invoice.created_at.strftime("%B %d, %Y"), "Student ID:", invoice.student.student_id],
        ["Academic Year:", invoice.academic_year.year, "Class:", invoice.student.current_class_name],
        ["Term:", invoice.term.name, "Parent:", invoice.student.parent_name],
        ["Status:", invoice.get_status_display().upper(), "Contact:", invoice.student.parent_contact],
    ]
    
    invoice_table = Table(invoice_header, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 2.5*inch])
    invoice_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#3498DB')),
        ('BACKGROUND', (2, 0), (3, 0), colors.HexColor('#2ECC71')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Roboto-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('FONTNAME', (0, 1), (-1, -1), 'Roboto'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(invoice_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Invoice items
    elements.append(Paragraph("INVOICE ITEMS", subtitle_style))
    
    # Prepare invoice items data
    items_data = [["S/N", "Description", "Amount ($)"]]
    
    for i, item in enumerate(invoice.items.all(), 1):
        items_data.append([str(i), item.fee_type.name, f"${item.amount:.2f}"])
    
    # Add totals row
    items_data.append(["", "TOTAL AMOUNT", f"${invoice.total_amount:.2f}"])
    
    items_table = Table(items_data, colWidths=[0.5*inch, 6*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Roboto-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -2), 1, colors.grey),
        ('FONTNAME', (0, 1), (-1, -2), 'Roboto'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ECF0F1')),
        ('FONTNAME', (0, -1), (-1, -1), 'Roboto-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#2C3E50')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Payment summary
    elements.append(Paragraph("PAYMENT SUMMARY", subtitle_style))
    
    payment_data = [
        ["Total Amount:", f"${invoice.total_amount:.2f}"],
        ["Amount Paid:", f"${float(invoice.total_amount) - float(invoice.amount_due):.2f}"],
        ["Amount Due:", f"${invoice.amount_due:.2f}"],
    ]
    
    # Color code amount due
    amount_due_color = colors.red if invoice.amount_due > 0 else colors.green
    
    payment_table = Table(payment_data, colWidths=[2*inch, 2*inch])
    payment_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Roboto'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8F9FA')),
        ('FONTNAME', (0, -1), (-1, -1), 'Roboto-Bold'),
        ('TEXTCOLOR', (1, -1), (1, -1), amount_due_color),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(payment_table)
    
    # Add payment history if exists
    payments = invoice.payments.all()
    if payments:
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph("PAYMENT HISTORY", subtitle_style))
        
        payment_history = [["Date", "Method", "Amount", "Status", "Reference"]]
        
        for payment in payments:
            payment_history.append([
                payment.payment_date.strftime("%b %d, %Y"),
                payment.get_payment_method_display(),
                f"${payment.amount_paid:.2f}",
                payment.get_status_display(),
                payment.notes or "-"
            ])
        
        payment_history_table = Table(payment_history, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch, 2*inch])
        payment_history_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Roboto-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Roboto'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(payment_history_table)
    
    # Footer notes
    elements.append(Spacer(1, 0.5*inch))
    notes = [
        "**Important Notes:**",
        "1. Please keep this invoice for your records.",
        "2. Payments can be made via bank transfer, mobile money, or at the school accounts office.",
        "3. For payment inquiries, contact: accounts@school.edu",
        "4. Late payments may incur additional charges as per school policy.",
    ]
    
    for note in notes:
        elements.append(Paragraph(note, normal_style))
    
    # Generate PDF
    doc.build(elements)
    
    # Get PDF value and write to response
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response



@login_required
def download_report_card_pdf(request, academic_year_id, term_id):

    # =========================
    # BASIC DATA
    # =========================
    student = get_object_or_404(StudentProfile, id=2)
    academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
    term = get_object_or_404(Term, id=term_id)
    settings = SystemSettings.get_settings()

    score_types = ScoreType.objects.all().order_by("id")

    scores = StudentScore.objects.filter(
        student=student,
        academic_session=academic_year,
        term=term
    ).select_related("subject", "score_type")

    # =========================
    # STUDENT CLASS (FIXED)
    # =========================
    class_record = student.class_records.filter(is_current=True).first()
    school_class = class_record.school_class if class_record else None
    student_class_name = school_class.name if school_class else "N/A"

    # =========================
    # CLASS STUDENTS (FIXED)
    # =========================
    class_students = StudentProfile.objects.filter(
        class_records__school_class=school_class,
        class_records__is_current=True
    ).distinct()

    total_students = class_students.count()

    # =========================
    # POSITION CALCULATION
    # =========================
    student_totals = (
        StudentScore.objects.filter(
            student__in=class_students,
            academic_session=academic_year,
            term=term
        )
        .values("student")
        .annotate(total=Sum("score"))
        .order_by("-total")
    )

    position = 0
    for index, record in enumerate(student_totals, start=1):
        if record["student"] == student.id:
            position = index
            break

    # =========================
    # STATS
    # =========================
    total_subjects = scores.values("subject").distinct().count()
    average_score = scores.aggregate(avg=Avg("score"))["avg"] or 0

    # =========================
    # PDF SETUP
    # =========================
    buffer = BytesIO()
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="report_{student.student_id}.pdf"'
    )

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="CenterBold",
        alignment=1,
        fontSize=12,
        spaceAfter=6,
        leading=14,
        fontName="Helvetica-Bold"
    ))

    elements = []

    # =========================
    # HEADER
    # =========================
    logo = ""
    if settings.school_logo:
        logo = Image(settings.school_logo.path, width=70, height=70)

    header_table = Table(
        [[
            logo,
            Paragraph(
                f"""
                <para align="center">
                <b>{settings.school_name.upper()}</b><br/>
                {settings.school_address}<br/>
                ACADEMIC SESSION: {academic_year.year}<br/>
                <b>{term.name.upper()} TERM EXAMINATION</b>
                </para>
                """,
                styles["Normal"]
            )
        ]],
        colWidths=[80, 440]
    )

    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 6))

    # =========================
    # STUDENT SUMMARY
    # =========================
    summary_data = [
        ["Name", student.full_name, "Register No", student.student_id],
        ["Class", student_class_name, "Term", term.name],
        ["Total Subjects", total_subjects, "Student Average", f"{average_score:.1f}%"],
        ["Position", f"{position} out of {total_students}", "Class Size", total_students],
    ]

    summary_table = Table(summary_data, colWidths=[90, 150, 90, 150])
    summary_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 8))

    # =========================
    # SUBJECT SCORE TABLE
    # =========================
    subject_scores = defaultdict(dict)

    for s in scores:
        subject_scores[s.subject.name][s.score_type.name] = s.score

    table_data = [["Subject"]]
    for st in score_types:
        table_data[0].append(st.name)

    table_data[0] += ["Total", "Grade", "Remark"]

    for subject, score_map in subject_scores.items():
        row = [subject]
        total = 0

        for st in score_types:
            val = score_map.get(st.name, 0)
            row.append(val)
            total += val

        row.extend([
            total,
            get_grade(total),
            get_remarks(total)
        ])
        table_data.append(row)

    score_table = Table(table_data, repeatRows=1)
    score_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("ALIGN", (1, 1), (-3, -1), "CENTER"),
        ("ALIGN", (-2, 1), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))

    elements.append(score_table)
    elements.append(Spacer(1, 10))

    # =========================
    # BUILD PDF
    # =========================
    doc.build(elements)
    response.write(buffer.getvalue())
    buffer.close()

    return response


