"""
LLM service — handles calls to the language model for RAG answers.

Supports Gemini or OpenAI.
"""

import os


async def generate_answer(question: str, context: str) -> str:
    """Generate an answer using the LLM with retrieved context.

    Args:
        question: The user's natural-language question.
        context: Concatenated relevant song lyrics / metadata from vector search.

    Returns:
        The LLM-generated answer string.

    TODO: plug in Gemini or OpenAI client.
    """
    raise NotImplementedError("LLM provider not configured yet.")
