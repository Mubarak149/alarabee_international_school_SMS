from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Sum
from django.http import HttpResponse
from django.template.loader import render_to_string
from datetime import datetime

from .models import StudentProfile, StudentScore, StudentClass
from finance.models import Invoice, Payment, FeeStructure, Sponsorship
from academics.models import AcademicYear, Term
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Sum
from django.http import HttpResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

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
def generate_invoice_pdf(request, invoice_id):
    # Get invoice and student
    student = get_object_or_404(StudentProfile, user=request.user)
    invoice = get_object_or_404(Invoice, id=invoice_id, student=student)
    
    # Create a file-like buffer to receive PDF data
    buffer = io.BytesIO()
    
    # Create the PDF object
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        alignment=1  # Center alignment
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=10,
        textColor=colors.HexColor('#2c3e50')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10
    )
    
    # Build the PDF content
    story = []
    
    # Title
    story.append(Paragraph(f"INVOICE #{invoice.id}", title_style))
    story.append(Spacer(1, 20))
    
    # School info
    school_info = [
        Paragraph("<b>School Management System</b>", heading_style),
        Paragraph("123 Education Street", normal_style),
        Paragraph("Academic City, AC 10001", normal_style),
        Paragraph("Phone: (555) 123-4567", normal_style),
        Paragraph("Email: accounts@school.edu", normal_style),
        Paragraph(f"Date: {invoice.created_at.strftime('%B %d, %Y')}", normal_style),
    ]
    
    for info in school_info:
        story.append(info)
    
    story.append(Spacer(1, 20))
    
    # Student info table
    student_data = [
        ['Student Information', ''],
        ['Name:', student.full_name],
        ['Student ID:', student.student_id],
        ['Class:', student.current_class_name],
        ['Academic Year:', f"{invoice.academic_year.name}"],
        ['Term:', f"{invoice.term.name}"]
    ]
    
    student_table = Table(student_data, colWidths=[2*inch, 4*inch])
    student_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4e73df')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(student_table)
    story.append(Spacer(1, 30))
    
    # Invoice items table
    items_data = [['Item', 'Description', 'Amount']]
    
    # Get invoice items
    invoice_items = invoice.items.all()
    for item in invoice_items:
        items_data.append([
            item.fee_type.name,
            f"{item.fee_type.name} Fee",
            f"${item.amount:,.2f}"
        ])
    
    # Add total row
    items_data.append([
        '', 
        Paragraph('<b>TOTAL</b>', ParagraphStyle(
            'BoldRight',
            parent=styles['Normal'],
            fontSize=10,
            alignment=2
        )), 
        Paragraph(f'<b>${invoice.total_amount:,.2f}</b>', ParagraphStyle(
            'BoldRight',
            parent=styles['Normal'],
            fontSize=10,
            alignment=2
        ))
    ])
    
    items_table = Table(items_data, colWidths=[1.5*inch, 3*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -2), colors.black),
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 10),
        ('GRID', (0, 0), (-1, -2), 1, colors.grey),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (2, 1), (2, -2), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ('LINEBELOW', (0, -1), (-1, -1), 2, colors.black),
    ]))
    
    story.append(items_table)
    story.append(Spacer(1, 30))
    
    # Payment status
    payment_data = [
        ['Payment Status', 'Amount'],
        ['Total Amount:', f"${invoice.total_amount:,.2f}"],
        ['Amount Paid:', f"${(invoice.total_amount - invoice.amount_due):,.2f}"],
        ['Amount Due:', f"<b>${invoice.amount_due:,.2f}</b>"],
        ['Status:', f"<b>{invoice.get_status_display()}</b>"]
    ]
    
    payment_table = Table(payment_data, colWidths=[2*inch, 4*inch])
    payment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#17a2b8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('FONTNAME', (1, 3), (1, 3), 'Helvetica-Bold'),
        ('FONTNAME', (1, 4), (1, 4), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, 3), (1, 3), colors.red),
        ('TEXTCOLOR', (1, 4), (1, 4), colors.green if invoice.status == 'paid' else colors.orange),
    ]))
    
    story.append(payment_table)
    story.append(Spacer(1, 40))
    
    # Footer note
    footer_note = """
    <para alignment="center">
    <font size="9" color="grey">
    <b>Payment Instructions:</b><br/>
    Please make payment to the school accounts office or through any of our online payment platforms.<br/>
    For inquiries, contact the accounts department at accounts@school.edu or call (555) 123-4567.<br/>
    <br/>
    <i>This is an official invoice from School Management System. Please keep this document for your records.</i>
    </font>
    </para>
    """
    
    story.append(Paragraph(footer_note, normal_style))
    
    # Build PDF
    doc.build(story)
    
    # Get the value of the BytesIO buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create HTTP response with PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.id}_{student.student_id}.pdf"'
    
    return response

