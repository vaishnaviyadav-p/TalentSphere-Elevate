import re
from typing import List, Dict, Any, Optional, Set
from django.db.models import Q
from django.contrib.auth.models import User

from candidate.models import CandidateProfile, ResumeData, JobApplication
from recruiter.models import Job
from candidate.skill_matching import (
    calculate_skill_match,
    extract_required_skills,
)

from .models import JobRecommendation, CandidateRecommendation
from recruiter.ranking import (
    get_candidate_skills,
    get_candidate_experience_text,
    parse_experience_years,
    get_experience_bucket,
    calculate_priority_score,
)


SKILL_ALIASES = {
    "react.js": "react",
    "reactjs": "react",
    "react.js": "react",
    "vue.js": "vue",
    "vuejs": "vue",
    "node.js": "node",
    "nodejs": "node",
    "express.js": "express",
    "expressjs": "express",
    "postgre sql": "postgresql",
    "postgres": "postgresql",
    "postgre": "postgresql",
    "ms sql": "sql server",
    "mssql": "sql server",
    "sql server": "sql server",
    "c#": "csharp",
    "c sharp": "csharp",
    "c++": "cpp",
    "c plus plus": "cpp",
    "golang": "go",
    "k8s": "kubernetes",
    "kube": "kubernetes",
    "ci/cd": "ci cd",
    "cicd": "ci cd",
    "rest api": "rest",
    "restful": "rest",
    "graphql": "graphql",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "computer vision": "cv",
    "aws": "amazon web services",
    "gcp": "google cloud platform",
    "azure": "microsoft azure",
    "ci": "continuous integration",
    "cd": "continuous deployment",
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "rb": "ruby",
    "php": "php",
    "html5": "html",
    "css3": "css",
    "scss": "sass",
    "less": "less",
    "styled-components": "styled components",
    "material-ui": "mui",
    "material ui": "mui",
    "next.js": "nextjs",
    "nextjs": "nextjs",
    "nuxt.js": "nuxtjs",
    "nuxtjs": "nuxtjs",
    "svelte": "svelte",
    "solid.js": "solidjs",
    "solidjs": "solidjs",
    "jest": "jest",
    "mocha": "mocha",
    "cypress": "cypress",
    "playwright": "playwright",
    "selenium": "selenium",
    "pytest": "pytest",
    "unittest": "unittest",
    "junit": "junit",
    "maven": "maven",
    "gradle": "gradle",
    "npm": "npm",
    "yarn": "yarn",
    "pnpm": "pnpm",
    "webpack": "webpack",
    "vite": "vite",
    "esbuild": "esbuild",
    "babel": "babel",
    "eslint": "eslint",
    "prettier": "prettier",
    "husky": "husky",
    "lint-staged": "lint staged",
    "git": "git",
    "github": "github",
    "gitlab": "gitlab",
    "bitbucket": "bitbucket",
    "jira": "jira",
    "confluence": "confluence",
    "slack": "slack",
    "teams": "microsoft teams",
    "zoom": "zoom",
    "figma": "figma",
    "sketch": "sketch",
    "adobe xd": "adobe xd",
    "photoshop": "photoshop",
    "illustrator": "illustrator",
    "after effects": "after effects",
    "premiere": "premiere",
    "docker": "docker",
    "podman": "podman",
    "containerd": "containerd",
    "helm": "helm",
    "argo": "argo",
    "flux": "flux",
    "rancher": "rancher",
    "terraform": "terraform",
    "pulumi": "pulumi",
    "ansible": "ansible",
    "chef": "chef",
    "puppet": "puppet",
    "salt": "saltstack",
    "saltstack": "saltstack",
    "jenkins": "jenkins",
    "gitlab ci": "gitlab ci",
    "github actions": "github actions",
    "circleci": "circleci",
    "travis": "travis ci",
    "travis ci": "travis ci",
    "azure devops": "azure devops",
    "bitbucket pipelines": "bitbucket pipelines",
    "prometheus": "prometheus",
    "grafana": "grafana",
    "datadog": "datadog",
    "newrelic": "new relic",
    "new relic": "new relic",
    "sentry": "sentry",
    "elk": "elk stack",
    "elk stack": "elk stack",
    "kafka": "kafka",
    "rabbitmq": "rabbitmq",
    "redis": "redis",
    "memcached": "memcached",
    "mongodb": "mongodb",
    "cassandra": "cassandra",
    "dynamodb": "dynamodb",
    "firebase": "firebase",
    "supabase": "supabase",
    "planetscale": "planetscale",
    "neon": "neon",
    "vercel": "vercel",
    "netlify": "netlify",
    "heroku": "heroku",
    "render": "render",
    "railway": "railway",
    "fly.io": "flyio",
    "flyio": "flyio",
    "digitalocean": "digitalocean",
    "linode": "linode",
    "vultr": "vultr",
    "nginx": "nginx",
    "apache": "apache",
    "caddy": "caddy",
    "traefik": "traefik",
    "envoy": "envoy",
    "istio": "istio",
    "linkerd": "linkerd",
    "consul": "consul",
    "vault": "vault",
    "nomad": "nomad",
    "packer": "packer",
    "vagrant": "vagrant",
    "virtualbox": "virtualbox",
    "vmware": "vmware",
    "parallels": "parallels",
    "qemu": "qemu",
    "libvirt": "libvirt",
    "openstack": "openstack",
    "kvm": "kvm",
    "xen": "xen",
    "hyperv": "hyperv",
    "hyper-v": "hyperv",
    "wsl": "wsl",
    "wsl2": "wsl",
    "linux": "linux",
    "ubuntu": "ubuntu",
    "debian": "debian",
    "centos": "centos",
    "redhat": "redhat",
    "rhel": "rhel",
    "fedora": "fedora",
    "arch": "arch",
    "manjaro": "manjaro",
    "mint": "mint",
    "opensuse": "opensuse",
    "alpine": "alpine",
    "nixos": "nixos",
    "macos": "macos",
    "mac os": "macos",
    "windows": "windows",
    "win10": "windows",
    "win11": "windows",
    "powershell": "powershell",
    "cmd": "cmd",
    "bash": "bash",
    "zsh": "zsh",
    "fish": "fish",
    "tmux": "tmux",
    "screen": "screen",
    "vim": "vim",
    "neovim": "neovim",
    "vscode": "vscode",
    "visual studio code": "vscode",
    "intellij": "intellij",
    "idea": "intellij",
    "pycharm": "pycharm",
    "webstorm": "webstorm",
    "goland": "goland",
    "rider": "rider",
    "clion": "clion",
    "datagrip": "datagrip",
    "android studio": "android studio",
    "xcode": "xcode",
    "swift": "swift",
    "objective-c": "objective c",
    "objective c": "objective c",
    "kotlin": "kotlin",
    "java": "java",
    "scala": "scala",
    "groovy": "groovy",
    "clojure": "clojure",
    "haskell": "haskell",
    "f#": "fsharp",
    "fsharp": "fsharp",
    "ocaml": "ocaml",
    "reason": "reasonml",
    "reasonml": "reasonml",
    "elm": "elm",
    "purescript": "purescript",
    "dart": "dart",
    "flutter": "flutter",
    "react native": "react native",
    "rn": "react native",
    "expo": "expo",
    "ionic": "ionic",
    "capacitor": "capacitor",
    "cordova": "cordova",
    "phonegap": "phonegap",
    "electron": "electron",
    "tauri": "tauri",
    "wails": "wails",
    "sciter": "sciter",
    "webview": "webview",
    "qt": "qt",
    "gtk": "gtk",
    "wxwidgets": "wxwidgets",
    "dear imgui": "imgui",
    "imgui": "imgui",
    "unreal": "unreal engine",
    "unreal engine": "unreal engine",
    "unity": "unity",
    "godot": "godot",
    "gamemaker": "gamemaker",
    "rpg maker": "rpg maker",
    "construct": "construct",
    "phaser": "phaser",
    "pixi": "pixijs",
    "pixijs": "pixijs",
    "three.js": "threejs",
    "threejs": "threejs",
    "babylon.js": "babylonjs",
    "babylonjs": "babylonjs",
    "playcanvas": "playcanvas",
    "aframe": "aframe",
    "webgl": "webgl",
    "webgpu": "webgpu",
    "wasm": "webassembly",
    "webassembly": "webassembly",
    "emscripten": "emscripten",
    "rust": "rust",
    "cargo": "cargo",
    "crates.io": "crates",
    "crates": "crates",
    "tokio": "tokio",
    "async-std": "async std",
    "async std": "async std",
    "actix": "actix",
    "actix-web": "actix web",
    "axum": "axum",
    "warp": "warp",
    "rocket": "rocket",
    "tide": "tide",
    "hyper": "hyper",
    "reqwest": "reqwest",
    "serde": "serde",
    "diesel": "diesel",
    "sqlx": "sqlx",
    "seaorm": "seaorm",
    "sea-orm": "seaorm",
    "bevy": "bevy",
    "egui": "egui",
    "iced": "iced",
    "druid": "druid",
    "fltk": "fltk",
    "slint": "slint",
    "tauri": "tauri",
    "wry": "wry",
    "webview": "webview",
}

