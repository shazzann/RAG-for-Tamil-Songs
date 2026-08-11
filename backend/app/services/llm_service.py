"""
LLM service — handles calls to the language model for grounded RAG answers.

Uses Gemini via the google-genai SDK, defaulting to gemini-2.5-flash.
"""

import os
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize client; will be None if API key is missing
_api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=_api_key) if _api_key else None

DEFAULT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")

SYSTEM_PROMPT = """You are a specialized Tamil Song RAG (Retrieval-Augmented Generation) assistant.
Your instructions:
1. STRICT GROUNDING: For questions about songs, movies, singers, composers, lyricists, or lyrics, answer STRICTLY and ONLY using the provided Retrieved Context.
2. DO NOT HALLUCINATE: Never invent songs, lyrics, artists, years, or movies that are not present in the Retrieved Context. If the Retrieved Context does not contain enough information to answer the question, clearly state: "I could not find enough information in the retrieved songs to answer your question."
3. BE CONCISE AND ATTRIBUTE: Mention song title and movie name when answering. Avoid reproducing unnecessarily long lyric passages.
4. LANGUAGE MATCHING: Answer in the language or script (English, Tanglish, or Tamil) used by the user where practical.
5. CONVERSATIONAL FALLBACK: If the user is just greeting you (e.g. "hello", "hi") or asking what you can do, politely introduce yourself as a Tamil Song RAG assistant without saying you lack information."""


def generate_answer(question: str, context: str, model: str | None = None) -> str:
    """Generate a grounded natural-language answer using Gemini and retrieved context.

    Args:
        question: The user's natural-language question.
        context: Concatenated relevant song lyrics / metadata from retrieval service.
        model: Optional model override; defaults to GEMINI_CHAT_MODEL env var or 'gemini-2.5-flash'.

    Returns:
        The LLM-generated answer string, or a graceful fallback message on API failure.
    """
    if not client:
        return "AI answer generation is currently unavailable (missing GEMINI_API_KEY)."

    model_name = model or DEFAULT_MODEL

    # Construct the full prompt with system guidelines and context
    prompt_text = f"""{SYSTEM_PROMPT}

=== RETRIEVED CONTEXT ===
{context if context else "(No relevant context found in database)"}
=========================

User Question: {question}

Answer:"""

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt_text,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
            ),
        )
        if response and response.text:
            return response.text.strip()
        return "I could not generate an answer from the retrieved context."
    except Exception as e:
        logger.error(f"LLM generation failed for question '{question}': {e}", exc_info=True)
        return (
            "I encountered an AI service issue while generating an answer. "
            "However, you can explore the retrieved sources below."
        )
