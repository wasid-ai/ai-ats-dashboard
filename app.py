import json
import streamlit as st
import pandas as pd
import google.generativeai as genai
from pypdf import PdfReader
from jsonschema import validate

st.set_page_config(page_title="Ultimate AI ATS", page_icon="🚀", layout="wide")
st.title("🚀 Ultimate AI-Powered ATS & Cover Letter Generator")
st.markdown("Get ATS Scores, Missing Skills, and Auto-Generated Cover Letters in one click!")
st.info("🔒 **Privacy Notice:** This app does not store your resume or API Key. All data is processed in memory and cleared on page refresh.")

st.sidebar.header("⚙️ Configuration")
st.sidebar.warning("⚠️ **Note:** Your API Key is used only for this session and is not stored. Please use your own API Key carefully.")
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password", placeholder="AIzaSy...")

default_jd = """We are looking for an AI/ML Engineer to join our team.
Minimum 2 years of experience required.
Required Skills: Python, Machine Learning, Deep Learning, SQL.
Preferred Skills: PyTorch, TensorFlow, AWS, Docker, NLP.
Minimum Education: bachelor."""

st.sidebar.subheader("📝 Target Role")
job_description_text = st.sidebar.text_area("Paste Job Description Here", value=default_jd, height=250)

EDUCATION_RANK = {"high_school": 0, "bachelor": 1, "master": 2, "phd": 3, "other": 0}
RESUME_SCHEMA = {
    "type": "object",
    "properties": {
        "full_name": {"type": "string"},
        "years_experience": {"type": "integer", "minimum": 0},
        "technical_skills": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "projects": {"type": "array", "items": {"type": "string"}},
        "education_level": {"type": "string", "enum": ["high_school", "bachelor", "master", "phd", "other"]},
    },
    "required": ["full_name", "years_experience", "technical_skills", "education_level"]
}

def extract_text_from_pdf(uploaded_file):
    try:
        reader = PdfReader(uploaded_file)
        return "".join([page.extract_text() or "" for page in reader.pages])
    except: return ""

def clean_json(raw):
    return raw.replace("```json", "").replace("