SKILL_CATEGORIES = {
    "programming": {
        "python", "javascript", "typescript", "java", "csharp", "cpp", "go", "rust",
        "ruby", "php", "swift", "kotlin", "scala", "clojure", "haskell", "fsharp",
        "ocaml", "reasonml", "elm", "purescript", "dart", "objective c"
    },
    "frontend": {
        "react", "vue", "svelte", "solidjs", "angular", "nextjs", "nuxtjs",
        "html", "css", "sass", "less", "styled components", "mui", "tailwind",
        "bootstrap", "webpack", "vite", "esbuild", "babel", "eslint", "prettier"
    },
    "backend": {
        "node", "express", "django", "flask", "fastapi", "spring", "actix web",
        "axum", "warp", "rocket", "tide", "gin", "echo", "fiber", "nestjs",
        "graphql", "rest", "grpc", "websockets", "microservices"
    },
    "database": {
        "postgresql", "mysql", "sqlite", "sql server", "mongodb", "redis",
        "cassandra", "dynamodb", "firebase", "supabase", "planetscale", "neon",
        "elasticsearch", "clickhouse", "snowflake", "bigquery", "redshift"
    },
    "cloud": {
        "aws", "azure", "gcp", "digitalocean", "linode", "vultr", "heroku",
        "vercel", "netlify", "render", "railway", "flyio", "cloudflare"
    },
    "devops": {
        "docker", "kubernetes", "terraform", "ansible", "jenkins", "github actions",
        "gitlab ci", "circleci", "prometheus", "grafana", "datadog", "sentry",
        "elk stack", "kafka", "rabbitmq", "nginx", "traefik", "istio", "linkerd",
        "consul", "vault", "nomad", "packer", "helm", "argo", "flux", "rancher"
    },
    "mobile": {
        "react native", "flutter", "swift", "kotlin", "ionic", "capacitor",
        "expo", "android", "ios", "xcode", "android studio"
    },
    "desktop": {
        "electron", "tauri", "wails", "qt", "gtk", "wxwidgets", "imgui",
        "flutter", "wpf", "winforms", "maui", "avalon"
    },
    "ml": {
        "machine learning", "deep learning", "nlp", "computer vision", "cv",
        "tensorflow", "pytorch", "scikit-learn", "keras", "jax", "huggingface",
        "transformers", "langchain", "llama", "openai", "anthropic", "cohere",
        "stable diffusion", "midjourney", "dall-e", "whisper", "bert", "gpt"
    },
    "data": {
        "pandas", "numpy", "polars", "dask", "spark", "hadoop", "airflow",
        "dbt", "tableau", "power bi", "looker", "metabase", "superset",
        "jupyter", "colab", "kaggle", "plotly", "matplotlib", "seaborn"
    },
}


