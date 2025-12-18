import streamlit as st
from src.auth import login_user, logout_user, get_current_user
from src.ui import apply_custom_css, display_theme_toggle

# Page Config
st.set_page_config(
    page_title="AI Recruitment Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_css()
display_theme_toggle()

# Auth Check
user = get_current_user()

if user:
    # Authenticated View
    from src.db import get_user_role
    role = get_user_role(user.id)
    
    if role == 'candidate':
        st.sidebar.write(f"User: {user.email}")
        if st.sidebar.button("Logout", key="logout_candidate_app"):
            logout_user()
            
        st.title("👋 Welcome Candidate!")
        st.markdown("Head to the **Candidate Portal** in the sidebar to view jobs.")
        st.info("Other pages are restricted to Recruiter use.")
    else:
        st.sidebar.title("Navigation")
        st.sidebar.write(f"Logged in: {user.email}")
        if st.sidebar.button("Logout"):
            logout_user()
        
        st.title("👋 Welcome to RecruiterAI")
        st.markdown("""
        Use the sidebar to navigate to:
        - **Dashboard**: View pipeline stats.
        - **Jobs**: Manage job requisitions.
        - **Candidates**: Track and evaluate applicants.
        """)
        st.info("Select a page from the sidebar to begin.")

else:
    # Login View
    st.title("🔐 Login / Sign Up")
    
    tab_login, tab_signup = st.tabs(["Login", "Sign Up (Candidates)"])
    
    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In")
            
            if submitted:
                session, user_obj = login_user(email, password)
                if session:
                    st.session_state["user"] = user_obj
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
                    
    with tab_signup:
        st.markdown("Create a candidate account to apply for jobs.")
        with st.form("signup_form"):
            s_email = st.text_input("Email")
            s_pass = st.text_input("Password", type="password")
            s_name = st.text_input("Full Name")
            s_submit = st.form_submit_button("Create Account")
            
            if s_submit:
                if len(s_pass) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    # Sign up
                    from src.db import get_supabase_client
                    sb = get_supabase_client()
                    try:
                        res = sb.auth.sign_up({
                            "email": s_email, 
                            "password": s_pass,
                            "options": {
                                "data": {
                                    "full_name": s_name,
                                    "role": "candidate" # We'll trigger profile creation or do it manually
                                }
                            }
                        })
                        if res.user:
                             # Auto-create profile entry if trigger doesn't exist?
                             # Our DB 'profiles' table usually relies on trigger or manual insert.
                             # Let's insert manually to be safe if trigger missing.
                             try:
                                 sb.table("profiles").insert({
                                     "id": res.user.id,
                                     "role": "candidate",
                                     "full_name": s_name
                                 }).execute()
                             except:
                                 pass # maybe trigger handled it
                                 
                             st.success("Account created! Please check your email to confirm, then Login.")
                        else:
                            st.error("Sign up failed.")
                    except Exception as e:
                        st.error(f"Error: {e}")

    st.markdown("---")
    st.caption("Recruiters: Contact administrator for account access.")
