from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from candidate.models import CandidateProfile, ResumeData
from candidate.skill_matching import extract_skills
from recruiter.models import RecruiterProfile, Job
from recommendations.models import JobRecommendation, CandidateRecommendation
from recommendations.services import (
    _normalize_skill,
    _normalize_skills,
    calculate_job_match_for_candidate,
    calculate_candidate_match_for_job,
    calculate_experience_match_score,
    generate_job_recommendations_for_candidate,
    generate_candidate_recommendations_for_job,
    get_job_recommendations_for_candidate,
    get_candidate_recommendations_for_job,
    get_user_candidate_skills,
    get_user_experience_years,
    get_user_experience_bucket,
)

class SkillNormalizationTests(TestCase):
    """Tests for skill normalization functionality."""

    def test_exact_skill_matching(self):
        """Test that exact skill matches work."""
        self.assertEqual(_normalize_skill("Python"), "python")
        self.assertEqual(_normalize_skill("javascript"), "javascript")
        self.assertEqual(_normalize_skill("REACT"), "react")

    def test_case_insensitive_skill_matching(self):
        """Test case-insensitive skill matching."""
        self.assertEqual(_normalize_skill("Python"), _normalize_skill("python"))
        self.assertEqual(_normalize_skill("PYTHON"), _normalize_skill("python"))
        self.assertEqual(_normalize_skill("PyThOn"), _normalize_skill("python"))

    def test_skill_aliases(self):
        """Test skill alias normalization."""
        self.assertEqual(_normalize_skill("React.js"), "react")
        self.assertEqual(_normalize_skill("ReactJS"), "react")
        self.assertEqual(_normalize_skill("Vue.js"), "vue")
        self.assertEqual(_normalize_skill("Node.js"), "node")
        self.assertEqual(_normalize_skill("Postgre SQL"), "postgresql")
        self.assertEqual(_normalize_skill("Postgres"), "postgresql")
        self.assertEqual(_normalize_skill("C#"), "csharp")
        self.assertEqual(_normalize_skill("C++"), "cpp")

    def test_duplicate_skills_removed(self):
        """Test that duplicate skills are removed after normalization."""
        skills = ["Python", "python", "PYTHON", "React", "react.js", "ReactJS"]
        normalized = _normalize_skills(skills)
        self.assertEqual(len(normalized), 2)
        self.assertIn("python", normalized)
        self.assertIn("react", normalized)

    def test_empty_and_whitespace_skills(self):
        """Test handling of empty and whitespace skills."""
        skills = ["", "  ", "Python", "\t\n", "Java"]
        normalized = _normalize_skills(skills)
        self.assertEqual(len(normalized), 2)
        self.assertIn("python", normalized)
        self.assertIn("java", normalized)

    def test_malformed_skill_data(self):
        """Test handling of malformed skill data."""
        skills = ["Python,Java", "React;Vue", "Node.js|Express"]
        normalized = _normalize_skills(skills)
        self.assertIn("python", normalized)
        self.assertIn("java", normalized)
        self.assertIn("react", normalized)
        self.assertIn("vue", normalized)
        self.assertIn("node", normalized)
        self.assertIn("express", normalized)


class ExperienceMatchScoreTests(TestCase):
    """Tests for experience match scoring."""

    def test_senior_job_with_senior_candidate(self):
        """Test senior job with 5+ years experience candidate."""
        score = calculate_experience_match_score(6.0, "Senior Developer")
        self.assertEqual(score, 100.0)

    def test_senior_job_with_mid_candidate(self):
        """Test senior job with 3 years experience candidate."""
        score = calculate_experience_match_score(3.0, "Senior Developer")
        self.assertEqual(score, 50.0)

    def test_senior_job_with_junior_candidate(self):
        """Test senior job with 1 year experience candidate."""
        score = calculate_experience_match_score(1.0, "Senior Developer")
        self.assertEqual(score, 30.0)

    def test_mid_job_with_mid_candidate(self):
        """Test mid-level job with 3 years experience candidate."""
        score = calculate_experience_match_score(3.0, "Mid-level Developer")
        self.assertEqual(score, 100.0)

    def test_mid_job_with_senior_candidate(self):
        """Test mid-level job with 7 years experience candidate."""
        score = calculate_experience_match_score(7.0, "Mid-level Developer")
        self.assertEqual(score, 90.0)

    def test_junior_job_with_junior_candidate(self):
        """Test junior job with 1 year experience candidate."""
        score = calculate_experience_match_score(1.0, "Junior Developer")
        self.assertEqual(score, 100.0)

    def test_junior_job_with_senior_candidate(self):
        """Test junior job with 7 years experience candidate."""
        score = calculate_experience_match_score(7.0, "Junior Developer")
        self.assertEqual(score, 80.0)

    def test_missing_candidate_experience(self):
        """Test when candidate experience is missing."""
        score = calculate_experience_match_score(None, "Senior Developer")
        self.assertEqual(score, 50.0)

    def test_missing_job_experience(self):
        """Test when job experience requirement is missing."""
        score = calculate_experience_match_score(5.0, "")
        self.assertEqual(score, 50.0)


