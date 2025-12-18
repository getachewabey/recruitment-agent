
import streamlit as st
import json
from src.auth import get_current_user
from src.db import create_job, get_jobs, get_user_role
from src.llm import parse_job_description
import pandas as pd
from src.constants import DEFAULT_INTERVIEW_STAGES
from src.utils import extract_text_from_file
from src.ui import apply_custom_css, display_theme_toggle

st.set_page_config(page_title="Jobs", page_icon="💼")
apply_custom_css()
display_theme_toggle()

user = get_current_user()
if not user:
    st.warning("Please log in.")
    st.stop()

from src.db import get_user_role
role = get_user_role(user.id)
if role == 'candidate':
    st.error("Access Denied. Please use the Candidate Portal.")
    st.stop()

st.title("💼 Job Requisitions")

role = get_user_role(user.id)
if not role:
    st.error("Could not determine user role.")
    st.stop()

# --- Create New Job Section ---
with st.expander("➕ Create New Job", expanded=False):
    st.subheader("Step 1: Upload or Paste JD")
    
    jd_file = st.file_uploader("Upload Job Description (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"])
    jd_text_input = st.text_area("Or Paste Job Description Text", height=200)
    
    # State for parsed data
    if "parsed_job" not in st.session_state:
        st.session_state["parsed_job"] = None

    if st.button("✨ Parse with AI"):
        text_to_parse = ""
        if jd_file:
            text_to_parse = extract_text_from_file(jd_file, jd_file.name)
        elif jd_text_input:
            text_to_parse = jd_text_input
            
        if text_to_parse:
            with st.spinner("Analyzing Job Description..."):
                parsed = parse_job_description(text_to_parse)
                if parsed:
                    st.session_state["parsed_job"] = parsed
                    st.session_state["jd_text_full"] = text_to_parse
                    st.success("Parsed successfully!")
                else:
                    st.error("AI could not parse the format.")
        else:
            st.warning("Please provide text or a file.")

    st.markdown("---")
    st.subheader("Step 2: Review & Edit Details")
    
    # Form
    with st.form("create_job_form"):
        # Pre-fill if parsed
        parsed_data = st.session_state.get("parsed_job")
        
        title = st.text_input("Job Title", value=parsed_data.title if parsed_data else "")
        team = st.text_input("Team", value=parsed_data.team if parsed_data else "")
        col1, col2 = st.columns(2)
        location = col1.text_input("Location", value=parsed_data.location if parsed_data else "")
        emp_type = col2.text_input("Employment Type", value=parsed_data.employment_type if parsed_data else "")
        
        col3, col4 = st.columns(2)
        min_comp = col3.number_input("Min Comp", value=parsed_data.comp_range_min if parsed_data and parsed_data.comp_range_min else 0.0)
        max_comp = col4.number_input("Max Comp", value=parsed_data.comp_range_max if parsed_data and parsed_data.comp_range_max else 0.0)

        must_skills = st.text_area("Must Have Skills (comma separated)", 
                                   value=", ".join(parsed_data.must_have_skills) if parsed_data else "")
        
        nice_skills = st.text_area("Nice To Have Skills (comma separated)", 
                                   value=", ".join(parsed_data.nice_to_have_skills) if parsed_data else "")
        
        responsibilities = st.text_area("Responsibilities (one per line)", 
                                        value="\n".join(parsed_data.responsibilities) if parsed_data else "")

        # Interview Stages (Default or parsed?)
        # For simplicity, stringify JSON to edit, or just standard list
        stages_val = json.dumps(parsed_data.interview_stages if parsed_data and parsed_data.interview_stages else DEFAULT_INTERVIEW_STAGES, indent=2)
        stages_input = st.text_area("Interview Stages (JSON)", value=stages_val, height=150)
        
        submitted = st.form_submit_button("Create Job")
        
        if submitted:
            if not title:
                st.error("Title is required")
            else:
                # Prepare data
                try:
                    stages_json = json.loads(stages_input)
                except:
                    stages_json = DEFAULT_INTERVIEW_STAGES
                
                final_jd_text = st.session_state.get("jd_text_full", jd_text_input or "")
                
                new_job = {
                    "created_by": user.id,
                    "title": title,
                    "team": team,
                    "location": location,
                    "employment_type": emp_type,
                    "comp_range_min": min_comp,
                    "comp_range_max": max_comp,
                    "must_have_skills": [s.strip() for s in must_skills.split(",") if s.strip()],
                    "nice_to_have_skills": [s.strip() for s in nice_skills.split(",") if s.strip()],
                    "responsibilities": [r.strip() for r in responsibilities.split("\n") if r.strip()],
                    "interview_stages": stages_json,
                    "jd_text": final_jd_text,
                    "status": "open"
                }
                
                res = create_job(new_job)
                if res:
                    st.success(f"Job '{title}' created!")
                    # Clear state
                    st.session_state["parsed_job"] = None
                    st.rerun()
                else:
                    st.error("Failed to save job.")

# --- List Jobs Section ---
st.header("Active Requisitions")

jobs_list = get_jobs(role, user.id)

if jobs_list:
    # Use a dataframe for clean view
    # Format for display
    display_data = []
    for j in jobs_list:
        display_data.append({
            "ID": j["id"],
            "Title": j["title"],
            "Team": j["team"],
            "Location": j["location"],
            "Status": j["status"],
            "Created": j["created_at"] or ""
        })
        
    st.dataframe(display_data, use_container_width=True)
else:
    st.info("No jobs found.")
