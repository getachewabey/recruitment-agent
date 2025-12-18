# Constants

# Enums
STAGES = ["new", "screened", "interview", "offer", "hired", "rejected"]

# Default interview stages if none provided
DEFAULT_INTERVIEW_STAGES = [
    {"name": "Initial Screening", "type": "Screening"},
    {"name": "Technical Interview", "type": "Video Call"},
    {"name": "Culture Fit", "type": "Video Call"},
    {"name": "Final Round", "type": "On-site"}
]

# Model Name
MODEL_NAME = "gemini-2.5-flash"

# Session State Keys
SESSION_KEYS = {
    "USER": "user",
    "PROFILE": "profile",
    "AUTH_EVENT": "auth_event"
}