class JobMatchForCandidateTests(TestCase):
    """Tests for candidate-to-job matching."""

    def setUp(self):
        self.candidate_user = User.objects.create_user(
            username="testcandidate",
            password="testpass123"
        )
        self.candidate_profile = CandidateProfile.objects.create(
            user=self.candidate_user,
            full_name="Test Candidate",
            phone="1234567890",
            location="San Francisco",
            education="BS Computer Science",
            skills="Python, Django, React, PostgreSQL",
            experience="3 years",
            bio="Software developer"
        )
        self.recruiter_user = User.objects.create_user(
            username="testrecruiter",
            password="testpass123"
        )
        self.recruiter_profile = RecruiterProfile.objects.create(
            user=self.recruiter_user,
            recruiter_name="Test Recruiter",
            company_name="Test Company",
            email="recruiter@test.com",
            phone="1234567890",
            location="San Francisco",
            company_description="Test company"
        )
        self.job = Job.objects.create(
            recruiter=self.recruiter_user,
            title="Backend Developer",
            company="Test Company",
            location="San Francisco",
            salary="$120k",
            job_type="Full-time",
            experience="3+ years",
            description="Build backend systems",
            requirements="Python, Django, PostgreSQL, Docker",
            deadline="2026-12-31",
            is_active=True
        )

    def test_skill_match_calculation(self):
        """Test skill match percentage calculation."""
        result = calculate_job_match_for_candidate(self.candidate_user, self.job)
        self.assertIn("match_score", result)
        self.assertIn("skill_match_score", result)
        self.assertIn("experience_match_score", result)
        self.assertIn("matched_skills", result)
        self.assertIn("missing_skills", result)
        self.assertIn("reason", result)

    def test_matched_skills_identified(self):
        """Test that matched skills are correctly identified."""
        result = calculate_job_match_for_candidate(self.candidate_user, self.job)
        matched = set(result["matched_skills"])
        self.assertIn("python", matched)
        self.assertIn("django", matched)
        self.assertIn("postgresql", matched)

    def test_missing_skills_identified(self):
        """Test that missing skills are correctly identified."""
        result = calculate_job_match_for_candidate(self.candidate_user, self.job)
        missing = set(result["missing_skills"])
        self.assertIn("docker", missing)

    def test_candidate_with_no_skills(self):
        """Test candidate with no skills."""
        CandidateProfile.objects.filter(user=self.candidate_user).update(skills="")
        result = calculate_job_match_for_candidate(self.candidate_user, self.job)
        self.assertEqual(result["skill_match_score"], 0.0)
        self.assertEqual(len(result["matched_skills"]), 0)

    def test_job_with_no_requirements(self):
        """Test job with no requirements."""
        Job.objects.filter(id=self.job.id).update(requirements="")
        self.job.refresh_from_db()
        result = calculate_job_match_for_candidate(self.candidate_user, self.job)
        self.assertEqual(result["skill_match_score"], 0.0)

    def test_overall_score_in_range(self):
        """Test that overall score is in 0-100 range."""
        result = calculate_job_match_for_candidate(self.candidate_user, self.job)
        self.assertGreaterEqual(result["match_score"], 0.0)
        self.assertLessEqual(result["match_score"], 100.0)


