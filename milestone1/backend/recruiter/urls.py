from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.recruiter_profile, name='recruiter_profile'),
    path('edit-profile/', views.edit_recruiter_profile, name='edit_recruiter_profile'),
    path('dashboard/', views.recruiter_dashboard, name='recruiter_dashboard'),
    path('candidate/<int:candidate_id>/', views.view_candidate_detail, name='view_candidate_detail'),
]