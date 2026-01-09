from django.shortcuts import render

# Create your views here.
def student_dashboard(request):
    return render(request, 'student/student_dashboard.html')

def student_report_cards(request):
    return render(request, 'student/report_cards.html')

def student_subject(request):
    return render(request, 'student/student_subject.html')

def student_profile(request):
    return render(request, 'student/profile.html')

def student_settings(request):
    return render(request, 'student/settings.html')