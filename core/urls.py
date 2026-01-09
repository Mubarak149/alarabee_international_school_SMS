from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('school/admin/', include('school_admin.urls')),
    path('staff/', include('staff.urls')),
    path('students/', include('students.urls')),
    path('academics/', include('academics.urls')),
]

