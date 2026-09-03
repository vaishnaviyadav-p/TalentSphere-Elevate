from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from django_ratelimit.decorators import ratelimit

from .models import UserProfile
from .forms import RegisterForm


# ============================================================
# HOME
# ============================================================

def home(request):
    return render(request, "accounts/home.html")


# ============================================================
# LOGIN
# RATE LIMITING: 5 POST REQUESTS / MINUTE / IP
# ============================================================

@ratelimit(
    key="ip",
    rate="5/m",
    method="POST",
    block=True
)
def login_view(request):

    if request.user.is_authenticated:

        if request.user.is_superuser:
            return redirect("/recruiter/dashboard/")

        try:
            profile = UserProfile.objects.get(
                user=request.user
            )

            if profile.role == "candidate":
                return redirect("candidate_profile")

            elif profile.role == "recruiter":
                return redirect("recruiter_profile")

        except UserProfile.DoesNotExist:
            return redirect("/")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            if user.is_superuser:
                return redirect("/recruiter/dashboard/")

            try:
                profile = UserProfile.objects.get(
                    user=user
                )

                if profile.role == "candidate":
                    return redirect("candidate_profile")

                elif profile.role == "recruiter":
                    return redirect("recruiter_profile")

            except UserProfile.DoesNotExist:

                messages.error(
                    request,
                    "User profile not found."
                )

                return redirect("login")

        else:

            messages.error(
                request,
                "Invalid username or password."
            )

    return render(
        request,
        "accounts/login.html"
    )


# ============================================================
# REGISTER
# ============================================================

def register_view(request):

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            role = form.cleaned_data["role"]

            # create_user() automatically hashes the password
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            UserProfile.objects.create(
                user=user,
                role=role
            )

            messages.success(
                request,
                "Registration successful! Please log in."
            )

            return redirect("login")

    else:

        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form
        }
    )


# ============================================================
# PRESENTATION
# ============================================================

def presentation_view(request):
    return render(request, "presentation.html")


# ============================================================
# LOGOUT
# ============================================================

def logout_view(request):

    logout(request)

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect("login")