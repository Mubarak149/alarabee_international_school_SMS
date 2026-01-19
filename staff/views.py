# teachers/views.py
import json
from django.shortcuts import render,get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Prefetch

from .models import TeacherProfile, TeacherSubject, TeacherBankDetails
from .forms import TeacherProfileForm, TeacherBankDetailsForm

from students.models import StudentClass, StudentScore
from academics.models import SchoolClass, ScoreType, Subject, AcademicYear, Term



@login_required(login_url='login')
def teacher_dashboard(request):

    # If user has NO teacher profile → redirect to login
    try:
        teacher = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return redirect('login')

    # Get current academic year
    current_year = AcademicYear.objects.filter(is_active=True).first()
    if not current_year:
        current_year = AcademicYear.objects.last()

    # Teacher assigned classes
    assigned_classes = TeacherSubject.objects.filter(
        teacher=teacher,
        academic_year=current_year
    ).select_related('class_assigned')

    selected_class_id = request.GET.get('class_id')
    selected_subject_id = request.GET.get('subject_id')

    students = []
    selected_class = None
    selected_subject = None
    score_types = []

    if selected_class_id and selected_subject_id:
        selected_class = get_object_or_404(SchoolClass, id=selected_class_id)
        selected_subject = get_object_or_404(Subject, id=selected_subject_id)

        is_assigned = TeacherSubject.objects.filter(
            teacher=teacher,
            class_assigned=selected_class,
            subject=selected_subject,
            academic_year=current_year
        ).exists()

        if is_assigned:
            students = StudentClass.objects.filter(
                school_class=selected_class,
                academic_year=current_year,
                is_current=True
            ).select_related('student')

            score_types = ScoreType.objects.all()

    context = {
        'teacher': teacher,
        'assigned_classes': assigned_classes,
        'students': students,
        'selected_class': selected_class,
        'selected_subject': selected_subject,
        'score_types': score_types,
        'current_year': current_year,
        'terms': Term.objects.all(),
    }

    return render(request, 'teachers/teacher_dashboard.html', context)


@login_required
def save_student_scores(request):
    if request.method == 'POST':
        teacher = get_object_or_404(TeacherProfile, user=request.user)
        
        # Get form data
        class_id = request.POST.get('class_id')
        subject_id = request.POST.get('subject_id')
        term_id = request.POST.get('term')
        
        # Validate teacher assignment
        is_assigned = TeacherSubject.objects.filter(
            teacher=teacher,
            class_assigned_id=class_id,
            subject_id=subject_id,
            academic_year=AcademicYear.objects.filter(is_active=True).first()
        ).exists()
        
        if not is_assigned:
            messages.error(request, 'You are not assigned to this class/subject.')
            return redirect('teacher_dashboard')
        
        # Get academic year
        academic_year = AcademicYear.objects.filter(is_active=True).first()
        
        # Process each student score
        student_ids = request.POST.getlist('student_ids')
        scores_saved = 0
        
        for student_id in student_ids:
            for key, value in request.POST.items():
                if key.startswith(f'score_{student_id}_') and value:
                    try:
                        score_type_id = key.split('_')[2]
                        score_value = float(value)
                        
                        # Create or update score
                        StudentScore.objects.update_or_create(
                            student_id=student_id,
                            subject_id=subject_id,
                            academic_session=academic_year,
                            term_id=term_id,
                            score_type_id=score_type_id,
                            defaults={'score': score_value}
                        )
                        scores_saved += 1
                    except (ValueError, IndexError):
                        continue
        
        messages.success(request, f'Successfully saved {scores_saved} scores.')
        return redirect(f'{request.path}?class_id={class_id}&subject_id={subject_id}')
    
    return redirect('teacher_dashboard')



@login_required(login_url='login')
def teacher_profile(request):
    try:
        teacher = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return redirect('login')
    
    bank_details, created = TeacherBankDetails.objects.get_or_create(teacher=teacher)
    
    # Get current assignments and statistics
    current_year = AcademicYear.objects.filter(is_active=True).first()
    
    # Count assigned classes for current year
    assigned_classes_count = TeacherSubject.objects.filter(
        teacher=teacher,
        academic_year=current_year
    ).count()
    
    # Count total students across all assigned classes
    total_students_count = 0
    assignments = TeacherSubject.objects.filter(
        teacher=teacher,
        academic_year=current_year
    ).select_related('class_assigned')
    
    for assignment in assignments:
        total_students_count += StudentClass.objects.filter(
            school_class=assignment.class_assigned,
            academic_year=current_year,
            is_current=True
        ).count()
    
    # Get subjects taught by this teacher
    subjects_taught = teacher.subjects.all()
    
    context = {
        'teacher': teacher,
        'bank_details': bank_details,
        'assigned_classes_count': assigned_classes_count,
        'total_students_count': total_students_count,
        'subjects_taught': subjects_taught,
        'current_year': current_year,
    }
    
    return render(request, 'teachers/teacher_profile.html', context)

@login_required
@require_POST
def update_teacher_profile(request):
    try:
        teacher = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return redirect('login')
    
    form = TeacherProfileForm(request.POST, instance=teacher)
    
    if form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully!')
    else:
        errors = form.errors.get_json_data()
        messages.error(request, 'Please correct the errors below.')
    
    return redirect('teacher_profile')

@login_required
@require_POST
def update_bank_details(request):
    try:
        teacher = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return redirect('login')
    
    bank_details, created = TeacherBankDetails.objects.get_or_create(teacher=teacher)
    form = TeacherBankDetailsForm(request.POST, instance=bank_details)
    
    if form.is_valid():
        form.save()
        messages.success(request, 'Bank details updated successfully!')
    else:
        messages.error(request, 'Please correct the errors in bank details.')
    
    return redirect('teacher_profile')

@login_required
def teacher_assigned_classes(request):
    try:
        teacher = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return redirect('login')
    
    current_year = AcademicYear.objects.filter(is_active=True).first()
    
    # Get all assignments grouped by academic year
    assignments_by_year = {}
    all_assignments = TeacherSubject.objects.filter(
        teacher=teacher
    ).select_related('academic_year', 'subject', 'class_assigned').order_by('-academic_year__year')
    
    for assignment in all_assignments:
        year = assignment.academic_year.year
        if year not in assignments_by_year:
            assignments_by_year[year] = []
        assignments_by_year[year].append(assignment)
    
    # Count current assigned classes
    assigned_classes_count = TeacherSubject.objects.filter(
        teacher=teacher,
        academic_year=current_year
    ).count()
    
    context = {
        'teacher': teacher,
        'assignments_by_year': assignments_by_year,
        'current_year': current_year,
        'assigned_classes_count': assigned_classes_count,
    }
    
    return render(request, 'teachers/teacher_classes.html', context)

@login_required
def teacher_reports(request):
    try:
        teacher = request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return redirect('login')
    
    context = {
        'teacher': teacher,
    }
    
    return render(request, 'teachers/teacher_reports.html', context)


def manage_result(request):
    context = {}
    return render(request, "teachers/manage_result.html", context)