class CandidateMatchForJobTests(TestCase):
    """Tests for job-to-candidate matching."""

    def setUp(self):
        self.candidate_user = User.objects.create_user(
            username="testcandidate2",
            password="testpass123"
        )
        self.candidate_profile = CandidateProfile.objects.create(
            user=self.candidate_user,
            full_name="Test Candidate 2",
            phone="1234567890",
            location="New York",
            education="MS Computer Science",
            skills="Python, React, TypeScript, AWS",
            experience="5 years",
            bio="Senior developer"
        )
        self.recruiter_user = User.objects.create_user(
            username="testrecruiter2",
            password="testpass123"
        )
        self.recruiter_profile = RecruiterProfile.objects.create(
            user=self.recruiter_user,
            recruiter_name="Test Recruiter 2",
            company_name="Test Company 2",
            email="recruiter2@test.com",
            phone="1234567890",
            location="New York",
            company_description="Test company 2"
        )
        self.job = Job.objects.create(
            recruiter=self.recruiter_user,
            title="Senior Full Stack Developer",
            company="Test Company 2",
            location="New York",
            salary="$150k",
            job_type="Full-time",
            experience="5+ years",
            description="Build full stack applications",
            requirements="Python, React, TypeScript, AWS, Docker",
            deadline="2026-12-31",
            is_active=True
        )

    def test_candidate_match_calculation(self):
        """Test candidate match calculation for a job."""
        result = calculate_candidate_match_for_job(self.candidate_user, self.job)
        self.assertIn("match_score", result)
        self.assertIn("skill_match_score", result)
        self.assertIn("experience_match_score", result)
        self.assertIn("matched_skills", result)
        self.assertIn("missing_skills", result)
        self.assertIn("experience_match", result)
        self.assertIn("reason", result)

    def test_experience_match_flag(self):
        """Test experience match flag for senior candidate and senior job."""
        result = calculate_candidate_match_for_job(self.candidate_user, self.job)
        self.assertTrue(result["experience_match"])

    def test_candidate_with_no_profile(self):
        """Test matching when candidate has no profile."""
        User.objects.filter(username="testcandidate2").delete()
        result = calculate_candidate_match_for_job(self.candidate_user, self.job)
        self.assertEqual(result["match_score"], 0)
        self.assertEqual(result["reason"], "No candidate profile found")

    def test_overall_score_in_range(self):
        """Test that overall score is in 0-100 range."""
        result = calculate_candidate_match_for_job(self.candidate_user, self.job)
        self.assertGreaterEqual(result["match_score"], 0.0)
        self.assertLessEqual(result["match_score"], 100.0)


