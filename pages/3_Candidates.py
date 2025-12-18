import streamlit as st

import pandas as pd
from src.auth import get_current_user
from src.db import get_jobs, get_candidates_for_job, get_user_role
from src.ui import apply_custom_css, display_theme_toggle

st.set_page_config(page_title="Candidates", page_icon="👥")
apply_custom_css()
display_theme_toggle()

user = get_current_user()
if not user:
    st.warning("Please log in.")
    st.stop()
    
role = get_user_role(user.id)
if role == 'candidate':
    st.error("Access Denied. Please use the Candidate Portal.")
    st.stop()

st.title("👥 Candidate Pipeline")

# Filter by Job
role = get_user_role(user.id)
jobs = get_jobs(role or "recruiter", user.id)

if not jobs:
    st.warning("No jobs found. Create unique jobs first.")
    st.stop()

job_options = {j["title"]: j["id"] for j in jobs}
selected_job_title = st.selectbox("Select Job", list(job_options.keys()))
selected_job_id = job_options[selected_job_title]

# Fetch Candidates
candidates = get_candidates_for_job(selected_job_id)

st.divider()

if not candidates:
    st.info("No candidates applied for this job yet. Add some in 'Candidate Detail' or Upload.")
    st.write("To add a candidate, go to the **Candidate Detail** page (or we can add an upload button here in future).") # Simplification for now, usually we upload here.
    
    # Actually, let's allow adding a candidate here or redirecting to specific flow.
    # For now, just listing.
else:
    # Display Metrics
    df = pd.DataFrame(candidates)
    
    # Flatten candidates jsonb if needed, but get_candidates_for_job does a join
    # The structure from Supabase join is:
    # { ..., "candidates": { "full_name": ... } }
    
    # Normalize for table
    table_rows = []
    for c in candidates:
        c_detail = c.get("candidates", {})
        table_rows.append({
            "Candidate Name": c_detail.get("full_name", "Unknown"),
            "Stage": c.get("stage"),
            "Match Score": c.get("overall_score"),
            "Email": c_detail.get("email"),
            "Applied": c.get("created_at"),
            "Candidate ID": c.get("candidate_id"), 
            "Application ID": c.get("id")
        })
        
    df_display = pd.DataFrame(table_rows)
    
    # Filters
    col1, col2 = st.columns(2)
    stage_filter = col1.multiselect("Filter by Stage", options=df_display["Stage"].unique())
    min_score = col2.slider("Min Match Score", 0, 100, 0)
    
    filtered_df = df_display.copy()
    if stage_filter:
        filtered_df = filtered_df[filtered_df["Stage"].isin(stage_filter)]
    if min_score > 0:
        filtered_df = filtered_df[filtered_df["Match Score"] >= min_score]
        
    st.dataframe(
        filtered_df, 
        column_config={
            "Match Score": st.column_config.ProgressColumn(
                "Match Score", min_value=0, max_value=100, format="%d"
            ),
        },
        use_container_width=True
    )
    
    st.caption("Copy 'Candidate ID' to view details in the Detail page (Navigation limitation of Streamlit MP without query params fully utilized).")
