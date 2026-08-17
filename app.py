import json
import time
import streamlit as st
import pandas as pd
import google.generativeai as genai
from pypdf import PdfReader
from jsonschema import validate
from datetime import datetime

st.set_page_config(page_title="Ultimate AI ATS & Talent Matcher", page_icon="⚡", layout="wide")

# Custom CSS with Professional Modern Tech Theme & Sleek Cards
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #1e293b 100%);
        color: #f8fafc;
    }
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        color: #38bdf8;
        text-align: center;
        margin-bottom: 0px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .sub-title {
        font-size: 1.2rem;
        color: #94a3b8;
        text-align: center;
        margin-bottom: 30px;
    }
    .stExpander {
        background-color: rgba(30, 41, 59, 0.7) !important;
        border: 1px solid #334155 !important;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 15px;
        color: #f8fafc !important;
    }
    .footer-text {
        text-align: center;
        color: #64748b;
        font-size: 0.9rem;
        margin-top: 50px;
        padding: 20px;
        border-top: 1px solid #334155;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">⚡ Ultimate AI-Powered ATS & Talent Matcher</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Instantly calculate ATS scores, detect skill gaps, generate interview questions, and export cover letters with Gemini AI.</p>', unsafe_allow_html=True)

st.info("🔒 **Privacy Notice:** This app does not store your full resume or sensitive text. Only public metrics (Name, Score, Decision) are logged securely for tracking.")

st.sidebar.header("⚙️ Configuration")
st.sidebar.warning("⚠️ **Note:** Your API Key is used only for this session and is not stored. Please use your own API Key carefully.")
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password", placeholder="AIzaSy...")

# --- SECURE ADMIN PANEL ---
st.sidebar.markdown("---")
st.sidebar.subheader("🔐 Admin Panel (Owner Only)")
admin_pass = st.sidebar.text_input("Admin Password", type="password", placeholder="Enter secure password")

try:
    correct_pass = st.secrets["ADMIN_PASSWORD"]
except:
    correct_pass = "DefaultSecret999"

if admin_pass == correct_pass:
    st.sidebar.success("✅ Welcome Admin!")
    st.sidebar.markdown("### 📊 Recent User Activity")
    if "activity_logs" in st.session_state and st.session_state["activity_logs"]:
        log_df = pd.DataFrame(st.session_state["activity_logs"])
        st.sidebar.dataframe(log_df, use_container_width=True)
    else:
        st.sidebar.info("No activity recorded in this session yet.")
elif admin_pass != "":
    st.sidebar.error("❌ Wrong Password")

role_presets = {
    "Custom / Paste Below": "We are looking for a professional to join our team.\nMinimum 2 years of experience required.\nRequired Skills: Python, SQL, Problem Solving.",
    "AI/ML Engineer": "We are looking for an AI/ML Engineer to join our team.\nMinimum 2 years of experience required.\nRequired Skills: Python, Machine Learning, Deep Learning, SQL.\nPreferred Skills: PyTorch, TensorFlow, AWS, Docker, NLP.\nMinimum Education: bachelor.",
    "Data Scientist": "We are looking for a Data Scientist.\nMinimum 2 years of experience required.\nRequired Skills: Python, Pandas, Statistics, SQL, Machine Learning.\nPreferred Skills: Tableau, Scikit-Learn, BigQuery.\nMinimum Education: bachelor.",
    "Full Stack Python Developer": "We are looking for a Python Developer.\nMinimum 1 year of experience required.\nRequired Skills: Python, Django, REST APIs, HTML, CSS, SQL.\nPreferred Skills: React, Docker, AWS.\nMinimum Education: bachelor."
}

st.sidebar.markdown("---")
st.sidebar.subheader("📝 Target Role Description")
selected_preset = st.sidebar.selectbox("📌 Select Preset Job Role", list(role_presets.keys()))
default_jd = role_presets[selected_preset]
job_description_text = st.sidebar.text_area("Edit or Paste Job Description Here", value=default_jd, height=220)

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
    except:
        return ""

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
    try: 
        return json.loads(clean_json(raw_text))
    except:
        return None

def get_working_model(api_key):
    genai.configure(api_key=api_key)
    preferred_models = ['gemini-1.5-flash', 'gemini-1.5-flash-8b', 'gemini-2.0-flash']
    
    for model_name in preferred_models:
        try:
            m = genai.GenerativeModel(model_name)
            m.generate_content("test", generation_config={"max_output_tokens": 5})
            return m
        except:
            continue
            
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for name in models:
            clean_name = name.replace("models/", "")
            if '2.5' in clean_name or '3.7' in clean_name:
                continue 
            if 'flash' in name.lower():
                try:
                    m = genai.GenerativeModel(clean_name)
                    m.generate_content("test", generation_config={"max_output_tokens": 5})
                    return m
                except:
                    continue
    except:
        pass
    
    return genai.GenerativeModel('gemini-1.5-flash')

def safe_generate(model, prompt):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            time.sleep(3)
            return response
        except Exception as e:
            if "429" in str(e) or "Quota exceeded" in str(e):
                if attempt < max_retries - 1:
                    time.sleep(20)
                    continue
            raise e
    return None

def get_jd_reqs(jd, model):
    prompt = f"Analyze Job Description and return JSON exactly matching keys: min_experience (int), required_skills (array), preferred_skills (array), min_education (string). JD: {jd}"
    try:
        response = safe_generate(model, prompt)
        if response and response.text:
            res = safe_parse(response.text)
            if res: return res
    except:
        pass
    return {"min_experience": 0, "required_skills": [], "preferred_skills": [], "min_education": "bachelor"}

def parse_resume(text, model):
    prompt = f"Parse resume text into JSON EXACTLY matching schema. Keys: full_name (string), years_experience (integer), technical_skills (array of strings), projects (array of strings), education_level (high_school/bachelor/master/phd/other). Resume: {text}"
    try:
        response = safe_generate(model, prompt)
        if response and response.text:
            raw_response = response.text
            parsed = safe_parse(raw_response)
            if parsed:
                if "years_experience" in parsed: 
                    parsed["years_experience"] = int(float(parsed["years_experience"]))
                validate(instance=parsed, schema=RESUME_SCHEMA)
                return parsed
    except:
        pass
    return None

def generate_cover_letter(cand, jd, model):
    prompt = f"""Write a professional, modern, and highly persuasive Cover Letter for {cand['full_name']} applying for this Job Description: {jd}.
    Highlight their skills: {cand.get('technical_skills', [])} and projects: {cand.get('projects', [])}. 
    Keep it under 300 words. Do not include placeholders like [Your Address]. Make it ready to copy-paste."""
    try:
        response = safe_generate(model, prompt)
        if response and response.text:
            return response.text
    except:
        pass
    return "⚠️ Failed to generate cover letter."

def generate_interview_questions(cand, model):
    prompt = f"Generate 3 smart technical interview questions and 2 HR questions tailored for candidate named {cand['full_name']} based on skills: {cand.get('technical_skills', [])} and projects: {cand.get('projects', [])}. Keep it clear and bulleted."
    try:
        response = safe_generate(model, prompt)
        if response and response.text:
            return response.text
    except:
        pass
    return "Could not generate questions."

def optimize_resume_bullets(cand, model):
    prompt = f"Provide 3 high-impact professional resume bullet point rewrites to improve resume strength for {cand['full_name']} who has skills {cand.get('technical_skills', [])}."
    try:
        response = safe_generate(model, prompt)
        if response and response.text:
            return response.text
    except:
        pass
    return "Could not generate optimization suggestions."

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
        "breakdown": {"Exp": exp_score, "Req Skills": req_score, "Pref Skills": pref_score, "Edu": edu_score, "Proj": proj_score}
    }

uploaded_files = st.file_uploader("📂 Upload Candidate Resumes (PDF)", type=["pdf"], accept_multiple_files=True)

if st.button("🚀 Process & Generate AI Report", type="primary"):
    if not api_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar!")
    elif not uploaded_files:
        st.error("⚠️ Please upload at least one PDF resume.")
    else:
        with st.spinner("🤖 AI is analyzing resumes and crafting insights... ⏳"):
            model = get_working_model(api_key)
            dynamic_reqs = get_jd_reqs(job_description_text, model)

            report_data = []
            
            if "activity_logs" not in st.session_state:
                st.session_state["activity_logs"] = []

            for i, f in enumerate(uploaded_files):
                text = extract_text_from_pdf(f)
                if not text.strip():
                    continue
                
                , cand = parse_resume(text, model), parse_resume(text, model) # standard parsing call below
