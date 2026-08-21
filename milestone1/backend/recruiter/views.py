from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)

from django.core.exceptions import PermissionDenied

from django.contrib.auth.decorators import login_required

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
# RECRUITER PROFILE
# ============================================================

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


# ============================================================
# RECRUITER DASHBOARD
# ============================================================

@login_required
def dashboard(request):

    active_jobs = Job.objects.filter(
        recruiter=request.user,
        is_active=True
    ).count()

    jobs = Job.objects.filter(
        recruiter=request.user
    ).order_by(
        "-created_at"
    )

    context = {
        "active_jobs": active_jobs,
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

@login_required
def analytics_dashboard(request):

    recruiter = request.user

    # ==========================================
    # JOBS POSTED BY THIS RECRUITER
    # ==========================================

    jobs = Job.objects.filter(recruiter=recruiter)

    # Total jobs
    total_jobs = jobs.count()

    # ==========================================
    # APPLICATIONS FOR RECRUITER'S JOBS
    # ==========================================

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

    # ==========================================
    # MONTH-WISE JOB POSTING DATA
    # ==========================================

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

    # ==========================================
    # WEEK-WISE JOB POSTING DATA
    # ==========================================

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

    # ==========================================
    # APPLICATION TREND BY MONTH
    # ==========================================

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

            if (
                score_threshold < 0
                or
                score_threshold > 100
            ):
                score_threshold = None


    # --------------------------------------------------------
    # Job filter
    # --------------------------------------------------------

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
            selected_skill
            .lower()
            .strip()
        )

        for row in ranked_rows:

            application = row[
                "application"
            ]


            # Job filter

            if (
                selected_job_id
                and
                application.job_id != selected_job_id
            ):
                continue


            # Status filter

            if (
                selected_status
                and
                application.status != selected_status
            ):
                continue


            # Score filter

            if (
                score_threshold is not None
                and
                row["score"] < score_threshold
            ):
                continue


            # Skill filter

            if (
                selected_skill_key
                and
                selected_skill_key
                not in row["candidate_skills_key"]
            ):
                continue


            # Experience filter

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


    # --------------------------------------------------------
    # Filter options
    # --------------------------------------------------------

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
# EDIT JOB
# ============================================================

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


# ============================================================
# DELETE JOB
# ============================================================

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


# ============================================================
# VIEW CANDIDATE DETAILS
# ============================================================

@login_required
def view_candidate_detail(
    request,
    candidate_id
):

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
        }
    )


# ============================================================
# MILESTONE 3 - MODULE 1
# INTERVIEW SCHEDULING
# ============================================================


# ------------------------------------------------------------
# Schedule Interview
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Interview List
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Update Interview Status
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Reschedule Interview
# ------------------------------------------------------------

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