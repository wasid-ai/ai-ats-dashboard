#  Ultimate AI-Powered ATS & Talent Matcher

A smart, modern, and high-performance Applicant Tracking System (ATS) built using **Python**, **Streamlit**, and **Google Gemini AI**. Designed to help recruiters and job seekers instantly parse resumes, calculate exact ATS scores, detect missing skills, and auto-generate tailored cover letters.

---

##  Complete Project Journey & What We Have Built / Updated

Here is a step-by-step breakdown of everything implemented, updated, and secured in this project:

### 1. Core Resume & AI Features
*  PDF Resume Parsing:** Allows uploading multiple PDF resumes simultaneously. The app extracts text seamlessly using `pypdf`.
*  Dynamic Job Description Analysis:** Powered by Google Gemini AI to automatically extract required skills, experience, and education levels from any pasted job description.
* **Smart Scoring Mechanism:** Calculates a total score out of 100 based on experience match, core required skills, preferred bonus skills, education level, and project counts.
*  Skill Gap & Upgrade Advice:** Instantly identifies missing core and bonus skills so applicants know exactly what to improve.
*  AI Cover Letter Generator:** Automatically writes professional, persuasive, and ready-to-copy cover letters customized for each candidate.
*  Interactive Leaderboard:** Displays a clean leaderboard table summarizing all processed candidates and their decision statuses (`STRONG HIRE`, `PROCEED TO INTERVIEW`, `NEEDS UPGRADE`).

### 2. UI, Design & Visual Upgrades (Recently Added)
*  Modern Gradient Background:** Upgraded the app appearance with a sleek, professional gradient background instead of a plain layout.
*  Custom UI Cards & Styling:** Added clean borders, shadow effects, responsive expanders, and custom headings.
*  Celebratory Animations:** Integrated automatic celebratory balloons whenever a candidate scores 80 or above (`STRONG HIRE`).
*  Developer Credits Footer:** Added a professional branding footer (`Developed with ❤️ by Wasid Khan`) at the bottom of the app.

### 3. Security & Admin Panel Upgrades (Crucial Updates)
*  Secure Admin Panel:** A password-protected sidebar area where the owner can view live session tracking logs (Candidate Name, ATS Score, and Status).
*  Hardcoded Password Removal (Updated for Security):** Initially, passwords were kept inside the code. To prevent anyone from viewing the password on GitHub, we updated it to use **Streamlit Secrets** (`st.secrets["ADMIN_PASSWORD"]`). 
*  Privacy & Safety Notices:** Added clear warnings and notices regarding session-only API key usage and privacy compliance so users feel secure.

---

##  Future Features We Can Add Next

*  Direct Export Options:** Download generated cover letters and reports as `.docx` or `.pdf` files.
*  Permanent Database:** Integrate Supabase or MongoDB to save activity logs permanently across refreshes.
*  Head-to-Head Comparison:** Compare two resumes side-by-side against the same job description.
* **📧 Email Integration:** Send generated cover letters directly to candidates via email.

---

##  Tech Stack Used
* **Frontend / UI:** Streamlit
* **AI Model Engine:** Google Gemini API (`gemini-1.5-flash`, etc.)
* **Data & Validation:** Pandas, PyPDF, JSON Schema
