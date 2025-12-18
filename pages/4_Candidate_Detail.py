import streamlit as st
import sys
from pathlib import Path

# Add project root to sys.path
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

import json
import pandas as pd
from src.auth import get_current_user
from src.db import (
    get_jobs, 
    get_candidates_for_job, 
    get_application_details,
    update_application_evaluation,
    update_application_stage,
    add_note,
    get_notes,
    get_user_role,
    create_candidate,
    create_application
)
from src.llm import evaluate_candidate, generate_outreach, parse_resume
from src.utils import extract_text_from_file
from src.ui import apply_custom_css, display_theme_toggle

st.set_page_config(page_title="Candidate Detail", page_icon="🧑‍💼", layout="wide")
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
    
# --- Sidebar Selection ---
st.sidebar.header("Select Candidate")
role = get_user_role(user.id)
jobs = get_jobs(role or "recruiter", user.id)
job_map = {j["title"]: j["id"] for j in jobs}

selected_job_title = st.sidebar.selectbox("1. Select Job", list(job_map.keys()) if jobs else [])

selected_app_id = None
if selected_job_title:
    job_id = job_map[selected_job_title]
    candidates = get_candidates_for_job(job_id)
    cand_map = {f"{c['candidates']['full_name']} ({c['overall_score'] or 'N/A'})": c['id'] for c in candidates}
    
    # helper for creating new
    cand_map["+ Add New Candidate"] = "NEW"
    
    selected_cand_label = st.sidebar.radio("2. Select Candidate", list(cand_map.keys()))
    if selected_cand_label:
        selected_app_id = cand_map[selected_cand_label]

# --- Main Content ---

if selected_app_id == "NEW":
    st.header("📥 Add New Candidate")
    uploaded_resume = st.file_uploader("Upload Resume (PDF/DOCX)", type=["pdf", "docx", "txt"])
    
    if uploaded_resume:
        if st.button("Parse & Add"):
            with st.spinner("Parsing Resume..."):
                text = extract_text_from_file(uploaded_resume, uploaded_resume.name)
                cand_parsed = parse_resume(text)
                
                if cand_parsed:
                    # Save Candidate
                    # Assume job_id is selected from sidebar
                    c_data = cand_parsed.dict()
                    c_data["resume_text"] = text
                    c_data["created_by"] = user.id
                    
                    # Insert Candidate
                    new_cand = create_candidate(c_data)
                    if new_cand:
                        # Create Application
                        app_data = {
                            "job_id": job_id,
                            "candidate_id": new_cand["id"],
                            "stage": "new"
                        }
                        new_app = create_application(app_data)
                        if new_app:
                            st.success("Candidate added successfully! Refreshing...")
                            st.session_state["selected_app_id"] = new_app["id"] # Try to persist selection?
                            st.rerun()
                        else:
                            st.error("Failed to create application.")
                    else:
                        st.error("Failed to create candidate record.")
                else:
                    st.error("Failed to parse resume.")

