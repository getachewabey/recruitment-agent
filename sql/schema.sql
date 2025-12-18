-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- 1. Enums
create type user_role as enum ('admin', 'recruiter', 'manager');
create type job_status as enum ('open', 'closed', 'draft');
create type application_stage as enum ('new', 'screened', 'interview', 'offer', 'hired', 'rejected');

-- 2. Profiles Table (Extends auth.users)
create table profiles (
  id uuid references auth.users on delete cascade not null primary key,
  full_name text,
  role user_role default 'recruiter',
  created_at timestamptz default now()
);

-- 3. Jobs Table
create table jobs (
  id uuid default uuid_generate_v4() primary key,
  created_by uuid references profiles(id) on delete set null,
  title text not null,
  team text,
  location text,
  employment_type text,
  comp_range_min numeric,
  comp_range_max numeric,
  must_have_skills text[],
  nice_to_have_skills text[],
  responsibilities text[],
  interview_stages jsonb, -- e.g. [{"name": "Screening", "type": "chat"}, {"name": "Tech", "type": "call"}]
  jd_text text,
  status job_status default 'draft',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- 4. Candidates Table
create table candidates (
  id uuid default uuid_generate_v4() primary key,
  created_by uuid references profiles(id) on delete set null,
  full_name text not null,
  email text,
  phone text,
  location text,
  links jsonb, -- {"linkedin": "...", "github": "..."}
  resume_text text, -- Extracted text
  resume_file_path text, -- Path in Supabase Storage
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- 5. Applications Table (Link Candidate <-> Job)
create table applications (
  id uuid default uuid_generate_v4() primary key,
  job_id uuid references jobs(id) on delete cascade not null,
  candidate_id uuid references candidates(id) on delete cascade not null,
  stage application_stage default 'new',
  overall_score numeric, -- 0-100
  score_breakdown jsonb, -- {"skills": 80, "impact": 90...}
  ai_summary text,
  risk_flags text[],
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique(job_id, candidate_id)
);

-- 6. Notes Table
create table notes (
  id uuid default uuid_generate_v4() primary key,
  application_id uuid references applications(id) on delete cascade not null,
  author_id uuid references profiles(id) on delete set null,
  note text not null,
  created_at timestamptz default now()
);

-- 7. Audit Log Table
create table audit_log (
  id uuid default uuid_generate_v4() primary key,
  actor_id uuid references profiles(id) on delete set null,
  action text not null, -- e.g. JOB_CREATED, CANDIDATE_EVALUATED
  entity_type text, -- 'job', 'application'
  entity_id uuid,
  metadata jsonb,
  created_at timestamptz default now()
);

-- 8. Storage Bucket Setup (This usually needs to be done via UI or API, but SQL can set policies if buckets exist)
-- Assuming a bucket named 'resumes' exists and is private.
