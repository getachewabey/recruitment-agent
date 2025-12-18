-- Enable RLS on all tables
alter table profiles enable row level security;
alter table jobs enable row level security;
alter table candidates enable row level security;
alter table applications enable row level security;
alter table notes enable row level security;
alter table audit_log enable row level security;

-- Helper function to get current user role
create or replace function get_my_role()
returns user_role as $$
  select role from profiles where id = auth.uid()
$$ language sql security definer;

-- --- PROFILES ---
-- Users can see their own profile
create policy "Users can view own profile" on profiles
  for select using (auth.uid() = id);

create policy "Users can insert own profile" on profiles
  for insert with check (auth.uid() = id);

create policy "Users can update own profile" on profiles
  for update using (auth.uid() = id);

-- Admins can view all profiles
create policy "Admins can view all profiles" on profiles
  for select using (get_my_role() = 'admin');

-- --- JOBS ---
-- Read: Recruiter/Admin see all. Managers see jobs they are assigned to (TODO: job_members table/logic) OR for simplicity, Manager sees all jobs for now (User story: "Read-only access to jobs they are assigned to"). 
-- Implementing strict "Assigned Only" requires a link table. For MVP, we'll allow Managers to see all Open jobs but not edit.
create policy "Everyone can view jobs" on jobs
  for select using (true); -- Refine later if strict privacy needed

-- Write: Admin and Recruiter can insert/update
create policy "Recruiters/Admins can insert jobs" on jobs
  for insert with check (get_my_role() in ('admin', 'recruiter'));

create policy "Recruiters/Admins can update jobs" on jobs
  for update using (get_my_role() in ('admin', 'recruiter'));

-- --- CANDIDATES ---
-- Read: Helper function or simple policy.
create policy "Authorized users can view candidates" on candidates
  for select using (auth.uid() is not null); -- Ideally restricted to job association

-- Write: Recruiter/Admin
create policy "Recruiters/Admins can create candidates" on candidates
  for insert with check (get_my_role() in ('admin', 'recruiter'));

-- --- APPLICATIONS ---
-- Read:
create policy "Authorized users can view applications" on applications
  for select using (auth.uid() is not null);

-- Write (Update stage/score): Recruiter/Admin
create policy "Recruiters/Admins can update applications" on applications
  for update using (get_my_role() in ('admin', 'recruiter'));

create policy "Recruiters/Admins can insert applications" on applications
  for insert with check (get_my_role() in ('admin', 'recruiter'));

-- --- NOTES ---
-- Read:
create policy "Authorized users can view notes" on notes
  for select using (auth.uid() is not null);

-- Write: All authenticated users (Recruiters, Managers) can comment
create policy "Authenticated users can create notes" on notes
  for insert with check (auth.uid() = author_id);

-- --- AUDIT LOG ---
-- Read: Admin only
create policy "Admins can view audit logs" on audit_log
  for select using (get_my_role() = 'admin');

-- Insert: System usually handles this, or any auth user if triggered via client
create policy "System/Users can insert audit logs" on audit_log
  for insert with check (auth.uid() = actor_id);

-- --- STORAGE POLICIES (Conceptual) ---
-- Bucket 'resumes':
-- READ: authenticated users
-- WRITE: recruiters/admin
