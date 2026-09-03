from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator
from django_ratelimit.decorators import ratelimit


from .models import CandidateProfile, ResumeData, JobApplication
from .forms import CandidateProfileForm, ResumeUploadForm
from .services.resume_parser import parse_resume

from recruiter.models import Job,Interview
from recruiter.models import Job, Interview

from .skill_matching import (
    extract_required_skills,
    calculate_skill_match,
    generate_learning_path,
)


# ============================================================
# CANDIDATE DASHBOARD
# ============================================================

@login_required
def candidate_dashboard(request):

    applications = JobApplication.objects.filter(
        candidate=request.user
    )

    # ---------------- Basic Application Metrics ----------------
    total = applications.count()

    applied = applications.filter(
        status="Applied"
    ).count()

    under_review = applications.filter(
        status="Under Review"
    ).count()

    shortlisted = applications.filter(
        status="Shortlisted"
    ).count()

    rejected = applications.filter(
        status="Rejected"
    ).count()

    selected = applications.filter(
        status="Selected"
    ).count()

    # ---------------- Weekly & Monthly Activity ----------------

    today = timezone.now().date()

    week_start = today - timedelta(days=today.weekday())

    month_start = today.replace(day=1)

    # Weekly Activity
    weekly_applications = applications.filter(
        applied_at__date__gte=week_start
    ).count()

    weekly_shortlisted = applications.filter(
        applied_at__date__gte=week_start,
        status="Shortlisted"
    ).count()

    weekly_interviews = applications.filter(
        applied_at__date__gte=week_start,
        status="Interview"
    ).count()

    weekly_rejected = applications.filter(
        applied_at__date__gte=week_start,
        status="Rejected"
    ).count()

    # Monthly Activity
    monthly_applications = applications.filter(
        applied_at__date__gte=month_start
    ).count()

    monthly_shortlisted = applications.filter(
        applied_at__date__gte=month_start,
        status="Shortlisted"
    ).count()

    monthly_interviews = applications.filter(
        applied_at__date__gte=month_start,
        status="Interview"
    ).count()

    monthly_rejected = applications.filter(
        applied_at__date__gte=month_start,
        status="Rejected"
    ).count()

    # ---------------- Candidate Profile ----------------

    candidate_profile = CandidateProfile.objects.filter(
        user=request.user
    ).first()

    # ---------------- Interviews ----------------

    interviews = Interview.objects.none()

    if candidate_profile:

        interviews = Interview.objects.filter(
            candidate=candidate_profile,
            status="Scheduled"
        ).select_related(
            "recruiter"
        ).order_by(
            "interview_date",
            "interview_time"
        )

    interview_count = interviews.values("candidate").distinct().count()

    # ---------------- Candidate Metrics ----------------

    if total > 0:
        success_rate = round(
            ((shortlisted + selected) / total) * 100,
            1
        )
    else:
        success_rate = 0

    if total > 0:
        interview_rate = round(
            (interview_count / total) * 100,
            1
        )
    else:
        interview_rate = 0

    # ---------------- Recent Applications ----------------

    recent_applications = applications.select_related(
        "job"
    ).order_by("-id")[:5]

    context = {

        "total": total,
        "applied": applied,
        "under_review": under_review,
        "shortlisted": shortlisted,

        # Important
        "interview": interview_count,

        "rejected": rejected,

        "selected": selected,

        "success_rate": success_rate,
        "interview_conversion": interview_rate,

        "recent_applications": recent_applications,

        # Interview details
        "interviews": interviews,

        # Weekly Activity
        "weekly_applications": weekly_applications,
        "weekly_shortlisted": weekly_shortlisted,
        "weekly_interviews": weekly_interviews,
        "weekly_rejected": weekly_rejected,

        # Monthly Activity
        "monthly_applications": monthly_applications,
        "monthly_shortlisted": monthly_shortlisted,
        "monthly_interviews": monthly_interviews,
        "monthly_rejected": monthly_rejected,

        "analytics_data": {
    "Applied": applied,
    "Under Review": under_review,
    "Shortlisted": shortlisted,
    "Interview": interview_count,
    "Selected": selected,
    "Rejected": rejected,
},
    }

    return render(
        request,
        "candidate/dashboard.html",
        context
    )


def candidate_interviews(request):

    candidate_profile = CandidateProfile.objects.filter(
        user=request.user
    ).first()

    if not candidate_profile:
        messages.error(
            request,
            "Candidate profile not found."
        )
        return redirect("candidate_dashboard")

    interviews = Interview.objects.filter(
        candidate=candidate_profile
    ).select_related(
        "recruiter"
    ).order_by(
        "-interview_date",
        "-interview_time"
    )

    return render(
        request,
        "candidate/interviews.html",
        {
            "interviews": interviews
        }
    )


# ============================================================
# BROWSE JOBS
# RATE LIMITING: 60 GET REQUESTS / MINUTE / IP
# ============================================================

