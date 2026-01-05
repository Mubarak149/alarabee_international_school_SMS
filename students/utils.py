# students/utils.py
from django.utils import timezone

def generate_student_id(student_db_id):
    """Generate a simple student ID like STU-2026-001"""
    year = timezone.now().year
    return f"STU-{year}-{student_db_id:03d}"  # e.g., STU-2026-001

def normalize_name(name):
    """Capitalize the first letter of each word in the name."""
    words = name.split()
    normalized_words = [word.capitalize() for word in words]
    return ' '.join(normalized_words)