from django.urls import path

from . import views


urlpatterns = [

    # Recruiter Profile

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


    # Recruiter Dashboard

    path(
        "dashboard/",
        views.dashboard,
        name="recruiter_dashboard"
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
]