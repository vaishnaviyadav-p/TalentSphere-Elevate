from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User

from django_ratelimit.decorators import ratelimit

from .models import Job


# ============================================================
# RECRUITER DASHBOARD
# ============================================================

@login_required
@ratelimit(
    key="user",
    rate="30/m",
    method="GET",
    block=True
)
def recruiter_dashboard(request):

    jobs = Job.objects.filter(
        recruiter=request.user
    ).order_by("-id")

    return render(
        request,
        "recruiter/dashboard.html",
        {
            "jobs": jobs
        }
    )


# ============================================================
# RECRUITER PROFILE
# ============================================================

@login_required
def recruiter_profile(request):

    return render(
        request,
        "recruiter/profile.html"
    )


# ============================================================
# CREATE JOB
# ============================================================

@login_required
@ratelimit(
    key="user",
    rate="10/m",
    method="POST",
    block=True
)
def create_job(request):

    if request.method == "POST":

        title = request.POST.get("title")
        description = request.POST.get("description")
        skills = request.POST.get("skills")
        location = request.POST.get("location")

        if not title or not description:

            messages.error(
                request,
                "Job title and description are required."
            )

            return redirect("create_job")

        Job.objects.create(
            recruiter=request.user,
            title=title,
            description=description,
            skills=skills,
            location=location
        )

        messages.success(
            request,
            "Job posted successfully."
        )

        return redirect("recruiter_dashboard")

    return render(
        request,
        "recruiter/create_job.html"
    )


# ============================================================
# JOB DETAIL
# ============================================================

@login_required
@ratelimit(
    key="user",
    rate="30/m",
    method="GET",
    block=True
)
def recruiter_job_detail(request, job_id):

    job = get_object_or_404(
        Job,
        id=job_id,
        recruiter=request.user
    )

    return render(
        request,
        "recruiter/job_detail.html",
        {
            "job": job
        }
    )


# ============================================================
# EDIT JOB
# ============================================================

@login_required
@ratelimit(
    key="user",
    rate="10/m",
    method="POST",
    block=True
)
def edit_job(request, job_id):

    job = get_object_or_404(
        Job,
        id=job_id,
        recruiter=request.user
    )

    if request.method == "POST":

        job.title = request.POST.get(
            "title",
            job.title
        )

        job.description = request.POST.get(
            "description",
            job.description
        )

        job.skills = request.POST.get(
            "skills",
            job.skills
        )

        job.location = request.POST.get(
            "location",
            job.location
        )

        job.save()

        messages.success(
            request,
            "Job updated successfully."
        )

        return redirect(
            "recruiter_dashboard"
        )

    return render(
        request,
        "recruiter/edit_job.html",
        {
            "job": job
        }
    )


# ============================================================
# DELETE JOB
# ============================================================

@login_required
@ratelimit(
    key="user",
    rate="10/m",
    method="POST",
    block=True
)
def delete_job(request, job_id):

    job = get_object_or_404(
        Job,
        id=job_id,
        recruiter=request.user
    )

    if request.method == "POST":

        job.delete()

        messages.success(
            request,
            "Job deleted successfully."
        )

    return redirect(
        "recruiter_dashboard"
    )


# ============================================================
# VIEW APPLICANTS
# ============================================================

@login_required
@ratelimit(
    key="user",
    rate="30/m",
    method="GET",
    block=True
)
def view_applicants(request, job_id):

    job = get_object_or_404(
        Job,
        id=job_id,
        recruiter=request.user
    )

    applications = job.applications.all().order_by(
        "-id"
    )

    return render(
        request,
        "recruiter/applicants.html",
        {
            "job": job,
            "applications": applications
        }
    )


# ============================================================
# RECRUITER ANALYTICS
# ============================================================

@login_required
@ratelimit(
    key="user",
    rate="30/m",
    method="GET",
    block=True
)
def analytics_dashboard(request):

    jobs = Job.objects.filter(
        recruiter=request.user
    )

    total_jobs = jobs.count()

    total_applications = 0

    for job in jobs:

        try:
            total_applications += job.applications.count()
        except Exception:
            pass

    return render(
        request,
        "recruiter/analytics_dashboard.html",
        {
            "jobs": jobs,
            "total_jobs": total_jobs,
            "total_applications": total_applications
        }
    )