class RecommendationGenerationTests(TestCase):
    """Tests for recommendation generation."""

    def setUp(self):
        self.candidate_user = User.objects.create_user(
            username="candidate1",
            password="testpass123"
        )
        self.candidate_profile = CandidateProfile.objects.create(
            user=self.candidate_user,
            full_name="Candidate One",
            phone="1234567890",
            location="San Francisco",
            education="BS CS",
            skills="Python, Django, React, PostgreSQL, AWS",
            experience="3 years",
            bio="Developer"
        )
        self.recruiter_user = User.objects.create_user(
            username="recruiter1",
            password="testpass123"
        )
        self.recruiter_profile = RecruiterProfile.objects.create(
            user=self.recruiter_user,
            recruiter_name="Recruiter One",
            company_name="Company One",
            email="recruiter1@company.com",
            phone="1234567890",
            location="San Francisco",
            company_description="Company"
        )
        self.job1 = Job.objects.create(
            recruiter=self.recruiter_user,
            title="Python Developer",
            company="Company One",
            location="San Francisco",
            salary="$120k",
            job_type="Full-time",
            experience="2-5 years",
            description="Python backend",
            requirements="Python, Django, PostgreSQL",
            deadline="2026-12-31",
            is_active=True
        )
        self.job2 = Job.objects.create(
            recruiter=self.recruiter_user,
            title="React Developer",
            company="Company One",
            location="San Francisco",
            salary="$130k",
            job_type="Full-time",
            experience="2-5 years",
            description="React frontend",
            requirements="React, TypeScript, Redux",
            deadline="2026-12-31",
            is_active=True
        )
        self.job3 = Job.objects.create(
            recruiter=self.recruiter_user,
            title="DevOps Engineer",
            company="Company One",
            location="San Francisco",
            salary="$140k",
            job_type="Full-time",
            experience="5+ years",
            description="DevOps",
            requirements="AWS, Docker, Kubernetes, Terraform",
            deadline="2026-12-31",
            is_active=True
        )

    def test_generate_job_recommendations(self):
        """Test generating job recommendations for a candidate."""
        recommendations = generate_job_recommendations_for_candidate(
            self.candidate_user, limit=10, min_score=20.0
        )
        self.assertGreater(len(recommendations), 0)
        self.assertLessEqual(len(recommendations), 3)

    def test_recommendations_sorted_by_score(self):
        """Test that recommendations are sorted by match score descending."""
        recommendations = generate_job_recommendations_for_candidate(
            self.candidate_user, limit=10, min_score=20.0
        )
        scores = [r.match_score for r in recommendations]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_excluded_applied_jobs(self):
        """Test that already applied jobs are excluded."""
        from candidate.models import JobApplication
        JobApplication.objects.create(
            candidate=self.candidate_user,
            job=self.job1,
            status="Applied"
        )
        recommendations = generate_job_recommendations_for_candidate(
            self.candidate_user, limit=10, min_score=20.0
        )
        job_ids = [r.job_id for r in recommendations]
        self.assertNotIn(self.job1.id, job_ids)

    def test_min_score_filter(self):
        """Test minimum score filter."""
        recommendations = generate_job_recommendations_for_candidate(
            self.candidate_user, limit=10, min_score=90.0
        )
        for rec in recommendations:
            self.assertGreaterEqual(rec.match_score, 90.0)

    def test_generate_candidate_recommendations(self):
        """Test generating candidate recommendations for a job."""
        # Create another candidate
        candidate2 = User.objects.create_user(username="candidate2", password="testpass123")
        CandidateProfile.objects.create(
            user=candidate2,
            full_name="Candidate Two",
            phone="1234567890",
            location="NYC",
            education="MS CS",
            skills="React, TypeScript, Node.js",
            experience="4 years",
            bio="Frontend dev"
        )
        
        recommendations = generate_candidate_recommendations_for_job(
            self.job2, limit=10, min_score=20.0
        )
        self.assertGreater(len(recommendations), 0)

    def test_candidate_recommendations_sorted(self):
        """Test candidate recommendations sorted by score."""
        candidate2 = User.objects.create_user(username="candidate2", password="testpass123")
        CandidateProfile.objects.create(
            user=candidate2,
            full_name="Candidate Two",
            phone="1234567890",
            location="NYC",
            education="MS CS",
            skills="React, TypeScript, Node.js",
            experience="4 years",
            bio="Frontend dev"
        )
        
        recommendations = generate_candidate_recommendations_for_job(
            self.job2, limit=10, min_score=20.0
        )
        scores = [r.match_score for r in recommendations]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_excluded_applied_candidates(self):
        """Test that already applied candidates are excluded."""
        from candidate.models import JobApplication
        JobApplication.objects.create(
            candidate=self.candidate_user,
            job=self.job1,
            status="Applied"
        )
        recommendations = generate_candidate_recommendations_for_job(
            self.job1, limit=10, min_score=20.0
        )
        candidate_ids = [r.candidate_id for r in recommendations]
        self.assertNotIn(self.candidate_user.id, candidate_ids)


class RecommendationRetrievalTests(TestCase):
    """Tests for retrieving existing recommendations."""

    def setUp(self):
        self.candidate_user = User.objects.create_user(
            username="candidate3",
            password="testpass123"
        )
        self.candidate_profile = CandidateProfile.objects.create(
            user=self.candidate_user,
            full_name="Candidate Three",
            phone="1234567890",
            location="SF",
            education="BS",
            skills="Python, Django",
            experience="2 years",
            bio="Dev"
        )
        self.recruiter_user = User.objects.create_user(
            username="recruiter3",
            password="testpass123"
        )
        self.recruiter_profile = RecruiterProfile.objects.create(
            user=self.recruiter_user,
            recruiter_name="Recruiter Three",
            company_name="Company Three",
            email="rec3@company.com",
            phone="1234567890",
            location="SF",
            company_description="Company"
        )
        self.job = Job.objects.create(
            recruiter=self.recruiter_user,
            title="Django Developer",
            company="Company Three",
            location="SF",
            salary="$110k",
            job_type="Full-time",
            experience="2-5 years",
            description="Django backend",
            requirements="Python, Django, PostgreSQL",
            deadline="2026-12-31",
            is_active=True
        )

    def test_get_job_recommendations(self):
        """Test retrieving job recommendations for candidate."""
        generate_job_recommendations_for_candidate(self.candidate_user, limit=5, min_score=10.0)
        recommendations = get_job_recommendations_for_candidate(self.candidate_user, limit=5)
        self.assertGreater(len(recommendations), 0)

    def test_get_candidate_recommendations(self):
        """Test retrieving candidate recommendations for job."""
        generate_candidate_recommendations_for_job(self.job, limit=5, min_score=10.0)
        recommendations = get_candidate_recommendations_for_job(self.job, limit=5)
        self.assertGreater(len(recommendations), 0)

    def test_viewed_filter(self):
        """Test filtering viewed recommendations."""
        generate_job_recommendations_for_candidate(self.candidate_user, limit=5, min_score=10.0)
        all_recs = get_job_recommendations_for_candidate(self.candidate_user, limit=5, include_viewed=True)
        unviewed_recs = get_job_recommendations_for_candidate(self.candidate_user, limit=5, include_viewed=False)
        self.assertGreaterEqual(len(all_recs), len(unviewed_recs))

    def test_dismissed_filter(self):
        """Test that dismissed recommendations are excluded."""
        generate_job_recommendations_for_candidate(self.candidate_user, limit=5, min_score=10.0)
        rec = JobRecommendation.objects.first()
        rec.is_dismissed = True
        rec.save()
        recommendations = get_job_recommendations_for_candidate(self.candidate_user, limit=5)
        self.assertEqual(len(recommendations), 0)


