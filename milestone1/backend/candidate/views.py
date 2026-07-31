from django.shortcuts import render, redirect
from .models import CandidateProfile
from .forms import CandidateProfileForm
from django.contrib import messages


# ---------------- Dashboard ----------------

def candidate_dashboard(request):
    return render(request, "candidate/dashboard.html")


# ---------------- Browse Jobs ----------------

def browse_jobs(request):

    jobs = [
        {
            "id": 1,
            "title": "Software Engineer",
            "company": "Google",
            "location": "Hyderabad",
            "salary": "12 LPA",
            "description": "Develop scalable software applications."
        },
        {
            "id": 2,
            "title": "Python Developer",
            "company": "Infosys",
            "location": "Bangalore",
            "salary": "8 LPA",
            "description": "Develop backend applications using Python."
        },
        {
            "id": 3,
            "title": "Frontend Developer",
            "company": "TCS",
            "location": "Pune",
            "salary": "7 LPA",
            "description": "Build responsive user interfaces."
        },
    ]

    return render(request, "candidate/jobs.html", {"jobs": jobs})


# ---------------- Job Detail ----------------

def job_detail(request, job_id):

    jobs = [
        {
            "id": 1,
            "title": "Software Engineer",
            "company": "Google",
            "location": "Hyderabad",
            "salary": "12 LPA",
            "description": "Develop scalable software applications."
        },
        {
            "id": 2,
            "title": "Python Developer",
            "company": "Infosys",
            "location": "Bangalore",
            "salary": "8 LPA",
            "description": "Develop backend applications using Python."
        },
        {
            "id": 3,
            "title": "Frontend Developer",
            "company": "TCS",
            "location": "Pune",
            "salary": "7 LPA",
            "description": "Build responsive user interfaces."
        },
    ]

    job = None

    for j in jobs:
        if j["id"] == job_id:
            job = j
            break

    return render(request, "candidate/job_detail.html", {"job": job})


# ---------------- Apply Job ----------------

from django.contrib import messages

def apply_job(request, job_id):

    jobs = [
        {
            "id": 1,
            "title": "Software Engineer",
            "company": "Google",
            "location": "Hyderabad",
            "salary": "12 LPA",
        },
        {
            "id": 2,
            "title": "Python Developer",
            "company": "Infosys",
            "location": "Bangalore",
            "salary": "8 LPA",
        },
        {
            "id": 3,
            "title": "Frontend Developer",
            "company": "TCS",
            "location": "Pune",
            "salary": "7 LPA",
        },
    ]

    job = None

    for j in jobs:
        if j["id"] == job_id:
            job = j
            break

    if job is None:
        messages.error(request, "Job not found.")
        return redirect("browse_jobs")

    applications = request.session.get("applications", [])

    already_applied = any(app["id"] == job_id for app in applications)

    if already_applied:
        messages.warning(request, "You have already applied for this job.")
    else:
        applications.append(job)
        request.session["applications"] = applications
        messages.success(request, "Application submitted successfully!")

    return redirect("my_applications")

# ---------------- My Applications ----------------

def my_applications(request):

    applications = request.session.get("applications", [])

    return render(
        request,
        "candidate/my_applications.html",
        {
            "applications": applications
        }
    )

# ---------------- Candidate Profile ----------------

def candidate_profile(request):

    profile = CandidateProfile.objects.first()

    return render(
        request,
        "candidate/profile.html",
        {"profile": profile},
    )


# ---------------- Edit Profile ----------------

def edit_candidate_profile(request):

    profile = CandidateProfile.objects.first()

    if request.method == "POST":

        form = CandidateProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Profile updated successfully!"
            )

            return redirect("candidate_profile")

    else:
        form = CandidateProfileForm(instance=profile)

    return render(
        request,
        "candidate/edit_profile.html",
        {"form": form},
    )