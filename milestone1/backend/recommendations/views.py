from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from candidate.models import CandidateProfile
from recruiter.models import Job, RecruiterProfile
from recruiter.views import _is_recruiter

from .services import (
    generate_job_recommendations_for_candidate,
    generate_candidate_recommendations_for_job,
    get_job_recommendations_for_candidate,
    get_candidate_recommendations_for_job,
    mark_recommendation_viewed,
    dismiss_recommendation,
)


@login_required
def candidate_job_recommendations(request):
    """Show AI-powered job recommendations for the candidate."""
    profile = CandidateProfile.objects.filter(user=request.user).first()
    
    if not profile:
        messages.error(request, "Please complete your candidate profile first.")
        return redirect("candidate_profile")
    
    resume_data = getattr(profile, "resume_data", None)
    has_resume = resume_data is not None
    
    if request.GET.get("refresh") == "1":
        recommendations = generate_job_recommendations_for_candidate(
            request.user, limit=15, min_score=25.0
        )
        messages.success(request, f"Generated {len(recommendations)} new job recommendations!")
    else:
        recommendations = get_job_recommendations_for_candidate(request.user, limit=15)
    
    context = {
        "recommendations": recommendations,
        "has_resume": has_resume,
        "profile": profile,
    }
    return render(request, "recommendations/candidate_job_recommendations.html", context)


@login_required
def recruiter_candidate_recommendations(request, job_id):
    """Show AI-powered candidate recommendations for a specific job."""
    if not _is_recruiter(request.user):
        messages.error(request, "Access denied.")
        return redirect("recruiter_dashboard")
    
    job = get_object_or_404(Job, id=job_id, recruiter=request.user)
    
    if request.GET.get("refresh") == "1":
        recommendations = generate_candidate_recommendations_for_job(
            job, limit=20, min_score=25.0
        )
        messages.success(request, f"Generated {len(recommendations)} new candidate recommendations!")
    else:
        recommendations = get_candidate_recommendations_for_job(job, limit=20)
    
    # Prepare job required skills for display (normalized)
    from candidate.skill_matching import extract_required_skills
    from recommendations.services import _normalize_skills
    required_skills_raw = extract_required_skills(job.requirements)
    required_skills_display = list(_normalize_skills(required_skills_raw))
    
    context = {
        "job": job,
        "recommendations": recommendations,
        "required_skills_display": required_skills_display,
    }
    return render(request, "recommendations/recruiter_candidate_recommendations.html", context)


@login_required
@require_POST
def mark_recommendation_viewed_ajax(request):
    """AJAX endpoint to mark a recommendation as viewed."""
    recommendation_id = request.POST.get("recommendation_id")
    model_type = request.POST.get("model_type")
    
    if not recommendation_id or not model_type:
        return JsonResponse({"success": False, "error": "Missing parameters"})
    
    success = mark_recommendation_viewed(int(recommendation_id), model_type)
    return JsonResponse({"success": success})


@login_required
@require_POST
def dismiss_recommendation_ajax(request):
    """AJAX endpoint to dismiss a recommendation."""
    recommendation_id = request.POST.get("recommendation_id")
    model_type = request.POST.get("model_type")
    
    if not recommendation_id or not model_type:
        return JsonResponse({"success": False, "error": "Missing parameters"})
    
    success = dismiss_recommendation(int(recommendation_id), model_type)
    return JsonResponse({"success": success})


@login_required
def recruiter_all_recommendations(request):
    """Show candidate recommendations across all of recruiter's jobs."""
    if not _is_recruiter(request.user):
        messages.error(request, "Access denied.")
        return redirect("recruiter_dashboard")
    
    recruiter_jobs = Job.objects.filter(recruiter=request.user, is_active=True)
    
    job_id = request.GET.get("job_id")
    if job_id:
        try:
            job = recruiter_jobs.get(id=job_id)
        except Job.DoesNotExist:
            job = None
    else:
        job = recruiter_jobs.first()
    
    recommendations = []
    if job:
        if request.GET.get("refresh") == "1":
            recommendations = generate_candidate_recommendations_for_job(
                job, limit=20, min_score=25.0
            )
            messages.success(request, f"Generated {len(recommendations)} new candidate recommendations!")
        else:
            recommendations = get_candidate_recommendations_for_job(job, limit=20)
    
    context = {
        "jobs": recruiter_jobs,
        "selected_job": job,
        "recommendations": recommendations,
    }
    return render(request, "recommendations/recruiter_all_recommendations.html", context)