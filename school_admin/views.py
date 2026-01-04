from django.shortcuts import render

# Create your views here.
def admin_panel(request):
    return render(request, "school_admin/admin_dashboard.html")

def manage_students(request):
    return render(request, "school_admin/manage_students.html")

def manage_teachers(request):
    return render(request, "school_admin/manage_teachers.html")

def manage_classes(request):
    return render(request, "school_admin/manage_classes.html")

def manage_subjects(request):
    return render(request, "school_admin/manage_subjects.html")

