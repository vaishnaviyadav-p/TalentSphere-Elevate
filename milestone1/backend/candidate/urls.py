from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.candidate_profile, name='candidate_profile'),
    path('edit-profile/', views.edit_candidate_profile, name='edit_candidate_profile'),
]