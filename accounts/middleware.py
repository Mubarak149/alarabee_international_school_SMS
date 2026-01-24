from django.shortcuts import redirect
from django.urls import reverse

class RoleBasedAccessMiddleware:
    """
    Middleware to restrict access to URLs based on user role,
    with special handling for Django superusers.
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Allowed paths per role
        self.allowed_paths = {
            "admin": [
                "/login/",
                "/accounts/logout/",
                "/admin/",
                "/school/admin/",
                "/finance/",        # ✅ ADD THIS
                "/academics/",      # (optional, if admin can access academics)
            ],
            "staff": [
                "/login/",
                "/accounts/logout/",
                "/staff/",
            ],
            "student": [
                "/login/",
                "/accounts/logout/",
                "/students/",
            ],
        }

        self.dashboard_redirect = {
            "admin": "admin_dashboard",
            "staff": "teacher_dashboard",
            "student": "student_dashboard",
        }

        self.public_paths = [
            "/static/",
            "/media/",
            "logout",
        ]

        # Dashboard redirects per role
        self.dashboard_redirect = {
            "admin": "admin_dashboard",
            "staff": "teacher_dashboard",
            "student": "student_dashboard",
            
        }

        # Paths everyone can access
        self.public_paths = [
            "/static/",
            "/media/",
            "/logout/"
        ]

    def __call__(self, request):
        path = request.path

        # Allow public paths
        for public_path in self.public_paths:
            if path.startswith(public_path):
                return self.get_response(request)

        # If user is not logged in, let Django handle it
        if not request.user.is_authenticated:
            return self.get_response(request)

        user = request.user

        # --- SUPERUSER FIX ---
        # If the user is a superuser, always treat them as admin
        role = "admin" if user.is_superuser else user.role

        allowed = self.allowed_paths.get(role, [])

        # Check if path is allowed
        for allowed_path in allowed:
            if path.startswith(allowed_path):
                return self.get_response(request)

        # Not allowed → redirect to user's dashboard
        return redirect(reverse(self.dashboard_redirect[role]))
