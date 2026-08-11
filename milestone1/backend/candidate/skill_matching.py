import PyPDF2
import docx
import pdfplumber


def extract_text_from_pdf(file):
    """Extract text from PDF file."""

    text = ""

    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""

    except Exception:
        try:
            file.seek(0)

            pdf_reader = PyPDF2.PdfReader(file)

            for page in pdf_reader.pages:
                text += page.extract_text() or ""

        except Exception:
            text = ""

    return text


def extract_text_from_docx(file):
    """Extract text from DOCX file."""

    text = ""

    try:
        doc = docx.Document(file)

        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"

    except Exception:
        text = ""

    return text


def extract_text_from_file(file):
    """Extract text from uploaded resume file."""

    file_name = file.name.lower()
    text = ""

    try:

        if file_name.endswith(".pdf"):
            text = extract_text_from_pdf(file)

        elif file_name.endswith(".docx"):
            text = extract_text_from_docx(file)

        elif file_name.endswith(".txt"):
            text = file.read().decode(
                "utf-8",
                errors="ignore"
            )

    except Exception as e:
        print(f"Error extracting text: {e}")
        text = ""

    return text


def extract_skills(text):
    """Extract known skills from text."""

    skills_db = [
        "python",
        "java",
        "javascript",
        "typescript",
        "c++",
        "c#",
        "ruby",
        "php",
        "swift",
        "kotlin",
        "go",
        "rust",
        "html",
        "css",
        "react",
        "angular",
        "vue",
        "node.js",
        "express",
        "django",
        "flask",
        "spring",
        "bootstrap",
        "tailwind",
        "sql",
        "mysql",
        "postgresql",
        "mongodb",
        "redis",
        "oracle",
        "sqlite",
        "firebase",
        "aws",
        "azure",
        "gcp",
        "docker",
        "kubernetes",
        "jenkins",
        "git",
        "github",
        "gitlab",
        "machine learning",
        "deep learning",
        "nlp",
        "tensorflow",
        "pytorch",
        "scikit-learn",
        "pandas",
        "numpy",
        "matplotlib",
        "seaborn",
        "agile",
        "scrum",
        "jira",
        "communication",
        "problem solving",
        "teamwork",
        "leadership",
        "project management",
        "rest api",
        "graphql",
        "microservices",
        "linux",
        "windows",
        "react native",
        "flutter",
        "frontend",
        "backend",
        "full stack",
        "mobile development",
    ]

    text_lower = text.lower()

    found_skills = []

    for skill in skills_db:

        if skill in text_lower:
            found_skills.append(skill)

    return sorted(set(found_skills))


def parse_resume(file):
    """Extract text and skills from a resume."""

    text = extract_text_from_file(file)

    if not text:
        return {
            "text": "",
            "skills": [],
            "success": False
        }

    skills = extract_skills(text)

    return {
        "text": text,
        "skills": skills,
        "success": True
    }


def extract_required_skills(requirements):
    """
    Extract skills from job requirements.
    """
    if not requirements:
        return []

    return extract_skills(requirements)


def calculate_skill_match(candidate_skills, required_skills):
    """
    Compare candidate skills with required job skills
    and calculate the fit percentage.
    """

    candidate_skills = {
        skill.lower().strip()
        for skill in candidate_skills
    }

    required_skills = {
        skill.lower().strip()
        for skill in required_skills
    }

    matched_skills = candidate_skills.intersection(
        required_skills
    )

    missing_skills = required_skills - candidate_skills

    if required_skills:
        score = (
            len(matched_skills)
            / len(required_skills)
        ) * 100
    else:
        score = 0

    return {
        "matched_skills": sorted(matched_skills),
        "missing_skills": sorted(missing_skills),
        "score": round(score, 2),
    }