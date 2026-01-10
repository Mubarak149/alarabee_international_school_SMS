from django.db import models

# Create your models here.
class StudentProfile(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    parent_name = models.CharField(max_length=100)
    parent_contact = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.student_id}"
    
class StudentClass(models.Model):
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="class_records"
    )
    school_class = models.ForeignKey(
        'academics.SchoolClass',
        on_delete=models.CASCADE
    )
    academic_year = models.ForeignKey(
        'academics.AcademicYear',
        on_delete=models.CASCADE
    )
    is_current = models.BooleanField(default=True)
    date_assigned = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'school_class', 'academic_year')

    def __str__(self):
        return f"{self.student} → {self.school_class} ({self.academic_year})"

class StudentScore(models.Model):
    student = models.ForeignKey("students.StudentProfile", on_delete=models.CASCADE)
    subject = models.ForeignKey("academics.Subject", on_delete=models.CASCADE)
    academic_session = models.ForeignKey('academics.AcademicYear', on_delete=models.CASCADE)
    term = models.ForeignKey("academics.Term", on_delete=models.CASCADE)
    score_type = models.ForeignKey("academics.ScoreType", on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        unique_together = (
            'student',
            'subject',
            'academic_session',
            'term',
            'score_type'
        )

    def __str__(self):
        return f"{self.student} - {self.subject} ({self.score_type}): {self.score}"

    

