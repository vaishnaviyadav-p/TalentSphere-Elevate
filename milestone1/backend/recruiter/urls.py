from django.urls import path
from . import views


urlpatterns = [

    # ============================================================
    # DASHBOARD
    # ============================================================

    path(
        "dashboard/",
        views.dashboard,
        name="recruiter_dashboard"
    ),

    # ============================================================
    # PROFILE
    # ============================================================

    path(
        "profile/",
        views.recruiter_profile,
        name="recruiter_profile"
    ),

    path(
        "edit-profile/",
        views.edit_recruiter_profile,
        name="edit_recruiter_profile"
    ),

    # ============================================================
    # SETTINGS
    # ============================================================

    path(
        "settings/",
        views.recruiter_settings,
        name="recruiter_settings"
    ),

    # ============================================================
    # ANALYTICS
    # ============================================================

    path(
        "analytics/",
        views.analytics_dashboard,
        name="analytics_dashboard"
    ),

    # ============================================================
    # JOB LISTINGS
    # ============================================================

    path(
        "job-listings/",
        views.job_listings,
        name="job_listings"
    ),

    # ============================================================
    # POST / CREATE JOB
    # ============================================================

    path(
        "post-job/",
        views.post_job,
        name="post_job"
    ),

    path(
        "create-job/",
        views.create_job,
        name="create_job"
    ),

    # ============================================================
    # JOB DETAIL
    # ============================================================

    path(
        "job/<int:job_id>/",
        views.recruiter_job_detail,
        name="recruiter_job_detail"
    ),

    # ============================================================
    # EDIT JOB
    # ============================================================

    path(
        "job/<int:job_id>/edit/",
        views.edit_job,
        name="edit_job"
    ),

    # ============================================================
    # DELETE JOB
    # ============================================================

    path(
        "job/<int:job_id>/delete/",
        views.delete_job,
        name="delete_job"
    ),

    # ============================================================
    # APPLICANTS
    # ============================================================

    path(
        "job/<int:job_id>/applicants/",
        views.view_applicants,
        name="view_applicants"
    ),

    # ============================================================
    # PRIORITY CANDIDATES
    # ============================================================

    path(
        "priority-candidates/",
        views.priority_candidates,
        name="priority_candidates"
    ),

    # ============================================================
    # APPLICATION STATUS
    # ============================================================

    path(
        "update-application-status/<int:application_id>/",
        views.update_application_status,
        name="update_application_status"
    ),

    # ============================================================
    # CANDIDATE DETAIL
    # ============================================================

    path(
        "candidate/<int:candidate_id>/",
        views.view_candidate_detail,
        name="view_candidate_detail"
    ),

    # ============================================================
    # INTERVIEW
    # ============================================================

    path(
        "schedule-interview/",
        views.schedule_interview,
        name="schedule_interview"
    ),

    path(
        "interviews/",
        views.interview_list,
        name="interview_list"
    ),

    path(
        "interview/<int:interview_id>/status/",
        views.update_interview_status,
        name="update_interview_status"
    ),

    path(
        "interview/<int:interview_id>/edit/",
        views.edit_interview,
        name="edit_interview"
    ),
]