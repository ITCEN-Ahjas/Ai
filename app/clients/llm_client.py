from groq import Groq
from app.config import settings

def get_groq_client() -> Groq:
    return Groq(api_key=settings.groq_api_key)
