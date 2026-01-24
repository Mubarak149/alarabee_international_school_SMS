from django.shortcuts import render
# accounts/views.py
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
# Create your views here.
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

class RoleBasedLoginView(LoginView):
    template_name = "login.html"

    def get_success_url(self):
        user = self.request.user

        if user.role == "admin":
            return reverse_lazy("admin_dashboard")

        elif user.role == "staff":
            return reverse_lazy("teacher_dashboard")

        elif user.role == "student":
            return reverse_lazy("student_dashboard")

        # fallback (just in case)
        return reverse_lazy("login")



def logout_view(request):
    """
    Logs out the user and redirects to login page.
    """
    # Log the user out
    logout(request)

    # Optional: add a message
    messages.success(request, "You have been successfully logged out.")

    # Redirect to login page
    return redirect("login")
