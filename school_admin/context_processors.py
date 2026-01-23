# school_admin/context_processors.py
from .models import SystemSettings

def system_settings(request):
    """
    Make system settings available in ALL templates.
    """
    try:
        settings = SystemSettings.get_settings()
        return {
            'system_settings': settings,

            # Basic
            'school_name': settings.school_name,

            # Branding & contact
            'school_logo': settings.school_logo,
            'school_email': settings.school_email,
            'school_phone': settings.school_phone,
            'school_address': settings.school_address,

            # Student options
            'student_id_option': settings.student_id_option,
            'default_student_password': settings.default_student_password,
        }
    except Exception as e:
        print(f"Error loading system settings: {e}")
        return {
            'system_settings': None,
            'school_name': "Our School",
            'school_logo': None,
            'school_email': "",
            'school_phone': "",
            'school_address': "",
            'student_id_option': "auto",
            'default_student_password': "Password123",
        }
