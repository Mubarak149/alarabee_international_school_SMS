from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.contrib.auth.decorators import login_required

from accounts.forms import StudentUserForm, TeacherUserForm, UserEditForm, AdminUserForm
from students.forms import StudentProfileForm, StudentClassForm

from students.models import StudentProfile, StudentClass
from students.utils import generate_student_id, normalize_name

from staff.forms import TeacherProfileForm, TeacherSubjectForm, TeacherBankDetailsForm
from staff.models import User, TeacherProfile, TeacherSubject, TeacherBankDetails

from academics.forms import SchoolClassForm, AcademicYearForm
from academics.models import AcademicYear, SchoolClass, Subject

from .models import AdminProfile
from .forms import AdminProfileForm

def admin_dashboard(request):
    # Get real data from database
    total_students = StudentProfile.objects.filter().count()
    total_teachers = TeacherProfile.objects.filter().count()
    
    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
    }
    
    return render(request, "school_admin/admin_dashboard.html", context)


def manage_admins(request):
    # Get all admins with related data
    admins_list = AdminProfile.objects.select_related('user').all().order_by('-id')
    med_count = admins_list.filter(qualification='MEd').count()
    phd_count = admins_list.filter(qualification='PhD').count()
    bed_count = admins_list.filter(qualification='BEd').count()
    # Get filter data
    qualification_filter = request.GET.get('qualification', '')
    
    # Pagination
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
        if per_page not in [10, 25, 50, 100]:
            per_page = 10
    except ValueError:
        per_page = 10
    
    page = request.GET.get('page', 1)
    paginator = Paginator(admins_list, per_page)
    
    try:
        admins = paginator.page(page)
    except PageNotAnInteger:
        admins = paginator.page(1)
    except EmptyPage:
        admins = paginator.page(paginator.num_pages)

    if request.method == "POST":
        action = request.POST.get('action')

        # ADD ADMIN
        if action == 'add':
            user_form = AdminUserForm(request.POST)
            profile_form = AdminProfileForm(request.POST)
            print("ADD ADMIN POST data", request.POST.dict())
            if all([user_form.is_valid(), profile_form.is_valid()]):
                try:
                    with transaction.atomic():
                        # Save User
                        user = user_form.save(commit=False)
                        user.first_name = normalize_name(user.first_name)
                        user.last_name = normalize_name(user.last_name)
                        user.role = 'admin'
                        user.username = user.email
                        user.save()
                        
                        # Save Profile
                        profile = profile_form.save(commit=False)
                        profile.user = user
                        profile.save()

                        messages.success(request, f'Admin {user.get_full_name()} added successfully! Login ID: {user.username}')
                        return redirect('manage_admins')

                except Exception as e:
                    messages.error(request, f'Error adding admin: {str(e)}')

            else:
                for form in [user_form, profile_form]:
                    for field, errors in form.errors.items():
                        for error in errors:
                            messages.error(request, f"{form.fields[field].label if field in form.fields else field}: {error}")
        
        # EDIT ADMIN
        elif action == 'edit':
            admin_id = request.POST.get('edit_id')
            try:
                profile = AdminProfile.objects.get(id=admin_id)
                user = profile.user

                user_form = UserEditForm(request.POST, instance=user)
                profile_form = AdminProfileForm(request.POST, instance=profile)

                if user_form.is_valid() and profile_form.is_valid():
                    with transaction.atomic():
                        user = user_form.save()   # ✅ password safe
                        profile_form.save()

                    messages.success(
                        request,
                        f'Admin {user.get_full_name()} updated successfully!'
                    )
                    return redirect('manage_admins')

            except AdminProfile.DoesNotExist:
                messages.error(request, 'Admin not found!')
            except Exception as e:
                messages.error(request, f'Error updating admin: {str(e)}')


        # DELETE ADMIN
        elif action == 'delete':
            admin_id = request.POST.get('delete_id')
            try:
                profile = AdminProfile.objects.get(id=admin_id)
                admin_name = profile.user.get_full_name()
                user = profile.user
    
                user.delete()  # Cascade delete will delete profile too
                messages.success(request, f'Admin {admin_name} deleted successfully!')

            except AdminProfile.DoesNotExist:
                messages.error(request, 'Admin not found!')
            return redirect('manage_admins')

    
    # GET request - initialize forms
    user_form = AdminUserForm()
    profile_form = AdminProfileForm()
    

    context = {
        'user_form': user_form,
        'profile_form': profile_form,

        'admins': admins,              # ✅ Page object for template
        'total_admins': admins_list.count(),
        'phd_count': phd_count,
        'med_count': med_count,
        'bed_count': bed_count,
    }

    return render(request, "school_admin/manage_admins.html", context)


