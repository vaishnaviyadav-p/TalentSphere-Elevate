import PyPDF2
import docx
import pdfplumber
import re


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


def _build_skill_pattern(skill: str) -> str:
    """
    Build a regex pattern that matches a skill at word boundaries.
    Handles special characters in skills like c++, c#, node.js.
    """

    escaped = re.escape(skill)

    escaped = escaped.replace(r"\ ", r"\s+")

    return r"(^|\s|[^\w])" + escaped + r"($|\s|[^\w])"


def extract_skills(text):
    """Extract known skills from text using word-boundary matching."""

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

    skills_sorted = sorted(skills_db, key=len, reverse=True)

    text_lower = text.lower()
    found_skills = []

    for skill in skills_sorted:
        pattern = _build_skill_pattern(skill)
        if re.search(pattern, text_lower):
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


def generate_learning_path(missing_skills):
    """
    Generate a recommended learning path for missing skills.
    Returns a list of dicts with skill, level, and description.
    """
    learning_resources = {
        "python": {
            "level": "Beginner to Advanced",
            "description": "Start with Python basics, then move to OOP, data structures, and popular frameworks like Django/FastAPI."
        },
        "java": {
            "level": "Beginner to Advanced",
            "description": "Learn core Java, collections, multithreading, and Spring Boot for enterprise development."
        },
        "javascript": {
            "level": "Beginner to Advanced",
            "description": "Master ES6+, async/await, DOM manipulation, and modern frameworks like React/Vue."
        },
        "typescript": {
            "level": "Intermediate",
            "description": "Learn static typing, interfaces, generics, and integration with React/Node.js projects."
        },
        "react": {
            "level": "Intermediate",
            "description": "Components, hooks, state management (Redux/Zustand), and Next.js for full-stack apps."
        },
        "node.js": {
            "level": "Intermediate",
            "description": "Express.js, async patterns, REST APIs, and database integration with MongoDB/PostgreSQL."
        },
        "django": {
            "level": "Intermediate",
            "description": "Django ORM, authentication, DRF for APIs, and deployment with Docker/Gunicorn."
        },
        "sql": {
            "level": "Beginner to Intermediate",
            "description": "Queries, joins, indexing, normalization, and advanced topics like window functions."
        },
        "aws": {
            "level": "Intermediate to Advanced",
            "description": "EC2, S3, RDS, Lambda, CloudFormation, and CI/CD pipelines."
        },
        "docker": {
            "level": "Intermediate",
            "description": "Containerization, Dockerfile best practices, docker-compose, and multi-stage builds."
        },
        "kubernetes": {
            "level": "Advanced",
            "description": "Pods, services, deployments, Helm charts, and cluster management."
        },
        "machine learning": {
            "level": "Intermediate to Advanced",
            "description": "Supervised/unsupervised learning, scikit-learn, model evaluation, and deployment."
        },
        "deep learning": {
            "level": "Advanced",
            "description": "Neural networks, TensorFlow/PyTorch, CNNs, RNNs, and transformers."
        },
        "git": {
            "level": "Beginner",
            "description": "Version control basics, branching strategies, merge vs rebase, and GitHub workflows."
        },
    }

    path = []
    for i, skill in enumerate(missing_skills, 1):
        skill_lower = skill.lower().strip()
        resource = learning_resources.get(skill_lower, {
            "level": "Beginner to Intermediate",
            "description": f"Learn {skill} through online courses, documentation, and hands-on projects."
        })
        path.append({
            "skill": skill,
            "level": resource["level"],
            "description": resource["description"]
        })

    return path
