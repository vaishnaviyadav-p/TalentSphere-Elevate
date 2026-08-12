import re

from candidate.skill_matching import (
    calculate_skill_match,
    extract_required_skills,
)


def _split_skills(raw_skills):
    if not raw_skills:
        return []

    if isinstance(raw_skills, (list, tuple, set)):
        values = raw_skills
    else:
        values = re.split(r"[,;\n/|]+", str(raw_skills))

    parsed = []

    for value in values:
        if isinstance(value, dict):
            value = value.get("skill") or value.get("name") or value.get("value")

        value = str(value).strip()

        if value:
            parsed.append(value)

    return parsed


def _normalize_skill(skill):
    return re.sub(r"\s+", " ", str(skill)).strip().lower()


def get_candidate_skills(candidate_profile=None, resume_data=None):
    skills = []

    if candidate_profile and candidate_profile.skills:
        skills.extend(_split_skills(candidate_profile.skills))

    if resume_data and resume_data.parsed_skills:
        skills.extend(_split_skills(resume_data.parsed_skills))

    unique_skills = {}

    for skill in skills:
        normalized = _normalize_skill(skill)

        if normalized and normalized not in unique_skills:
            unique_skills[normalized] = skill.strip()

    return list(unique_skills.values())


def get_candidate_experience_text(candidate_profile=None, resume_data=None):
    if candidate_profile and candidate_profile.experience:
        return str(candidate_profile.experience).strip()

    if resume_data and resume_data.parsed_experience:
        if isinstance(resume_data.parsed_experience, (list, tuple, set)):
            return ", ".join(
                str(item).strip()
                for item in resume_data.parsed_experience
                if str(item).strip()
            )

        return ", ".join(
            part.strip()
            for part in str(resume_data.parsed_experience).split(",")
            if part.strip()
        )

    return ""


def parse_experience_years(experience_text):
    if not experience_text:
        return None

    text = str(experience_text).lower()

    patterns = [
        r"(\d+(?:\.\d+)?)\s*\+\s*years?",
        r"(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)\s*years?",
        r"(\d+(?:\.\d+)?)\s*(?:to)\s*(\d+(?:\.\d+)?)\s*years?",
        r"(\d+(?:\.\d+)?)\s*years?",
        r"(\d+(?:\.\d+)?)\s*yrs?",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if not match:
            continue

        if len(match.groups()) >= 2 and match.group(2):
            return float(match.group(1))

        return float(match.group(1))

    return None


def get_experience_bucket(experience_years):
    if experience_years is None:
        return None

    if experience_years < 2:
        return "0-2"

    if experience_years < 5:
        return "2-5"

    return "5+"


def format_score(score):
    if score is None:
        return "0%"

    if float(score).is_integer():
        return f"{int(score)}%"

    return f"{round(float(score), 1)}%"


def get_candidate_name(application, candidate_profile=None):
    if candidate_profile and candidate_profile.full_name:
        return candidate_profile.full_name.strip()

    full_name = application.candidate.get_full_name()

    if full_name:
        return full_name.strip()

    return getattr(application.candidate, "username", "Unknown Candidate")


def calculate_priority_score(candidate_profile, job, resume_data=None):
    """
    Calculate a candidate's ATS priority score for a job using the
    existing skill matching logic.
    """

    candidate_skills = get_candidate_skills(candidate_profile, resume_data)
    required_skills = extract_required_skills(job.requirements)

    result = calculate_skill_match(candidate_skills, required_skills)

    return {
        "score": result["score"],
        "score_display": format_score(result["score"]),
        "matched_skills": result["matched_skills"],
        "missing_skills": result["missing_skills"],
        "candidate_skills": candidate_skills,
        "required_skills": required_skills,
    }


def collect_available_skills(applications):
    skills = {}

    for application in applications:
        candidate_profile = None

        try:
            candidate_profile = application.candidate.candidateprofile
        except Exception:
            candidate_profile = None

        resume_data = None

        if candidate_profile is not None:
            try:
                resume_data = candidate_profile.resume_data
            except Exception:
                resume_data = None

        for skill in get_candidate_skills(candidate_profile, resume_data):
            normalized = _normalize_skill(skill)

            if normalized and normalized not in skills:
                skills[normalized] = skill.strip()

        for skill in extract_required_skills(application.job.requirements):
            normalized = _normalize_skill(skill)

            if normalized and normalized not in skills:
                skills[normalized] = skill.strip()

    return sorted(skills.values(), key=lambda value: value.lower())


def build_priority_candidate_rows(applications):
    rows = []

    for application in applications:
        candidate_profile = None
        resume_data = None

        try:
            candidate_profile = application.candidate.candidateprofile
        except Exception:
            candidate_profile = None

        if candidate_profile is not None:
            try:
                resume_data = candidate_profile.resume_data
            except Exception:
                resume_data = None

        priority = calculate_priority_score(
            candidate_profile,
            application.job,
            resume_data,
        )

        candidate_skills = priority["candidate_skills"]
        experience_text = get_candidate_experience_text(candidate_profile, resume_data)
        experience_years = parse_experience_years(experience_text)

        rows.append({
            "application": application,
            "candidate_name": get_candidate_name(application, candidate_profile),
            "candidate_skills": candidate_skills,
            "candidate_skills_key": {
                _normalize_skill(skill)
                for skill in candidate_skills
            },
            "candidate_experience": experience_text,
            "candidate_experience_years": experience_years,
            "experience_bucket": get_experience_bucket(experience_years),
            "job_title": application.job.title if application.job_id else "Unknown Job",
            "score": priority["score"],
            "score_display": priority["score_display"],
            "matched_skills": priority["matched_skills"],
            "missing_skills": priority["missing_skills"],
            "applied_at": application.applied_at,
        })

    rows.sort(
        key=lambda row: (
            row["score"],
            row["applied_at"],
        ),
        reverse=True,
    )

    return rows