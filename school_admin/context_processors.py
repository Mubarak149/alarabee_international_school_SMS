# school_admin/context_processors.py
from .models import SystemSettings

def system_settings(request):
    """
    Make system settings available in ALL templates.
    This function is called for every request.
    """
    try:
        settings = SystemSettings.get_settings()
        return {
            'system_settings': settings,
            'school_name': settings.school_name,
            'student_id_option': settings.student_id_option,
            'default_student_password': settings.default_student_password,
        }
    except Exception as e:
        # Return default values if there's an error
        print(f"Error loading system settings: {e}")
        return {
            'system_settings': None,
            'school_name': "Our School",
            'student_id_option': "auto",
            'default_student_password': "Password123",
        }