def admin_profile(request):
    return render(request, "school_admin/admin_profile.html")


# views.py
def manage_students(request):
    # Get all students with related data, ordered from newest to oldest
    students_list = StudentProfile.objects.select_related('user').prefetch_related('class_records').all().order_by('-id')  # '-' means descending
    
    # Get items per page from request or use default
    per_page = request.GET.get('per_page', 12)
    try:
        per_page = int(per_page)
        if per_page not in [12, 24, 36, 48, 100]:
            per_page = 12
    except ValueError:
        per_page = 12

    # Pagination setup
    page = request.GET.get('page', 1)
    paginator = Paginator(students_list, 12)  # Show 12 students per page
    
    try:
        students = paginator.page(page)
    except PageNotAnInteger:
        students = paginator.page(1)
    except EmptyPage:
        students = paginator.page(paginator.num_pages)
    
    if request.method == "POST":
        print("POST request received", request.POST)
        action = request.POST.get('action')
        # ADD STUDENT
        if action == 'add':
            user_form = StudentUserForm(request.POST)
            profile_form = StudentProfileForm(request.POST)
            class_form = StudentClassForm(request.POST)
            
            if all([user_form.is_valid(), profile_form.is_valid(), class_form.is_valid()]):
                try:
                    with transaction.atomic():
                        # 1️⃣ Save User first to get a DB ID
                        user = user_form.save(commit=False)

                        # Normalize the first_name and last_name
                        user.first_name = normalize_name(user.first_name)
                        user.last_name = normalize_name(user.last_name)
                        user.role = 'student'
                        user.save()  # user.id exists now

                        # 2️⃣ Save Profile
                        profile = profile_form.save(commit=False)
                        profile.user = user
                        profile.save()  # profile.id exists now

                        # 3️⃣ Generate student ID using profile.id
                        student_id = generate_student_id(profile.id)
                        profile.student_id = student_id
                        profile.save()

                        # 4️⃣ Set username to student_id
                        user.username = student_id
                        user.set_password("Password123")  # default password same as student_id
                        user.save()

                        # 5️⃣ Save StudentClass
                        student_class = class_form.save(commit=False)
                        student_class.student = profile
                        student_class.save()

                    messages.success(request, f'Student {user.get_full_name()} added successfully! Login ID: {student_id}')
                    return redirect('manage_students')

                except Exception as e:
                    messages.error(request, f'Error adding student: {str(e)}')

            else:
                # Handle form errors
                print("Form errors found", user_form.errors, profile_form.errors, class_form.errors)
                for form in [user_form, profile_form, class_form]:
                    for error in form.errors.values():
                        messages.error(request, error)
                return redirect('manage_students')
        
       # EDIT STUDENT
        elif action == 'edit':
            student_id = request.POST.get('edit_id')
            try:
                profile = StudentProfile.objects.get(id=student_id)
                user = profile.user
                
                # Create form instances with existing data
                user_form = StudentUserForm(request.POST, instance=user)
                profile_form = StudentProfileForm(request.POST, instance=profile)
                
                # Get or create StudentClass
                student_class = profile.class_records.first()
                if student_class:
                    class_form = StudentClassForm(request.POST, instance=student_class)
                else:
                    class_form = StudentClassForm(request.POST)
                
                # Clean the form data - strip whitespace from select fields
                post_data = request.POST.copy()
                post_data['school_class'] = post_data.get('school_class', '').strip()
                post_data['academic_year'] = post_data.get('academic_year', '').strip()
                
                # Update forms with cleaned data
                if 'school_class' in post_data and 'academic_year' in post_data:
                    class_form = StudentClassForm(post_data, instance=student_class if student_class else None)
                
                # Validate all forms
                if all([user_form.is_valid(), profile_form.is_valid(), class_form.is_valid()]):
                    try:
                        with transaction.atomic():
                            # Save user
                            user = user_form.save(commit=False)
                            user.first_name = normalize_name(user.first_name)
                            user.last_name = normalize_name(user.last_name)
                            user.save()
                            
                            # Save profile
                            profile = profile_form.save(commit=False)
                            profile.user = user
                            profile.save()
                            
                            # Save or update class record
                            student_class_instance = class_form.save(commit=False)
                            student_class_instance.student = profile
                            student_class_instance.save()
                        
                        messages.success(request, f'Student {user.get_full_name()} updated successfully!')
                        return redirect('manage_students')
                        
                    except Exception as e:
                        messages.error(request, f'Error updating student: {str(e)}')
                else:
                    print("Form errors found", user_form.errors, profile_form.errors, class_form.errors)
                    # Pass form errors to template context
                    context = {
                        'students': students,
                        'user_form': user_form,
                        'profile_form': profile_form,
                        'class_form': class_form,
                    }
                    # Add error messages
                    for form in [user_form, profile_form, class_form]:
                        for field, errors in form.errors.items():
                            for error in errors:
                                messages.error(request, f"{form.fields[field].label if field in form.fields else field}: {error}")
                    return render(request, 'school_admin/manage_students.html', context)
                        
            except StudentProfile.DoesNotExist:
                messages.error(request, 'Student not found!')
                return redirect('manage_students')

        # DELETE STUDENT
        elif action == 'delete':
            student_id = request.POST.get('delete_id')
            try:
                profile = StudentProfile.objects.get(id=student_id)
                student_name = profile.user.get_full_name()
                profile.user.delete()  # This will cascade delete profile and class
                messages.success(request, f'Student {student_name} deleted successfully!')
            except StudentProfile.DoesNotExist:
                messages.error(request, 'Student not found!')
            return redirect('manage_students')

    
    # GET request - initialize forms
    user_form = StudentUserForm()
    profile_form = StudentProfileForm()
    class_form = StudentClassForm()
    
    return render(request, "school_admin/manage_students.html", {
        "user_form": user_form,
        "profile_form": profile_form,
        "class_form": class_form,
        "students": students,
    })

