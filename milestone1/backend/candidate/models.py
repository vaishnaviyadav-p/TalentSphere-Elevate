from django.db import models
from django.contrib.auth.models import User


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
        upload_to='profile_images/',
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