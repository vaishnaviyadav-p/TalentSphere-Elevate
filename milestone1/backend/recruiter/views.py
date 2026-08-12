from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required

from accounts.models import UserProfile
from candidate.models import JobApplication, CandidateProfile, ResumeData
from .models import RecruiterProfile, Job
from .forms import RecruiterProfileForm, JobForm
from .ranking import (
    build_priority_candidate_rows,
    collect_available_skills,
)


def _is_recruiter(user):
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    try:
        return user.userprofile.role == "recruiter"
    except UserProfile.DoesNotExist:
        return False


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
def priority_candidates(request):
    if not _is_recruiter(request.user):
        raise PermissionDenied

    recruiter_jobs = Job.objects.filter(
        recruiter=request.user
    ).order_by("-created_at")

    applications = JobApplication.objects.filter(
        job__recruiter=request.user
    ).select_related(
        "candidate",
        "candidate__candidateprofile",
        "candidate__candidateprofile__resume_data",
        "job",
        "job__recruiter",
    )

    selected_job = request.GET.get("job", "").strip()
    selected_status = request.GET.get("status", "").strip()
    selected_skill = request.GET.get("skill", "").strip()
    selected_experience = request.GET.get("experience", "").strip()
    selected_score = request.GET.get("score", "").strip()

    score_threshold = None
    if selected_score:
        try:
            score_threshold = int(selected_score)
        except ValueError:
            score_threshold = None
        else:
            if score_threshold < 0 or score_threshold > 100:
                score_threshold = None

    accessible_job_ids = set(
        recruiter_jobs.values_list("id", flat=True)
    )

    selected_job_id = None
    invalid_job_filter = False

    if selected_job:
        try:
            selected_job_id = int(selected_job)
        except ValueError:
            invalid_job_filter = True
        else:
            if selected_job_id not in accessible_job_ids:
                invalid_job_filter = True

    available_skills = collect_available_skills(applications)
    ranked_rows = build_priority_candidate_rows(applications)

    filtered_rows = []

    if not invalid_job_filter:
        selected_skill_key = selected_skill.lower().strip()

        for row in ranked_rows:
            application = row["application"]

            if selected_job_id and application.job_id != selected_job_id:
                continue

            if selected_status and application.status != selected_status:
                continue

            if score_threshold is not None and row["score"] < score_threshold:
                continue

            if selected_skill_key and selected_skill_key not in row["candidate_skills_key"]:
                continue

            if selected_experience and row["experience_bucket"] != selected_experience:
                continue

            filtered_rows.append(row)

    job_filter_options = list(recruiter_jobs.values("id", "title"))

    context = {
        "applications": filtered_rows,
        "jobs": recruiter_jobs,
        "job_filter_options": job_filter_options,
        "skill_filter_options": available_skills,
        "status_filter_options": JobApplication.STATUS_CHOICES,
        "score_filter_options": [
            ("", "All Scores"),
            ("90", "90%+"),
            ("80", "80%+"),
            ("70", "70%+"),
            ("60", "60%+"),
        ],
        "experience_filter_options": [
            ("", "All Experience"),
            ("0-2", "0–2 years"),
            ("2-5", "2–5 years"),
            ("5+", "5+ years"),
        ],
        "selected_job": selected_job,
        "selected_status": selected_status,
        "selected_skill": selected_skill,
        "selected_experience": selected_experience,
        "selected_score": selected_score,
        "invalid_job_filter": invalid_job_filter,
        "total_candidates": len(filtered_rows),
    }

    return render(
        request,
        "recruiter/priority_candidates.html",
        context,
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


@login_required
def view_candidate_detail(request, candidate_id):
    recruiter_profile_obj = RecruiterProfile.objects.first()
    candidate = get_object_or_404(CandidateProfile, id=candidate_id)
    resume_data = ResumeData.objects.filter(candidate=candidate).first()

    return render(
        request,
        "recruiter/candidate_detail.html",
        {
            "recruiter_profile": recruiter_profile_obj,
            "candidate": candidate,
            "resume_data": resume_data,
        }
    )