@login_required
@ratelimit(
    key="ip",
    rate="60/m",
    method="GET",
    block=True
)
def browse_jobs(request):

    jobs_list = Job.objects.filter(
        is_active=True
    ).order_by("-created_at")

    # 10 jobs per page
    paginator = Paginator(
        jobs_list,
        10
    )

    page_number = request.GET.get("page")

    jobs = paginator.get_page(
        page_number
    )

    return render(
        request,
        "candidate/jobs.html",
        {
            "jobs": jobs
        }
    )


# ============================================================
# JOB DETAIL
# RATE LIMITING: 30 GET REQUESTS / MINUTE / IP
# ============================================================

@login_required
@ratelimit(
    key="ip",
    rate="30/m",
    method="GET",
    block=True
)
def job_detail(request, job_id):

    job = get_object_or_404(
        Job,
        id=job_id,
        is_active=True
    )

    # Use AI-based match calculation from recommendations app
    from recommendations.services import calculate_job_match_for_candidate

    match_data = calculate_job_match_for_candidate(request.user, job)

    # Also get learning path for missing skills
    learning_path = generate_learning_path(match_data["missing_skills"])

    return render(
        request,
        "candidate/job_detail.html",
        {
            "job": job,
            "fit_score": match_data["match_score"],
            "skill_match_score": match_data["skill_match_score"],
            "experience_match_score": match_data["experience_match_score"],
            "matched_skills": match_data["matched_skills"],
            "missing_skills": match_data["missing_skills"],
            "experience_match": match_data["experience_match"],
            "match_reason": match_data["reason"],
            "learning_path": learning_path
        }
    )


@login_required
def candidate_settings(request):

    user = request.user

    if request.method == "POST":

        # Update email
        email = request.POST.get("email")

        if email:
            user.email = email

        # Update username
        username = request.POST.get("username")

        if username:
            user.username = username

        user.save()

        # Change password if entered
        password_form = PasswordChangeForm(
            user,
            request.POST
        )

        if (
            request.POST.get("old_password")
            or request.POST.get("new_password1")
            or request.POST.get("new_password2")
        ):

            if password_form.is_valid():

                password_form.save()

                update_session_auth_hash(
                    request,
                    user
                )

                messages.success(
                    request,
                    "Settings and password updated successfully!"
                )

                return redirect("candidate_settings")

            else:

                return render(
                    request,
                    "candidate/settings.html",
                    {
                        "password_form": password_form,
                        "user": user
                    }
                )

        messages.success(
            request,
            "Settings updated successfully!"
        )

        return redirect("candidate_settings")

    password_form = PasswordChangeForm(user)

    return render(
        request,
        "candidate/settings.html",
        {
            "user": user,
            "password_form": password_form
        }
    )


@login_required
def change_password(request):

    if request.method == "POST":

        form = PasswordChangeForm(
            request.user,
            request.POST
        )

        if form.is_valid():

            form.save()

            update_session_auth_hash(
                request,
                request.user
            )

            messages.success(
                request,
                "Password changed successfully!"
            )

            return redirect("candidate_settings")

    else:

        form = PasswordChangeForm(
            request.user
        )

    return render(
        request,
        "candidate/change_password.html",
        {
            "form": form
        }
    )


# ============================================================
# APPLY FOR JOB
# RATE LIMITING: 10 POST REQUESTS / MINUTE / IP
# ============================================================

@login_required
@ratelimit(
    key="ip",
    rate="10/m",
    method="POST",
    block=True
)
def apply_job(request, job_id):

    job = get_object_or_404(
        Job,
        id=job_id
    )

    application, created = JobApplication.objects.get_or_create(
        candidate=request.user,
        job=job
    )

    if created:

        messages.success(
            request,
            "Application submitted successfully!"
        )

    else:

        messages.warning(
            request,
            "You have already applied for this job."
        )

    return redirect(
        "my_applications"
    )


# ============================================================
# MY APPLICATIONS
# RATE LIMITING: 30 GET REQUESTS / MINUTE / IP
# ============================================================

@login_required
@ratelimit(
    key="ip",
    rate="30/m",
    method="GET",
    block=True
)
def my_applications(request):

    applications = JobApplication.objects.filter(
        candidate=request.user
    ).select_related("job")

    candidate_profile = CandidateProfile.objects.filter(
        user=request.user
    ).first()

    candidate_skills = []

    # Prefer resume-parsed skills
    if candidate_profile:

        resume = ResumeData.objects.filter(
            candidate=candidate_profile
        ).first()

        if resume and resume.parsed_skills:

            candidate_skills = [
                skill.strip()
                for skill in resume.parsed_skills
                if skill.strip()
            ]
        # Fallback to profile skills
        elif candidate_profile.skills:

            candidate_skills = [
                skill.strip()
                for skill in candidate_profile.skills.split(",")
                if skill.strip()
            ]

    # Calculate fit score for each application
    for application in applications:

        required_skills = extract_required_skills(
            application.job.requirements
        )

        result = calculate_skill_match(
            candidate_skills,
            required_skills
        )

        application.fit_score = result["score"]

        application.matched_skills = (
            result["matched_skills"]
        )

        application.missing_skills = (
            result["missing_skills"]
        )

    return render(
        request,
        "candidate/my_applications.html",
        {
            "applications": applications
        }
    )


