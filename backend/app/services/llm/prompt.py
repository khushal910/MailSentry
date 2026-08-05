"""
Centralized, reusable system prompt for all LLM providers (Groq, Gemini, OpenAI, etc.).
Ensures single source of truth for email summarization prompt engineering across providers.
"""

SYSTEM_SUMMARY_PROMPT = """You are an intelligent email assistant.

Summarize this email.

Include:
- Purpose
- Important dates
- Required actions
- Deadlines
- Tone

Return the summary in under 50 words."""


def format_summary_prompt(email_body: str) -> str:
    """Formats the system prompt with the target email body."""
    clean_body = str(email_body).strip() if email_body else ""
    return f"{SYSTEM_SUMMARY_PROMPT}\n\nEmail Body:\n{clean_body}"
