from django.urls import path
from . import views


urlpatterns = [

    # ==============================
    # Candidate Dashboard
    # ==============================

    path(
        "dashboard/",
        views.candidate_dashboard,
        name="candidate_dashboard"
    ),

    # ==============================
    # Jobs
    # ==============================

    path(
        "jobs/",
        views.browse_jobs,
        name="browse_jobs"
    ),

    path(
        "jobs/<int:job_id>/",
        views.job_detail,
        name="job_detail"
    ),

    path(
        "apply/<int:job_id>/",
        views.apply_job,
        name="apply_job"
    ),

    # ==============================
    # Applications
    # ==============================

    path(
        "applications/",
        views.my_applications,
        name="my_applications"
    ),

    # ==============================
    # Interviews
    # ==============================

    path(
        "interviews/",
        views.candidate_interviews,
        name="candidate_interviews"
    ),

    # ==============================
    # Candidate Profile
    # ==============================

    path(
        "profile/",
        views.candidate_profile,
        name="candidate_profile"
    ),

    path(
        "edit-profile/",
        views.edit_candidate_profile,
        name="edit_candidate_profile"
    ),

    # ==============================
    # Resume
    # ==============================

    path(
        "upload-resume/",
        views.upload_resume,
        name="upload_resume"
    ),
]