from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import RecruiterProfile
from .forms import RecruiterProfileForm
from candidate.models import CandidateProfile, ResumeData


def recruiter_profile(request):
    profile = RecruiterProfile.objects.first()
    return render(request, "recruiter/profile.html", {"profile": profile})


def edit_recruiter_profile(request):
    profile = RecruiterProfile.objects.first()

    if request.method == "POST":
        form = RecruiterProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if form.is_valid():
            form.save()
            return redirect("recruiter_profile")

    else:
        form = RecruiterProfileForm(instance=profile)

    return render(
        request,
        "recruiter/edit_profile.html",
        {"form": form},
    )


def recruiter_dashboard(request):
    profile = RecruiterProfile.objects.first()

    query = request.GET.get('q', '').strip()
    skill_filter = request.GET.get('skill', '').strip()

    candidates = CandidateProfile.objects.all().select_related('resume_data')

    if query:
        candidates = candidates.filter(
            Q(full_name__icontains=query) |
            Q(location__icontains=query) |
            Q(skills__icontains=query) |
            Q(bio__icontains=query) |
            Q(education__icontains=query) |
            Q(resume_data__extracted_text__icontains=query) |
            Q(resume_data__parsed_name__icontains=query)
        )

    if skill_filter:
        # Check both manual skills list (comma-separated string) and parsed JSON array
        # Note: __icontains in SQLite handles string representations of JSON lists
        candidates = candidates.filter(
            Q(skills__icontains=skill_filter) |
            Q(resume_data__parsed_skills__icontains=skill_filter)
        )

    # Collect unique skills to render quick-filter badges
    all_skills = set()
    for cand in CandidateProfile.objects.all():
        if cand.skills:
            for s in cand.skills.split(','):
                clean_s = s.strip().lower()
                if clean_s:
                    all_skills.add(clean_s)

    resumes = ResumeData.objects.all()
    for res in resumes:
        if isinstance(res.parsed_skills, list):
            for s in res.parsed_skills:
                all_skills.add(s.lower())

    common_skills = sorted(list(all_skills))[:15]

    # Calculate metrics
    total_candidates = CandidateProfile.objects.count()
    parsed_resumes_count = ResumeData.objects.filter(resume_file__isnull=False).count()

    return render(
        request,
        "recruiter/dashboard.html",
        {
            "recruiter_profile": profile,
            "candidates": candidates,
            "query": query,
            "selected_skill": skill_filter,
            "common_skills": common_skills,
            "total_candidates": total_candidates,
            "parsed_resumes_count": parsed_resumes_count,
        }
    )


def view_candidate_detail(request, candidate_id):
    recruiter_profile = RecruiterProfile.objects.first()
    candidate = get_object_or_404(CandidateProfile, id=candidate_id)
    resume_data = ResumeData.objects.filter(candidate=candidate).first()

    return render(
        request,
        "recruiter/candidate_detail.html",
        {
            "recruiter_profile": recruiter_profile,
            "candidate": candidate,
            "resume_data": resume_data,
        }
    )