from django.urls import path
from . import views

urlpatterns = [
    path("profile/", views.recruiter_profile, name="recruiter_profile"),
    path("edit-profile/", views.edit_recruiter_profile, name="edit_recruiter_profile"),
    path("dashboard/", views.dashboard, name="recruiter_dashboard"),
    path("candidate/<int:candidate_id>/", views.view_candidate_detail, name="view_candidate_detail"),
    path("priority-candidates/", views.priority_candidates, name="priority_candidates"),
    path("post-job/", views.post_job, name="post_job"),
    path("edit-job/<int:job_id>/", views.edit_job, name="edit_job"),
    path("delete-job/<int:job_id>/", views.delete_job, name="delete_job"),
]