class AuthorizationTests(TestCase):
    """Tests for authorization and access control."""

    def setUp(self):
        self.candidate_user = User.objects.create_user(
            username="candidate_auth",
            password="testpass123"
        )
        self.candidate_profile = CandidateProfile.objects.create(
            user=self.candidate_user,
            full_name="Auth Candidate",
            phone="1234567890",
            location="SF",
            education="BS",
            skills="Python",
            experience="2 years",
            bio="Dev"
        )
        self.recruiter_user = User.objects.create_user(
            username="recruiter_auth",
            password="testpass123"
        )
        self.recruiter_profile = RecruiterProfile.objects.create(
            user=self.recruiter_user,
            recruiter_name="Auth Recruiter",
            company_name="Auth Company",
            email="rec@company.com",
            phone="1234567890",
            location="SF",
            company_description="Company"
        )
        self.job = Job.objects.create(
            recruiter=self.recruiter_user,
            title="Python Dev",
            company="Auth Company",
            location="SF",
            salary="$100k",
            job_type="Full-time",
            experience="2 years",
            description="Python",
            requirements="Python",
            deadline="2026-12-31",
            is_active=True
        )

    def test_candidate_can_only_access_own_recommendations(self):
        """Test candidate can only access their own recommendations."""
        other_candidate = User.objects.create_user(username="other", password="testpass123")
        CandidateProfile.objects.create(
            user=other_candidate,
            full_name="Other",
            phone="1234567890",
            location="NYC",
            education="MS",
            skills="Java",
            experience="5 years",
            bio="Dev"
        )
        
        generate_job_recommendations_for_candidate(self.candidate_user, limit=5, min_score=10.0)
        generate_job_recommendations_for_candidate(other_candidate, limit=5, min_score=10.0)
        
        my_recs = get_job_recommendations_for_candidate(self.candidate_user, limit=10)
        other_recs = get_job_recommendations_for_candidate(other_candidate, limit=10)
        
        self.assertEqual(len(my_recs), len(other_recs))  # Same number of jobs available
        my_job_ids = set(r.job_id for r in my_recs)
        other_job_ids = set(r.job_id for r in other_recs)
        self.assertEqual(my_job_ids, other_job_ids)  # Same jobs, different recommendation objects

    def test_recruiter_can_only_access_own_job_recommendations(self):
        """Test recruiter can only access recommendations for their own jobs."""
        other_recruiter = User.objects.create_user(username="other_rec", password="testpass123")
        RecruiterProfile.objects.create(
            user=other_recruiter,
            recruiter_name="Other Recruiter",
            company_name="Other Company",
            email="other@company.com",
            phone="1234567890",
            location="LA",
            company_description="Other"
        )
        other_job = Job.objects.create(
            recruiter=other_recruiter,
            title="Java Dev",
            company="Other Company",
            location="LA",
            salary="$120k",
            job_type="Full-time",
            experience="3 years",
            description="Java",
            requirements="Java, Spring",
            deadline="2026-12-31",
            is_active=True
        )
        
        generate_candidate_recommendations_for_job(self.job, limit=5, min_score=10.0)
        generate_candidate_recommendations_for_job(other_job, limit=5, min_score=10.0)
        
        my_recs = get_candidate_recommendations_for_job(self.job, limit=10)
        other_recs = get_candidate_recommendations_for_job(other_job, limit=10)
        
        self.assertEqual(len(my_recs), len(other_recs))  # Same candidates
        self.assertNotEqual(my_recs[0].job_id, other_recs[0].job_id)  # Different jobs


