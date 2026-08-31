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

# ============================================================
# RECRUITER SETTINGS
# ============================================================

@login_required
def recruiter_settings(request):
    return render(request, "recruiter/settings.html")  # Redirect to the settings page

    settings_obj, created = RecruiterSettings.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        # ------------------------------------------
        # CHANGE PASSWORD
        # ------------------------------------------

        if "change_password" in request.POST:

            password_form = RecruiterPasswordChangeForm(
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

            password_form = RecruiterPasswordChangeForm(
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

        password_form = RecruiterPasswordChangeForm(
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


# ============================================================
# RECRUITER DASHBOARD
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
from candidate.models import JobApplication  # Adjust path if JobApplication is in another app

@login_required
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

    # 5.recruiter trends
    context = {
    "total_jobs": total_jobs,
    "total_applications": total_applications,
    "shortlisted": shortlisted,
    "interviews": interviews,

    "month_labels_json": json.dumps(month_labels),
    "month_data_json": json.dumps(month_data), # This is your monthly recruitment trend!
    "week_labels_json": json.dumps(week_labels),
    "week_data_json": json.dumps(week_data),  
    }

    # 6. CONTEXT DICTIONARY (Includes Counter Metrics AND Chart JSON Data)
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