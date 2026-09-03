from datetime import date, datetime, timedelta
import json
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth, TruncWeek, ExtractMonth, ExtractYear
from django.utils import timezone

from django_ratelimit.decorators import ratelimit

from accounts.models import UserProfile

from candidate.models import (
    JobApplication,
    CandidateProfile,
    ResumeData,
)

from .models import (
    RecruiterProfile,
    Job,
    Interview,
    RecruiterSettings,
)

from .forms import (
    RecruiterProfileForm,
    JobForm,
    InterviewForm,
    EditInterviewForm,
)

from .ranking import (
    build_priority_candidate_rows,
    collect_available_skills,
)


logger = logging.getLogger(__name__)


# ============================================================
# RECRUITER AUTHENTICATION / ROLE CHECK
# ============================================================

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
    """
    Recruiter settings page.

    Password changes use Django's built-in PasswordChangeForm.
    Notification settings are supported when the corresponding
    RecruiterSettingsForm is available in recruiter.forms.
    """
    settings_obj, created = RecruiterSettings.objects.get_or_create(
        user=request.user
    )

    # Import these only if the project contains them.
    # This keeps the rest of recruiter/views.py independent.
    try:
        from .forms import (
            RecruiterSettingsForm,
            RecruiterPasswordChangeForm,
        )
    except ImportError:
        RecruiterSettingsForm = None
        RecruiterPasswordChangeForm = PasswordChangeForm

    if request.method == "POST":

        # ----------------------------------------------------
        # CHANGE PASSWORD
        # ----------------------------------------------------
        if "change_password" in request.POST:

            password_form = RecruiterPasswordChangeForm(
                request.user,
                request.POST,
            )

            settings_form = (
                RecruiterSettingsForm(instance=settings_obj)
                if RecruiterSettingsForm
                else None
            )

            if password_form.is_valid():
                user = password_form.save()

                update_session_auth_hash(
                    request,
                    user,
                )

                messages.success(
                    request,
                    "Password changed successfully!",
                )

                return redirect("recruiter_settings")

        # ----------------------------------------------------
        # SAVE NOTIFICATION SETTINGS
        # ----------------------------------------------------
        elif "save_notifications" in request.POST and RecruiterSettingsForm:

            settings_form = RecruiterSettingsForm(
                request.POST,
                instance=settings_obj,
            )

            password_form = RecruiterPasswordChangeForm(
                request.user,
            )

            if settings_form.is_valid():
                settings_form.save()

                messages.success(
                    request,
                    "Notification settings updated successfully!",
                )

                return redirect("recruiter_settings")

        else:
            settings_form = (
                RecruiterSettingsForm(instance=settings_obj)
                if RecruiterSettingsForm
                else None
            )
            password_form = RecruiterPasswordChangeForm(
                request.user,
            )

    else:
        settings_form = (
            RecruiterSettingsForm(instance=settings_obj)
            if RecruiterSettingsForm
            else None
        )
        password_form = RecruiterPasswordChangeForm(
            request.user,
        )

    return render(
        request,
        "recruiter/settings.html",
        {
            "settings_form": settings_form,
            "password_form": password_form,
        },
    )


# ============================================================
# RECRUITER PROFILE
# ============================================================

@login_required
def recruiter_profile(request):
    profile, created = RecruiterProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "recruiter_name": (
                request.user.get_full_name()
                or request.user.username
            ),
            "company_name": "My Company",
            "email": (
                request.user.email
                or "recruiter@example.com"
            ),
            "phone": "",
            "location": "",
            "company_description": "",
        },
    )

    return render(
        request,
        "recruiter/profile.html",
        {
            "profile": profile,
        },
    )


@login_required
def edit_recruiter_profile(request):
    profile, created = RecruiterProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "recruiter_name": (
                request.user.get_full_name()
                or request.user.username
            ),
            "company_name": "My Company",
            "email": (
                request.user.email
                or "recruiter@example.com"
            ),
            "phone": "",
            "location": "",
            "company_description": "",
        },
    )

    if request.method == "POST":
        form = RecruiterProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Profile updated successfully!",
            )

            return redirect("recruiter_profile")

    else:
        form = RecruiterProfileForm(
            instance=profile,
        )

    return render(
        request,
        "recruiter/edit_profile.html",
        {
            "form": form,
        },
    )


# ============================================================
# RECRUITER DASHBOARD
# ============================================================

