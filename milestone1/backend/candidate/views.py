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

    if profile:
        resume = ResumeData.objects.filter(
            candidate=profile
        ).first()

        if resume and resume.parsed_skills:
            candidate_skills = [
                skill.strip()
                for skill in resume.parsed_skills
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

            print("RESUME SKILLS:", candidate_skills)

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

    resume_data = ResumeData.objects.filter(
        candidate=profile
    ).first()

    return render(
        request,
        "candidate/profile.html",
        {
            "profile": profile,
            "resume_data":
        resume_data

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

# ---------------- Upload Resume ----------------

def upload_resume(request):

    profile = CandidateProfile.objects.filter(user=request.user).first()

    # Make sure a candidate profile exists
    if not profile:
        messages.error(
            request,
            "Candidate profile not found. Please create a profile first."
        )
        return redirect("candidate_profile")

    if request.method == "POST":

        form = ResumeUploadForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            resume_data, created = ResumeData.objects.get_or_create(
                candidate=profile
            )

            resume_data.resume_file = form.cleaned_data["resume_file"]
            resume_data.save()

            try:

                parsed_data = parse_resume(
                    resume_data.resume_file.path
                )
                print("========== RESUME TEXT ==========")
                print(parsed_data["extracted_text"])
                print("=================================")

                resume_data.extracted_text = parsed_data["extracted_text"]
                resume_data.parsed_name = parsed_data["name"]
                resume_data.parsed_email = parsed_data["email"]
                resume_data.parsed_phone = parsed_data["phone"]
                resume_data.parsed_skills = parsed_data["skills"]
                resume_data.parsed_experience = parsed_data["experience"]
                resume_data.parsed_projects = parsed_data["projects"]
                resume_data.parsed_keywords = parsed_data["keywords"]

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

            return redirect("candidate_profile")

    else:
        form = ResumeUploadForm()

    return render(
        request,
        "candidate/upload_resume.html",
        {
            "form": form
        }
    )
