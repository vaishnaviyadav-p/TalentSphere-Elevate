from django.test import TestCase, override_settings
from django.core import mail
from django.contrib.auth.models import User
from django.urls import reverse
from candidate.models import CandidateProfile, JobApplication
from recruiter.models import RecruiterProfile, Job, Interview
import datetime

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class EmailNotificationTests(TestCase):

    def setUp(self):
        # Create users
        self.candidate_user = User.objects.create_user(
            username="candidate1",
            email="candidate@example.com",
            password="password123",
            first_name="Jane",
            last_name="Doe"
        )
        self.recruiter_user = User.objects.create_user(
            username="recruiter1",
            email="recruiter@example.com",
            password="password123"
        )

        # Create profiles
        self.candidate_profile = CandidateProfile.objects.create(
            user=self.candidate_user,
            full_name="Jane Doe",
            phone="1234567890",
            location="New York",
            education="MSCS",
            skills="Python, Django",
            experience="3 years",
            bio="Software engineer"
        )
        self.recruiter_profile = RecruiterProfile.objects.create(
            user=self.recruiter_user,
            recruiter_name="John Recruiter",
            company_name="Google",
            email="recruiter@google.com",
            phone="9876543210",
            location="Mountain View",
            company_description="Search engine"
        )

        # Create a Job
        self.job = Job.objects.create(
            recruiter=self.recruiter_user,
            title="Software Developer",
            company="Google",
            location="Mountain View",
            salary="150k",
            job_type="Full Time",
            experience="3+ years",
            description="Coding in Python",
            requirements="Python, Django",
            deadline=datetime.date.today() + datetime.timedelta(days=30),
            is_active=True
        )

        # Create Job Application
        self.application = JobApplication.objects.create(
            candidate=self.candidate_user,
            job=self.job,
            status="Applied"
        )

    def test_schedule_interview_sends_email(self):
        """Test scheduling an interview triggers email sending."""
        # Clear outbox
        mail.outbox = []

        # Create interview
        interview = Interview.objects.create(
            recruiter=self.recruiter_profile,
            candidate=self.candidate_profile,
            interview_date=datetime.date.today() + datetime.timedelta(days=2),
            interview_time=datetime.time(10, 0),
            meeting_link="https://meet.google.com/abc-defg-hij",
            notes="Be on time",
            status="Scheduled"
        )

        # Trigger scheduled email (usually called in views, but we can trigger it or test view)
        from recruiter.email_services import send_interview_scheduled_email
        success = send_interview_scheduled_email(interview)
        self.assertTrue(success)

        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ["candidate@example.com"])
        self.assertIn("Interview Scheduled", email.subject)
        self.assertIn("Jane Doe", email.body)
        self.assertIn("Software Developer", email.body)
        self.assertIn("https://meet.google.com/abc-defg-hij", email.body)

    def test_edit_interview_sends_email(self):
        """Test rescheduling an interview triggers email sending."""
        # Create interview
        interview = Interview.objects.create(
            recruiter=self.recruiter_profile,
            candidate=self.candidate_profile,
            interview_date=datetime.date.today() + datetime.timedelta(days=2),
            interview_time=datetime.time(10, 0),
            meeting_link="https://meet.google.com/abc-defg-hij",
            notes="Be on time",
            status="Scheduled"
        )

        mail.outbox = []

        # Update details
        interview.interview_date = datetime.date.today() + datetime.timedelta(days=3)
        interview.meeting_link = "https://meet.google.com/new-link"
        interview.save()

        from recruiter.email_services import send_interview_rescheduled_email
        success = send_interview_rescheduled_email(interview)
        self.assertTrue(success)

        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ["candidate@example.com"])
        self.assertIn("Interview Rescheduled", email.subject)
        self.assertIn("https://meet.google.com/new-link", email.body)

    def test_update_interview_status_sends_email(self):
        """Test updating interview status triggers email sending."""
        interview = Interview.objects.create(
            recruiter=self.recruiter_profile,
            candidate=self.candidate_profile,
            interview_date=datetime.date.today() + datetime.timedelta(days=2),
            interview_time=datetime.time(10, 0),
            meeting_link="https://meet.google.com/abc-defg-hij",
            notes="Be on time",
            status="Scheduled"
        )

        mail.outbox = []

        # Cancel interview
        previous_status = interview.status
        interview.status = "Cancelled"
        interview.save()

        from recruiter.email_services import send_interview_status_update_email
        success = send_interview_status_update_email(interview, previous_status)
        self.assertTrue(success)

        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ["candidate@example.com"])
        self.assertIn("Interview Status Update", email.subject)
        self.assertIn("Cancelled", email.body)

    def test_job_application_status_update_sends_email(self):
        """Test modifying JobApplication status triggers email notification automatically via save method."""
        mail.outbox = []

        # Change status to Shortlisted
        self.application.status = "Shortlisted"
        self.application.save()

        # Verify email was sent automatically
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ["candidate@example.com"])
        self.assertIn("Application Status Update", email.subject)
        self.assertIn("Shortlisted", email.body)
        self.assertIn("Google", email.body)

        # Reset outbox and change to Interview
        mail.outbox = []
        self.application.status = "Interview"
        self.application.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Interview", mail.outbox[0].body)