def manage_teachers(request):
    # Get all teachers with related data
    teachers_list = TeacherProfile.objects.select_related('user').prefetch_related(
        'subject_assignments'
    ).all().order_by('-id')
    phd_count = teachers_list.filter(qualification='phd').count()
    # Get filter data
    status_filter = request.GET.get('status', '')
    qualification_filter = request.GET.get('qualification', '')
    
    if status_filter:
        teachers_list = teachers_list.filter(status=status_filter)
    if qualification_filter:
        teachers_list = teachers_list.filter(qualification=qualification_filter)
    
    # Pagination
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
        if per_page not in [10, 25, 50, 100]:
            per_page = 10
    except ValueError:
        per_page = 10
    
    page = request.GET.get('page', 1)
    paginator = Paginator(teachers_list, per_page)
    
    try:
        teachers = paginator.page(page)
    except PageNotAnInteger:
        teachers = paginator.page(1)
    except EmptyPage:
        teachers = paginator.page(paginator.num_pages)
    
    if request.method == "POST":
        action = request.POST.get('action')
        
        # ADD TEACHER (removed subject assignment logic)
        if action == 'add':
            user_form = TeacherUserForm(request.POST)
            profile_form = TeacherProfileForm(request.POST)
            print("ADD TEACHER POST data", request.POST.dict())
            if all([user_form.is_valid(), profile_form.is_valid()]):
                try:
                    with transaction.atomic():
                        # Save User
                        user = user_form.save(commit=False)
                        user.first_name = normalize_name(user.first_name)
                        user.last_name = normalize_name(user.last_name)
                        user.role = 'staff'
                        user.username = user.email
                        user.save()
                        
                        # Save Profile
                        profile = profile_form.save(commit=False)
                        profile.user = user
                        profile.save()
                        
                        messages.success(request, f'Teacher {user.get_full_name()} added successfully! Login ID: {user.username}')
                        return redirect('manage_teachers')
                        
                except Exception as e:
                    messages.error(request, f'Error adding teacher: {str(e)}')
            
            else:
                for form in [user_form, profile_form]:
                    for field, errors in form.errors.items():
                        for error in errors:
                            messages.error(request, f"{form.fields[field].label if field in form.fields else field}: {error}")
        
        # EDIT TEACHER (removed subject assignment logic)
        elif action == 'edit':
            teacher_id = request.POST.get('edit_id')
            try:
                profile = TeacherProfile.objects.get(id=teacher_id)
                user = profile.user

                user_form = UserEditForm(request.POST, instance=user)
                profile_form = TeacherProfileForm(request.POST, instance=profile)

                if user_form.is_valid() and profile_form.is_valid():
                    with transaction.atomic():
                        user = user_form.save()   # ✅ password safe
                        profile_form.save()

                    messages.success(
                        request,
                        f'Teacher {user.get_full_name()} updated successfully!'
                    )
                    return redirect('manage_teachers')

            except TeacherProfile.DoesNotExist:
                messages.error(request, 'Teacher not found!')
            except Exception as e:
                messages.error(request, f'Error updating teacher: {str(e)}') 


        
        # DELETE TEACHER
        elif action == 'delete':
            teacher_id = request.POST.get('delete_id')
            try:
                profile = TeacherProfile.objects.get(id=teacher_id)
                teacher_name = profile.user.get_full_name()
                user = profile.user
    
                user.delete()  # Cascade delete will delete profile too
                messages.success(request, f'Teacher {teacher_name} deleted successfully!')
                
                    
            except TeacherProfile.DoesNotExist:
                messages.error(request, 'Teacher not found!')
            return redirect('manage_teachers')
        
    
    # GET request - initialize forms
    user_form = TeacherUserForm()
    profile_form = TeacherProfileForm()
    bank_form = TeacherBankDetailsForm()
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'bank_form': bank_form,
        'teachers': teachers,
        'total_teachers': teachers_list.count(),
        'active_teachers': teachers_list.filter(status='active').count(),
        'on_leave_teachers': teachers_list.filter(status='on_leave').count(),
        'inactive_teachers': teachers_list.filter(status='inactive').count(),
        'status_filter': status_filter,
        'qualification_filter': qualification_filter,
        'per_page': per_page,
        'phd_count': phd_count,
    }
    
    return render(request, "school_admin/manage_teachers.html", context)

