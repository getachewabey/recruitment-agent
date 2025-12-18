import streamlit as st

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.auth import get_current_user
from src.db import get_user_role, get_dashboard_stats
from src.ui import apply_custom_css, display_theme_toggle

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
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

st.title("📊 Recruitment Command Center")
st.markdown("Overview of your hiring pipeline.")
st.divider()

# Fetch Data
role = get_user_role(user.id)
with st.spinner("Crunching numbers..."):
    stats = get_dashboard_stats(user.id, role or "recruiter")

# --- Top Level Metrics ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Active Jobs", stats["open_jobs"], help="Jobs with 'Open' status")
c2.metric("Total Candidates", stats["total_candidates"], help="Total applications received")
# Simple conversion rate (Hired / Total)
conversion = 0
if stats["total_candidates"] > 0:
    conversion = (stats["funnel"].get("hired", 0) / stats["total_candidates"]) * 100
c3.metric("Hired", stats["funnel"].get("hired", 0))
c4.metric("Conversion Rate", f"{conversion:.1f}%")

st.divider()

# --- Main Charts ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("Candidate Pipeline")
    # Funnel Chart
    funnel_data = stats["funnel"]
    stages_ordered = ["new", "screened", "interview", "offer", "hired"] # Exclude rejected for funnel flow usually? Or include.
    
    # Let's filter out 0s for cleaner chart if desired, or keep to show dropoff
    values = [funnel_data.get(s, 0) for s in stages_ordered]
    
    fig = go.Figure(go.Funnel(
        y=stages_ordered,
        x=values,
        textinfo="value+percent initial"
    ))
    fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Action Needed")
    # Highlight things stuck in 'New' 
    new_count = funnel_data.get("new", 0)
    interview_count = funnel_data.get("interview", 0)
    
    st.info(f"**{new_count}** Candidates waiting for review.")
    st.warning(f"**{interview_count}** Candidates in Interview stage.")
    
    with st.expander("Show Rejected Count"):
        st.write(f"{funnel_data.get('rejected', 0)} Rejected")

# --- Recent Activity ---
st.subheader("Recent Applications")
recent = stats.get("recent_activity", [])
if recent:
    formatted_activity = []
    for a in recent:
        cand_name = a['candidates']['full_name'] if a['candidates'] else "Unknown"
        job_title = a['jobs']['title'] if a['jobs'] else "Unknown"
        formatted_activity.append({
            "Time": a['created_at'].split("T")[0], # Simple date
            "Candidate": cand_name,
            "Job": job_title,
            "Stage": a['stage'].upper()
        })
    st.dataframe(pd.DataFrame(formatted_activity), use_container_width=True, hide_index=True)
else:
    st.caption("No recent activity.")
