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

EXPANSION_PROMPT = """You are a Tamil language expert and query expansion assistant for a Tamil song search engine.
Your task is to take a user's search query (which could be in English, Tanglish, or Tamil script) and rewrite it into a comma-separated list of 3-5 optimized Tanglish (Tamil in English script) keywords for vector similarity search against a database of Tanglish song lyrics.

Instructions:
1. TRANSLITERATE: If the query contains Tamil script, transliterate it to Tanglish.
2. EXTRACT INTENT: Identify the core semantic meaning, emotion, or theme (e.g. "sad", "love", "rain", "mother").
3. EXPAND: Add 2-3 highly relevant synonyms or related terms in Tanglish.
4. FORMAT: Output strictly a comma-separated list of 3-5 Tanglish keywords. NO OTHER TEXT.

Examples:
Input: காதல் பாடல்கள்
Output: kadhal, anbu, love, kaadhal, romance

Input: sad songs about missing someone
Output: sogam, pirivu, thanimai, pain, missing

Input: mazhai
Output: mazhai, rain, drizzle, megam

Input: {}
Output:"""

def expand_query(query: str, model: str | None = None) -> str:
    """
    Expand query with Tanglish/English synonyms and transliterate Tamil script using Gemini.
    """
    if not client:
        return query

    model_name = model or DEFAULT_MODEL
    prompt_text = EXPANSION_PROMPT.format(query)

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt_text,
            config=types.GenerateContentConfig(
                temperature=0.1,
            ),
        )
        if response and response.text:
            keywords = response.text.strip()
            # Replace commas with spaces to form the expanded query
            expanded_query = keywords.replace(",", " ")
            return expanded_query
    except Exception as e:
        logger.error(f"LLM query expansion failed for '{query}': {e}", exc_info=True)
    
    return query