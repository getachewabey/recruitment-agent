from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field

# --- User Roles ---
class UserRole(BaseModel):
    role: Literal['admin', 'recruiter', 'manager']

# --- Job Schemas ---
class JobParsingSchema(BaseModel):
    """Schema for parsing a Job Description"""
    title: str = Field(description="Job title")
    team: Optional[str] = Field(description="Department or team")
    location: Optional[str] = Field(description="Job location (City, Remote, etc.)")
    employment_type: Optional[str] = Field(description="Full-time, Part-time, Contract, etc.")
    comp_range_min: Optional[float] = Field(description="Minimum compensation")
    comp_range_max: Optional[float] = Field(description="Maximum compensation")
    must_have_skills: List[str] = Field(description="List of required technical or soft skills")
    nice_to_have_skills: List[str] = Field(description="List of preferred skills")
    responsibilities: List[str] = Field(description="List of key responsibilities")
    interview_stages: Optional[List[Dict[str, str]]] = Field(
        description="List of stages, e.g. [{'name': 'Screening', 'type': 'video'}]"
    )

class Job(JobParsingSchema):
    id: str
    created_by: str
    status: Literal['open', 'closed', 'draft']
    jd_text: str
    created_at: str

# --- Candidate Schemas ---
class CandidateParsingSchema(BaseModel):
    """Schema for extracted candidate profile from Resume"""
    full_name: str = Field(description="Candidate's full name")
    email: Optional[str] = Field(description="Email address")
    phone: Optional[str] = Field(description="Phone number")
    location: Optional[str] = Field(description="Current location")
    links: Optional[Dict[str, str]] = Field(description="Links like LinkedIn, GitHub, Portfolio")
    experience_years: Optional[float] = Field(description="Approximate years of experience")
    skills: List[str] = Field(description="List of extracted skills")
    education: List[str] = Field(description="List of degrees/universities")

class Candidate(CandidateParsingSchema):
    id: str
    resume_text: str
    resume_file_path: Optional[str]
    created_at: str

# --- Evaluation / Application Schemas ---
class ScoreBreakdown(BaseModel):
    skills_match: int = Field(description="0-100 score on required skills")
    experience_relevance: int = Field(description="0-100 score on relevant experience")
    impact: int = Field(description="0-100 score on demonstrated impact")
    communication: int = Field(description="0-100 score on communication style (if inferable)")
    seniority_fit: int = Field(description="0-100 score on seniority level match")

class EvaluationResult(BaseModel):
    """Output from the LLM evaluation"""
    overall_score: int = Field(description="Overall match score 0-100")
    score_breakdown: ScoreBreakdown
    ai_summary: str = Field(description="Summary of the fit assessment")
    strengths: List[str] = Field(description="Key strengths matching the JD")
    concerns: List[str] = Field(description="Potential risks or gaps")
    missing_must_haves: List[str] = Field(description="Critical skills missing from the resume")
    risk_flags: List[str] = Field(description="Red flags like short tenures without explanation")
    suggested_interview_questions: List[str] = Field(description="Tailored questions for the interview")

class ScreeningResult(BaseModel):
    """Output from screening Q&A summarization"""
    summary: str
    recommended_stage: Literal['screened', 'interview', 'rejected']
    updated_rubric_notes: str

# --- Outreach ---
class OutreachMessage(BaseModel):
    subject: str
    body: str
