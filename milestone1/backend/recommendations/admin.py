from django.contrib import admin
from .models import JobRecommendation, CandidateRecommendation


@admin.register(JobRecommendation)
class JobRecommendationAdmin(admin.ModelAdmin):
    list_display = ["candidate", "job", "match_score", "is_viewed", "is_dismissed", "created_at"]
    list_filter = ["is_viewed", "is_dismissed", "created_at"]
    search_fields = ["candidate__username", "job__title", "job__company"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]


@admin.register(CandidateRecommendation)
class CandidateRecommendationAdmin(admin.ModelAdmin):
    list_display = ["job", "candidate", "match_score", "experience_match", "is_viewed", "is_dismissed", "created_at"]
    list_filter = ["is_viewed", "is_dismissed", "experience_match", "created_at"]
    search_fields = ["job__title", "candidate__username", "candidate__email"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]