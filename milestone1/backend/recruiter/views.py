from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)

from datetime import timedelta

from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone

from django.contrib import messages
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User

from django_ratelimit.decorators import ratelimit

from candidate.models import (
    JobApplication,
    CandidateProfile,
    ResumeData
)

from .models import (
    RecruiterProfile,
    Job,
    Interview,
    RecruiterSettings
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


# ============================================================
# RECRUITER SETTINGS
# ============================================================

@login_required
def recruiter_settings(request):
    settings_obj, created = RecruiterSettings.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        # ------------------------------------------
        # CHANGE PASSWORD
        # ------------------------------------------

        if "change_password" in request.POST:

            password_form = PasswordChangeForm(
                request.user,
                request.POST
            )

            settings_form = RecruiterSettingsForm(
                instance=settings_obj
            )

            if password_form.is_valid():

                user = password_form.save()

                # Keep user logged in after password change
                update_session_auth_hash(
                    request,
                    user
                )

                messages.success(
                    request,
                    "Password changed successfully!"
                )

                return redirect(
                    "recruiter_settings"
                )

        # ------------------------------------------
        # SAVE NOTIFICATION SETTINGS
        # ------------------------------------------

        elif "save_notifications" in request.POST:

            settings_form = RecruiterSettingsForm(
                request.POST,
                instance=settings_obj
            )

            password_form = PasswordChangeForm(
                request.user
            )

            if settings_form.is_valid():

                settings_form.save()

                messages.success(
                    request,
                    "Notification settings updated successfully!"
                )

                return redirect(
                    "recruiter_settings"
                )

    else:

        settings_form = RecruiterSettingsForm(
            instance=settings_obj
        )

        password_form = PasswordChangeForm(
            request.user
        )

    return render(
        request,
        "recruiter/settings.html",
        {
            "settings_form": settings_form,
            "password_form": password_form,
        }
    )


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


@login_required
def recruiter_profile(request):

    return render(
        request,
        "recruiter/profile.html"
    )


# ============================================================
# DETAILED RECRUITER DASHBOARD (with metrics)
# ============================================================

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
# UPDATE APPLICATION STATUS
# ============================================================

def update_application_status(request, application_id):
    application = get_object_or_404(JobApplication, id=application_id)

    if request.method == "POST":
        new_status = request.POST.get("status")

        if new_status in dict(JobApplication.STATUS_CHOICES):
            application.status = new_status
            application.save()
            messages.success(request, "Application status updated successfully.")

    return redirect("priority_candidates")


# ============================================================
# ANALYTICS DASHBOARD
# ============================================================

import json
import calendar
from datetime import date, datetime, timedelta

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone

from .models import Job
from candidate.models import JobApplication


@login_required
@ratelimit(
    key="user",
    rate="30/m",
    method="GET",
    block=True
)
def analytics_dashboard(request):
    recruiter = request.user

    # 1. JOBS & APPLICATIONS BASE QUERYSETS
    jobs = Job.objects.filter(recruiter=recruiter)
    applications = JobApplication.objects.filter(job__recruiter=recruiter)

    # 2. COUNTER METRICS (Total Jobs, Applications, Shortlisted, Interviews)
    total_jobs = jobs.count()
    total_applications = applications.count()
    shortlisted = applications.filter(status="Shortlisted").count()
    interviews = applications.filter(status="Interview").count()

    today = timezone.now().date()

    from django.db.models.functions import ExtractMonth, ExtractYear

    # ==========================================
    # 3. MONTH-WISE DATA (EXACT MATCH LIKE WEEK-WISE)
    # ==========================================
    month_labels = []
    month_keys = []

    for i in range(11, -1, -1):
        year = today.year - ((today.month - 1 - i) // -12 if (today.month - 1 - i) < 0 else 0)
        month = (today.month - 1 - i) % 12 + 1
        
        # Unique key formatted as "YYYY-M" (e.g., "2026-8")
        month_keys.append(f"{year}-{month}")
        
        # Display label (e.g., "Aug 2026")
        dt = date(year, month, 1)
        month_labels.append(dt.strftime("%b %Y"))

    # Query DB and extract exact integer Year and Month
    jobs_by_month_qs = (
        jobs
        .annotate(
            y=ExtractYear("created_at"),
            m=ExtractMonth("created_at")
        )
        .values("y", "m")
        .annotate(total=Count("id"))
    )

    # Build dictionary lookup: {"2026-8": 5, "2026-7": 2, ...}
    month_counts = {
        f"{item['y']}-{item['m']}": item["total"]
        for item in jobs_by_month_qs if item["y"] and item["m"]
    }

    # Match counts to month keys (defaults to 0 if no jobs posted that month)
    month_data = [month_counts.get(key, 0) for key in month_keys]
    
    # 4. WEEK-WISE DATA (LAST 12 WEEKS)
    current_monday = today - timedelta(days=today.weekday())
    
    week_labels = []
    week_keys = []

    for i in range(11, -1, -1):
        week_monday = current_monday - timedelta(weeks=i)
        week_keys.append(week_monday.strftime("%Y-%W"))
        week_labels.append(week_monday.strftime("%d %b"))

    naive_week_start = datetime.combine(current_monday - timedelta(weeks=11), datetime.min.time())
    week_start_date = timezone.make_aware(naive_week_start)

    jobs_by_week_qs = (
        jobs
        .filter(created_at__gte=week_start_date)
        .annotate(week=TruncWeek("created_at"))
        .values("week")
        .annotate(total=Count("id"))
    )

    week_counts = {
        item["week"].strftime("%Y-%W"): item["total"]
        for item in jobs_by_week_qs if item["week"]
    }

    week_data = [week_counts.get(key, 0) for key in week_keys]

    # 5. CONTEXT DICTIONARY (Includes Counter Metrics AND Chart JSON Data)
    context = {
        "total_jobs": total_jobs,
        "total_applications": total_applications,
        "shortlisted": shortlisted,
        "interviews": interviews,

        "month_labels_json": json.dumps(month_labels),
        "month_data_json": json.dumps(month_data),
        "week_labels_json": json.dumps(week_labels),
        "week_data_json": json.dumps(week_data),
    }

    return render(request, "recruiter/analytics_dashboard.html", context)


# ============================================================
# RECRUITER JOB LISTINGS
# ============================================================

@login_required
def job_listings(request):

    jobs = Job.objects.filter(
        recruiter=request.user
    ).order_by("-created_at")

    return render(
        request,
        "recruiter/job_listings.html",
        {
            "jobs": jobs
        }
    )


# ============================================================
# POST JOB
# ============================================================

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

            # Assign logged-in recruiter
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
        "recruiter/edit_job.html",
        {
            "form": form,
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
# CANDIDATE RANKING (Priority Candidates)
# ============================================================

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


# ============================================================
# VIEW CANDIDATE DETAIL
# ============================================================

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


# ============================================================
# SCHEDULE INTERVIEW
# ============================================================

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


# ============================================================
# INTERVIEW LIST
# ============================================================

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


# ============================================================
# UPDATE INTERVIEW STATUS
# ============================================================

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


# ============================================================
# EDIT INTERVIEW
# ============================================================

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

    if not _is_recruiter(request.user):
        raise PermissionDenied

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