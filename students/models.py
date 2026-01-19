from django.db import models
from django.db.models import Avg

# Create your models here.

class StudentProfile(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    parent_name = models.CharField(max_length=100)
    parent_contact = models.CharField(max_length=15)

    @property
    def current_class_name(self):
        """Get the name of the current class"""
        current_class = self.class_records.filter(is_current=True).first()
        if current_class and current_class.school_class:
            return current_class.school_class.name
        return ""
    
    @property
    def full_name(self):
        """Get student's full name"""
        return f"{self.user.first_name} {self.user.last_name}"

    def average_score(self, academic_session, term):
        return StudentScore.objects.filter(
            student=self,
            academic_session=academic_session,
            term=term
        ).aggregate(avg_score=Avg('score'))['avg_score']
    

    def class_rank(self, academic_session, term):
        # Step 1: get this student's average
        my_avg = StudentScore.objects.filter(
            student=self,
            academic_session=academic_session,
            term=term
        ).aggregate(avg=Avg('score'))['avg']

        if my_avg is None:
            return None

        # Step 2: get all students' averages in the same class
        class_averages = (
            StudentScore.objects.filter(
                academic_session=academic_session,
                term=term,
                student__class_records__is_current=True,
                student__class_records__school_class=
                self.class_records.filter(is_current=True).first().school_class
            )
            .values('student')
            .annotate(avg=Avg('score'))
            .order_by('-avg')
        )

        # Step 3: calculate rank
        rank = 1
        for record in class_averages:
            if record['avg'] > my_avg:
                rank += 1

        return rank


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

    

