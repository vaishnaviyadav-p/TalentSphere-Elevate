from django.contrib import admin
from .models import CandidateProfile, JobApplication


admin.site.register(CandidateProfile)
admin.site.register(JobApplication)