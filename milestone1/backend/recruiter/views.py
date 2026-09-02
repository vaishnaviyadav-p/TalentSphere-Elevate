from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)

from datetime import timedelta

from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone

from django.contrib import messages
from django.db.models import Count

from accounts.models import UserProfile

from candidate.models import (
    JobApplication,
    CandidateProfile,
    ResumeData
)

from .models import (
    RecruiterProfile,
    Job,
    Interview
)

from .forms import (
    RecruiterProfileForm,
    JobForm,
    InterviewForm,
    EditInterviewForm
)

from .ranking import (
    build_priority_candidate_rows,
    collect_available_skills,
)

from django.db.models.functions import TruncMonth, TruncWeek
from django.db.models import Count


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

    profile, created = RecruiterProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "recruiter_name": request.user.get_full_name() or request.user.username,
            "company_name": "My Company",
            "email": request.user.email or "recruiter@example.com",
            "phone": "",
            "location": "",
            "company_description": ""
        }
    )

    return render(
        request,
        "recruiter/profile.html",
        {
            "profile": profile
        }
    )


@login_required
def edit_recruiter_profile(request):

    profile, created = RecruiterProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "recruiter_name": request.user.get_full_name() or request.user.username,
            "company_name": "My Company",
            "email": request.user.email or "recruiter@example.com",
            "phone": "",
            "location": "",
            "company_description": ""
        }
    )

    if request.method == "POST":

        form = RecruiterProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if form.is_valid():

            form.save()

            return redirect(
                "recruiter_profile"
            )

    else:

        form = RecruiterProfileForm(
            instance=profile
        )

    return render(
        request,
        "recruiter/edit_profile.html",
        {
            "form": form
        }
    )

def update_application_status(request, application_id):
    application = get_object_or_404(JobApplication, id=application_id)

    if request.method == "POST":
        new_status = request.POST.get("status")

        if new_status in dict(JobApplication.STATUS_CHOICES):
            application.status = new_status
            application.save()
            messages.success(request, "Application status updated successfully.")

    return redirect("priority_candidates")


@login_required
def dashboard(request):
    now = timezone.now()
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    recruiter_jobs = Job.objects.filter(recruiter=request.user)

    total_jobs_posted = recruiter_jobs.count()
    active_jobs = recruiter_jobs.filter(is_active=True).count()
    inactive_jobs = recruiter_jobs.filter(is_active=False).count()

    recruiter_applications = JobApplication.objects.filter(job__recruiter=request.user)
    total_applications = recruiter_applications.count()
    candidates_interviewed = recruiter_applications.filter(status="Interview").count()
    candidates_shortlisted = recruiter_applications.filter(status="Shortlisted").count()

    jobs_posted_this_week = recruiter_jobs.filter(created_at__gte=week_start).count()
    applications_this_week = recruiter_applications.filter(applied_at__gte=week_start).count()
    interviews_this_week = recruiter_applications.filter(
        status="Interview", applied_at__gte=week_start
    ).count()

    jobs = Job.objects.filter(
        recruiter=request.user
    ).order_by(
        "-created_at"
    )
    jobs_posted_this_month = recruiter_jobs.filter(created_at__gte=month_start).count()
    applications_this_month = recruiter_applications.filter(applied_at__gte=month_start).count()
    interviews_this_month = recruiter_applications.filter(
        status="Interview", applied_at__gte=month_start
    ).count()

    jobs = recruiter_jobs.order_by("-created_at")

    context = {
        "active_jobs": active_jobs,
        "inactive_jobs": inactive_jobs,
        "total_jobs_posted": total_jobs_posted,
        "total_applications": total_applications,
        "candidates_interviewed": candidates_interviewed,
        "candidates_shortlisted": candidates_shortlisted,
        "jobs_posted_this_week": jobs_posted_this_week,
        "applications_this_week": applications_this_week,
        "interviews_this_week": interviews_this_week,
        "jobs_posted_this_month": jobs_posted_this_month,
        "applications_this_month": applications_this_month,
        "interviews_this_month": interviews_this_month,
        "jobs": jobs,
    }

    return render(
        request,
        "recruiter/dashboard.html",
        context
    )