@login_required
def generate_report_card_pdf(request, academic_year_id, term_id):
    # Get student
    student = get_object_or_404(StudentProfile, user=request.user)
    academic_year = get_object_or_404(AcademicYear, id=academic_year_id)
    term = get_object_or_404(Term, id=term_id)
    
    # Get scores
    scores = StudentScore.objects.filter(
        student=student,
        academic_session=academic_year,
        term=term
    ).select_related('subject', 'score_type')
    
    # Calculate average
    average_score = scores.aggregate(avg=Avg('score'))['avg'] or 0
    
    # Create a file-like buffer to receive PDF data
    buffer = io.BytesIO()
    
    # Create the PDF object
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=20,
        alignment=1,
        textColor=colors.HexColor('#2c3e50')
    )
    
    subtitle_style = ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=15,
        alignment=1,
        textColor=colors.HexColor('#4e73df')
    )
    
    student_style = ParagraphStyle(
        'StudentInfo',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=5
    )
    
    # Build the PDF content
    story = []
    
    # Title
    story.append(Paragraph("OFFICIAL REPORT CARD", title_style))
    story.append(Paragraph(f"{academic_year.name} - {term.name} Term", subtitle_style))
    story.append(Spacer(1, 20))
    
    # Student info
    student_info = [
        Paragraph(f"<b>Student:</b> {student.full_name}", student_style),
        Paragraph(f"<b>Student ID:</b> {student.student_id}", student_style),
        Paragraph(f"<b>Class:</b> {student.current_class_name}", student_style),
        Paragraph(f"<b>Academic Year:</b> {academic_year.name}", student_style),
        Paragraph(f"<b>Term:</b> {term.name}", student_style),
        Paragraph(f"<b>Date Generated:</b> {datetime.now().strftime('%B %d, %Y')}", student_style),
    ]
    
    for info in student_info:
        story.append(info)
    
    story.append(Spacer(1, 30))
    
    # Academic performance header
    story.append(Paragraph("ACADEMIC PERFORMANCE", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Calculate scores by subject
    subject_scores = {}
    for score in scores:
        if score.subject.name not in subject_scores:
            subject_scores[score.subject.name] = []
        subject_scores[score.subject.name].append({
            'type': score.score_type.name,
            'score': score.score
        })
    
    # Create scores table
    scores_data = [['Subject', '1st CA', '2nd CA', 'Exam', 'Total', 'Grade', 'Remark']]
    
    for subject, score_list in subject_scores.items():
        ca1 = next((s['score'] for s in score_list if '1st' in s['type']), 0)
        ca2 = next((s['score'] for s in score_list if '2nd' in s['type']), 0)
        exam = next((s['score'] for s in score_list if 'Exam' in s['type']), 0)
        total = ca1 + ca2 + exam
        
        # Determine grade
        if total >= 80:
            grade = 'A'
            remark = 'Excellent'
        elif total >= 70:
            grade = 'B'
            remark = 'Very Good'
        elif total >= 60:
            grade = 'C'
            remark = 'Good'
        elif total >= 50:
            grade = 'D'
            remark = 'Pass'
        else:
            grade = 'F'
            remark = 'Fail'
        
        scores_data.append([
            subject,
            f"{ca1:.1f}" if ca1 else '-',
            f"{ca2:.1f}" if ca2 else '-',
            f"{exam:.1f}" if exam else '-',
            f"{total:.1f}",
            grade,
            remark
        ])
    
    # Add total row
    scores_data.append([
        '<b>TOTAL AVERAGE</b>',
        '', '', '',
        f"<b>{average_score:.1f}%</b>",
        '',
        '<b>See Comments</b>'
    ])
    
    scores_table = Table(scores_data, colWidths=[1.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.6*inch, 1.5*inch])
    scores_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -2), colors.black),
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 10),
        ('GRID', (0, 0), (-1, -2), 1, colors.grey),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (1, 1), (4, -2), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ('LINEBELOW', (0, -1), (-1, -1), 2, colors.black),
    ]))
    
    story.append(scores_table)
    story.append(Spacer(1, 30))
    
    # Summary section
    story.append(Paragraph("PERFORMANCE SUMMARY", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Calculate statistics
    total_subjects = len(subject_scores)
    passed_subjects = sum(1 for row in scores_data[1:-1] if row[4] and float(row[4].replace('-', '0')) >= 50)
    failed_subjects = total_subjects - passed_subjects
    
    summary_data = [
        ['Total Subjects:', str(total_subjects)],
        ['Subjects Passed:', str(passed_subjects)],
        ['Subjects Failed:', str(failed_subjects)],
        ['Overall Average:', f"{average_score:.1f}%"],
        ['Class Position:', '5th'],  # You can calculate this from your database
        ['Attendance:', '94%'],  # You can add attendance tracking
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#17a2b8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 30))
    
    # Comments section
    story.append(Paragraph("TEACHER'S COMMENTS", subtitle_style))
    story.append(Spacer(1, 10))
    
    comments = """
    <para>
    <font size="10">
    John has shown consistent improvement throughout the term. His performance in Mathematics and Physics is particularly commendable. 
    He participates actively in class discussions and shows great interest in learning. 
    With continued effort, he has the potential to achieve even better results in the coming terms.
    <br/><br/>
    <b>Recommendation:</b> Promoted to next class.
    </font>
    </para>
    """
    
    story.append(Paragraph(comments, student_style))
    story.append(Spacer(1, 30))
    
    # Signatures
    signature_data = [
        ['Class Teacher:', 'Principal:'],
        ['________________________', '________________________'],
        ['Mrs. Sarah Johnson', 'Dr. Michael Williams'],
        ['Date: __________________', 'Date: __________________']
    ]
    
    signature_table = Table(signature_data, colWidths=[3*inch, 3*inch])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 15),
    ]))
    
    story.append(signature_table)
    story.append(Spacer(1, 20))
    
    # Footer note
    footer_note = """
    <para alignment="center">
    <font size="9" color="grey">
    <i>This is an official report card from School Management System. Please keep this document for your records.</i><br/>
    For inquiries, contact the academic office at academics@school.edu or call (555) 123-4567.
    </font>
    </para>
    """
    
    story.append(Paragraph(footer_note, student_style))
    
    # Build PDF
    doc.build(story)
    
    # Get the value of the BytesIO buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create HTTP response with PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="report_card_{academic_year.name}_{term.name}_{student.student_id}.pdf"'
    
    return response

    return render(request, "student/student_dashboard.html", context)

def student_report_cards(request):
    return render(request, 'student/report_cards.html')

def student_subject(request):
    return render(request, 'student/student_subject.html')

def student_profile(request):
    return render(request, 'student/profile.html')

def student_settings(request):
    return render(request, 'student/settings.html')