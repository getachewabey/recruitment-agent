import streamlit as st

from src.db import get_supabase_client

def login_user(email, password):
    """
    Login with Supabase Auth.
    Returns the session object or None if failed.
    """
    supabase = get_supabase_client()
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return response.session, response.user
    except Exception as e:
        st.error(f"Login Failed: {e}")
        return None, None

def logout_user():
    """Sign out."""
    supabase = get_supabase_client()
    try:
        supabase.auth.sign_out()
    except Exception as e:
        st.warning("One (1) issue signing out: " + str(e))
    
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

def get_current_user():
    """Get current user from st.session_state or validate with Supabase"""
    # Assuming we store session in st.session_state upon login
    # Supabase-py generally maintains state in the client if we re-use it,
    # but Streamlit runs are stateless.
    # We rely on the session/user object stored in st.session_state['user']
    
    if "user" in st.session_state:
        return st.session_state["user"]
    return None
