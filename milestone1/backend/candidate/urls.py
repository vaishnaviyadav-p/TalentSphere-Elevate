from django.urls import path
from . import views


urlpatterns = [

    path(
        "dashboard/", views.candidate_dashboard, name="candidate_dashboard"),

    path("jobs/", views.browse_jobs, name="browse_jobs"),
    path("jobs/<int:job_id>/", views.job_detail, name="job_detail"),
    path("apply/<int:job_id>/", views.apply_job, name="apply_job"),

    path("applications/", views.my_applications, name="my_applications"),

    path("profile/",
        views.candidate_profile,
        name="candidate_profile"
    ),

    path(
        "edit-profile/",
        views.edit_candidate_profile,
        name="edit_candidate_profile"
    ),

    path(
        'upload-resume/',
        views.upload_resume,
        name='upload_resume'
    ),

]