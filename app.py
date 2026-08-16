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
    raw = raw.strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    elif raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    return raw.strip()

def safe_parse(raw_text):
    try: return json.loads(clean_json(raw_text))
    except: return None

def get_jd_reqs(jd, model):
    prompt = f"Analyze Job Description and return JSON exactly matching keys: min_experience (int), required_skills (array), preferred_skills (array), min_education (string). JD: {jd}"
    try:
        res = safe_parse(model.generate_content(prompt).text)
        if res: return res
    except: pass
    return {"min_experience": 0, "required_skills": [], "preferred_skills": [], "min_education": "bachelor"}

def parse_resume(text, model):
    prompt = f"Parse resume text into JSON EXACTLY matching schema. Keys: full_name (string), years_experience (integer), technical_skills (array of strings), projects (array of strings), education_level (high_school/bachelor/master/phd/other). Resume: {text}"
    try:
        raw_response = model.generate_content(prompt).text
        parsed = safe_parse(raw_response)
        if parsed:
            if "years_experience" in parsed: parsed["years_experience"] = int(float(parsed["years_experience"]))
            validate(instance=parsed, schema=RESUME_SCHEMA)
            return parsed
        else:
            st.error(f"JSON Parse Failed. Raw Response was: {raw_response}")
    except Exception as e:
        st.error(f"Validation/API Error: {str(e)}")
    return None

def generate_cover_letter(cand, jd, model):
    prompt = f"""Write a professional, modern, and highly persuasive Cover Letter for {cand['full_name']} applying for this Job Description: {jd}.
    Highlight their skills: {cand.get('technical_skills', [])} and projects: {cand.get('projects', [])}. 
    Keep it under 300 words. Do not include placeholders like [Your Address]. Make it ready to copy-paste."""
    try:
        return model.generate_content(prompt).text
    except Exception as e:
        return "⚠️ Failed to generate cover letter."

def score_candidate(candidate, reqs):
    skills_lower = [s.lower() for s in candidate.get("technical_skills", [])]
    exp = candidate.get("years_experience", 0)
    exp_req = reqs.get("min_experience", 0)
    
    exp_score = 20 if exp_req == 0 and exp >= 0 else min(20, int((exp / max(exp_req, 1)) * 20))
    req_skills = reqs.get("required_skills", [])
    req_score = int((sum(1 for s in req_skills if s.lower() in skills_lower) / len(req_skills)) * 40) if req_skills else 40
    pref_skills = reqs.get("preferred_skills", [])
    pref_score = int((sum(1 for s in pref_skills if s.lower() in skills_lower) / len(pref_skills)) * 20) if pref_skills else 20
    edu_score = 10 if EDUCATION_RANK.get(candidate.get("education_level", "other"), 0) >= EDUCATION_RANK.get(reqs.get("min_education", "bachelor"), 0) else 0
    proj_score = min(10, len(candidate.get("projects", [])) * 5)
    
    total = exp_score + req_score + pref_score + edu_score + proj_score
    rec = "🟢 STRONG HIRE" if total >= 80 else ("🔵 PROCEED TO INTERVIEW" if total >= 60 else "🔴 NEEDS UPGRADE")
    
    return {
        "total": total, "recommendation": rec,
        "missing_req": [s for s in req_skills if s.lower() not in skills_lower],
        "missing_pref": [s for s in pref_skills if s.lower() not in skills_lower],
        "projects_found": len(candidate.get("projects", [])),
        "breakdown": {"Exp": exp_score, "Req Skills": req_score, "Pref Skills": pref_score, "Edu": edu_score, "Proj": proj_score}
    }

uploaded_files = st.file_uploader("📂 Upload Candidate Resumes (PDF)", type=["pdf"], accept_multiple_files=True)

if st.button("🚀 Process & Generate AI
