from django.shortcuts import render, redirect
from .models import CandidateProfile
from .forms import CandidateProfileForm


def candidate_profile(request):
    profile = CandidateProfile.objects.first()
    return render(request, "candidate/profile.html", {"profile": profile})


def edit_candidate_profile(request):
    profile = CandidateProfile.objects.first()

    if request.method == "POST":
        form = CandidateProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if form.is_valid():
            form.save()
            return redirect("candidate_profile")

    else:
        form = CandidateProfileForm(instance=profile)

    return render(
        request,
        "candidate/edit_profile.html",
        {"form": form},
    )