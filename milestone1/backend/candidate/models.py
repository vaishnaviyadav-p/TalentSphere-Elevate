from django.db import models
from django.contrib.auth.models import User
from recruiter.models import Job


class CandidateProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    full_name = models.CharField(max_length=100)

    phone = models.CharField(max_length=15)

    location = models.CharField(max_length=100)

    education = models.CharField(max_length=200)

    skills = models.TextField()

    experience = models.TextField()

    bio = models.TextField()

    profile_image = models.ImageField(
        upload_to="profile_images/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name


class ResumeData(models.Model):
    candidate = models.OneToOneField(
        CandidateProfile,
        on_delete=models.CASCADE,
        related_name='resume_data'
    ) 

    resume_file = models.FileField(
        upload_to='resumes/'
    )

    extracted_text = models.TextField(
        blank=True,
        null=True
    )

    parsed_name = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    parsed_email = models.EmailField(
        blank=True,
        null=True
    )

    parsed_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    parsed_skills = models.JSONField(
        default=list,
        blank=True
    )

    parsed_experience = models.JSONField(
        default=list,
        blank=True
    )

    parsed_projects = models.JSONField(
        default=list,
        blank=True
    )

    parsed_keywords = models.JSONField(
        default=list,
        blank=True
    )

    parsed_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Resume - {self.candidate.full_name}"


class JobApplication(models.Model):

    STATUS_CHOICES = [
        ("Applied", "Applied"),
        ("Shortlisted", "Shortlisted"),
        ("Interview", "Interview"),
        ("Rejected", "Rejected"),
        ("Selected", "Selected"),
    ]

    candidate = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="job_applications"
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="applications"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Applied"
    )

    applied_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ("candidate", "job")
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.candidate.username} applied for {self.job.title}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        if not is_new:
            try:
                old_status = JobApplication.objects.get(pk=self.pk).status
            except JobApplication.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
        
        if (not is_new and old_status != self.status) or (is_new and self.status != "Applied"):
            try:
                from recruiter.email_services import send_application_status_update_email
                send_application_status_update_email(self)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error sending application status update email: {e}")
