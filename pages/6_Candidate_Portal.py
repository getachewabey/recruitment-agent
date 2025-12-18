import streamlit as st
import sys
from pathlib import Path

# Add project root to sys.path
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))
import pandas as pd
from src.auth import get_current_user
from src.db import (
    get_jobs, 
    get_candidate_profile, 
    create_candidate_profile, 
    update_candidate_profile, 
    apply_for_job_as_candidate, 
    get_my_applications
)
from src.utils import extract_text_from_file
from src.llm import parse_resume
from src.ui import apply_custom_css, display_theme_toggle

st.set_page_config(page_title="Candidate Portal", page_icon="🚀", layout="wide")
apply_custom_css()
display_theme_toggle()

user = get_current_user()
if not user:
    st.stop()

# Logout Option
from src.auth import logout_user
st.sidebar.write(f"User: {user.email}")
if st.sidebar.button("Logout"):
    logout_user()

st.title("🚀 Career Portal")

# 1. Fetch or Create Candidate Profile
candidate = get_candidate_profile(user.id)

# Initialize Session State for profile creation if needed
if "parsed_profile" not in st.session_state:
    st.session_state.parsed_profile = {}

if not candidate:
    st.info("👋 Welcome! Let's build your profile to get started.")
    
    with st.container():
        st.subheader("Upload Resume")
        uploaded_resume = st.file_uploader("Upload PDF/DOCX to auto-fill", type=["pdf", "docx", "txt"])
        
        if uploaded_resume and st.button("Parse Resume"):
            with st.spinner("Analyzing resume..."):
                text = extract_text_from_file(uploaded_resume, uploaded_resume.name)
                parsed = parse_resume(text)
                if parsed:
                    st.session_state.parsed_profile = parsed.dict()
                    st.session_state.parsed_profile["resume_text"] = text
                    st.success("Resume parsed! Please review below.")
                else:
                    st.error("Could not parse resume.")

        with st.form("create_profile_form"):
            st.subheader("Your Details")
            # Defaults from parsed
            defaults = st.session_state.parsed_profile
            
            full_name = st.text_input("Full Name", value=defaults.get("full_name", ""))
            email = st.text_input("Email", value=defaults.get("email", user.email))
            phone = st.text_input("Phone", value=defaults.get("phone", ""))
            location = st.text_input("Location", value=defaults.get("location", ""))
            
            links_data = defaults.get("links") or {}
            linkedin = st.text_input("LinkedIn URL", value=links_data.get("linkedin", ""))
            
            if st.form_submit_button("Create Profile"):
                if not full_name:
                    st.error("Name is required.")
                else:
                    new_data = {
                        "full_name": full_name,
                        "email": email,
                        "phone": phone,
                        "location": location,
                        "links": {"linkedin": linkedin},
                        "resume_text": defaults.get("resume_text", "")
                    }
                    res = create_candidate_profile(user.id, new_data)
                    if res:
                        st.success("Profile created!")
                        st.rerun()
    st.stop() # Don't show tabs until profile exists

# --- Main Portal Interface (Profile Exists) ---

tab1, tab2, tab3 = st.tabs(["💼 Job Board", "📂 My Applications", "👤 My Profile"])

with tab1:
    st.header("Open Roles")
    # Fetch OPEN jobs only
    # We can reuse get_jobs but we need to ensure it uses the "open" filter if not admin.
    # Actually get_jobs in db.py selects all. Let's filter or assume RLS handles it?
    # RLS says "Candidates can view open jobs". So `supabase.table('jobs').select('*')` will return ONLY open jobs for this user.
    # But get_jobs has a role check. Let's check db.py...
    # get_jobs checks for 'manager' or executes select *.
    # We should just call a simple fetch here or accept get_jobs behavior.
    
    # Direct fetch to rely on RLS
    from src.db import get_supabase_client
    supabase = get_supabase_client()
    res = supabase.table("jobs").select("*").eq("status", "open").execute()
    jobs = res.data
    
    if jobs:
        st.markdown("### 🎯 Featured Opportunities")
        
        
        for j in jobs:
            # Custom Card Container
            with st.container():
                st.markdown(f"""
                <div style="background-color: var(--card-bg); padding: 20px; border-radius: 10px; border: 1px solid var(--card-border); margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: background-color 0.2s ease-in-out;">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <h3 style="margin: 0; color: var(--text-main);">{j['title']}</h3>
                            <p style="margin: 5px 0 10px 0; color: var(--text-sub); font-size: 0.9em;">
                                📍 {j.get('location', 'Remote')} &nbsp; | &nbsp; 💼 {j.get('employment_type', 'Full-time')} &nbsp; | &nbsp; 🏢 {j.get('team', 'General')}
                            </p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                
                # Helper to format JD text
                jd_text = j.get("jd_text", "No description available.")
                # Fix aggressive headers - replace # or ## with smaller headers or bold
                # This prevents the huge "JOB QUALIFICATIONS" seen in screenshot
                cleaned_jd = jd_text.replace("# ", "### ").replace("## ", "#### ")
                
                c1, c2 = st.columns([4, 1])
                with c1:
                    with st.expander("📄 Read Job Description"):
                        st.markdown(cleaned_jd)
                with c2:
                    if st.button(f"🚀 Apply Now", key=f"apply_{j['id']}", use_container_width=True):
                        if apply_for_job_as_candidate(j['id'], candidate['id']):
                            st.success(f"Applied!")
                            st.balloons()
            st.write("")
    else:
        st.info("No open positions at the moment.")

with tab2:
    st.header("My Applications")
    my_apps = get_my_applications(candidate['id'])
    
    if my_apps:
        for app in my_apps:
            job_title = app['jobs']['title']
            status = app['stage'].upper()
            date = app['created_at'].split("T")[0]
            
            with st.container():
                st.markdown(f"### {job_title}")
                st.caption(f"Applied: {date}")
                
                # Status Pill
                color = "blue"
                if status == "HIRED": color = "green"
                if status == "REJECTED": color = "red"
                st.markdown(f":{color}[**Status: {status}**]")
                st.divider()
    else:
        st.info("You haven't applied to any jobs yet.")

with tab3:
    st.header("My Profile")
    
    with st.form("edit_profile"):
        full_name = st.text_input("Full Name", value=candidate.get("full_name", ""))
        email = st.text_input("Email", value=candidate.get("email", ""))
        phone = st.text_input("Phone", value=candidate.get("phone", ""))
        location = st.text_input("Location", value=candidate.get("location", ""))
        
        # Resume text
        st.text_area("Resume Content (Parsed)", value=candidate.get("resume_text", ""), height=200, disabled=True)
        
        if st.form_submit_button("Update Profile"):
            updates = {
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "location": location
            }
            if update_candidate_profile(candidate['id'], updates):
                st.success("Updated!")
                st.rerun()
