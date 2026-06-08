from __future__ import annotations

import re

FIELD_RULES = {
    "Computer Science": {
        "title": (
            "backend developer",
            "backend engineer",
            "data engineer",
            "data scientist",
            "devops engineer",
            "machine learning engineer",
            "ml engineer",
            "software developer",
            "software engineer",
        ),
        "description": (
            "api",
            "cloud",
            "data pipeline",
            "devops",
            "docker",
            "kubernetes",
            "machine learning",
            "python",
            "software",
            "sql",
        ),
    },
    "Finance": {
        "title": (
            "accounting analyst",
            "finance analyst",
            "financial analyst",
            "financial risk analyst",
            "investment analyst",
            "risk analyst",
        ),
        "description": (
            "accounting",
            "budgeting",
            "finance",
            "financial",
            "forecasting",
            "portfolio analysis",
            "risk analysis",
            "valuation",
            "variance analysis",
        ),
    },
    "Logistics": {
        "title": (
            "demand planner",
            "inventory analyst",
            "logistics analyst",
            "supply chain analyst",
            "supply chain manager",
            "warehouse analyst",
        ),
        "description": (
            "demand planning",
            "erp",
            "inventory",
            "logistics",
            "operations research",
            "route optimization",
            "supply chain",
            "warehouse",
        ),
    },
    "Marketing": {
        "title": (
            "brand manager",
            "growth marketer",
            "marketing analyst",
            "marketing manager",
            "seo specialist",
        ),
        "description": (
            "brand",
            "campaign",
            "content",
            "crm",
            "growth",
            "marketing",
            "seo",
            "social media",
        ),
    },
    "Healthcare": {
        "title": (
            "clinical analyst",
            "healthcare analyst",
            "medical analyst",
            "nurse",
            "public health analyst",
        ),
        "description": (
            "clinical",
            "healthcare",
            "hospital",
            "medical",
            "patient",
            "public health",
        ),
    },
    "Engineering": {
        "title": (
            "civil engineer",
            "electrical engineer",
            "manufacturing engineer",
            "mechanical engineer",
            "quality engineer",
            "robotics engineer",
        ),
        "description": (
            "cad",
            "civil",
            "electrical",
            "manufacturing",
            "mechanical",
            "quality control",
            "robotics",
        ),
    },
}

JOB_FAMILY_RULES = {
    "Data Engineering": {
        "title": ("data engineer", "etl developer"),
        "description": (
            "airflow",
            "data pipeline",
            "data warehouse",
            "data warehousing",
            "dbt",
            "elt",
            "etl",
            "kafka",
            "spark",
        ),
    },
    "Data Science": {
        "title": ("data scientist", "decision scientist"),
        "description": (
            "analytics product",
            "experiment",
            "predictive model",
            "scikit-learn",
            "statistical model",
            "statistics",
        ),
    },
    "Machine Learning": {
        "title": ("machine learning engineer", "ml engineer"),
        "description": (
            "deep learning",
            "machine learning",
            "mlflow",
            "model deployment",
            "pytorch",
            "tensorflow",
        ),
    },
    "Backend Development": {
        "title": ("backend developer", "backend engineer"),
        "description": (
            "api",
            "backend",
            "fastapi",
            "microservice",
            "rest api",
            "server-side",
        ),
    },
    "DevOps": {
        "title": ("cloud engineer", "devops engineer", "platform engineer", "sre"),
        "description": (
            "ci/cd",
            "cloud infrastructure",
            "devops",
            "docker",
            "infrastructure",
            "kubernetes",
        ),
    },
    "Financial Analysis": {
        "title": (
            "accounting analyst",
            "finance analyst",
            "financial analyst",
            "financial risk analyst",
            "risk analyst",
        ),
        "description": (
            "accounting",
            "budgeting",
            "financial modeling",
            "portfolio analysis",
            "risk analysis",
            "valuation",
            "variance analysis",
        ),
    },
    "Supply Chain": {
        "title": (
            "demand planner",
            "inventory analyst",
            "logistics analyst",
            "supply chain analyst",
        ),
        "description": (
            "demand planning",
            "erp",
            "inventory",
            "logistics",
            "route optimization",
            "supply chain",
            "warehouse",
        ),
    },
    "Business Analysis": {
        "title": ("business analyst", "operations analyst", "reporting analyst"),
        "description": (
            "business analysis",
            "dashboard",
            "kpi",
            "process improvement",
            "requirements",
            "stakeholder",
        ),
    },
}

