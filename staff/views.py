# teachers/views.py
from django.shortcuts import render,get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.db.models import Prefetch
from .models import TeacherProfile, TeacherSubject
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

def teacher_classes(request):
    context = {}
    return render(request, "teachers/teacher_classes.html", context)

def manage_result(request):
    context = {}
    return render(request, "teachers/manage_result.html", context)