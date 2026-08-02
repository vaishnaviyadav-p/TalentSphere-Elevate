from django import forms
from .models import RecruiterProfile, Job


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
            "deadline": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 5}),
            "requirements": forms.Textarea(attrs={"rows": 5}),
        }