@login_required
def dashboard(request):
    now = timezone.now()

    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    month_start = now.replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    recruiter_jobs = Job.objects.filter(
        recruiter=request.user
    )

    recruiter_applications = JobApplication.objects.filter(
        job__recruiter=request.user
    )

    total_jobs_posted = recruiter_jobs.count()
    active_jobs = recruiter_jobs.filter(
        is_active=True
    ).count()
    inactive_jobs = recruiter_jobs.filter(
        is_active=False
    ).count()

    total_applications = recruiter_applications.count()

    candidates_interviewed = recruiter_applications.filter(
        status="Interview"
    ).count()

    candidates_shortlisted = recruiter_applications.filter(
        status="Shortlisted"
    ).count()

    jobs_posted_this_week = recruiter_jobs.filter(
        created_at__gte=week_start
    ).count()

    applications_this_week = recruiter_applications.filter(
        applied_at__gte=week_start
    ).count()

    interviews_this_week = recruiter_applications.filter(
        status="Interview",
        applied_at__gte=week_start,
    ).count()

    jobs_posted_this_month = recruiter_jobs.filter(
        created_at__gte=month_start
    ).count()

    applications_this_month = recruiter_applications.filter(
        applied_at__gte=month_start
    ).count()

    interviews_this_month = recruiter_applications.filter(
        status="Interview",
        applied_at__gte=month_start,
    ).count()

    jobs = recruiter_jobs.order_by(
        "-created_at"
    )

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
        context,
    )


# ============================================================
# RECRUITER ANALYTICS
# ============================================================

@login_required
@ratelimit(
    key="user",
    rate="30/m",
    method="GET",
    block=True,
)
def analytics_dashboard(request):
    recruiter = request.user

    jobs = Job.objects.filter(
        recruiter=recruiter
    )

    applications = JobApplication.objects.filter(
        job__recruiter=recruiter
    )

    total_jobs = jobs.count()
    total_applications = applications.count()

    shortlisted = applications.filter(
        status="Shortlisted"
    ).count()

    interviews = applications.filter(
        status="Interview"
    ).count()

    today = timezone.now().date()

    # --------------------------------------------------------
    # LAST 12 MONTHS
    # --------------------------------------------------------

    month_labels = []
    month_keys = []

    for i in range(11, -1, -1):
        total_month_index = (
            today.year * 12
            + today.month
            - 1
            - i
        )

        year = total_month_index // 12
        month = total_month_index % 12 + 1

        month_keys.append(
            f"{year}-{month}"
        )

        month_labels.append(
            date(
                year,
                month,
                1,
            ).strftime("%b %Y")
        )

    jobs_by_month_qs = (
        jobs
        .annotate(
            y=ExtractYear("created_at"),
            m=ExtractMonth("created_at"),
        )
        .values("y", "m")
        .annotate(total=Count("id"))
    )

    month_counts = {
        f"{item['y']}-{item['m']}": item["total"]
        for item in jobs_by_month_qs
        if item["y"] and item["m"]
    }

    month_data = [
        month_counts.get(key, 0)
        for key in month_keys
    ]

    # --------------------------------------------------------
    # LAST 12 WEEKS
    # --------------------------------------------------------

    current_monday = (
        today
        - timedelta(days=today.weekday())
    )

    week_labels = []
    week_keys = []

    for i in range(11, -1, -1):
        week_monday = (
            current_monday
            - timedelta(weeks=i)
        )

        week_keys.append(
            week_monday.strftime("%Y-%W")
        )

        week_labels.append(
            week_monday.strftime("%d %b")
        )

    week_start = (
        current_monday
        - timedelta(weeks=11)
    )

    naive_week_start = datetime.combine(
        week_start,
        datetime.min.time(),
    )

    if timezone.is_aware(timezone.now()):
        week_start_date = timezone.make_aware(
            naive_week_start,
            timezone.get_current_timezone(),
        )
    else:
        week_start_date = naive_week_start

    jobs_by_week_qs = (
        jobs
        .filter(
            created_at__gte=week_start_date
        )
        .annotate(
            week=TruncWeek("created_at")
        )
        .values("week")
        .annotate(total=Count("id"))
    )

    week_counts = {
        item["week"].strftime("%Y-%W"): item["total"]
        for item in jobs_by_week_qs
        if item["week"]
    }

    week_data = [
        week_counts.get(key, 0)
        for key in week_keys
    ]

    context = {
        "total_jobs": total_jobs,
        "total_applications": total_applications,
        "shortlisted": shortlisted,
        "interviews": interviews,

        "month_labels": month_labels,
        "month_data": month_data,

        "week_labels": week_labels,
        "week_data": week_data,

        "month_labels_json": json.dumps(
            month_labels
        ),
        "month_data_json": json.dumps(
            month_data
        ),
        "week_labels_json": json.dumps(
            week_labels
        ),
        "week_data_json": json.dumps(
            week_data
        ),
    }

    return render(
        request,
        "recruiter/analytics_dashboard.html",
        context,
    )


# ============================================================
# RECRUITER JOB LISTINGS
# ============================================================

