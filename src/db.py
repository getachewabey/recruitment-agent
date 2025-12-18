import os
import streamlit as st
from supabase import create_client, Client
from typing import Optional, List, Dict, Any
from src.schemas import Job, Candidate, UserRole

# Initialize Supabase Client
# We use a singleton pattern via st.cache_resource/cache_data isn't needed for the client object itself
# if we just create it. But for connection pooling efficiency in Streamlit re-runs, caching is good.

@st.cache_resource
def get_supabase_client() -> Client:
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        # Fallback to env vars if secrets not found (for local testing without streamlit run)
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            raise ValueError("Supabase Response: Missing SUPABASE_URL or SUPABASE_ANON_KEY in secrets or env.")
        return create_client(url, key)

# --- DB Operations ---

def get_user_role(user_id: str) -> Optional[str]:
    """Fetch user role from profiles table. Auto-create if missing."""
    supabase = get_supabase_client()
    try:
        response = supabase.table("profiles").select("role").eq("id", user_id).single().execute()
        if response.data:
            return response.data["role"]
    except Exception:
        # If error (likely no row found), create default profile
        try:
            # Check if it was a 'Row not found' error implicitly by trying insert
            # We default to 'recruiter'
            data = {"id": user_id, "role": "recruiter", "full_name": "New User"}
            supabase.table("profiles").insert(data).execute()
            return "recruiter"
        except Exception as insert_error:
            print(f"Error creating profile: {insert_error}")
            
    return None