def manage_teacher_subjects(request):
    # Get all subject assignments with related data
    assignments_list = TeacherSubject.objects.select_related(
        'teacher__user', 'subject', 'academic_year', 'class_assigned'
    ).all().order_by('-id')
    
    # Get filter data
    teacher_filter = request.GET.get('teacher', '')
    subject_filter = request.GET.get('subject', '')
    year_filter = request.GET.get('academic_year', '')
    class_filter = request.GET.get('class_assigned', '')
    
    if teacher_filter:
        assignments_list = assignments_list.filter(teacher_id=teacher_filter)
    if subject_filter:
        assignments_list = assignments_list.filter(subject_id=subject_filter)
    if year_filter:
        assignments_list = assignments_list.filter(academic_year_id=year_filter)
    if class_filter:
        assignments_list = assignments_list.filter(class_assigned_id=class_filter)
    
    # Pagination
    per_page = request.GET.get('per_page', 10)
    try:
        per_page = int(per_page)
        if per_page not in [10, 25, 50, 100]:
            per_page = 10
    except ValueError:
        per_page = 10
    
    page = request.GET.get('page', 1)
    paginator = Paginator(assignments_list, per_page)
    
    try:
        assignments = paginator.page(page)
    except PageNotAnInteger:
        assignments = paginator.page(1)
    except EmptyPage:
        assignments = paginator.page(paginator.num_pages)
    
    if request.method == "POST":
        action = request.POST.get('action')
        
        # ADD SUBJECT ASSIGNMENT
        if action == 'add':
            form = TeacherSubjectForm(request.POST)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        assignment = form.save()
                        teacher = assignment.teacher
                        teacher_name = teacher.user.get_full_name()
                        subject_name = assignment.subject.name
                        
                        messages.success(
                            request, 
                            f'Subject "{subject_name}" assigned to Teacher "{teacher_name}" successfully!'
                        )
                        return redirect('manage_teacher_subjects')
                        
                except Exception as e:
                    messages.error(request, f'Error adding subject assignment: {str(e)}')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{form.fields[field].label if field in form.fields else field}: {error}")
        
        # EDIT SUBJECT ASSIGNMENT
        elif action == 'edit':
            assignment_id = request.POST.get('edit_id')
            try:
                assignment = TeacherSubject.objects.get(id=assignment_id)
                form = TeacherSubjectForm(request.POST, instance=assignment)
                
                if form.is_valid():
                    form.save()
                    messages.success(request, 'Subject assignment updated successfully!')
                    return redirect('manage_teacher_subjects')
                else:
                    for field, errors in form.errors.items():
                        for error in errors:
                            messages.error(request, f"{form.fields[field].label if field in form.fields else field}: {error}")
                            
            except TeacherSubject.DoesNotExist:
                messages.error(request, 'Subject assignment not found!')
        
        # DELETE SUBJECT ASSIGNMENT
        elif action == 'delete':
            assignment_id = request.POST.get('delete_id')
            try:
                assignment = TeacherSubject.objects.get(id=assignment_id)
                teacher_name = assignment.teacher.user.get_full_name()
                subject_name = assignment.subject.name
                assignment.delete()
                messages.success(
                    request, 
                    f'Subject "{subject_name}" removed from Teacher "{teacher_name}"!'
                )
            except TeacherSubject.DoesNotExist:
                messages.error(request, 'Subject assignment not found!')
            return redirect('manage_teacher_subjects')
        
        # BULK DELETE
        elif action == 'bulk_delete':
            assignment_ids = request.POST.getlist('assignment_ids')
            if assignment_ids:
                try:
                    with transaction.atomic():
                        assignments = TeacherSubject.objects.filter(id__in=assignment_ids)
                        count = assignments.count()
                        assignments.delete()
                        messages.success(request, f'{count} subject assignment(s) deleted successfully!')
                except Exception as e:
                    messages.error(request, f'Error deleting assignments: {str(e)}')
            else:
                messages.warning(request, 'No assignments selected for deletion')
            return redirect('manage_teacher_subjects')
    
    # GET request - initialize form
    form = TeacherSubjectForm()
    
    context = {
        'form': form,
        'assignments': assignments,
        'teachers': TeacherProfile.objects.all(),
        'subjects': Subject.objects.all(),
        'academic_years': AcademicYear.objects.all(),
        'classes': SchoolClass.objects.all(),
        'total_assignments': assignments_list.count(),
        'teacher_filter': teacher_filter,
        'subject_filter': subject_filter,
        'year_filter': year_filter,
        'class_filter': class_filter,
        'per_page': per_page,
    }
    
    return render(request, "school_admin/manage_teacher_subjects.html", context)


