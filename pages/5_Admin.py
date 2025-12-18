import streamlit as st

import pandas as pd
from src.auth import get_current_user
from src.db import get_user_role, get_audit_logs, get_all_users, update_user_role
from src.ui import apply_custom_css, display_theme_toggle

st.set_page_config(page_title="Admin Console", page_icon="🛡️")
apply_custom_css()
display_theme_toggle()

user = get_current_user()
if not user:
    st.warning("Please log in.")
    st.stop()

# Check Admin Role
current_role = get_user_role(user.id)
if current_role != 'admin':
    st.error("Access Denied. Admin privileges required.")
    st.stop()

st.title("🛡️ Admin Console")

tab1, tab2 = st.tabs(["👥 User Management", "📜 Audit Logs"])

with tab1:
    st.header("Manage Users")
    users = get_all_users()
    if users:
        # editable data editor? or just list
        for u in users:
            with st.expander(f"{u.get('full_name') or u.get('id')} ({u['role']})"):
                st.write(f"ID: {u['id']}")
                st.write(f"Current Role: **{u['role']}**")
                
                new_role = st.selectbox("Change Role", ["admin", "recruiter", "manager", "candidate"], index=["admin", "recruiter", "manager", "candidate"].index(u['role']), key=f"role_{u['id']}")
                if new_role != u['role']:
                    if st.button("Update Role", key=f"btn_{u['id']}"):
                        if update_user_role(u['id'], new_role):
                            st.success("Role Updated!")
                            st.rerun()
    else:
        st.info("No users found.")

with tab2:
    st.header("System Audit Log")
    logs = get_audit_logs()
    if logs:
        data = []
        for l in logs:
            data.append({
                "Time": l['created_at'],
                "Actor": l['profiles']['full_name'] if l['profiles'] else "System",
                "Action": l['action'],
                "Entity Type": l['entity_type'],
                "Entity ID": l['entity_id']
            })
        st.dataframe(data, use_container_width=True)
    else:
        st.info("No audit logs.")
