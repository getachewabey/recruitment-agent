import re
import io
from typing import Optional
import PyPDF2
from docx import Document

def extract_text_from_file(file_obj: io.BytesIO, file_name: str) -> str:
    """
    Extracts text from PDF, DOCX, or TXT files.
    file_obj: The file-like object (BytesIO) from streamlit uploader.
    file_name: Original filename to determine extension.
    """
    text = ""
    file_lower = file_name.lower()

    try:
        if file_lower.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file_obj)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        
        elif file_lower.endswith('.docx'):
            doc = Document(file_obj)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        
        elif file_lower.endswith('.txt'):
            text = file_obj.getvalue().decode("utf-8")
            
        else:
            # Fallback for other text-based formats or error
            try:
                text = file_obj.getvalue().decode("utf-8")
            except:
                return f"Error: Unsupported file format for {file_name}"
                
    except Exception as e:
        return f"Error extracting text: {str(e)}"

    return text.strip()

def redact_pii(text: str) -> str:
    """
    Simple regex-based PII redaction for emails and phone numbers.
    LLM instructions will also help, but this is a first pass.
    """
    # Redact Emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    text = re.sub(email_pattern, "[REDACTED_EMAIL]", text)

    # Redact Phone Numbers (Basic US/Intl formats)
    # Matches: (123) 456-7890, 123-456-7890, +1 123 456 7890
    phone_pattern = r'(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'
    # Be careful not to redact years or other numbers, this regex is a bit aggressive? 
    # Let's make it stricter to avoid false positives on years/dates if possible.
    # Checks for at least a separator.
    
    # A safer regex for phones often helps avoid deleting "2023" or independent numbers
    phone_pattern_strict = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}'
    
    text = re.sub(phone_pattern_strict, "[REDACTED_PHONE]", text)

    return text