@login_required
def manage_bank_details(request, teacher_id):
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    bank_details, created = TeacherBankDetails.objects.get_or_create(teacher=teacher)
    
    if request.method == 'POST':
        form = TeacherBankDetailsForm(request.POST, instance=bank_details)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bank details updated successfully!')
            return redirect('view_teacher', teacher_id=teacher.id)
    else:
        form = TeacherBankDetailsForm(instance=bank_details)
    
    context = {
        'teacher': teacher,
        'form': form,
    }
    return render(request, 'school_admin/manage_bank_details.html', context)

# views.py
def manage_classes(request):
    classes = SchoolClass.objects.all().order_by('name')
    form = SchoolClassForm()

    if request.method == "POST":
        action = request.POST.get('action')

        # ADD
        if action == 'add':
            form = SchoolClassForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Class created successfully!')
                return redirect('manage_classes')

        # EDIT
        elif action == 'edit':
            class_id = request.POST.get('edit_id')  # 🔥 FIXED
            school_class = get_object_or_404(SchoolClass, id=class_id)
            form = SchoolClassForm(request.POST, instance=school_class)
            if form.is_valid():
                form.save()
                messages.success(request, 'Class updated successfully!')
                return redirect('manage_classes')

        # DELETE (single)
        elif action == 'delete':
            class_id = request.POST.get('delete_id')  # 🔥 FIXED
            school_class = get_object_or_404(SchoolClass, id=class_id)
            school_class.delete()
            messages.success(request, 'Class deleted successfully!')
            return redirect('manage_classes')

        # BULK DELETE
        elif action == 'bulk_delete':
            class_ids = request.POST.getlist('class_ids')
            if class_ids:
                SchoolClass.objects.filter(id__in=class_ids).delete()
                messages.success(
                    request, f'{len(class_ids)} class(es) deleted successfully!'
                )
            return redirect('manage_classes')

    return render(request, "school_admin/manage_classes.html", {
        "form": form,
        "classes": classes
    })


