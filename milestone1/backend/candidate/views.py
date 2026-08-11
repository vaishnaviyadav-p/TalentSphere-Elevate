from django.shortcuts import render, redirect
from django.contrib import messages

from .models import CandidateProfile, ResumeData
from .forms import CandidateProfileForm, ResumeUploadForm
from .services.resume_parser import parse_resume


def candidate_profile(request):
    profile = CandidateProfile.objects.first()

    resume_data = None

    if profile:
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


def edit_candidate_profile(request):
    profile = CandidateProfile.objects.first()

    if request.method == "POST":
        form = CandidateProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if form.is_valid():
            form.save()
            return redirect("candidate_profile")

    else:
        form = CandidateProfileForm(
            instance=profile
        )

    return render(
        request,
        "candidate/edit_profile.html",
        {"form": form},
    )


def upload_resume(request):

    profile = CandidateProfile.objects.first()

    # Make sure a candidate profile exists
    if not profile:
        messages.error(
            request,
            "Candidate profile not found. Please create a profile first."
        )

        return redirect("candidate_profile")

    if request.method == "POST":

        # Receive uploaded file
        form = ResumeUploadForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            # Get existing ResumeData or create a new one
            resume_data, created = ResumeData.objects.get_or_create(
                candidate=profile
            )

            # Save uploaded resume
            resume_data.resume_file = form.cleaned_data[
                "resume_file"
            ]

            resume_data.save()

            try:

                # Run our resume parser
                parsed_data = parse_resume(
                    resume_data.resume_file.path
                )

                # Save extracted text
                resume_data.extracted_text = parsed_data[
                    "extracted_text"
                ]

                # Save candidate information
                resume_data.parsed_name = parsed_data[
                    "name"
                ]

                resume_data.parsed_email = parsed_data[
                    "email"
                ]

                resume_data.parsed_phone = parsed_data[
                    "phone"
                ]

                # Save skills
                resume_data.parsed_skills = parsed_data[
                    "skills"
                ]

                # Save experience
                resume_data.parsed_experience = parsed_data[
                    "experience"
                ]

                # Save projects
                resume_data.parsed_projects = parsed_data[
                    "projects"
                ]

                # Save keywords
                resume_data.parsed_keywords = parsed_data[
                    "keywords"
                ]

                # Save everything to database
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