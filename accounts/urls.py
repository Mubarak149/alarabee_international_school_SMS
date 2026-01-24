from .views import RoleBasedLoginView, logout_view
from django.contrib.auth import views as auth_views
from django.urls import path

urlpatterns = [
    path(
        "",
        RoleBasedLoginView.as_view(redirect_authenticated_user=True),
        name="login",
    ),
    path(
        "login/",
        RoleBasedLoginView.as_view(redirect_authenticated_user=True),
        name="login",
    ),
    path("logout/", logout_view, name="logout"),

]
