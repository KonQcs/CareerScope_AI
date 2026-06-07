import os
from typing import Any

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

DEFAULT_API_BASE_URL = os.getenv("STREAMLIT_API_BASE_URL", "http://localhost:8000")
CAREER_FIELDS = [
    "Computer Science",
    "Finance",
    "Logistics",
    "Marketing",
    "Healthcare",
    "Engineering",
]
SENIORITY_OPTIONS = ["Internship", "Junior", "Mid", "Senior", "Any"]
REMOTE_OPTIONS = ["Any", "Remote", "Hybrid", "On-site"]


def main() -> None:
    st.set_page_config(page_title="CareerScope AI", layout="wide")
    _init_state()

    st.title("CareerScope AI")
    sidebar_state = _render_sidebar()
    api_base_url = sidebar_state["api_base_url"].rstrip("/")

    _render_candidate_profile(api_base_url, sidebar_state)
    _render_upload_cv(api_base_url)
    _render_portfolio(api_base_url)
    _render_import_jobs(api_base_url)
    _render_skill_gap(api_base_url, sidebar_state)
    _render_job_recommendations(api_base_url, sidebar_state)


def _init_state() -> None:
    defaults = {
        "candidate_id": None,
        "candidate_profile": None,
        "cv_analysis": None,
        "portfolio_analysis": None,
        "sample_jobs_import": None,
        "skill_gap_report": None,
        "job_recommendations": [],
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _render_sidebar() -> dict[str, str]:
    with st.sidebar:
        st.header("Target")
        api_base_url = st.text_input("API base URL", value=DEFAULT_API_BASE_URL)
        target_field = st.selectbox("Target field", CAREER_FIELDS)
        target_job_title = st.text_input("Desired job title", value="Data Engineer")
        seniority_preference = st.selectbox("Seniority preference", SENIORITY_OPTIONS)
        location_preference = st.text_input("Location preference", value="")
        remote_preference = st.selectbox("Remote preference", REMOTE_OPTIONS)

        candidate_id = st.session_state.get("candidate_id")
        if candidate_id:
            st.success(f"Candidate ID: {candidate_id}")
        else:
            st.info("Create a candidate profile to begin.")

    return {
        "api_base_url": api_base_url,
        "target_field": target_field,
        "target_job_title": target_job_title,
        "seniority_preference": seniority_preference,
        "location_preference": location_preference,
        "remote_preference": remote_preference,
    }


def _render_candidate_profile(api_base_url: str, sidebar_state: dict[str, str]) -> None:
    st.header("1. Create Candidate Profile")
    left, right = st.columns(2)
    with left:
        full_name = st.text_input("Full name", value="")
    with right:
        email = st.text_input("Email", value="")

    if st.button("Create candidate", type="primary"):
        if not full_name.strip() or not email.strip():
            st.error("Enter a full name and email.")
            return
        if not sidebar_state["target_job_title"].strip():
            st.error("Enter a desired job title in the sidebar.")
            return

        payload = {
            "full_name": full_name.strip(),
            "email": email.strip(),
            "target_field": sidebar_state["target_field"],
            "target_job_title": sidebar_state["target_job_title"].strip(),
            "seniority_preference": _optional_choice(sidebar_state["seniority_preference"]),
            "location_preference": sidebar_state["location_preference"].strip() or None,
            "remote_preference": _optional_choice(sidebar_state["remote_preference"]),
        }
        data = _api_request("POST", api_base_url, "/candidates", json=payload)
        if data:
            st.session_state["candidate_id"] = data["id"]
            st.session_state["candidate_profile"] = data
            st.success("Candidate profile created.")
            st.json(data)


def _render_upload_cv(api_base_url: str) -> None:
    st.header("2. Upload CV")
    candidate_id = st.session_state.get("candidate_id")
    cv_file = st.file_uploader("CV file", type=["pdf", "txt"])

    disabled = candidate_id is None or cv_file is None
    if st.button("Upload and analyze CV", disabled=disabled):
        files = {
            "cv": (
                cv_file.name,
                cv_file.getvalue(),
                cv_file.type or "application/octet-stream",
            )
        }
        data = _api_request("POST", api_base_url, f"/candidates/{candidate_id}/cv", files=files)
        if data:
            st.session_state["cv_analysis"] = data
            st.success(f"Stored {data['stored_skill_count']} CV skills.")

    analysis = st.session_state.get("cv_analysis")
    if analysis:
        st.subheader("Extracted skills")
        _render_skill_table(analysis.get("skills", []))


def _render_portfolio(api_base_url: str) -> None:
    st.header("3. Add Portfolio Links")
    candidate_id = st.session_state.get("candidate_id")
    raw_urls = st.text_area(
        "Portfolio URLs",
        placeholder="https://github.com/example/project\nhttps://example.com",
    )
    urls = [url.strip() for url in raw_urls.splitlines() if url.strip()]

    if st.button("Analyze portfolio", disabled=candidate_id is None or not urls):
        data = _api_request(
            "POST",
            api_base_url,
            f"/candidates/{candidate_id}/portfolio",
            json={"urls": urls},
        )
        if data:
            st.session_state["portfolio_analysis"] = data
            st.success("Portfolio links analyzed.")

    analysis = st.session_state.get("portfolio_analysis")
    if analysis:
        st.subheader("Detected projects and skills")
        for project in analysis.get("projects", []):
            with st.container(border=True):
                st.markdown(f"**{project['project_name']}**")
                st.caption(project["source_url"])
                st.write(project["description"])
                st.write(_format_list(project.get("detected_skills", [])) or "No skills detected")


def _render_import_jobs(api_base_url: str) -> None:
    st.header("4. Import Sample Jobs")
    if st.button("Import sample job data"):
        data = _api_request("POST", api_base_url, "/jobs/import-sample")
        if data:
            st.session_state["sample_jobs_import"] = data
            st.success(f"Inserted {data['inserted_jobs']} new sample jobs.")

    if st.session_state.get("sample_jobs_import"):
        inserted_jobs = st.session_state["sample_jobs_import"]["inserted_jobs"]
        st.caption(f"Last import inserted {inserted_jobs} jobs.")


def _render_skill_gap(api_base_url: str, sidebar_state: dict[str, str]) -> None:
    st.header("5. Skill Gap Analysis")
    candidate_id = st.session_state.get("candidate_id")

    if st.button("Run skill gap analysis", disabled=candidate_id is None):
        payload = {
            "target_field": sidebar_state["target_field"],
            "target_job_title": sidebar_state["target_job_title"].strip(),
        }
        data = _api_request(
            "POST",
            api_base_url,
            f"/matching/{candidate_id}/skill-gap",
            json=payload,
        )
        if data:
            st.session_state["skill_gap_report"] = data

    report = st.session_state.get("skill_gap_report")
    if report:
        st.metric("Readiness score", f"{report['overall_readiness_score']:.0f}/100")
        st.progress(min(report["overall_readiness_score"] / 100, 1.0))

        columns = st.columns(3)
        with columns[0]:
            st.subheader("Strong skills")
            _render_list(report.get("strong_skills", []))
        with columns[1]:
            st.subheader("Partial skills")
            _render_list(report.get("partial_skills", []))
        with columns[2]:
            st.subheader("Missing skills")
            _render_list(report.get("missing_skills", []))

        st.subheader("Recommended projects")
        _render_list(report.get("recommended_projects", []))

        st.subheader("Recommended learning topics")
        _render_list(report.get("recommended_learning_topics", []))

        st.subheader("Explanation")
        st.write(report["explanation"])


def _render_job_recommendations(api_base_url: str, sidebar_state: dict[str, str]) -> None:
    st.header("6. Job Recommendations")
    candidate_id = st.session_state.get("candidate_id")

    if st.button("Recommend jobs", disabled=candidate_id is None):
        payload = {
            "target_field": sidebar_state["target_field"],
            "target_job_title": sidebar_state["target_job_title"].strip(),
            "limit": 10,
        }
        data = _api_request(
            "POST",
            api_base_url,
            f"/matching/{candidate_id}/recommend-jobs",
            json=payload,
        )
        if data is not None:
            st.session_state["job_recommendations"] = data

    recommendations = st.session_state.get("job_recommendations", [])
    if recommendations:
        for index, job in enumerate(recommendations, start=1):
            with st.container(border=True):
                top_left, top_right = st.columns([3, 1])
                with top_left:
                    st.markdown(f"**{index}. {job['title']}**")
                    st.write(job["company"])
                with top_right:
                    st.metric("Score", f"{job['overall_score']:.0f}/100")

                st.caption(job.get("location") or "Location not specified")
                st.write(f"**Matching skills:** {_format_list(job.get('matching_skills', []))}")
                st.write(f"**Missing skills:** {_format_list(job.get('missing_skills', []))}")
                st.write(job["explanation"])


def _api_request(
    method: str,
    api_base_url: str,
    path: str,
    **kwargs: Any,
) -> Any | None:
    try:
        response = requests.request(method, f"{api_base_url}{path}", timeout=45, **kwargs)
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = _response_detail(exc.response)
        st.error(f"API error: {detail}")
        return None
    except requests.RequestException as exc:
        st.error(f"Could not reach the API: {exc}")
        return None

    if not response.content:
        return {}
    return response.json()


def _response_detail(response: requests.Response | None) -> str:
    if response is None:
        return "No response received."
    try:
        payload = response.json()
    except ValueError:
        return response.text or response.reason
    return str(payload.get("detail", payload))


def _render_skill_table(skills: list[dict[str, Any]]) -> None:
    if not skills:
        st.info("No skills detected yet.")
        return

    rows = [
        {
            "Skill": skill.get("normalized_skill") or skill.get("normalized_skill_name"),
            "Category": skill.get("category"),
            "Evidence": skill.get("evidence_snippet") or skill.get("evidence_text"),
        }
        for skill in skills
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)


def _render_list(items: list[str]) -> None:
    if not items:
        st.write("None yet.")
        return
    for item in items:
        st.write(f"- {item}")


def _format_list(items: list[str]) -> str:
    return ", ".join(items) if items else "None"


def _optional_choice(value: str) -> str | None:
    return None if value == "Any" else value


if __name__ == "__main__":
    main()
