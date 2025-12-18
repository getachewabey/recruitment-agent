-- 1. Update Enum (Postgres workaround for adding value to enum)
-- Ideally: ALTER TYPE user_role ADD VALUE 'candidate';
-- However, running this in valid block:
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_enum e ON t.oid = e.enumtypid  
                   WHERE t.typname = 'user_role' AND e.enumlabel = 'candidate') THEN
        ALTER TYPE user_role ADD VALUE 'candidate';
    END IF;
END$$;

-- 2. Link Candidates to Users
-- We need to link a Candidate record to a proper User ID (auth.users)
-- This allows a user to "claim" or "be" a candidate.
ALTER TABLE candidates 
ADD COLUMN IF NOT EXISTS user_id uuid references auth.users(id) on delete set null;

-- 3. RLS Policies for Candidates

-- A. JOBS: Candidates can view OPEN jobs
CREATE POLICY "Candidates can view open jobs" ON jobs
  FOR SELECT USING (status = 'open');

-- B. CANDIDATES: Candidates can view/update ONLY their own profile
CREATE POLICY "Candidates can view own profile" ON candidates
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Candidates can update own profile" ON candidates
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Candidates can insert own profile" ON candidates
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- C. APPLICATIONS: Candidates can view their own applications and Create new ones
CREATE POLICY "Candidates can view own applications" ON applications
  FOR SELECT USING (
    candidate_id IN (SELECT id FROM candidates WHERE user_id = auth.uid())
  );

CREATE POLICY "Candidates can apply" ON applications
  FOR INSERT WITH CHECK (
    -- The candidate_id being inserted must belong to the current user
    candidate_id IN (SELECT id FROM candidates WHERE user_id = auth.uid())
  );