# ============================================================
# CANDIDATE PROFILE
# RATE LIMITING: 30 GET REQUESTS / MINUTE / IP
# ============================================================

@login_required
@ratelimit(
    key="ip",
    rate="30/m",
    method="GET",
    block=True
)
def candidate_profile(request):

    profile, created = CandidateProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "full_name": (
                request.user.get_full_name()
                or request.user.username
            ),
            "phone": "",
            "location": "",
            "education": "",
            "skills": "",
            "experience": "",
            "bio": "",
        }
    )

    # Get the resume linked to this candidate
    resume_data = ResumeData.objects.filter(
        candidate=profile
    ).first()

    return render(
        request,
        "candidate/profile.html",
        {
            "profile": profile,
            "resume_data": resume_data,
        }
    )


# ============================================================
# EDIT CANDIDATE PROFILE
# RATE LIMITING: 5 POST REQUESTS / MINUTE / IP
# ============================================================

@login_required
@ratelimit(
    key="ip",
    rate="5/m",
    method="POST",
    block=True
)
def edit_candidate_profile(request):

    profile, created = CandidateProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "full_name": (
                request.user.get_full_name()
                or request.user.username
            ),
            "phone": "",
            "location": "",
            "education": "",
            "skills": "",
            "experience": "",
            "bio": "",
        }
    )

    if request.method == "POST":

        form = CandidateProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Profile updated successfully!"
            )

            return redirect(
                "candidate_profile"
            )

    else:

        form = CandidateProfileForm(
            instance=profile
        )

    return render(
        request,
        "candidate/edit_profile.html",
        {
            "form": form
        }
    )


def candidate_analytics(request):

    applications = JobApplication.objects.filter(
        candidate=request.user
    )

    analytics_data = {
        "Applied": applications.filter(status="Applied").count(),
        "Under Review": applications.filter(status="Under Review").count(),
        "Shortlisted": applications.filter(status="Shortlisted").count(),
        "Interview": applications.filter(status="Interview").count(),
        "Selected": applications.filter(status="Selected").count(),
        "Rejected": applications.filter(status="Rejected").count(),
    }

    return render(
        request,
        "candidate/analytics.html",
        {
            "analytics_data": analytics_data
        }
    )


# ============================================================
# UPLOAD RESUME + RESUME PARSING
# RATE LIMITING: 5 POST REQUESTS / MINUTE / IP
# ============================================================

@login_required
@ratelimit(
    key="ip",
    rate="5/m",
    method="POST",
    block=True
)
def upload_resume(request):

    # Get the profile belonging to the logged-in user
    profile = CandidateProfile.objects.filter(
        user=request.user
    ).first()

    # Make sure candidate profile exists
    if not profile:

        messages.error(
            request,
            "Candidate profile not found. Please create a profile first."
        )

        return redirect(
            "candidate_profile"
        )

    if request.method == "POST":

        form = ResumeUploadForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            # Get existing resume or create a new one
            resume_data, created = ResumeData.objects.get_or_create(
                candidate=profile
            )

            # Save uploaded resume file
            resume_data.resume_file = form.cleaned_data[
                "resume_file"
            ]

            resume_data.save()

            try:

                # Parse uploaded resume
                parsed_data = parse_resume(
                    resume_data.resume_file.path
                )

                # Save extracted information
                resume_data.extracted_text = (
                    parsed_data["extracted_text"]
                )

                resume_data.parsed_name = (
                    parsed_data["name"]
                )

                resume_data.parsed_email = (
                    parsed_data["email"]
                )

                resume_data.parsed_phone = (
                    parsed_data["phone"]
                )

                resume_data.parsed_skills = (
                    parsed_data["skills"]
                )

                resume_data.parsed_experience = (
                    parsed_data["experience"]
                )

                resume_data.parsed_projects = (
                    parsed_data["projects"]
                )

                resume_data.parsed_keywords = (
                    parsed_data["keywords"]
                )

                resume_data.save()

                messages.success(
                    request,
                    "Resume uploaded and parsed successfully!"
                )

            except Exception as error:

                messages.error(
                    request,
                    f"Resume parsing failed: {error}"
                )

            return redirect(
                "candidate_profile"
            )

    else:

        form = ResumeUploadForm()

    return render(
        request,
        "candidate/upload_resume.html",
        {
            "form": form
        }
    )