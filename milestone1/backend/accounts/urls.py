from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("presentation/", views.presentation_view, name="presentation"),
    path("candidate-login/", views.candidate_login, name="candidate_login"),
    path("recruiter-login/", views.recruiter_login, name="recruiter_login"),
]