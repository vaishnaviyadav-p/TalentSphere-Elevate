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


class JobApplication(models.Model):

    STATUS_CHOICES = (
        ("Applied", "Applied"),
        ("Shortlisted", "Shortlisted"),
        ("Interview", "Interview"),
        ("Rejected", "Rejected"),
    )

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