elif selected_app_id:
    # Load Data
    app_details = get_application_details(selected_app_id)
    if not app_details:
        st.error("Could not load application.")
        st.stop()
        
    candidate = app_details["candidates"]
    job = app_details["jobs"]
    
    st.title(f"{candidate['full_name']}")
    st.caption(f"Applied for: **{job['title']}** | Stage: **{app_details['stage'].upper()}** | Score: **{app_details['overall_score'] or 'N/A'}**")
    
    # Stage Mover
    new_stage = st.selectbox("Update Stage", ["new", "screened", "interview", "offer", "hired", "rejected"], 
                             index=["new", "screened", "interview", "offer", "hired", "rejected"].index(app_details['stage']))
    if new_stage != app_details['stage']:
        if update_application_stage(selected_app_id, new_stage):
            st.success(f"Moved to {new_stage}")
            st.rerun()

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📄 Profile", "🤖 AI Evaluation", "✉️ Outreach", "💬 Screening", "📝 Notes"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Experience & Skills")
            st.write(f"**Email:** {candidate.get('email')}")
            st.write(f"**Phone:** {candidate.get('phone')}")
            st.write(f"**Location:** {candidate.get('location')}")
            st.markdown("### Resume Text")
            st.text_area("Extracted Text", candidate.get("resume_text", ""), height=400)
            
        with col2:
            st.subheader("Links")
            links = candidate.get("links") or {}
            for k, v in links.items():
                st.markdown(f"[{k}]({v})")
    
    with tab2:
        st.header("AI Match Evaluation")
        
        if not app_details.get("ai_summary"):
            st.info("Not evaluated yet.")
            if st.button("✨ Run Evaluation"):
                with st.spinner("Evaluator Bot is reading..."):
                    # construct job and cand json
                    # We might need to parse JD text again or rely on stored fields
                    # We have job struct in DB, let's use that
                    eval_res = evaluate_candidate(job, candidate, candidate.get("resume_text", ""))
                    
                    if eval_res:
                        # Save
                        update_data = {
                            "overall_score": eval_res.overall_score,
                            "score_breakdown": eval_res.score_breakdown.dict(),
                            "ai_summary": eval_res.ai_summary,
                            "risk_flags": eval_res.risk_flags
                            # We could store strengths/questions in a separate JSONB col if schema supported, 
                            # or append to ai_summary. Schema has score_breakdown (jsonb) and ai_summary (text).
                            # Let's verify Schema.
                            # schema.sql: overall_score, score_breakdown, ai_summary, risk_flags
                            # We'll stick to that. strengths/concerns can go into 'score_breakdown' or we assume we append to summary.
                        }
                        update_application_evaluation(selected_app_id, update_data)
                        st.success("Evaluation Complete!")
                        st.rerun()
                    else:
                        st.error("Evaluation failed.")
        else:
            # Display Evaluation
            score = app_details.get("overall_score")
            st.metric("Overall Match Score", f"{score}/100")
            
            # Breakdown
            breakdown = app_details.get("score_breakdown")
            if breakdown:
                st.json(breakdown)
                
            st.subheader("Summary")
            st.write(app_details.get("ai_summary"))
            
            st.subheader("Risk Flags")
            flags = app_details.get("risk_flags")
            if flags:
                for f in flags:
                    st.error(f"🚩 {f}")
            else:
                st.success("No major risk flags detected.")

            if st.button("🔄 Re-run Evaluation"):
                 # Duplicate logic, simplified
                 pass

    with tab3:
        st.header("Generate Outreach")
        tone = st.select_slider("Tone", options=["friendly", "formal", "concise"])
        if st.button("Wait, Write Email"):
            outreach = generate_outreach(candidate.get("full_name").split(" ")[0], job.get("title"), "Acme Corp", tone) # Company name hardcoded for demo or add to settings
            if outreach:
                st.text_input("Subject", value=outreach.subject)
                st.text_area("Body", value=outreach.body, height=300)
    
    with tab4:
        st.header("Screening Interview (Simulated)")
        # Simple chat interface stored in session state momentarily (or Notes?)
        # For simplicity, we just have a text area for Q&A history and a "Summarize" button
        
        qa_history = st.text_area("Paste Interview Transcript / Q&A", height=300)
        if st.button("Analyze Screening"):
            # Call llm summarize
            st.info("Feature placeholder: LLM analyzes text and updates score.")
            
    with tab5:
        st.header("Team Notes")
        new_note = st.text_area("Add a note...")
        if st.button("Post Note"):
            if new_note:
                add_note(selected_app_id, user.id, new_note)
                st.success("Posted!")
                st.rerun()
        
        notes = get_notes(selected_app_id)
        for n in notes:
            st.markdown(f"**{n['profiles']['full_name']}** ({n['created_at']})")
            st.write(n['note'])
            st.divider()

else:
    st.info("Select a job and candidate from the sidebar.")