@login_required
def job_listings(request):
    jobs = Job.objects.filter(
        recruiter=request.user
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "recruiter/job_listings.html",
        {
            "jobs": jobs,
        },
    )


# ============================================================
# POST / CREATE JOB
# ============================================================

@login_required
@ratelimit(
    key="user",
    rate="10/m",
    method="POST",
    block=True,
)
def post_job(request):
    if request.method == "POST":

        form = JobForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            job = form.save(
                commit=False
            )

            job.recruiter = request.user
            job.save()

            messages.success(
                request,
                "Job posted successfully!",
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
            "form": form,
        },
    )


# Keep create_job as a compatibility alias/view for URLs
# that may still use the older Resume-NLP branch name.
@login_required
@ratelimit(
    key="user",
    rate="10/m",
    method="POST",
    block=True,
)
def create_job(request):
    return post_job(request)


# ============================================================
# JOB DETAIL
# ============================================================

@login_required
@ratelimit(
    key="user",
    rate="30/m",
    method="GET",
    block=True,
)
def recruiter_job_detail(request, job_id):
    job = get_object_or_404(
        Job,
        id=job_id,
        recruiter=request.user,
    )

    return render(
        request,
        "recruiter/job_detail.html",
        {
            "job": job,
        },
    )


# ============================================================
# EDIT JOB
# ============================================================

@login_required
@ratelimit(
    key="user",
    rate="10/m",
    method="POST",
    block=True,
)
def edit_job(request, job_id):
    job = get_object_or_404(
        Job,
        id=job_id,
        recruiter=request.user,
    )

    if request.method == "POST":
        form = JobForm(
            request.POST,
            request.FILES,
            instance=job,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Job updated successfully!",
            )

            return redirect(
                "recruiter_dashboard"
            )

    else:
        form = JobForm(
            instance=job,
        )

    return render(
        request,
        "recruiter/post_job.html",
        {
            "form": form,
            "job": job,
        },
    )


# ============================================================
# DELETE JOB
# ============================================================

@login_required
@ratelimit(
    key="user",
    rate="10/m",
    method="POST",
    block=True,
)
def delete_job(request, job_id):
    job = get_object_or_404(
        Job,
        id=job_id,
        recruiter=request.user,
    )

    if request.method == "POST":
        job.delete()

        messages.success(
            request,
            "Job deleted successfully!",
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
    block=True,
)
def view_applicants(request, job_id):
    job = get_object_or_404(
        Job,
        id=job_id,
        recruiter=request.user,
    )

    applications = job.applications.all().order_by(
        "-id"
    )

    return render(
        request,
        "recruiter/applicants.html",
        {
            "job": job,
            "applications": applications,
        },
    )


# ============================================================
# UPDATE APPLICATION STATUS
# ============================================================

@login_required
@ratelimit(
    key="user",
    rate="30/m",
    method="POST",
    block=True,
)
def update_application_status(
    request,
    application_id,
):
    application = get_object_or_404(
        JobApplication,
        id=application_id,
        job__recruiter=request.user,
    )

    if request.method == "POST":
        new_status = request.POST.get(
            "status"
        )

        valid_statuses = dict(
            JobApplication.STATUS_CHOICES
        )

        if new_status in valid_statuses:
            application.status = new_status
            application.save(
                update_fields=["status"]
            )

            messages.success(
                request,
                "Application status updated successfully.",
            )
        else:
            messages.error(
                request,
                "Invalid application status.",
            )

    return redirect(
        "priority_candidates"
    )


