# AI Recruitment Agent

A production-ready AI-powered recruitment assistant built with Streamlit, Supabase, and Google Gemini.

## Features
- **Job Management**: Create and manage job requisitions with AI-powered JD parsing.
- **Candidate Pipeline**: Track candidates from "New" to "Hired".
- **AI Evaluation**: Automatically parse resumes, score candidates against JDs, and generate interview questions manually.
- **Outreach**: Generate personalized emails/messages.
- **Role-Based Access**: Admins, Recruiters, and Hiring Managers.

## Architecture
- **Frontend**: Streamlit (Multipage App)
- **Backend/DB**: Supabase (Postgres, Auth, Storage)
- **AI**: Google Gemini 2.5 Flash
- **Language**: Python 3.10+

## Setup Instructions

### 1. Prerequisites
- Python 3.10+
- Supabase Account
- Google Cloud API Key (for Gemini)

### 2. Implementation Steps

#### A. Database Setup (Supabase)
1. Go to your Supabase Dashboard > SQL Editor.
2. Run the specific content of `sql/schema.sql`.
3. Run the content of `sql/rls_policies.sql`.
4. Create a **Private** Storage Bucket named `resumes`.

#### B. Local Environment
1. Clone this repo.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create `.streamlit/secrets.toml`:
   ```toml
   [supabase]
   url = "YOUR_SUPABASE_URL"
   key = "YOUR_SUPABASE_ANON_KEY"
   service_key = "YOUR_SERVICE_ROLE_KEY" # Optional, usually for admin scripts

   [google]
   api_key = "YOUR_GOOGLE_API_KEY"
   ```

#### C. Run the App
```bash
streamlit run app.py
```

### 3. Deployment (Streamlit Community Cloud)
1. Push code to GitHub.
2. Link repo to Streamlit Cloud.
3. Add the secrets from `.streamlit/secrets.toml` to the Streamlit Cloud "Secrets" settings.

## Security
- PII is redacted before sending to LLM where possible.
- RLS ensures data privacy between roles.
- Resumes are stored in a private bucket.