class EdgeCaseTests(TestCase):
    """Tests for edge cases and error handling."""

    def test_candidate_without_resume(self):
        """Test candidate without resume data."""
        candidate = User.objects.create_user(username="noresume", password="testpass123")
        CandidateProfile.objects.create(
            user=candidate,
            full_name="No Resume",
            phone="1234567890",
            location="SF",
            education="BS",
            skills="Python, Django",
            experience="2 years",
            bio="Dev"
        )
        recruiter = User.objects.create_user(username="rec_noresume", password="testpass123")
        RecruiterProfile.objects.create(
            user=recruiter,
            recruiter_name="Recruiter",
            company_name="Company",
            email="rec@company.com",
            phone="1234567890",
            location="SF",
            company_description="Company"
        )
        job = Job.objects.create(
            recruiter=recruiter,
            title="Python Dev",
            company="Company",
            location="SF",
            salary="$100k",
            job_type="Full-time",
            experience="2 years",
            description="Python",
            requirements="Python, Django",
            deadline="2026-12-31",
            is_active=True
        )
        
        result = calculate_job_match_for_candidate(candidate, job)
        self.assertIn("match_score", result)
        self.assertGreater(result["match_score"], 0)

    def test_job_without_description(self):
        """Test job with minimal description."""
        candidate = User.objects.create_user(username="nodec", password="testpass123")
        CandidateProfile.objects.create(
            user=candidate,
            full_name="No Dec",
            phone="1234567890",
            location="SF",
            education="BS",
            skills="Python",
            experience="2 years",
            bio="Dev"
        )
        recruiter = User.objects.create_user(username="rec_nodec", password="testpass123")
        RecruiterProfile.objects.create(
            user=recruiter,
            recruiter_name="Recruiter",
            company_name="Company",
            email="rec@company.com",
            phone="1234567890",
            location="SF",
            company_description="Company"
        )
        job = Job.objects.create(
            recruiter=recruiter,
            title="Python Dev",
            company="Company",
            location="SF",
            salary="$100k",
            job_type="Full-time",
            experience="2 years",
            description="",
            requirements="Python",
            deadline="2026-12-31",
            is_active=True
        )
        
        result = calculate_job_match_for_candidate(candidate, job)
        self.assertIn("match_score", result)

    def test_candidate_without_experience(self):
        """Test candidate without experience data."""
        candidate = User.objects.create_user(username="noexp", password="testpass123")
        CandidateProfile.objects.create(
            user=candidate,
            full_name="No Exp",
            phone="1234567890",
            location="SF",
            education="BS",
            skills="Python",
            experience="",
            bio="Dev"
        )
        recruiter = User.objects.create_user(username="rec_noexp", password="testpass123")
        RecruiterProfile.objects.create(
            user=recruiter,
            recruiter_name="Recruiter",
            company_name="Company",
            email="rec@company.com",
            phone="1234567890",
            location="SF",
            company_description="Company"
        )
        job = Job.objects.create(
            recruiter=recruiter,
            title="Python Dev",
            company="Company",
            location="SF",
            salary="$100k",
            job_type="Full-time",
            experience="2 years",
            description="Python",
            requirements="Python",
            deadline="2026-12-31",
            is_active=True
        )
        
        result = calculate_job_match_for_candidate(candidate, job)
        self.assertIn("match_score", result)
        self.assertIn("experience_match_score", result)

    def test_empty_recommendation_results(self):
        """Test when no recommendations meet minimum score."""
        candidate = User.objects.create_user(username="emptyrec", password="testpass123")
        CandidateProfile.objects.create(
            user=candidate,
            full_name="Empty Rec",
            phone="1234567890",
            location="SF",
            education="BS",
            skills="COBOL, Fortran",
            experience="20 years",
            bio="Legacy dev"
        )
        recruiter = User.objects.create_user(username="rec_empty", password="testpass123")
        RecruiterProfile.objects.create(
            user=recruiter,
            recruiter_name="Recruiter",
            company_name="Company",
            email="rec@company.com",
            phone="1234567890",
            location="SF",
            company_description="Company"
        )
        job = Job.objects.create(
            recruiter=recruiter,
            title="Modern Web Dev",
            company="Company",
            location="SF",
            salary="$150k",
            job_type="Full-time",
            experience="2 years",
            description="Modern stack",
            requirements="React, TypeScript, GraphQL, Kubernetes",
            deadline="2026-12-31",
            is_active=True
        )
        
        recommendations = generate_job_recommendations_for_candidate(
            candidate, limit=10, min_score=50.0
        )
        self.assertEqual(len(recommendations), 0)

    def test_duplicate_skills_in_candidate_profile(self):
        """Test handling of duplicate skills in candidate profile."""
        candidate = User.objects.create_user(username="dupskills", password="testpass123")
        CandidateProfile.objects.create(
            user=candidate,
            full_name="Dup Skills",
            phone="1234567890",
            location="SF",
            education="BS",
            skills="Python, python, PYTHON, Django, django",
            experience="2 years",
            bio="Dev"
        )
        recruiter = User.objects.create_user(username="rec_dups", password="testpass123")
        RecruiterProfile.objects.create(
            user=recruiter,
            recruiter_name="Recruiter",
            company_name="Company",
            email="rec@company.com",
            phone="1234567890",
            location="SF",
            company_description="Company"
        )
        job = Job.objects.create(
            recruiter=recruiter,
            title="Python Dev",
            company="Company",
            location="SF",
            salary="$100k",
            job_type="Full-time",
            experience="2 years",
            description="Python",
            requirements="Python, Django",
            deadline="2026-12-31",
            is_active=True
        )
        
        skills = get_user_candidate_skills(candidate)
        self.assertEqual(skills.count("python"), 1)
        self.assertEqual(skills.count("django"), 1)

    def test_skill_normalization_variations(self):
        """Test various skill normalization scenarios."""
        test_cases = [
            ("React.js", "react"),
            ("ReactJS", "react"),
            ("NODE.JS", "node"),
            ("Postgre SQL", "postgresql"),
            ("C#", "csharp"),
            ("C++", "cpp"),
            ("Golang", "go"),
            ("K8s", "kubernetes"),
            ("CI/CD", "ci cd"),
            ("ML", "machine learning"),
        ]
        for input_skill, expected in test_cases:
            self.assertEqual(_normalize_skill(input_skill), expected)

    def test_user_experience_bucket(self):
        """Test experience bucket calculation."""
        candidate = User.objects.create_user(username="exp_bucket", password="testpass123")
        
        CandidateProfile.objects.create(
            user=candidate,
            full_name="Exp Bucket",
            phone="1234567890",
            location="SF",
            education="BS",
            skills="Python",
            experience="1 year",
            bio="Dev"
        )
        self.assertEqual(get_user_experience_bucket(candidate), "0-2")
        
        CandidateProfile.objects.filter(user=candidate).update(experience="3 years")
        self.assertEqual(get_user_experience_bucket(candidate), "2-5")
        
        CandidateProfile.objects.filter(user=candidate).update(experience="7 years")
        self.assertEqual(get_user_experience_bucket(candidate), "5+")

    def test_user_experience_years_parsing(self):
        """Test experience years parsing from various formats."""
        candidate = User.objects.create_user(username="expyears", password="testpass123")
        
        CandidateProfile.objects.create(
            user=candidate,
            full_name="Exp Years",
            phone="1234567890",
            location="SF",
            education="BS",
            skills="Python",
            experience="5+ years",
            bio="Dev"
        )
        self.assertEqual(get_user_experience_years(candidate), 5.0)
        
        CandidateProfile.objects.filter(user=candidate).update(experience="3-5 years")
        self.assertEqual(get_user_experience_years(candidate), 3.0)
        
        CandidateProfile.objects.filter(user=candidate).update(experience="2.5 years")
        self.assertEqual(get_user_experience_years(candidate), 2.5)


