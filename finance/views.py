from django.shortcuts import render

# Create your views here.
def finance_dashboard(request):
    return render(request, 'finance/finance_dashboard.html')