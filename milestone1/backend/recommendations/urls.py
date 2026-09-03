from django.urls import path
from . import views

urlpatterns = [
    # Candidate: Job Recommendations
    path(
        "jobs/",
        views.candidate_job_recommendations,
        name="candidate_job_recommendations"
    ),
    
    # Recruiter: Candidate Recommendations for a specific job
    path(
        "recruiter/job/<int:job_id>/candidates/",
        views.recruiter_candidate_recommendations,
        name="recruiter_candidate_recommendations"
    ),
    
    # Recruiter: All candidate recommendations across jobs
    path(
        "recruiter/candidates/",
        views.recruiter_all_recommendations,
        name="recruiter_all_recommendations"
    ),
    
    # AJAX endpoints
    path(
        "mark-viewed/",
        views.mark_recommendation_viewed_ajax,
        name="mark_recommendation_viewed"
    ),
    path(
        "dismiss/",
        views.dismiss_recommendation_ajax,
        name="dismiss_recommendation"
    ),
]