import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def generate_embedding(text: str):
    """
    Generate embedding for a text chunk using Gemini.
    """
    if not text or not text.strip():
        return None

    response = client.models.embed_content(
        model="gemini-embedding-2",
        contents=text
    )

    return response.embeddings[0].values