# ============================================================
# PRIORITY CANDIDATES
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

    applications = (
        JobApplication.objects
        .filter(
            job__recruiter=request.user
        )
        .select_related(
            "candidate",
            "candidate__candidateprofile",
            "candidate__candidateprofile__resume_data",
            "job",
            "job__recruiter",
        )
    )

    selected_job = request.GET.get(
        "job",
        "",
    ).strip()

    selected_status = request.GET.get(
        "status",
        "",
    ).strip()

    selected_skill = request.GET.get(
        "skill",
        "",
    ).strip()

    selected_experience = request.GET.get(
        "experience",
        "",
    ).strip()

    selected_score = request.GET.get(
        "score",
        "",
    ).strip()

    # --------------------------------------------------------
    # Score filter
    # --------------------------------------------------------

    score_threshold = None

    if selected_score:
        try:
            score_threshold = int(
                selected_score
            )
        except ValueError:
            score_threshold = None
        else:
            if not 0 <= score_threshold <= 100:
                score_threshold = None

    # --------------------------------------------------------
    # Job filter
    # --------------------------------------------------------

    accessible_job_ids = set(
        recruiter_jobs.values_list(
            "id",
            flat=True,
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

    # --------------------------------------------------------
    # Ranking
    # --------------------------------------------------------

    available_skills = collect_available_skills(
        applications
    )

    ranked_rows = build_priority_candidate_rows(
        applications
    )

    # --------------------------------------------------------
    # Apply filters
    # --------------------------------------------------------

    filtered_rows = []

    if not invalid_job_filter:
        selected_skill_key = (
            selected_skill.lower().strip()
        )

        for row in ranked_rows:
            application = row["application"]

            if (
                selected_job_id
                and application.job_id != selected_job_id
            ):
                continue

            if (
                selected_status
                and application.status != selected_status
            ):
                continue

            if (
                score_threshold is not None
                and row["score"] < score_threshold
            ):
                continue

            if (
                selected_skill_key
                and selected_skill_key
                not in row["candidate_skills_key"]
            ):
                continue

            if (
                selected_experience
                and row["experience_bucket"]
                != selected_experience
            ):
                continue

            filtered_rows.append(row)

    # --------------------------------------------------------
    # Filter options
    # --------------------------------------------------------

    job_filter_options = list(
        recruiter_jobs.values(
            "id",
            "title",
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

        "selected_job": selected_job,
        "selected_status": selected_status,
        "selected_skill": selected_skill,
        "selected_experience": selected_experience,
        "selected_score": selected_score,

        "invalid_job_filter":
            invalid_job_filter,

        "total_candidates":
            len(filtered_rows),
    }

    return render(
        request,
        "recruiter/priority_candidates.html",
        context,
    )


# ============================================================
# VIEW CANDIDATE DETAILS
# ============================================================

@login_required
def view_candidate_detail(request, candidate_id):
    recruiter_profile_obj = (
        RecruiterProfile.objects
        .filter(user=request.user)
        .first()
    )

    candidate = get_object_or_404(
        CandidateProfile,
        id=candidate_id,
    )

    resume_data = ResumeData.objects.filter(
        candidate=candidate
    ).first()

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
        },
    )


# ============================================================
# MILESTONE 3 - MODULE 1
# INTERVIEW SCHEDULING
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
            "Please create a recruiter profile first.",
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
                from .email_services import (
                    send_interview_scheduled_email
                )

                send_interview_scheduled_email(
                    interview
                )

            except Exception as exc:
                logger.error(
                    "Error sending interview scheduled email: %s",
                    exc,
                )

            messages.success(
                request,
                "Interview scheduled successfully!",
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
            "form": form,
        },
    )


# ============================================================
# INTERVIEW LIST
# ============================================================

@login_required
def interview_list(request):
    recruiter = RecruiterProfile.objects.filter(
        user=request.user
    ).first()

    interviews = (
        Interview.objects
        .filter(recruiter=recruiter)
        .select_related("candidate")
        .order_by(
            "interview_date",
            "interview_time",
        )
    )

    return render(
        request,
        "recruiter/interviews.html",
        {
            "interviews": interviews,
        },
    )


# ============================================================
# UPDATE INTERVIEW STATUS
# ============================================================

@login_required
def update_interview_status(
    request,
    interview_id,
):
    recruiter = RecruiterProfile.objects.filter(
        user=request.user
    ).first()

    interview = get_object_or_404(
        Interview,
        id=interview_id,
        recruiter=recruiter,
    )

    if request.method == "POST":
        new_status = request.POST.get(
            "status"
        )

        valid_statuses = [
            "Scheduled",
            "Completed",
            "Cancelled",
            "Rescheduled",
        ]

        if new_status in valid_statuses:
            previous_status = interview.status

            interview.status = new_status
            interview.save()

            try:
                from .email_services import (
                    send_interview_status_update_email
                )

                send_interview_status_update_email(
                    interview,
                    previous_status,
                )

            except Exception as exc:
                logger.error(
                    "Error sending interview status update email: %s",
                    exc,
                )

            messages.success(
                request,
                "Interview status updated successfully!",
            )

        else:
            messages.error(
                request,
                "Invalid interview status.",
            )

    return redirect(
        "interview_list"
    )


# ============================================================
# RESCHEDULE INTERVIEW
# ============================================================

@login_required
def edit_interview(
    request,
    interview_id,
):
    recruiter = RecruiterProfile.objects.filter(
        user=request.user
    ).first()

    interview = get_object_or_404(
        Interview,
        id=interview_id,
        recruiter=recruiter,
    )

    if request.method == "POST":
        form = EditInterviewForm(
            request.POST,
            instance=interview,
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
                from .email_services import (
                    send_interview_rescheduled_email
                )

                send_interview_rescheduled_email(
                    updated_interview
                )

            except Exception as exc:
                logger.error(
                    "Error sending interview rescheduled email: %s",
                    exc,
                )

            messages.success(
                request,
                "Interview rescheduled successfully!",
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
            "interview": interview,
        },
    )
