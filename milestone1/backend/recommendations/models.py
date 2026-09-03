from django.db import models
from django.contrib.auth.models import User
from candidate.models import CandidateProfile, JobApplication
from recruiter.models import Job


class JobRecommendation(models.Model):
    """AI-generated job recommendations for candidates."""
    
    candidate = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="job_recommendations"
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="job_recommendations_for_candidates"
    )
    match_score = models.FloatField(help_text="Overall match percentage (0-100)")
    skill_match_score = models.FloatField(help_text="Skill match percentage (0-100)")
    experience_match_score = models.FloatField(help_text="Experience match percentage (0-100)", default=50.0)
    matched_skills = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    reason = models.TextField(help_text="Explanation of why this job was recommended")
    is_viewed = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("candidate", "job")
        ordering = ["-match_score", "-created_at"]
        indexes = [
            models.Index(fields=["candidate", "is_viewed", "is_dismissed"]),
            models.Index(fields=["candidate", "match_score"]),
        ]

    def __str__(self):
        return f"{self.candidate.username} -> {self.job.title} ({self.match_score}%)"


class CandidateRecommendation(models.Model):
    """AI-generated candidate recommendations for recruiters/jobs."""
    
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="candidate_recommendations_for_job"
    )
    candidate = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="candidate_recommendations_for_recruiters"
    )
    match_score = models.FloatField(help_text="Overall match percentage (0-100)")
    skill_match_score = models.FloatField(help_text="Skill match percentage (0-100)")
    experience_match_score = models.FloatField(help_text="Experience match percentage (0-100)", default=50.0)
    matched_skills = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    experience_match = models.BooleanField(default=False)
    reason = models.TextField(help_text="Explanation of why this candidate was recommended")
    is_viewed = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("job", "candidate")
        ordering = ["-match_score", "-created_at"]
        indexes = [
            models.Index(fields=["job", "is_viewed", "is_dismissed"]),
            models.Index(fields=["job", "match_score"]),
        ]

    def __str__(self):
        return f"{self.job.title} -> {self.candidate.username} ({self.match_score}%)"