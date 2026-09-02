from django.urls import path
from . import views


urlpatterns = [

    path(
        "dashboard/",
        views.recruiter_dashboard,
        name="recruiter_dashboard"
    ),

    path(
        "profile/",
        views.recruiter_profile,
        name="recruiter_profile"
    ),

    path(
        "edit-profile/",
        views.recruiter_profile,
        name="edit_recruiter_profile"
    ),


    # Recruiter Dashboard (detailed)

    path(
        "dashboard/detailed/",
        views.dashboard,
        name="recruiter_dashboard_detailed"
    ),


    # Recruiter Analytics (from origin/main)

    path(
        "analytics/",
        views.analytics_dashboard,
        name="analytics_dashboard"
    ),


    # Candidate

    path(
        "candidate/<int:candidate_id>/",
        views.view_candidate_detail,
        name="view_candidate_detail"
    ),


    # Priority Candidates

    path(
        "priority-candidates/",
        views.priority_candidates,
        name="priority_candidates"
    ),


    # Jobs

    path(
        "post-job/",
        views.post_job,
        name="post_job"
    ),

    path(
        "edit-job/<int:job_id>/",
        views.edit_job,
        name="edit_job"
    ),

    path(
        "delete-job/<int:job_id>/",
        views.delete_job,
        name="delete_job"
    ),


    # ==============================
    # Interview Scheduling
    # ==============================

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
        "interviews/<int:interview_id>/status/",
        views.update_interview_status,
        name="update_interview_status"
    ),

    path(
        "interviews/<int:interview_id>/edit/",
        views.edit_interview,
        name="edit_interview"
    ),
    path(
    "update-application-status/<int:application_id>/",
    views.update_application_status,
    name="update_application_status",
),

path(
    "job-listings/",
    views.job_listings,
    name="job_listings"
),

path(
    "settings/",
    views.recruiter_settings,

    name="recruiter_settings"
),
]