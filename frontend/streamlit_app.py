import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("STREAMLIT_API_BASE_URL", "http://localhost:8000")
CAREER_FIELDS = [
    "Computer Science",
    "Logistics",
    "Finance",
    "Marketing",
    "Healthcare",
    "Engineering",
]


st.set_page_config(page_title="CareerScope AI", layout="wide")

st.title("CareerScope AI")

with st.form("candidate_profile_form"):
    career_field = st.selectbox("Career field", CAREER_FIELDS)
    desired_job_title = st.text_input("Desired job title", placeholder="Data Scientist")
    cv_file = st.file_uploader("Upload CV", type=["pdf", "docx", "txt"])
    portfolio_links = st.text_area(
        "Portfolio links",
        placeholder="https://github.com/example\nhttps://example.com",
    )
    submitted = st.form_submit_button("Analyze profile")

if submitted:
    if not desired_job_title.strip():
        st.error("Enter a desired job title.")
    elif cv_file is None:
        st.error("Upload a CV to continue.")
    else:
        files = {
            "cv": (
                cv_file.name,
                cv_file.getvalue(),
                cv_file.type or "application/octet-stream",
            )
        }
        data = {
            "career_field": career_field,
            "desired_job_title": desired_job_title,
            "portfolio_links": portfolio_links,
        }

        try:
            response = requests.post(
                f"{API_BASE_URL}/api/candidate/analyze",
                data=data,
                files=files,
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            st.error(f"API request failed: {exc}")
        else:
            analysis = response.json()
            st.subheader("Analysis preview")
            st.json(analysis)
