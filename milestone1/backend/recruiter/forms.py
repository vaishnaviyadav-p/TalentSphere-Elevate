from django import forms
from .models import RecruiterProfile


class RecruiterProfileForm(forms.ModelForm):
    class Meta:
        model = RecruiterProfile
        exclude = ['user']

        widgets = {
            'recruiter_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'company_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'company_logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }