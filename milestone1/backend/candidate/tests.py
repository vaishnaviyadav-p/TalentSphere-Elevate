import os
import shutil
import tempfile
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.contrib.auth.models import User
from candidate.models import CandidateProfile, ResumeData
from candidate.forms import ResumeUploadForm

# Create a temporary directory for media files during tests
TEMP_MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ResumeUploadTests(TestCase):

    @classmethod
    def tearDownClass(cls):
        # Clean up the temporary media directory after tests finish
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        # Create a candidate user and profile for view tests
        self.user = User.objects.create_user(username="testcandidate", password="password")
        self.profile = CandidateProfile.objects.create(
            user=self.user,
            full_name="John Doe",
            phone="9876543210",
            location="Mumbai, India",
            education="B.Tech in Computer Science",
            skills="Python, SQL",
            experience="2 years",
            bio="Software engineer"
        )
        self.client.force_login(self.user)

    def test_resume_upload_form_valid_pdf(self):
        """Test ResumeUploadForm accepts valid PDF file."""
        pdf_file = SimpleUploadedFile("resume.pdf", b"pdf content", content_type="application/pdf")
        form = ResumeUploadForm(files={"resume_file": pdf_file})
        self.assertTrue(form.is_valid())

    def test_resume_upload_form_valid_docx(self):
        """Test ResumeUploadForm accepts valid DOCX file."""
        docx_file = SimpleUploadedFile("resume.docx", b"docx content", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        form = ResumeUploadForm(files={"resume_file": docx_file})
        self.assertTrue(form.is_valid())

    def test_resume_upload_form_invalid_extension(self):
        """Test ResumeUploadForm rejects invalid file types (e.g. TXT)."""
        txt_file = SimpleUploadedFile("resume.txt", b"text content", content_type="text/plain")
        form = ResumeUploadForm(files={"resume_file": txt_file})
        self.assertFalse(form.is_valid())
        self.assertIn("Only PDF and DOCX files are allowed.", form.errors["resume_file"][0])

    def test_resume_upload_form_too_large(self):
        """Test ResumeUploadForm rejects files larger than 5MB."""
        large_content = b"0" * (5 * 1024 * 1024 + 1)  # 5MB + 1 byte
        pdf_file = SimpleUploadedFile("resume.pdf", large_content, content_type="application/pdf")
        form = ResumeUploadForm(files={"resume_file": pdf_file})
        self.assertFalse(form.is_valid())
        self.assertIn("Resume size must be less than 5 MB.", form.errors["resume_file"][0])

    def test_resume_upload_form_empty(self):
        """Test ResumeUploadForm validation fails when no file is uploaded."""
        form = ResumeUploadForm(files={})
        self.assertFalse(form.is_valid())
        self.assertIn("Please select a resume.", form.errors["resume_file"][0])

    @patch('candidate.views.parse_resume')
    def test_upload_resume_view_success(self, mock_parse_resume):
        """Test upload_resume view successfully uploads, parses, stores and links resume to profile."""
        # Mock parser output
        mock_parse_resume.return_value = {
            "extracted_text": "John Doe Resume Python SQL Developer",
            "name": "John Doe",
            "email": "johndoe@example.com",
            "phone": "+919876543210",
            "skills": ["python", "sql"],
            "experience": ["2 years of experience"],
            "projects": ["Project A"],
            "keywords": ["python", "sql", "developer"]
        }

        # Create request post data
        pdf_file = SimpleUploadedFile("resume.pdf", b"pdf content", content_type="application/pdf")
        
        response = self.client.post(
            reverse("upload_resume"),
            data={"resume_file": pdf_file}
        )

        # Check redirect
        self.assertRedirects(response, reverse("candidate_profile"))

        # Verify ResumeData created and linked
        resume_data = ResumeData.objects.filter(candidate=self.profile).first()
        self.assertIsNotNone(resume_data)
        self.assertTrue(resume_data.resume_file.name.endswith(".pdf"))
        self.assertEqual(resume_data.extracted_text, "John Doe Resume Python SQL Developer")
        self.assertEqual(resume_data.parsed_name, "John Doe")
        self.assertEqual(resume_data.parsed_email, "johndoe@example.com")
        self.assertEqual(resume_data.parsed_phone, "+919876543210")
        self.assertEqual(resume_data.parsed_skills, ["python", "sql"])

        # Check physical file was saved on disk inside our temp media folder
        physical_path = os.path.join(TEMP_MEDIA_ROOT, resume_data.resume_file.name)
        self.assertTrue(os.path.exists(physical_path))

    def test_upload_resume_view_no_profile(self):
        """Test upload_resume view fails and redirects when no candidate profile exists."""
        # Delete profile created in setUp
        CandidateProfile.objects.all().delete()

        pdf_file = SimpleUploadedFile("resume.pdf", b"pdf content", content_type="application/pdf")
        response = self.client.post(
            reverse("upload_resume"),
            data={"resume_file": pdf_file}
        )

        # Check redirect and error message
        self.assertRedirects(response, reverse("candidate_profile"))
        
        # Verify no ResumeData was created
        self.assertEqual(ResumeData.objects.count(), 0)

    @patch('candidate.views.parse_resume')
    def test_upload_resume_view_parsing_failure(self, mock_parse_resume):
        """Test upload_resume view behaves correctly when resume parsing fails/raises exception."""
        # Make parser raise exception
        mock_parse_resume.side_effect = Exception("Parsing error")

        pdf_file = SimpleUploadedFile("resume.pdf", b"pdf content", content_type="application/pdf")
        response = self.client.post(
            reverse("upload_resume"),
            data={"resume_file": pdf_file}
        )

        # It should still redirect to candidate_profile and save the file
        self.assertRedirects(response, reverse("candidate_profile"))
        
        # ResumeData is saved, but fields from parser are not set
        resume_data = ResumeData.objects.filter(candidate=self.profile).first()
        self.assertIsNotNone(resume_data)
        self.assertTrue(resume_data.resume_file.name.endswith(".pdf"))
        self.assertIsNone(resume_data.extracted_text)

