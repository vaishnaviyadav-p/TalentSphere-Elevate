from django import forms

from .models import (
    RecruiterProfile,
    Job,
    Interview
)


class RecruiterProfileForm(forms.ModelForm):

    class Meta:
        model = RecruiterProfile

        fields = "__all__"


class JobForm(forms.ModelForm):

    class Meta:
        model = Job

        fields = [
            "title",
            "company",
            "location",
            "salary",
            "job_type",
            "experience",
            "description",
            "requirements",
            "deadline",
            "is_active",
        ]

        widgets = {

            "deadline": forms.DateInput(
                attrs={
                    "type": "date"
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "rows": 5
                }
            ),

            "requirements": forms.Textarea(
                attrs={
                    "rows": 5
                }
            ),
        }


class InterviewForm(forms.ModelForm):

    class Meta:
        model = Interview

        fields = [
            "candidate",
            "interview_date",
            "interview_time",
            "meeting_link",
            "notes",
        ]

        widgets = {

            "candidate": forms.Select(
                attrs={
                    "class": "form-select"
                }
            ),

            "interview_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date"
                }
            ),

            "interview_time": forms.TimeInput(
                attrs={
                    "class": "form-control",
                    "type": "time"
                }
            ),

            "meeting_link": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://meet.google.com/..."
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Enter interview notes..."
                }
            ),
        }


class EditInterviewForm(forms.ModelForm):

    class Meta:
        model = Interview

        fields = [
            "interview_date",
            "interview_time",
            "meeting_link",
            "notes",
        ]

        widgets = {

            "interview_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date"
                }
            ),

            "interview_time": forms.TimeInput(
                attrs={
                    "class": "form-control",
                    "type": "time"
                }
            ),

            "meeting_link": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://meet.google.com/..."
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4
                }
            ),
        }