@login_required
def analytics_dashboard(request):

    recruiter = request.user

    jobs = Job.objects.filter(recruiter=recruiter)

    total_jobs = jobs.count()

    applications = JobApplication.objects.filter(
        job__recruiter=recruiter
    )

    total_applications = applications.count()

    shortlisted = applications.filter(
        status="Shortlisted"
    ).count()

    interviews = applications.filter(
        status="Interview"
    ).count()

    jobs_by_month = (
        jobs
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )

    month_labels = []
    month_data = []

    for item in jobs_by_month:
        month_labels.append(
            item["month"].strftime("%b %Y")
        )
        month_data.append(item["total"])

    jobs_by_week = (
        jobs
        .annotate(week=TruncWeek("created_at"))
        .values("week")
        .annotate(total=Count("id"))
        .order_by("week")
    )

    week_labels = []
    week_data = []

    for item in jobs_by_week:
        week_labels.append(
            item["week"].strftime("%d %b")
        )
        week_data.append(item["total"])

    applications_by_month = (
        applications
        .annotate(month=TruncMonth("applied_at"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )

    trend_labels = []
    trend_data = []

    for item in applications_by_month:
        trend_labels.append(
            item["month"].strftime("%b %Y")
        )
        trend_data.append(item["total"])

    context = {

        "total_jobs": total_jobs,

        "total_applications": total_applications,

        "shortlisted": shortlisted,

        "interviews": interviews,

        "month_labels": month_labels,
        "month_data": month_data,

        "week_labels": week_labels,
        "week_data": week_data,

        "trend_labels": trend_labels,
        "trend_data": trend_data,
    }

    return render(
        request,
        "recruiter/analytics_dashboard.html",
        context
    )   


@login_required
def post_job(request):

    if request.method == "POST":

        form = JobForm(
            request.POST
        )

        if form.is_valid():

            job = form.save(
                commit=False
            )

            job.recruiter = request.user

            job.save()

            messages.success(
                request,
                "Job posted successfully!"
            )

            return redirect(
                "recruiter_dashboard"
            )

    else:

        form = JobForm()

    return render(
        request,
        "recruiter/post_job.html",
        {
            "form": form
        }
    )


@login_required
def priority_candidates(request):

    if not _is_recruiter(request.user):
        raise PermissionDenied

    recruiter_jobs = Job.objects.filter(
        recruiter=request.user
    ).order_by(
        "-created_at"
    )

    applications = JobApplication.objects.filter(
        job__recruiter=request.user
    ).select_related(
        "candidate",
        "candidate__candidateprofile",
        "candidate__candidateprofile__resume_data",
        "job",
        "job__recruiter",
    )

    selected_job = request.GET.get(
        "job",
        ""
    ).strip()

    selected_status = request.GET.get(
        "status",
        ""
    ).strip()

    selected_skill = request.GET.get(
        "skill",
        ""
    ).strip()

    selected_experience = request.GET.get(
        "experience",
        ""
    ).strip()

    selected_score = request.GET.get(
        "score",
        ""
    ).strip()

    score_threshold = None

    if selected_score:

        try:

            score_threshold = int(
                selected_score
            )

        except ValueError:

            score_threshold = None

        else:

            if (
                score_threshold < 0
                or
                score_threshold > 100
            ):
                score_threshold = None

    accessible_job_ids = set(
        recruiter_jobs.values_list(
            "id",
            flat=True
        )
    )

    selected_job_id = None

    invalid_job_filter = False

    if selected_job:

        try:

            selected_job_id = int(
                selected_job
            )

        except ValueError:

            invalid_job_filter = True

        else:

            if selected_job_id not in accessible_job_ids:

                invalid_job_filter = True

    available_skills = collect_available_skills(
        applications
    )

    ranked_rows = build_priority_candidate_rows(
        applications
    )

    filtered_rows = []

    if not invalid_job_filter:

        selected_skill_key = (
            selected_skill
            .lower()
            .strip()
        )

        for row in ranked_rows:

            application = row[
                "application"
            ]



            if (
                selected_job_id
                and
                application.job_id != selected_job_id
            ):
                continue



            if (
                selected_status
                and
                application.status != selected_status
            ):
                continue



            if (
                score_threshold is not None
                and
                row["score"] < score_threshold
            ):
                continue



            if (
                selected_skill_key
                and
                selected_skill_key
                not in row["candidate_skills_key"]
            ):
                continue



            if (
                selected_experience
                and
                row["experience_bucket"]
                != selected_experience
            ):
                continue


            filtered_rows.append(
                row
            )

    job_filter_options = list(
        recruiter_jobs.values(
            "id",
            "title"
        )
    )


    context = {

        "applications": filtered_rows,

        "jobs": recruiter_jobs,

        "job_filter_options":
            job_filter_options,

        "skill_filter_options":
            available_skills,

        "status_filter_options":
            JobApplication.STATUS_CHOICES,

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

        "selected_job":
            selected_job,

        "selected_status":
            selected_status,

        "selected_skill":
            selected_skill,

        "selected_experience":
            selected_experience,

        "selected_score":
            selected_score,

        "invalid_job_filter":
            invalid_job_filter,

        "total_candidates":
            len(filtered_rows),
    }

    return render(
        request,
        "recruiter/priority_candidates.html",
        context
    )


@login_required
def edit_job(
    request,
    job_id
):

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

            messages.success(
                request,
                "Job updated successfully!"
            )

            return redirect(
                "recruiter_dashboard"
            )

    else:

        form = JobForm(
            instance=job
        )

    return render(
        request,
        "recruiter/post_job.html",
        {
            "form": form
        }
    )


@login_required
def delete_job(
    request,
    job_id
):

    job = Job.objects.get(
        id=job_id,
        recruiter=request.user
    )

    job.delete()

    messages.success(
        request,
        "Job deleted successfully!"
    )

    return redirect(
        "recruiter_dashboard"
    )


@login_required
def view_candidate_detail(
    request,
    candidate_id
):

    if not _is_recruiter(request.user):
        raise PermissionDenied

    recruiter_profile_obj = (
        RecruiterProfile.objects.filter(
            user=request.user
        ).first()
    )

    candidate = get_object_or_404(
        CandidateProfile,
        id=candidate_id
    )

    resume_data = ResumeData.objects.filter(
        candidate=candidate
    ).first()

    match_score = request.GET.get("match_score")
    skill_match_score = request.GET.get("skill_match_score")
    experience_match_score = request.GET.get("experience_match_score")
    matched_skills = request.GET.get("matched_skills")
    missing_skills = request.GET.get("missing_skills")
    reason = request.GET.get("reason")

    if matched_skills:
        matched_skills = [s.strip() for s in matched_skills.split(",") if s.strip()]
    if missing_skills:
        missing_skills = [s.strip() for s in missing_skills.split(",") if s.strip()]

    back_url = request.GET.get("next", "recruiter_all_recommendations")

    return render(
        request,
        "recruiter/candidate_detail.html",
        {
            "recruiter_profile":
                recruiter_profile_obj,

            "candidate":
                candidate,

            "resume_data":
                resume_data,

            "match_score": match_score,
            "skill_match_score": skill_match_score,
            "experience_match_score": experience_match_score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "reason": reason,
            "back_url": back_url,
        }
    )


@login_required
def schedule_interview(request):

    recruiter = RecruiterProfile.objects.filter(
        user=request.user
    ).first()

    if not recruiter:

        messages.error(
            request,
            "Recruiter profile not found. "
            "Please create a recruiter profile first."
        )

        return redirect(
            "recruiter_profile"
        )


    if request.method == "POST":

        form = InterviewForm(
            request.POST
        )

        if form.is_valid():

            interview = form.save(
                commit=False
            )

            interview.recruiter = recruiter

            interview.status = "Scheduled"

            interview.save()

            try:
                from .email_services import send_interview_scheduled_email
                send_interview_scheduled_email(interview)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error sending interview scheduled email: {e}")

            messages.success(
                request,
                "Interview scheduled successfully!"
            )

            return redirect(
                "interview_list"
            )

    else:

        form = InterviewForm()


    return render(
        request,
        "recruiter/schedule_interview.html",
        {
            "form": form
        }
    )


@login_required
def interview_list(request):

    recruiter = RecruiterProfile.objects.filter(
        user=request.user
    ).first()

    interviews = Interview.objects.filter(
        recruiter=recruiter
    ).select_related(
        "candidate"
    ).order_by(
        "interview_date",
        "interview_time"
    )

    return render(
        request,
        "recruiter/interviews.html",
        {
            "interviews": interviews
        }
    )


@login_required
def update_interview_status(
    request,
    interview_id
):

    recruiter = RecruiterProfile.objects.filter(
        user=request.user
    ).first()

    interview = get_object_or_404(
        Interview,
        id=interview_id,
        recruiter=recruiter
    )


    if request.method == "POST":

        new_status = request.POST.get(
            "status"
        )

        valid_statuses = [
            "Scheduled",
            "Completed",
            "Cancelled",
            "Rescheduled"
        ]

        if new_status in valid_statuses:
            previous_status = interview.status
            interview.status = new_status
            interview.save()

            try:
                from .email_services import send_interview_status_update_email
                send_interview_status_update_email(interview, previous_status)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error sending interview status update email: {e}")

            messages.success(
                request,
                "Interview status updated successfully!"
            )


    return redirect(
        "interview_list"
    )


@login_required
def edit_interview(
    request,
    interview_id
):

    recruiter = RecruiterProfile.objects.filter(
        user=request.user
    ).first()

    interview = get_object_or_404(
        Interview,
        id=interview_id,
        recruiter=recruiter
    )


    if request.method == "POST":

        form = EditInterviewForm(
            request.POST,
            instance=interview
        )

        if form.is_valid():

            updated_interview = form.save(
                commit=False
            )

            updated_interview.status = (
                "Rescheduled"
            )

            updated_interview.save()

            try:
                from .email_services import send_interview_rescheduled_email
                send_interview_rescheduled_email(updated_interview)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error sending interview rescheduled email: {e}")

            messages.success(
                request,
                "Interview rescheduled successfully!"
            )

            return redirect(
                "interview_list"
            )

    else:

        form = EditInterviewForm(
            instance=interview
        )


    return render(
        request,
        "recruiter/edit_interview.html",
        {
            "form": form,
            "interview": interview
        }
    )
