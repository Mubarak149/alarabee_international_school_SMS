from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.forms import StudentUserForm
from students.forms import StudentProfileForm, StudentClassForm
from students.models import StudentProfile, StudentClass
from academics.forms import SchoolClassForm, AcademicYearForm
from academics.models import AcademicYear, SchoolClass, Subject
from django.db import transaction
from datetime import datetime
# Create your views here.
def admin_panel(request):
    return render(request, "school_admin/admin_dashboard.html")

def admin_profile(request):
    return render(request, "school_admin/admin_profile.html")


# views.py
def manage_students(request):
    # Get all students with related data
    students = StudentProfile.objects.select_related('user').prefetch_related('studentclass_set').all()
    
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
                        # Save User
                        user = user_form.save(commit=False)
                        user.user_type = 'student'
                        user.set_password('student123')  # Default password
                        user.save()
                        
                        # Save StudentProfile
                        profile = profile_form.save(commit=False)
                        profile.user = user
                        
                        # Generate student ID if not provided
                        if not profile.student_id:
                            year = datetime.now().year % 100
                            last_student = StudentProfile.objects.filter(
                                student_id__startswith=f'STU-{year}'
                            ).order_by('-student_id').first()
                            
                            if last_student and last_student.student_id:
                                try:
                                    last_num = int(last_student.student_id.split('-')[2])
                                    new_num = last_num + 1
                                except (IndexError, ValueError):
                                    new_num = 1
                            else:
                                new_num = 1
                            
                            profile.student_id = f'STU-{year}-{new_num:03d}'
                        
                        profile.save()
                        
                        # Save StudentClass
                        student_class = class_form.save(commit=False)
                        student_class.student = profile
                        student_class.save()
                    
                    messages.success(request, f'Student {user.get_full_name()} added successfully!')
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
                
                user_form = StudentUserForm(request.POST, instance=user)
                profile_form = StudentProfileForm(request.POST, instance=profile)
                
                # Get or create StudentClass
                student_class = profile.studentclass_set.first()
                if student_class:
                    class_form = StudentClassForm(request.POST, instance=student_class)
                else:
                    class_form = StudentClassForm(request.POST)
                
                if all([user_form.is_valid(), profile_form.is_valid(), class_form.is_valid()]):
                    try:
                        with transaction.atomic():
                            user_form.save()
                            profile_form.save()
                            
                            student_class_instance = class_form.save(commit=False)
                            student_class_instance.student = profile
                            student_class_instance.save()
                        
                        messages.success(request, f'Student {user.get_full_name()} updated successfully!')
                        return redirect('manage_students')
                        
                    except Exception as e:
                        messages.error(request, f'Error updating student: {str(e)}')
                else:
                    for form in [user_form, profile_form, class_form]:
                        for error in form.errors.values():
                            messages.error(request, error)
                    return redirect('manage_students')
                        
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

        # BULK DELETE
        elif action == 'bulk_delete':
            student_ids = request.POST.getlist('student_ids')
            if student_ids:
                deleted_count = 0
                for student_id in student_ids:
                    try:
                        profile = StudentProfile.objects.get(id=student_id)
                        profile.user.delete()
                        deleted_count += 1
                    except StudentProfile.DoesNotExist:
                        continue
                
                messages.success(request, f'{deleted_count} student(s) deleted successfully!')
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
    return render(request, "school_admin/manage_teachers.html")
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
    return render(request, "school_admin/manage_subjects.html")

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