SENIORITY_RULES = {
    "Internship": {
        "title": ("intern", "internship", "trainee"),
        "description": ("internship", "student", "trainee"),
    },
    "Junior": {
        "title": ("associate", "entry level", "entry-level", "jr", "junior"),
        "description": ("entry level", "entry-level", "junior", "0-2 years", "1+ years"),
    },
    "Mid": {
        "title": ("intermediate", "mid", "mid level", "mid-level"),
        "description": ("2+ years", "3+ years", "intermediate", "mid-level"),
    },
    "Senior": {
        "title": ("senior", "sr"),
        "description": ("5+ years", "experienced", "senior"),
    },
    "Lead": {
        "title": ("head", "lead", "manager", "principal", "staff"),
        "description": ("lead", "leadership", "manager", "mentor", "principal", "staff"),
    },
}

TITLE_WEIGHT = 5
DESCRIPTION_WEIGHT = 2
WEAK_DESCRIPTION_WEIGHT = 1


def classify_job_field(title: str, description: str) -> str:
    return _classify(title, description, FIELD_RULES, default="Other")


def classify_job_family(title: str, description: str) -> str:
    return _classify(title, description, JOB_FAMILY_RULES, default="Other")


def classify_seniority(title: str, description: str) -> str:
    return _classify(title, description, SENIORITY_RULES, default="Any/Unknown")


def normalize_remote_type(text: str) -> str:
    normalized_text = _normalize_text(text)
    if not normalized_text:
        return "Any/Unknown"

    if _contains_any(normalized_text, ("hybrid", "part remote", "partly remote")):
        return "Hybrid"
    if _contains_any(normalized_text, ("not remote", "on site", "on-site", "onsite", "office")):
        return "On-site"
    if _contains_any(
        normalized_text,
        ("fully remote", "remote", "remote-first", "work from home", "wfh", "anywhere"),
    ):
        return "Remote"
    return "Any/Unknown"


def _classify(
    title: str,
    description: str,
    rules: dict[str, dict[str, tuple[str, ...]]],
    default: str,
) -> str:
    normalized_title = _normalize_text(title)
    normalized_description = _normalize_text(description)
    scores = {
        label: _score_rule(normalized_title, normalized_description, rule)
        for label, rule in rules.items()
    }
    return _winning_label(scores, default)


def _score_rule(
    title: str,
    description: str,
    rule: dict[str, tuple[str, ...]],
) -> int:
    score = 0
    for keyword in rule.get("title", ()):
        if _contains_keyword(title, keyword):
            score += TITLE_WEIGHT
        elif _contains_keyword(description, keyword):
            score += DESCRIPTION_WEIGHT

    for keyword in rule.get("description", ()):
        if _contains_keyword(title, keyword):
            score += DESCRIPTION_WEIGHT
        elif _contains_keyword(description, keyword):
            score += WEAK_DESCRIPTION_WEIGHT

    return score


def _winning_label(scores: dict[str, int], default: str) -> str:
    top_score = max(scores.values(), default=0)
    if top_score <= 0:
        return default

    winners = [label for label, score in scores.items() if score == top_score]
    if len(winners) > 1:
        return default
    return winners[0]


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(_contains_keyword(text, keyword) for keyword in keywords)


def _contains_keyword(text: str, keyword: str) -> bool:
    normalized_keyword = _normalize_text(keyword)
    if not normalized_keyword:
        return False

    pattern = rf"(?<![\w+#.]){re.escape(normalized_keyword)}(?![\w+#.])"
    return re.search(pattern, text) is not None


def _normalize_text(value: str) -> str:
    normalized = value.casefold().replace("/", " ")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()