def create_job(job_data: Dict[str, Any]) -> Optional[Dict]:
    """Insert a new job"""
    supabase = get_supabase_client()
    try:
        response = supabase.table("jobs").insert(job_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Error creating job: {e}")
        return None

def get_jobs(user_role: str, user_id: str) -> List[Dict]:
    """
    Get jobs based on role.
    Admin/Recruiter: All jobs (or created by them). 
    Manager: Assigned jobs (For MVP: All open jobs).
    """
    supabase = get_supabase_client()
    try:
        query = supabase.table("jobs").select("*").order("created_at", desc=True)
        # RLS in Supabase handles the actual filtering security.
        # We just query everything the user is allowed to see.
        response = query.execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching jobs: {e}")
        return []

def get_job_by_id(job_id: str) -> Optional[Dict]:
    supabase = get_supabase_client()
    try:
        response = supabase.table("jobs").select("*").eq("id", job_id).single().execute()
        return response.data
    except Exception:
        return None

def create_candidate(candidate_data: Dict[str, Any]) -> Optional[Dict]:
    supabase = get_supabase_client()
    try:
        response = supabase.table("candidates").insert(candidate_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"Error creating candidate: {e}")
        return None

def create_application(application_data: Dict[str, Any]) -> Optional[Dict]:
    supabase = get_supabase_client()
    try:
        # Check if exists first to avoid duplicate error if we don't want to rely solely on DB constraint error
        # Actually DB constraint unique(job_id, candidate_id) is best.
        response = supabase.table("applications").insert(application_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        # duplicate key value violates unique constraint
        if "duplicate key" in str(e):
             st.warning("Candidate already applied to this job.")
        else:
             st.error(f"Error creating application: {e}")
        return None

def get_candidates_for_job(job_id: str) -> List[Dict]:
    """
    Fetch candidates for a job, joining applications table.
    """
    supabase = get_supabase_client()
    try:
        # Join applications and select candidate details
        # Supabase syntax for joins: select("*, candidates(*)")
        # We want info from applications (score, stage) AND candidates (name, etc)
        response = supabase.table("applications")\
            .select("*, candidates(*)")\
            .eq("job_id", job_id)\
            .order("overall_score", desc=True)\
            .execute()
        return response.data
    except Exception as e:
        st.error(f"Error feching candidates: {e}")
        return []

def update_application_stage(app_id: str, stage: str):
    supabase = get_supabase_client()
    try:
        supabase.table("applications").update({"stage": stage}).eq("id", app_id).execute()
        return True
    except Exception as e:
        st.error(f"Error updating stage: {e}")
        return False

def add_note(app_id: str, author_id: str, note_text: str):
    supabase = get_supabase_client()
    try:
        data = {"application_id": app_id, "author_id": author_id, "note": note_text}
        supabase.table("notes").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error adding note: {e}")
        return False

def get_notes(app_id: str) -> List[Dict]:
    supabase = get_supabase_client()
    try:
        # Join profiles to get author name
        response = supabase.table("notes")\
            .select("*, profiles(full_name)")\
            .eq("application_id", app_id)\
            .order("created_at", desc=True)\
            .execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching notes: {e}")
        return []

def update_application_evaluation(app_id: str, evaluation_data: Dict[str, Any]):
    """Update AI evaluation results"""
    supabase = get_supabase_client()
    try:
        supabase.table("applications").update(evaluation_data).eq("id", app_id).execute()
        return True
    except Exception as e:
        st.error(f"Error updating evaluation: {e}")
        return False

def get_application_details(app_id: str) -> Optional[Dict]:
    """Get full application details joined with job and candidate"""
    supabase = get_supabase_client()
    try:
        # Join jobs and candidates
        response = supabase.table("applications")\
            .select("*, jobs(*), candidates(*)")\
            .eq("id", app_id)\
            .single()\
            .execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching application details: {e}")
        return None

def get_audit_logs() -> List[Dict]:
    """Fetch audit logs (Admin only)"""
    supabase = get_supabase_client()
    try:
        # Join actor
        response = supabase.table("audit_log")\
            .select("*, profiles(full_name)")\
            .order("created_at", desc=True)\
            .execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching audit logs: {e}")
        return []

def get_all_users() -> List[Dict]:
    """Fetch all user profiles"""
    supabase = get_supabase_client()
    try:
        response = supabase.table("profiles").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching users: {e}")
        return []

def get_dashboard_stats(user_id: str, role: str) -> Dict[str, Any]:
    """Fetch aggregated stats for the dashboard"""
    supabase = get_supabase_client()
    stats = {
        "total_jobs": 0,
        "open_jobs": 0,
        "total_candidates": 0,
        "funnel": {},
        "recent_activity": []
    }
    
    try:
        # 1. Jobs
        # If admin/recruiter, get all. If manager, maybe filtered (but we do all for MVP)
        jobs_query = supabase.table("jobs").select("id, status, title", count="exact")
        if role == 'manager':
             # simplified: manager sees all for now as per policy
             pass
        jobs_res = jobs_query.execute()
        stats["total_jobs"] = len(jobs_res.data)
        stats["open_jobs"] = len([j for j in jobs_res.data if j['status'] == 'open'])
        
        # 2. Applications (Funnel)
        # We need all applications visible to this user
        apps_query = supabase.table("applications").select("stage, created_at, candidates(full_name), jobs(title)")
        apps_res = apps_query.order("created_at", desc=True).execute()
        
        all_apps = apps_res.data
        stats["total_candidates"] = len(all_apps)
        
        # Group by stage
        stages = ["new", "screened", "interview", "offer", "hired", "rejected"]
        funnel_counts = {s: 0 for s in stages}
        for a in all_apps:
            s = a.get("stage", "new")
            if s in funnel_counts:
                funnel_counts[s] += 1
        stats["funnel"] = funnel_counts
        
        # Recent Activity (Last 5 apps)
        stats["recent_activity"] = all_apps[:5]
        
    except Exception as e:
        print(f"Error fetching dashboard stats: {e}")
        
    return stats

def update_user_role(user_id: str, new_role: str):
    supabase = get_supabase_client()
    try:
        supabase.table("profiles").update({"role": new_role}).eq("id", user_id).execute()
        return True
    except Exception as e:
        print(f"Error updating user role: {e}")
        return False

# --- Candidate Portal Functions ---

def get_candidate_profile(user_id: str) -> Optional[Dict]:
    """Get the candidate record associated with this user_id"""
    supabase = get_supabase_client()
    try:
        # We need to find the candidate record where user_id matches
        res = supabase.table("candidates").select("*").eq("user_id", user_id).single().execute()
        return res.data
    except Exception:
        return None

def create_candidate_profile(user_id: str, data: Dict[str, Any]) -> Optional[Dict]:
    """Create a new candidate profile linked to the user"""
    supabase = get_supabase_client()
    try:
        data["user_id"] = user_id
        # Ensure we don't duplicate if one exists (though UI should handle)
        res = supabase.table("candidates").insert(data).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        st.error(f"Error creating profile: {e}")
        return None

def update_candidate_profile(candidate_id: str, data: Dict[str, Any]) -> bool:
    supabase = get_supabase_client()
    try:
        supabase.table("candidates").update(data).eq("id", candidate_id).execute()
        return True
    except Exception as e:
        st.error(f"Error updating profile: {e}")
        return False

def apply_for_job_as_candidate(job_id: str, candidate_id: str) -> bool:
    """Create an application record"""
    supabase = get_supabase_client()
    try:
        data = {
            "job_id": job_id,
            "candidate_id": candidate_id,
            "stage": "new"
        }
        supabase.table("applications").insert(data).execute()
        return True
    except Exception as e:
        # duplicate key error likely if already applied
        if "duplicate key" in str(e):
             st.warning("You have already applied for this job.")
        else:
             st.error(f"Error applying: {e}")
        return False

def get_my_applications(candidate_id: str) -> List[Dict]:
    """Fetch applications for this candidate"""
    supabase = get_supabase_client()
    try:
        # we want job details too
        res = supabase.table("applications").select("*, jobs(title, location, status)").eq("candidate_id", candidate_id).execute()
        return res.data
    except Exception as e:
        st.error(f"Error fetching applications: {e}")
        return []
