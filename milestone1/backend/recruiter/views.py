from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .models import RecruiterProfile, Job
from .forms import RecruiterProfileForm, JobForm


@login_required
def recruiter_profile(request):
    profile = RecruiterProfile.objects.first()

    return render(
        request,
        "recruiter/profile.html",
        {
            "profile": profile
        },
    )


@login_required
def edit_recruiter_profile(request):
    profile = RecruiterProfile.objects.first()

    if request.method == "POST":

        form = RecruiterProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
        )

        if form.is_valid():

            form.save()

            return redirect("recruiter_profile")

    else:

        form = RecruiterProfileForm(instance=profile)

    return render(
        request,
        "recruiter/edit_profile.html",
        {
            "form": form
        },
    )


@login_required
def dashboard(request):

    active_jobs = Job.objects.filter(
        recruiter=request.user,
        is_active=True
    ).count()

    jobs = Job.objects.filter(
        recruiter=request.user
    ).order_by("-created_at")

    context = {
        "active_jobs": active_jobs,
        "jobs": jobs,
    }

    return render(
        request,
        "recruiter/dashboard.html",
        context,
    )


@login_required
def post_job(request):

    if request.method == "POST":

        form = JobForm(request.POST)

        if form.is_valid():

            job = form.save(commit=False)

            # Assign logged-in recruiter
            job.recruiter = request.user

            job.save()

            return redirect("recruiter_dashboard")

    else:

        form = JobForm()

    return render(
        request,
        "recruiter/post_job.html",
        {
            "form": form
        },
    )

@login_required
def edit_job(request, job_id):

    job = Job.objects.get(
        id=job_id,
        recruiter=request.user
    )

    if request.method == "POST":

        form = JobForm(
            request.POST,
            instance=job
        )

        if form.is_valid():

            form.save()

            return redirect("recruiter_dashboard")

    else:

        form = JobForm(instance=job)

    return render(
        request,
        "recruiter/post_job.html",
        {
            "form": form
        },
    )


@login_required
def delete_job(request, job_id):

    job = Job.objects.get(
        id=job_id,
        recruiter=request.user
    )

    job.delete()

    return redirect("recruiter_dashboard")