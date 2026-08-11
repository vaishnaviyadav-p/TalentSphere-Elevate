from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages


from .models import CandidateProfile, ResumeData, JobApplication
from .forms import CandidateProfileForm, ResumeUploadForm
from .services.resume_parser import parse_resume
from recruiter.models import Job

from .skill_matching import (
    extract_required_skills,
    calculate_skill_match,
)


# ---------------- Dashboard ----------------

def candidate_dashboard(request):

    applications = JobApplication.objects.filter(
        candidate=request.user
    )

    context = {
        "total": applications.count(),
        "applied": applications.filter(status="Applied").count(),
        "shortlisted": applications.filter(status="Shortlisted").count(),
        "interview": applications.filter(status="Interview").count(),
        "rejected": applications.filter(status="Rejected").count(),
    }

    return render(
        request,
        "candidate/dashboard.html",
        context
    )


# ---------------- Browse Jobs ----------------

def browse_jobs(request):

    jobs = Job.objects.filter(
        is_active=True
    ).order_by("-created_at")

    return render(
        request,
        "candidate/jobs.html",
        {
            "jobs": jobs
        }
    )


# ---------------- Job Detail ----------------

def job_detail(request, job_id):

    job = get_object_or_404(
        Job,
        id=job_id,
        is_active=True
    )

    profile = CandidateProfile.objects.filter(
        user=request.user
    ).first()

    candidate_skills = []

    if profile and profile.skills:
        candidate_skills = [
            skill.strip()
            for skill in profile.skills.split(",")
            if skill.strip()
        ]

    # Extract required skills from job requirements
    required_skills = extract_required_skills(
        job.requirements
    )

    # Calculate ATS / Fit Score
    result = calculate_skill_match(
        candidate_skills,
        required_skills
    )

    return render(
        request,
        "candidate/job_detail.html",
        {
            "job": job,
            "fit_score": result["score"],
            "matched_skills": result["matched_skills"],
            "missing_skills": result["missing_skills"],
        }
    )


# ---------------- Apply Job ----------------

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

    return redirect("my_applications")


# ---------------- My Applications ----------------

def my_applications(request):

    applications = JobApplication.objects.filter(
        candidate=request.user
    ).select_related("job")

    candidate_profile = CandidateProfile.objects.filter(
        user=request.user
    ).first()

    candidate_skills = []

    if candidate_profile and candidate_profile.skills:
        candidate_skills = [
            skill.strip()
            for skill in candidate_profile.skills.split(",")
            if skill.strip()
        ]

    for application in applications:

        required_skills = extract_required_skills(
            application.job.requirements
        )

        result = calculate_skill_match(
            candidate_skills,
            required_skills
        )

        application.fit_score = result["score"]
        application.matched_skills = result["matched_skills"]
        application.missing_skills = result["missing_skills"]

        print(
            "JOB:",
            application.job.title,
            "REQUIRED:",
            required_skills,
            "CANDIDATE:",
            candidate_skills,
            "SCORE:",
            application.fit_score
        )

    return render(
        request,
        "candidate/my_applications.html",
        {
            "applications": applications
        }
    )



# ---------------- Candidate Profile ----------------

def candidate_profile(request):

    profile, created = CandidateProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "full_name": request.user.get_full_name()
            or request.user.username,
            "phone": "",
            "location": "",
            "education": "",
            "skills": "",
            "experience": "",
            "bio": "",
        }
    )

    return render(
        request,
        "candidate/profile.html",
        {
            "profile": profile
        }
    )


# ---------------- Edit Profile ----------------

def edit_candidate_profile(request):

    profile, created = CandidateProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "full_name": request.user.get_full_name()
            or request.user.username,
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

            return redirect("candidate_profile")

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

# ---------------- Candidate Dashboard ----------------

def candidate_dashboard(request):

    applications = JobApplication.objects.filter(
        candidate=request.user
    )

    context = {
        "total": applications.count(),

        "applied": applications.filter(
            status="Applied"
        ).count(),

        "under_review": applications.filter(
            status="Shortlisted"
        ).count(),

        "interview": applications.filter(
            status="Interview"
        ).count(),

        "rejected": applications.filter(
            status="Rejected"
        ).count(),
    }

    return render(
        request,
        "candidate/dashboard.html",
        context
    )

