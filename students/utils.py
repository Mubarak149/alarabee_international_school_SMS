# students/utils.py
import io
import os
from django.utils import timezone
from django.conf import settings
# PDF Generation imports
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4



def register_fonts():
    ROBOTO_DIR = os.path.join(settings.BASE_DIR, 'static', 'Roboto', 'static')

    try:
        pdfmetrics.registerFont(
            TTFont('Roboto', os.path.join(ROBOTO_DIR, 'Roboto-Regular.ttf'))
        )
        pdfmetrics.registerFont(
            TTFont('Roboto-Bold', os.path.join(ROBOTO_DIR, 'Roboto-Bold.ttf'))
        )
        pdfmetrics.registerFont(
            TTFont('Roboto-Italic', os.path.join(ROBOTO_DIR, 'Roboto-Italic.ttf'))
        )
        pdfmetrics.registerFont(
            TTFont('Roboto-BoldItalic', os.path.join(ROBOTO_DIR, 'Roboto-BoldItalic.ttf'))
        )

        # THIS LINE IS THE KEY 🔑
        registerFontFamily(
            'Roboto',
            normal='Roboto',
            bold='Roboto-Bold',
            italic='Roboto-Italic',
            boldItalic='Roboto-BoldItalic'
        )

    except Exception as e:
        print("Font registration failed:", e)


register_fonts()


def generate_student_id(prefix, student_db_id):
    """Generate a simple student ID like STU-2026-00001"""
    year = timezone.now().year
    return f"{prefix}-{year}-{student_db_id:05d}"  # e.g., STU-2026-00001

def normalize_name(name):
    """Capitalize the first letter of each word in the name."""
    words = name.split()
    normalized_words = [word.capitalize() for word in words]
    return ' '.join(normalized_words)


# Helper functions
def get_performance_label(average_score):
    if average_score >= 80:
        return "EXCELLENT"
    elif average_score >= 70:
        return "VERY GOOD"
    elif average_score >= 60:
        return "GOOD"
    elif average_score >= 50:
        return "AVERAGE"
    else:
        return "NEEDS IMPROVEMENT"

def get_best_subject(scores):
    if scores.exists():
        best = max(scores, key=lambda x: x.score)
        return f"{best.subject.name} ({best.score}%)"
    return "N/A"

def get_weakest_subject(scores):
    if scores.exists():
        weakest = min(scores, key=lambda x: x.score)
        return f"{weakest.subject.name} ({weakest.score}%)"
    return "N/A"

def get_grade(score):
    if score >= 70:
        return "A"
    elif score >= 60:
        return "B"
    elif score >= 50:
        return "C"
    elif score >= 40:
        return "D"
    else:
        return "F"


def get_remarks(score):
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    else:
        return "Needs Improvement"

def get_teacher_comment(score):
    if score >= 90:
        return "Outstanding performance!"
    elif score >= 80:
        return "Very good work."
    elif score >= 70:
        return "Good effort shown."
    elif score >= 60:
        return "Satisfactory."
    elif score >= 50:
        return "Can do better."
    else:
        return "Needs more attention."

def get_score_color(score):
    if score >= 90:
        return colors.HexColor('#27AE60')  # Green
    elif score >= 80:
        return colors.HexColor('#2ECC71')  # Light Green
    elif score >= 70:
        return colors.HexColor('#F1C40F')  # Yellow
    elif score >= 60:
        return colors.HexColor('#E67E22')  # Orange
    elif score >= 50:
        return colors.HexColor('#E74C3C')  # Red
    else:
        return colors.HexColor('#C0392B')  # Dark Red
