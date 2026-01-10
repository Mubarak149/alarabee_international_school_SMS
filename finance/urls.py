from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.finance_dashboard, name='finance_dashboard'),
]
