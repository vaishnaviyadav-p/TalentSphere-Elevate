from django import forms
from .models import CandidateProfile, ResumeData


class CandidateProfileForm(forms.ModelForm):

    class Meta:
        model = CandidateProfile
        exclude = ['user']

        widgets = {
            'full_name': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'phone': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'location': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'education': forms.TextInput(
                attrs={'class': 'form-control'}
            ),
            'skills': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3
                }
            ),
            'experience': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3
                }
            ),
            'bio': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4
                }
            ),
            'profile_image': forms.ClearableFileInput(
                attrs={
                    'class': 'form-control'
                }
            ),
        }


class ResumeUploadForm(forms.ModelForm):

    class Meta:
        model = ResumeData
        fields = ['resume_file']

        widgets = {
            'resume_file': forms.ClearableFileInput(
                attrs={
                    'class': 'form-control',
                    'accept': '.pdf,.docx'
                }
            )
        }

        error_messages = {
            'resume_file': {
                'required': 'Please select a resume.'
            }
        }

    def clean_resume_file(self):
        resume = self.cleaned_data.get('resume_file')

        if not resume:
            raise forms.ValidationError(
                "Please select a resume."
            )

        filename = resume.name.lower()

        # Allow only PDF and DOCX
        if not (
            filename.endswith('.pdf')
            or filename.endswith('.docx')
        ):
            raise forms.ValidationError(
                "Only PDF and DOCX files are allowed."
            )

        # Maximum size: 5 MB
        if resume.size > 5 * 1024 * 1024:
            raise forms.ValidationError(
                "Resume size must be less than 5 MB."
            )

        return resume