def _normalize_skill(skill: str) -> str:
    """Normalize a skill string to a canonical form."""
    if not skill:
        return ""
    
    normalized = re.sub(r"\s+", " ", str(skill)).strip().lower()
    
    if normalized in SKILL_ALIASES:
        return SKILL_ALIASES[normalized]
    
    normalized = re.sub(r"[^\w\s#+.-]", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    
    return normalized


def _normalize_skills(skills: List[str]) -> Set[str]:
    """Normalize a list of skills, removing duplicates.
    Also splits skills by common delimiters (comma, semicolon, pipe, newline).
    """
    normalized = set()
    for skill in skills:
        # Split by common delimiters
        parts = re.split(r"[,;\n/|]+", str(skill))
        for part in parts:
            part = part.strip()
            if part:
                norm = _normalize_skill(part)
                if norm:
                    normalized.add(norm)
    return normalized


def get_user_candidate_skills(user: User) -> List[str]:
    """Get all skills for a candidate user from profile and resume."""
    try:
        profile = CandidateProfile.objects.get(user=user)
    except CandidateProfile.DoesNotExist:
        return []

    resume_data = None
    try:
        resume_data = profile.resume_data
    except ResumeData.DoesNotExist:
        pass

    skills = get_candidate_skills(profile, resume_data)
    return list(_normalize_skills(skills))


def get_user_experience_bucket(user: User) -> Optional[str]:
    """Get experience bucket (0-2, 2-5, 5+) for a candidate."""
    try:
        profile = CandidateProfile.objects.get(user=user)
    except CandidateProfile.DoesNotExist:
        return None

    resume_data = None
    try:
        resume_data = profile.resume_data
    except ResumeData.DoesNotExist:
        pass

    experience_text = get_candidate_experience_text(profile, resume_data)
    experience_years = parse_experience_years(experience_text)
    return get_experience_bucket(experience_years)


def get_user_experience_years(user: User) -> Optional[float]:
    """Get experience in years for a candidate."""
    try:
        profile = CandidateProfile.objects.get(user=user)
    except CandidateProfile.DoesNotExist:
        return None

    resume_data = None
    try:
        resume_data = profile.resume_data
    except ResumeData.DoesNotExist:
        pass

    experience_text = get_candidate_experience_text(profile, resume_data)
    return parse_experience_years(experience_text)


def calculate_experience_match_score(candidate_experience_years: Optional[float], job_experience: str) -> float:
    """
    Calculate experience match score (0-100).
    Returns a score based on how well candidate's experience matches job requirements.
    """
    if candidate_experience_years is None or not job_experience:
        return 50.0  # Neutral score when data is missing
    
    job_exp_lower = job_experience.lower()
    
    if "senior" in job_exp_lower or "lead" in job_exp_lower or "principal" in job_exp_lower:
        required_min = 5
    elif "mid" in job_exp_lower or "intermediate" in job_exp_lower:
        required_min = 2
    elif "junior" in job_exp_lower or "entry" in job_exp_lower or "0" in job_exp_lower or "1" in job_exp_lower:
        required_min = 0
    else:
        numbers = re.findall(r"(\d+)", job_exp_lower)
        if numbers:
            required_min = int(numbers[0])
        else:
            required_min = 2  # Default to mid-level
    
    if candidate_experience_years >= required_min:
        excess = candidate_experience_years - required_min
        if excess <= 2:
            return 100.0
        elif excess <= 5:
            return 90.0
        else:
            return 80.0
    else:
        deficit = required_min - candidate_experience_years
        if deficit <= 1:
            return 70.0
        elif deficit <= 2:
            return 50.0
        else:
            return 30.0


def calculate_job_match_for_candidate(candidate_user: User, job: Job) -> Dict[str, Any]:
    """
    Calculate how well a job matches a candidate's profile.
    Returns detailed match information with weighted scoring.
    Both candidate and job skills are normalized using the same canonical form.
    """
    candidate_skills = get_user_candidate_skills(candidate_user)
    required_skills = extract_required_skills(job.requirements)
    
    # Normalize BOTH sides using the same canonical normalization (SKILL_ALIASES)
    candidate_skills_normalized = _normalize_skills(candidate_skills)
    required_skills_normalized = _normalize_skills(required_skills)
    
    # Calculate skill match using normalized skills
    skill_result = calculate_skill_match(
        list(candidate_skills_normalized),
        list(required_skills_normalized)
    )
    
    candidate_experience_years = get_user_experience_years(candidate_user)
    experience_match_score = calculate_experience_match_score(candidate_experience_years, job.experience)
    
    skill_weight = 0.75
    experience_weight = 0.25
    
    overall_score = (
        skill_result["score"] * skill_weight +
        experience_match_score * experience_weight
    )
    
    matched_skills_count = len(skill_result["matched_skills"])
    total_required = len(required_skills_normalized)
    
    reason_parts = []
    if matched_skills_count > 0:
        reason_parts.append(f"Matches {matched_skills_count} of {total_required} required skills: {', '.join(skill_result['matched_skills'][:5])}")
    if skill_result["missing_skills"]:
        reason_parts.append(f"Missing: {', '.join(skill_result['missing_skills'][:5])}")
    
    candidate_exp_bucket = get_user_experience_bucket(candidate_user)
    if candidate_experience_years is not None:
        reason_parts.append(f"Experience: {candidate_experience_years} years (job requires: {job.experience})")
    elif candidate_exp_bucket:
        reason_parts.append(f"Experience level: {candidate_exp_bucket} years")
    
    return {
        "match_score": round(overall_score, 2),
        "skill_match_score": skill_result["score"],
        "experience_match_score": round(experience_match_score, 2),
        "matched_skills": skill_result["matched_skills"],
        "missing_skills": skill_result["missing_skills"],
        "experience_match": experience_match_score >= 70,
        "reason": " | ".join(reason_parts) if reason_parts else "General match based on profile",
    }


def calculate_candidate_match_for_job(candidate_user: User, job: Job) -> Dict[str, Any]:
    """
    Calculate how well a candidate matches a job's requirements.
    Both candidate and job skills are normalized using the same canonical form (SKILL_ALIASES).
    """
    try:
        candidate_profile = CandidateProfile.objects.get(user=candidate_user)
    except CandidateProfile.DoesNotExist:
        return {
            "match_score": 0,
            "skill_match_score": 0,
            "experience_match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "experience_match": False,
            "reason": "No candidate profile found",
        }

    resume_data = None
    try:
        resume_data = candidate_profile.resume_data
    except ResumeData.DoesNotExist:
        pass

    # Get candidate skills (already normalized via get_user_candidate_skills -> _normalize_skills)
    candidate_skills = get_user_candidate_skills(candidate_user)
    
    # Get required skills and normalize both sides
    required_skills = extract_required_skills(job.requirements)
    
    # Normalize BOTH sides using the same canonical normalization (SKILL_ALIASES)
    candidate_skills_normalized = _normalize_skills(candidate_skills)
    required_skills_normalized = _normalize_skills(required_skills)
    
    # Calculate skill match using normalized skills
    skill_result = calculate_skill_match(
        list(candidate_skills_normalized),
        list(required_skills_normalized)
    )
    
    experience_match = False
    experience_text = get_candidate_experience_text(candidate_profile, resume_data)
    experience_years = parse_experience_years(experience_text)
    job_experience = job.experience.lower() if job.experience else ""
    
    experience_match_score = 50.0
    if experience_years is not None and job_experience:
        experience_match_score = calculate_experience_match_score(experience_years, job.experience)
        is_senior_job = ("senior" in job_experience or "lead" in job_experience 
                         or "principal" in job_experience or "5+" in job_experience)
        is_mid_job = ("mid" in job_experience or "intermediate" in job_experience
                      or "2" in job_experience or "3" in job_experience or "4" in job_experience)
        is_junior_job = ("junior" in job_experience or "entry" in job_experience
                         or "0" in job_experience or "1" in job_experience)
        
        if experience_years >= 5 and is_senior_job:
            experience_match = True
        elif 2 <= experience_years < 5 and is_mid_job:
            experience_match = True
        elif experience_years < 2 and is_junior_job:
            experience_match = True
    
    skill_weight = 0.75
    experience_weight = 0.25
    
    overall_score = (
        skill_result["score"] * skill_weight +
        experience_match_score * experience_weight
    )
    
    matched_skills_count = len(skill_result["matched_skills"])
    total_required = len(required_skills_normalized)
    
    reason_parts = []
    if matched_skills_count > 0:
        reason_parts.append(f"Matches {matched_skills_count} of {total_required} required skills: {', '.join(skill_result['matched_skills'][:5])}")
    if skill_result["missing_skills"]:
        reason_parts.append(f"Missing: {', '.join(skill_result['missing_skills'][:5])}")
    if experience_match:
        reason_parts.append("Experience level matches well")
    elif experience_years is not None:
        reason_parts.append(f"{experience_years} years experience")
    
    return {
        "match_score": round(overall_score, 2),
        "skill_match_score": skill_result["score"],
        "experience_match_score": round(experience_match_score, 2),
        "matched_skills": skill_result["matched_skills"],
        "missing_skills": skill_result["missing_skills"],
        "experience_match": experience_match,
        "reason": " | ".join(reason_parts) if reason_parts else "General match based on profile",
    }
    if experience_match:
        reason_parts.append("Experience level matches well")
    elif experience_years is not None:
        reason_parts.append(f"{experience_years} years experience")
    
    return {
        "match_score": round(overall_score, 2),
        "skill_match_score": priority["score"],
        "experience_match_score": round(experience_match_score, 2),
        "matched_skills": priority["matched_skills"],
        "missing_skills": priority["missing_skills"],
        "experience_match": experience_match,
        "reason": " | ".join(reason_parts) if reason_parts else "General match based on profile",
    }


def get_candidate_job_history(candidate_user: User) -> List[int]:
    """Get IDs of jobs the candidate has already applied to."""
    return list(
        JobApplication.objects.filter(candidate=candidate_user)
        .values_list("job_id", flat=True)
    )


def generate_job_recommendations_for_candidate(
    candidate_user: User,
    limit: int = 10,
    min_score: float = 30.0,
) -> List[JobRecommendation]:
    """
    Generate job recommendations for a candidate.
    Returns list of created/updated JobRecommendation objects.
    """
    applied_job_ids = get_candidate_job_history(candidate_user)
    
    active_jobs = Job.objects.filter(is_active=True).exclude(
        id__in=applied_job_ids
    ).select_related("recruiter")
    
    recommendations = []
    
    for job in active_jobs:
        match_data = calculate_job_match_for_candidate(candidate_user, job)
        
        if match_data["match_score"] < min_score:
            continue
        
        rec, created = JobRecommendation.objects.update_or_create(
            candidate=candidate_user,
            job=job,
            defaults={
                "match_score": match_data["match_score"],
                "skill_match_score": match_data["skill_match_score"],
                "experience_match_score": match_data["experience_match_score"],
                "matched_skills": match_data["matched_skills"],
                "missing_skills": match_data["missing_skills"],
                "reason": match_data["reason"],
            }
        )
        recommendations.append(rec)
    
    recommendations.sort(key=lambda r: r.match_score, reverse=True)
    return recommendations[:limit]


def generate_candidate_recommendations_for_job(
    job: Job,
    limit: int = 10,
    min_score: float = 30.0,
) -> List[CandidateRecommendation]:
    """
    Generate candidate recommendations for a specific job.
    Returns list of created/updated CandidateRecommendation objects.
    """
    applied_candidate_ids = list(
        JobApplication.objects.filter(job=job)
        .values_list("candidate_id", flat=True)
    )
    
    candidate_users = User.objects.filter(
        candidateprofile__isnull=False
    ).exclude(
        id__in=applied_candidate_ids
    ).select_related("candidateprofile", "candidateprofile__resume_data")
    
    recommendations = []
    
    for candidate_user in candidate_users:
        match_data = calculate_candidate_match_for_job(candidate_user, job)
        
        if match_data["match_score"] < min_score:
            continue
        
        rec, created = CandidateRecommendation.objects.update_or_create(
            job=job,
            candidate=candidate_user,
            defaults={
                "match_score": match_data["match_score"],
                "skill_match_score": match_data["skill_match_score"],
                "experience_match_score": match_data["experience_match_score"],
                "matched_skills": match_data["matched_skills"],
                "missing_skills": match_data["missing_skills"],
                "experience_match": match_data["experience_match"],
                "reason": match_data["reason"],
            }
        )
        recommendations.append(rec)
    
    recommendations.sort(key=lambda r: r.match_score, reverse=True)
    return recommendations[:limit]


def get_job_recommendations_for_candidate(
    candidate_user: User,
    limit: int = 10,
    include_viewed: bool = False,
) -> List[JobRecommendation]:
    """Get existing job recommendations for a candidate."""
    qs = JobRecommendation.objects.filter(
        candidate=candidate_user,
        is_dismissed=False,
    ).select_related("job", "job__recruiter")
    
    if not include_viewed:
        qs = qs.filter(is_viewed=False)
    
    return list(qs.order_by("-match_score")[:limit])


def get_candidate_recommendations_for_job(
    job: Job,
    limit: int = 10,
    include_viewed: bool = False,
) -> List[CandidateRecommendation]:
    """Get existing candidate recommendations for a job."""
    qs = CandidateRecommendation.objects.filter(
        job=job,
        is_dismissed=False,
    ).select_related("candidate", "candidate__candidateprofile", "candidate__candidateprofile__resume_data")
    
    if not include_viewed:
        qs = qs.filter(is_viewed=False)
    
    return list(qs.order_by("-match_score")[:limit])


def mark_recommendation_viewed(recommendation_id: int, model_type: str) -> bool:
    """Mark a recommendation as viewed."""
    try:
        if model_type == "job":
            JobRecommendation.objects.filter(id=recommendation_id).update(is_viewed=True)
        elif model_type == "candidate":
            CandidateRecommendation.objects.filter(id=recommendation_id).update(is_viewed=True)
        else:
            return False
        return True
    except Exception:
        return False


def dismiss_recommendation(recommendation_id: int, model_type: str) -> bool:
    """Dismiss a recommendation."""
    try:
        if model_type == "job":
            JobRecommendation.objects.filter(id=recommendation_id).update(is_dismissed=True)
        elif model_type == "candidate":
            CandidateRecommendation.objects.filter(id=recommendation_id).update(is_dismissed=True)
        else:
            return False
        return True
    except Exception:
        return False