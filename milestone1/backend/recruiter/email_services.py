import logging
from django.core.mail import send_mail
from django.conf import settings
from candidate.models import JobApplication

logger = logging.getLogger(__name__)

def get_job_for_interview(interview):
    try:
        candidate_user = interview.candidate.user
        recruiter_user = interview.recruiter.user
        if candidate_user and recruiter_user:
            app = JobApplication.objects.filter(
                candidate=candidate_user,
                job__recruiter=recruiter_user
            ).first()
            if app:
                return app.job
    except Exception as e:
        logger.error(f"Error finding job for interview: {e}")
    return None

def send_interview_scheduled_email(interview):
    candidate = interview.candidate
    recipient = candidate.user.email if candidate.user else None
    if not recipient:
        logger.warning(f"No email found for candidate {candidate.full_name}")
        return False
    
    job = get_job_for_interview(interview)
    company_name = interview.recruiter.company_name
    job_title = job.title if job else "Position"
    
    subject = f"Interview Scheduled: {job_title} at {company_name}"
    
    body = (
        f"Dear {candidate.full_name},\n\n"
        f"We are pleased to inform you that your interview for the {job_title} position "
        f"at {company_name} has been scheduled.\n\n"
        f"Here are the details of your interview:\n"
        f"- Date: {interview.interview_date}\n"
        f"- Time: {interview.interview_time}\n"
        f"- Meeting Link: {interview.meeting_link}\n"
    )
    if interview.notes:
        body += f"- Additional Notes: {interview.notes}\n"
        
    body += (
        f"\nPlease join the meeting using the link provided above at the scheduled time.\n\n"
        f"Best regards,\n"
        f"{company_name} Recruiting Team"
    )
    
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@talentsphere.com'),
            recipient_list=[recipient],
            fail_silently=False
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send interview scheduled email to {recipient}: {e}")
        return False

def send_interview_rescheduled_email(interview):
    candidate = interview.candidate
    recipient = candidate.user.email if candidate.user else None
    if not recipient:
        logger.warning(f"No email found for candidate {candidate.full_name}")
        return False
    
    job = get_job_for_interview(interview)
    company_name = interview.recruiter.company_name
    job_title = job.title if job else "Position"
    
    subject = f"Interview Rescheduled: {job_title} at {company_name}"
    
    body = (
        f"Dear {candidate.full_name},\n\n"
        f"Your interview for the {job_title} position at {company_name} has been rescheduled.\n\n"
        f"Please find the updated interview details below:\n"
        f"- New Date: {interview.interview_date}\n"
        f"- New Time: {interview.interview_time}\n"
        f"- New Meeting Link: {interview.meeting_link}\n"
    )
    if interview.notes:
        body += f"- Updated Notes: {interview.notes}\n"
        
    body += (
        f"\nPlease join the meeting using the link provided above at the scheduled time.\n\n"
        f"Best regards,\n"
        f"{company_name} Recruiting Team"
    )
    
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@talentsphere.com'),
            recipient_list=[recipient],
            fail_silently=False
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send interview rescheduled email to {recipient}: {e}")
        return False

def send_interview_status_update_email(interview, previous_status):
    candidate = interview.candidate
    recipient = candidate.user.email if candidate.user else None
    if not recipient:
        logger.warning(f"No email found for candidate {candidate.full_name}")
        return False
    
    job = get_job_for_interview(interview)
    company_name = interview.recruiter.company_name
    job_title = job.title if job else "Position"
    
    subject = f"Interview Status Update: {job_title} at {company_name}"
    
    body = (
        f"Dear {candidate.full_name},\n\n"
        f"We want to notify you that the status of your interview for the {job_title} position "
        f"at {company_name} has been updated.\n\n"
        f"- Interview Date: {interview.interview_date}\n"
        f"- New Status: {interview.status}\n"
    )
    
    if interview.status == "Cancelled":
        body += f"\nUnfortunately, this interview session has been cancelled. We will contact you if we need to reschedule.\n"
    elif interview.status == "Completed":
        body += f"\nThank you for attending the interview. We will review the session and get back to you with the next steps soon.\n"
    elif interview.status == "Scheduled":
        body += f"\nYour interview is confirmed for the scheduled time.\n"
        
    body += (
        f"\nBest regards,\n"
        f"{company_name} Recruiting Team"
    )
    
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@talentsphere.com'),
            recipient_list=[recipient],
            fail_silently=False
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send interview status update email to {recipient}: {e}")
        return False

def send_application_status_update_email(application):
    candidate_user = application.candidate
    recipient = candidate_user.email
    if not recipient:
        logger.warning(f"No email found for candidate user {candidate_user.username}")
        return False
    
    job = application.job
    company_name = job.company
    job_title = job.title
    candidate_name = candidate_user.get_full_name() or candidate_user.username
    
    subject = f"Application Status Update: {job_title} at {company_name}"
    
    body = (
        f"Dear {candidate_name},\n\n"
        f"We wanted to update you on the status of your application for the {job_title} position "
        f"at {company_name}.\n\n"
        f"Your application status has been updated to: {application.status}\n\n"
    )
    
    if application.status == "Shortlisted":
        body += "Congratulations! Your application has been shortlisted. We will reach out to you soon with next steps.\n"
    elif application.status == "Interview":
        body += "Great news! We would like to invite you for an interview. We will reach out to schedule a convenient time.\n"
    elif application.status == "Rejected":
        body += "Thank you for taking the time to apply. We have reviewed your application carefully and regret to inform you that we will not be moving forward with your application at this time. We wish you the best in your search.\n"
        
    body += (
        f"\nBest regards,\n"
        f"{company_name} Recruiting Team"
    )
    
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@talentsphere.com'),
            recipient_list=[recipient],
            fail_silently=False
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send application status email to {recipient}: {e}")
        return False
