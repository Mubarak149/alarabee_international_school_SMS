from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('school/admin/', include('school_admin.urls')),
    path('staff/', include('staff.urls')),
    path('students/', include('students.urls')),
    path('academics/', include('academics.urls')),
    path('finance/', include('finance.urls')),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
