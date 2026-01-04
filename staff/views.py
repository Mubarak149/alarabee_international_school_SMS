from django.shortcuts import render

# Create your views here.
def teachers_dashboard(request):
    return render(request, "teachers/teacher_dashboard.html")

def teacher_classes(request):
    return render(request, "teachers/teacher_classes.html")