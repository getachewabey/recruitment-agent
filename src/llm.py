import os
import streamlit as st
import json
import google.generativeai as genai
from typing import Optional, Dict, List, Type
from pydantic import BaseModel

from src.constants import MODEL_NAME
from src.schemas import (
    JobParsingSchema, 
    CandidateParsingSchema, 
    EvaluationResult, 
    OutreachMessage, 
    ScreeningResult
)

# Config GenAI
def configure_genai():
    api_key = st.secrets.get("google", {}).get("api_key") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("Missing Google API Key.")
        return False
    genai.configure(api_key=api_key)
    return True

def get_model():
    # Use the requested model
    return genai.GenerativeModel(MODEL_NAME)

def call_llm_json(prompt: str, schema_model: Type[BaseModel]) -> Optional[BaseModel]:
    """
    Calls Gemini with a prompt and forces JSON output matching the Pydantic schema.
    Incorporates retry logic (manual, though Gemini mostly respects schema in prompt).
    """
    if not configure_genai():
        return None

    model = get_model()
    
    # Construct the system instruction for JSON enforcement
    # We use valid JSON schema dump from pydantic Model
    schema_json = schema_model.model_json_schema()
    
    full_prompt = f"""
    You are an expert AI recruitment assistant.
    System Instruction: You MUST return a valid JSON object matching the following schema. 
    Do not wrap in markdown code blocks. Return ONLY the JSON string.
    
    Schema:
    {json.dumps(schema_json, indent=2)}
    
    Task:
    {prompt}
    """

    # Retry loop
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            # Using generation_config to encourage JSON (if supported by model version)
            # gemini-1.5-flash and later support response_mime_type="application/json"
            response = model.generate_content(
                full_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            # Clean response text just in case (remove backticks)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            # Validate with Pydantic
            data_dict = json.loads(text)
            validated_obj = schema_model(**data_dict)
            return validated_obj
            
        except Exception as e:
            if attempt < max_retries:
                print(f"LLM Parsing Error (Attempt {attempt+1}): {e}. Retrying...")
                continue
            else:
                st.error(f"LLM Error after retries: {e}")
                return None
    return None

# --- Specific Tasks ---

def parse_job_description(text: str) -> Optional[JobParsingSchema]:
    prompt = f"""
    Extract structured job details from the following Job Description text.
    If a field is missing, leave it null or empty list.
    
    Job Description:
    {text}
    """
    return call_llm_json(prompt, JobParsingSchema)

def parse_resume(text: str) -> Optional[CandidateParsingSchema]:
    prompt = f"""
    Extract structured candidate details from the following Resume text.
    Analyze carefully.
    
    Resume Text:
    {text}
    """
    return call_llm_json(prompt, CandidateParsingSchema)

def evaluate_candidate(job_json: Dict, candidate_json: Dict, resume_text: str) -> Optional[EvaluationResult]:
    prompt = f"""
    Evaluate the candidate against the job description.
    
    Job Details:
    {json.dumps(job_json, indent=2)}
    
    Candidate Details:
    {json.dumps(candidate_json, indent=2)}
    
    Full Resume Context:
    {resume_text[:5000]} 
    
    Criteria:
    - strict scoring: 0-100.
    - provide evidence based on text.
    - identify risk flags (e.g. gaps, job hopping without reason).
    """
    return call_llm_json(prompt, EvaluationResult)

def generate_outreach(candidate_first_name: str, job_title: str, company_name: str, tone: str) -> Optional[OutreachMessage]:
    prompt = f"""
    Write a recruitment outreach email.
    Candidate: {candidate_first_name}
    Job: {job_title}
    Company: {company_name or 'Our Company'}
    Tone: {tone} (options: friendly, formal, concise)
    
    Return JSON with 'subject' and 'body'.
    """
    return call_llm_json(prompt, OutreachMessage)

def summarize_screening(chat_history: str) -> Optional[ScreeningResult]:
    prompt = f"""
    Analyze the following screening chat history between a recruiter and candidate.
    Update the rubric notes. suggest stage.
    
    Chat Limit:
    {chat_history}
    """
    return call_llm_json(prompt, ScreeningResult)
