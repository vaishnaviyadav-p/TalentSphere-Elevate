from django.shortcuts import render, redirect
from .models import RecruiterProfile
from .forms import RecruiterProfileForm


def recruiter_profile(request):
    profile = RecruiterProfile.objects.first()
    return render(request, "recruiter/profile.html", {"profile": profile})


def edit_recruiter_profile(request):
    profile = RecruiterProfile.objects.first()

    if request.method == "POST":
        form = RecruiterProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if form.is_valid():
            form.save()
            return redirect("recruiter_profile")

    else:
        form = RecruiterProfileForm(instance=profile)

    return render(
        request,
        "recruiter/edit_profile.html",
        {"form": form}
    )


def dashboard(request):
    return render(request, "recruiter/dashboard.html")