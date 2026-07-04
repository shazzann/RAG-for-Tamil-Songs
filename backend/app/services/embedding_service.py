"""
Embedding service — generates vector embeddings for song lyrics.

Supports OpenAI, Gemini, or a multilingual sentence-transformer model.
"""

import os
from typing import List


async def get_embedding(text: str) -> List[float]:
    """Generate an embedding vector for the given text.

    TODO: plug in the chosen embedding provider (OpenAI / Gemini / HuggingFace).
    """
    raise NotImplementedError("Embedding provider not configured yet.")
