from django.db import models
from django.contrib.auth.models import User


class RecruiterProfile(models.Model):
    user = models.OneToOneField(
    User,
    on_delete=models.CASCADE,
    null=True,
    blank=True
)

    recruiter_name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    location = models.CharField(max_length=100)

    company_description = models.TextField()

    company_logo = models.ImageField(
        upload_to='company_logo/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name

class Job(models.Model):

    recruiter = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    title = models.CharField(max_length=200)

    company = models.CharField(max_length=150)

    location = models.CharField(max_length=100)

    salary = models.CharField(max_length=100)

    job_type = models.CharField(max_length=50)

    experience = models.CharField(max_length=50)

    description = models.TextField()

    requirements = models.TextField()

    deadline = models.DateField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title