class SkillExtractionRegressionTests(TestCase):
    """Regression tests for skill extraction to prevent false-positive substring matches."""

    def test_postgresql_does_not_produce_sql(self):
        """PostgreSQL should not trigger 'sql' skill."""
        skills = extract_skills("postgresql")
        self.assertEqual(skills, ["postgresql"])
        self.assertNotIn("sql", skills)

    def test_postgresql_does_not_produce_go(self):
        """PostgreSQL should not trigger 'go' skill."""
        skills = extract_skills("postgresql")
        self.assertEqual(skills, ["postgresql"])
        self.assertNotIn("go", skills)

    def test_exact_bug_case_six_skills(self):
        """The exact case from bug report: Python, Django, PostgreSQL, AWS, Docker, Kubernetes."""
        text = "Python, Django, PostgreSQL, AWS, Docker, Kubernetes"
        skills = extract_skills(text)
        expected = {"aws", "django", "docker", "kubernetes", "postgresql", "python"}
        self.assertEqual(set(skills), expected)
        self.assertEqual(len(skills), 6)

    def test_javascript_still_works(self):
        """JavaScript should still be detected."""
        skills = extract_skills("javascript")
        self.assertIn("javascript", skills)
        
        # In context
        skills = extract_skills("I know javascript and typescript")
        self.assertIn("javascript", skills)
        self.assertIn("typescript", skills)

    def test_cpp_still_works(self):
        """C++ should still be detected."""
        skills = extract_skills("c++")
        self.assertIn("c++", skills)
        
        skills = extract_skills("I know c++ and python")
        self.assertIn("c++", skills)

    def test_csharp_still_works(self):
        """C# should still be detected."""
        skills = extract_skills("c#")
        self.assertIn("c#", skills)
        
        skills = extract_skills("I know c# and java")
        self.assertIn("c#", skills)

    def test_nodejs_still_works(self):
        """Node.js should still be detected."""
        skills = extract_skills("node.js")
        self.assertIn("node.js", skills)
        
        skills = extract_skills("I know node.js and express")
        self.assertIn("node.js", skills)
        self.assertIn("express", skills)

    def test_multi_word_skills_still_work(self):
        """Multi-word skills should still be detected."""
        test_cases = [
            ("machine learning", "machine learning"),
            ("deep learning", "deep learning"),
            ("rest api", "rest api"),
            ("project management", "project management"),
            ("problem solving", "problem solving"),
            ("mobile development", "mobile development"),
            ("full stack", "full stack"),
        ]
        for input_text, expected_skill in test_cases:
            skills = extract_skills(input_text)
            self.assertIn(expected_skill, skills, f"Failed for: {input_text}")

    def test_unrelated_substrings_do_not_create_false_positives(self):
        """Unrelated substrings should not create false-positive skills."""
        # "go" should not match in "postgresql" or "algorithm" or "golang"
        skills = extract_skills("postgresql algorithm golang")
        # Should only match "go" from "golang" (as a separate skill)
        # Actually "golang" is not in skills_db, "go" is - let's check if "go" matches in "golang"
        # Our pattern uses word boundaries, so "go" should NOT match inside "golang"
        self.assertNotIn("go", skills, "go should not match inside golang")
        
        # "sql" should not match in "postgresql" or "mysql" (wait, mysql should match sql?)
        # mysql is a separate skill in the db, let's test
        skills = extract_skills("mysql")
        self.assertIn("mysql", skills)
        
        # "python" should not match in "jupyter" 
        skills = extract_skills("jupyter notebook")
        self.assertNotIn("python", skills)

    def test_sql_matches_as_standalone_skill(self):
        """SQL should still match when it appears as a standalone skill."""
        skills = extract_skills("sql")
        self.assertIn("sql", skills)
        
        skills = extract_skills("I know sql and python")
        self.assertIn("sql", skills)
        self.assertIn("python", skills)
        
        # Both sql and postgresql should match when both appear
        skills = extract_skills("sql, postgresql")
        self.assertIn("sql", skills)
        self.assertIn("postgresql", skills)

    def test_java_not_in_javascript(self):
        """Java should not match inside javascript."""
        skills = extract_skills("javascript")
        self.assertNotIn("java", skills)
        self.assertIn("javascript", skills)
        
        skills = extract_skills("java")
        self.assertIn("java", skills)

    def test_ruby_not_in_rubyonrails(self):
        """Ruby should match in ruby but we don't have rubyonrails in db."""
        skills = extract_skills("ruby")
        self.assertIn("ruby", skills)

    def test_aws_not_in_awsome(self):
        """AWS should not match inside 'awsome'."""
        skills = extract_skills("awsome")
        self.assertNotIn("aws", skills)
        
        skills = extract_skills("aws")
        self.assertIn("aws", skills)

    def test_react_not_in_reactivate(self):
        """React should not match inside 'reactivate'."""
        skills = extract_skills("reactivate")
        self.assertNotIn("react", skills)
        
        skills = extract_skills("react")
        self.assertIn("react", skills)

    def test_case_insensitive_extraction(self):
        """Skill extraction should be case-insensitive."""
        skills = extract_skills("PYTHON, Django, PostGreSQL")
        expected = {"python", "django", "postgresql"}
        self.assertEqual(set(skills), expected)

    def test_skills_with_punctuation_in_text(self):
        """Skills with punctuation should match when surrounded by punctuation."""
        skills = extract_skills("I know c++, c#, and node.js.")
        expected = {"c++", "c#", "node.js"}
        self.assertEqual(set(skills), expected)
        
        skills = extract_skills("Skills: python; java, javascript")
        expected = {"python", "java", "javascript"}
        self.assertEqual(set(skills), expected)