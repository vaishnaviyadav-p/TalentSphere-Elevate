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


def generate_learning_path(missing_skills):
    """
    Generate a learning path for missing skills.
    """

    learning_resources = {

        "python": {
            "level": "Beginner",
            "description": "Learn Python syntax, functions, OOP, and basic problem solving."
        },

        "java": {
            "level": "Beginner",
            "description": "Learn Java fundamentals, OOP, collections, and exception handling."
        },

        "javascript": {
            "level": "Beginner",
            "description": "Learn JavaScript fundamentals, DOM manipulation, ES6, and asynchronous programming."
        },

        "html": {
            "level": "Beginner",
            "description": "Learn HTML structure, semantic elements, forms, and accessibility."
        },

        "css": {
            "level": "Beginner",
            "description": "Learn CSS layouts, Flexbox, Grid, responsive design, and styling."
        },

        "react": {
            "level": "Intermediate",
            "description": "Learn React components, props, state, hooks, and API integration."
        },

        "django": {
            "level": "Intermediate",
            "description": "Learn Django models, views, templates, URLs, forms, and REST APIs."
        },

        "flask": {
            "level": "Intermediate",
            "description": "Learn Flask routing, templates, forms, APIs, and database integration."
        },

        "sql": {
            "level": "Beginner",
            "description": "Learn SQL queries, joins, aggregation, subqueries, and database design."
        },

        "mysql": {
            "level": "Beginner",
            "description": "Learn MySQL databases, tables, queries, joins, and database management."
        },

        "mongodb": {
            "level": "Intermediate",
            "description": "Learn NoSQL concepts, MongoDB collections, queries, and CRUD operations."
        },

        "git": {
            "level": "Beginner",
            "description": "Learn Git commands, branching, merging, commits, and version control."
        },

        "github": {
            "level": "Beginner",
            "description": "Learn GitHub repositories, pull requests, branches, and collaboration."
        },

        "rest api": {
            "level": "Intermediate",
            "description": "Learn REST principles, HTTP methods, status codes, JSON, and API development."
        },

        "node.js": {
            "level": "Intermediate",
            "description": "Learn Node.js, npm, modules, asynchronous programming, and backend APIs."
        },

        "express": {
            "level": "Intermediate",
            "description": "Learn Express routing, middleware, REST APIs, and backend development."
        },

        "machine learning": {
            "level": "Intermediate",
            "description": "Learn supervised learning, preprocessing, model training, evaluation, and prediction."
        },

        "tensorflow": {
            "level": "Advanced",
            "description": "Learn neural networks, model creation, training, and deployment using TensorFlow."
        },

        "pytorch": {
            "level": "Advanced",
            "description": "Learn tensors, neural networks, training loops, and deep learning using PyTorch."
        },

        "docker": {
            "level": "Intermediate",
            "description": "Learn containers, Dockerfiles, images, containers, and Docker Compose."
        },

        "aws": {
            "level": "Intermediate",
            "description": "Learn AWS core services, deployment, storage, networking, and cloud fundamentals."
        },

        "linux": {
            "level": "Beginner",
            "description": "Learn Linux commands, file management, permissions, processes, and shell basics."
        },

        "communication": {
            "level": "Beginner",
            "description": "Improve professional communication, presentation, and workplace communication skills."
        },

        "problem solving": {
            "level": "Beginner",
            "description": "Practice logical reasoning, algorithms, data structures, and coding problems."
        },

        "teamwork": {
            "level": "Beginner",
            "description": "Develop collaboration, communication, and team-based problem-solving skills."
        },

    }

    learning_path = []

    for skill in missing_skills:

        skill_lower = skill.lower().strip()

        if skill_lower in learning_resources:

            learning_path.append({
                "skill": skill.title(),
                "level": learning_resources[skill_lower]["level"],
                "description": learning_resources[skill_lower]["description"]
            })

        else:

            learning_path.append({
                "skill": skill.title(),
                "level": "Beginner",
                "description": f"Learn the fundamentals and practical applications of {skill.title()}."
            })

    return learning_path