def manage_subjects(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            name = request.POST.get('name')
            if name:
                Subject.objects.create(name=name)
                messages.success(request, f'Subject "{name}" added successfully!')
        
        elif action == 'edit':
            subject_id = request.POST.get('edit_id')
            name = request.POST.get('name')
            if subject_id and name:
                subject = get_object_or_404(Subject, id=subject_id)
                subject.name = name
                subject.save()
                messages.success(request, f'Subject updated successfully!')
        
        elif action == 'delete':
            subject_id = request.POST.get('delete_id')
            if subject_id:
                subject = get_object_or_404(Subject, id=subject_id)
                subject_name = subject.name
                subject.delete()
                messages.success(request, f'Subject "{subject_name}" deleted successfully!')
        
        return redirect('manage_subjects')
    
    # GET request - show subjects
    search_query = request.GET.get('search', '')
    per_page = int(request.GET.get('per_page', 10))
    
    subjects_list = Subject.objects.all()
    
    if search_query:
        subjects_list = subjects_list.filter(name__icontains=search_query)
    
    paginator = Paginator(subjects_list, per_page)
    page_number = request.GET.get('page')
    subjects = paginator.get_page(page_number)
    
    context = {
        'subjects': subjects,
        'total_subjects': Subject.objects.count(),
        'teachers_count': 0,  # Update with your actual data
        'classes_count': 0,   # Update with your actual data
        'students_count': 0,  # Update with your actual data
        'per_page': per_page,
    }
    
    return render(request, "school_admin/manage_subjects.html", context)

# You'll need to create this form
def manage_academic_years(request):
    academic_years = AcademicYear.objects.all().order_by('-year')
    
    if request.method == "POST":
        action = request.POST.get('action')
        
        # ADD
        if action == 'add':
            form = AcademicYearForm(request.POST)
            if form.is_valid():
                academic_year = form.save(commit=False)
                
                # If setting as active, deactivate others
                if academic_year.is_active:
                    AcademicYear.objects.filter(is_active=True).update(is_active=False)
                
                academic_year.save()
                messages.success(request, f'Academic year "{academic_year.year}" created successfully!')
                return redirect('manage_academic_years')
            else:
                # Handle form errors
                for error in form.errors.values():
                    messages.error(request, error)
                return redirect('manage_academic_years')
        
        # EDIT
        elif action == 'edit':
            year_id = request.POST.get('edit_id')
            academic_year = get_object_or_404(AcademicYear, id=year_id)
            form = AcademicYearForm(request.POST, instance=academic_year)
            
            if form.is_valid():
                updated_year = form.save(commit=False)
                
                # If setting as active, deactivate others
                if updated_year.is_active and not academic_year.is_active:
                    AcademicYear.objects.filter(is_active=True).update(is_active=False)
                
                updated_year.save()
                messages.success(request, f'Academic year "{updated_year.year}" updated successfully!')
                return redirect('manage_academic_years')
            else:
                for error in form.errors.values():
                    messages.error(request, error)
                return redirect('manage_academic_years')
        
        # SET ACTIVE
        elif action == 'set_active':
            year_id = request.POST.get('year_id')
            academic_year = get_object_or_404(AcademicYear, id=year_id)
            
            # Deactivate all years
            AcademicYear.objects.filter(is_active=True).update(is_active=False)
            
            # Activate selected year
            academic_year.is_active = True
            academic_year.save()
            
            messages.success(request, f'Academic year "{academic_year.year}" is now active!')
            return redirect('manage_academic_years')
        
        # DELETE
        elif action == 'delete':
            year_id = request.POST.get('delete_id')
            academic_year = get_object_or_404(AcademicYear, id=year_id)
            
            # Prevent deletion of active year
            if academic_year.is_active:
                messages.error(request, 'Cannot delete the active academic year!')
                return redirect('manage_academic_years')
            
            year_name = academic_year.year
            academic_year.delete()
            messages.success(request, f'Academic year "{year_name}" deleted successfully!')
            return redirect('manage_academic_years')
        
        # BULK DELETE
        elif action == 'bulk_delete':
            year_ids = request.POST.getlist('year_ids')
            
            # Check if any active year is in the selection
            active_years = AcademicYear.objects.filter(id__in=year_ids, is_active=True)
            if active_years.exists():
                messages.error(request, 'Cannot delete active academic years!')
                return redirect('manage_academic_years')
            
            if year_ids:
                deleted_count = AcademicYear.objects.filter(id__in=year_ids).delete()[0]
                messages.success(request, f'{deleted_count} academic year(s) deleted successfully!')
            
            return redirect('manage_academic_years')
    
    return render(request, 'school_admin/manage_academic_years.html', {
        'academic_years': academic_years
    })