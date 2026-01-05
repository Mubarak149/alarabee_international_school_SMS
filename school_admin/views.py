from django.shortcuts import render, redirect
from accounts.forms import StudentUserForm
from students.forms import StudentProfileForm, StudentClassForm
from academics.forms import SchoolClassForm
# Create your views here.
def admin_panel(request):
    return render(request, "school_admin/admin_dashboard.html")

def admin_profile(request):
    return render(request, "school_admin/admin_profile.html")

def manage_students(request):
# 🔥 GET request → send empty forms to frontend
    user_form = StudentUserForm()
    profile_form = StudentProfileForm()
    class_form = StudentClassForm()
    return render(request, "school_admin/manage_students.html", {
        "user_form": user_form,
        "profile_form": profile_form,
        "class_form": class_form,
    })

def manage_teachers(request):
    return render(request, "school_admin/manage_teachers.html")

def manage_classes(request):
    if request.method == "POST":
        form = SchoolClassForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("manage_classes")  # reload page after save

    else:
        # GET request → empty form
        form = SchoolClassForm()

    return render(request, "school_admin/manage_classes.html", {
        "form": form
    })

def manage_subjects(request):
    return render(request, "school_admin/manage_subjects.html")


