import json
import time
import streamlit as st
import pandas as pd
import google.generativeai as genai
from pypdf import PdfReader
from jsonschema import validate
from datetime import datetime

st.set_page_config(page_title="Ultimate AI ATS", page_icon="🚀", layout="wide")
st.title("🚀 Ultimate AI-Powered ATS & Cover Letter Generator")
st.markdown("Get ATS Scores, Missing Skills, and Auto-Generated Cover Letters in one click!")
st.info("🔒 **Privacy Notice:** This app does not store your full resume or sensitive data. Only public metrics (Name, Score, Decision) are logged for tracking.")

st.sidebar.header("⚙️ Configuration")
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password", placeholder="AIzaSy...")

# --- ADMIN PANEL FOR YOU TO VIEW USERS ---
st.sidebar.markdown("---")
st.sidebar.subheader("🔐 Admin Panel (Owner Only)")
admin_pass = st.sidebar.text_input("Admin Password", type="password", placeholder="Enter password")
if admin_pass == "wasid123": # Tu yahan apna password change kar sakta hai
    st.sidebar.success("✅ Welcome Admin!")
    st.sidebar.markdown("### 📊 Recent User Activity")
    # Session state se temporary logs dikhayenge (Ya Google Sheets ka link laga sakte hain)
    if "activity_logs" in st.session_state and st.session_state["activity_logs"]:
        log_df = pd.DataFrame(st.session_state["activity_logs"])
        st.sidebar.dataframe(log_df, use_container_width=True)
    else:
        st.sidebar.info("No activity recorded in this session yet.")
elif admin_pass != "":
    st.sidebar.error("❌ Wrong Password")

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
    except Exception as e:
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
    except Exception as e:
        return None

def get_working_model(api_key):
    genai.configure(api_key=api_key)
    preferred_models = ['gemini-1.5-flash', 'gemini-1.5-flash-8b', 'gemini-2.0-flash']
    
    for model_name in preferred_models:
        try:
            m = genai.GenerativeModel(model_name)
            m.generate_content("test", generation_config={"max_output_tokens": 5})
            return m
        except Exception:
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
    except Exception as e:
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

if st.button("🚀 Process & Generate AI Report"):
    if not api_key:
        st.error("⚠️ Please enter your Gemini API Key in the sidebar!")
    elif not uploaded_files:
        st.error("⚠️ Please upload at least one PDF resume.")
    else:
        with st.spinner("AI is analyzing resumes... ⏳"):
            model = get_working_model(api_key)
            dynamic_reqs = get_jd_reqs(job_description_text, model)

            report_data = []
            
            # Session state initialize for tracking logs
            if "activity_logs" not in st.session_state:
                st.session_state["activity_logs"] = []

            for i, f in enumerate(uploaded_files):
                text = extract_text_from_pdf(f)
                if not text.strip():
                    continue
                
                cand = parse_resume(text, model)
                if cand:
                    scores = score_candidate(cand, dynamic_reqs)
                    cover_letter = generate_cover_letter(cand, job_description_text, model)
                    
                    candidate_name = cand['full_name']
                    candidate_score = scores['total']
                    candidate_decision = scores['recommendation']
                    
                    report_data.append({"Name": candidate_name, "Score": candidate_score, "Decision": candidate_decision})
                    
                    # --- TRACKING LOG SAVED SECURELY (Privacy Protected) ---
                    log_entry = {
                        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Candidate Name": candidate_name,
                        "ATS Score": candidate_score,
                        "Status": candidate_decision
                    }
                    st.session_state["activity_logs"].append(log_entry)
                    
                    with st.expander(f"👤 {candidate_name} — Score: {candidate_score}/100 ({candidate_decision})", expanded=True):
                        st.progress(candidate_score / 100)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("📊 **Score Breakdown:**")
                            st.write(f"- Experience: {scores['breakdown']['Exp']}/20 | Projects: {scores['breakdown']['Proj']}/10")
                            st.write(f"- Core Skills: {scores['breakdown']['Req Skills']}/40 | Bonus Skills: {scores['breakdown']['Pref Skills']}/20")
                            
                        with col2:
                            st.write("🛠️ **AI Upgrade Advice:**")
                            if scores['missing_req']: st.error(f"**Missing Core Skills:** {', '.join(scores['missing_req'])}")
                            else: st.success("✅ All Core Skills Matched!")
                            if scores['missing_pref']: st.warning(f"**Missing Bonus Skills:** {', '.join(scores['missing_pref'])}")
                        
                        st.markdown("### ✉️ AI-Generated Cover Letter")
                        st.text_area(f"Tailored for {candidate_name} (Copy-Paste Ready)", value=cover_letter, height=250, key=f"cl_{candidate_name}_{i}")

            if report_data:
                st.markdown("### 🏆 Overall Leaderboard")
                df = pd.DataFrame(report_data)
                st.dataframe(df, use_container_width=True)
