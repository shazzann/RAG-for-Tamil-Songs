"""
Retrieval service — handles multi-stage routing (Title -> SQL Metadata -> Vector Semantic fallback)
for RAG Chat queries.
"""

from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import Song, LyricsChunk
from app.services.embedding_service import generate_embedding
from app.routes.qa import (
    find_song_by_title,
    detect_mood,
    detect_theme,
    detect_year,
    find_person_name,
)


class RetrievedResult(BaseModel):
    song_id: int
    title: str
    movie: str | None = None
    chunk_text: str | None = None
    score: float | None = None
    source_type: str  # "metadata" or "semantic"


def _build_metadata_chunk_text(song: Song) -> str:
    """Build a descriptive text block for a song retrieved via SQL metadata matching."""
    parts = [
        f"Title: {song.title}",
        f"Movie: {song.movie or 'N/A'}",
        f"Year: {song.year or 'N/A'}",
        f"Singers: {song.singers or 'N/A'}",
        f"Lyricist: {song.lyricist or 'N/A'}",
        f"Composer: {song.composer or 'N/A'}",
        f"Mood: {song.mood or 'N/A'}",
        f"Themes: {song.themes or 'N/A'}",
    ]
    return " | ".join(parts)


def retrieve(question: str, db: Session, top_k: int = 5) -> tuple[list[RetrievedResult], str]:
    """Retrieve relevant song/lyric records for a question.

    Returns:
        tuple[list[RetrievedResult], str]: A tuple of (results, retrieval_type)
        where retrieval_type is either 'metadata' or 'semantic'.
    """
    question_clean = question.strip()
    question_lower = question_clean.lower()

    # 1. Exact or partial title match for factual song QA
    matched_song = find_song_by_title(question_clean, db)
    if matched_song:
        # Check if question is asking factual metadata about this song
        is_factual = any(
            kw in question_lower
            for kw in [
                "who wrote",
                "lyricist",
                "written by",
                "lyrics by",
                "composer",
                "music director",
                "music by",
                "composed",
                "singer",
                "sung by",
                "who sang",
                "movie",
                "film",
                "which film",
                "what is",
                "tell me about",
                "about",
            ]
        ) or len(question_clean.split()) <= 4  # Short query matching a title
        if is_factual:
            result = RetrievedResult(
                song_id=matched_song.id,
                title=matched_song.title,
                movie=matched_song.movie,
                chunk_text=_build_metadata_chunk_text(matched_song),
                score=1.0,
                source_type="metadata",
            )
            return [result], "metadata"

    # 2. Analytical metadata filters (mood, theme, year, person)
    mood = detect_mood(question_lower)
    theme = detect_theme(question_lower)
    year = detect_year(question_lower)
    person = find_person_name(question_clean, db)

    if mood or theme or year or person:
        query = db.query(Song)
        if mood:
            query = query.filter(Song.mood.ilike(f"%{mood}%"))
        if theme:
            query = query.filter(Song.themes.ilike(f"%{theme}%"))
        if year:
            query = query.filter(Song.year == year)
        if person:
            person_search = f"%{person}%"
            query = query.filter(
                or_(
                    Song.lyricist.ilike(person_search),
                    Song.composer.ilike(person_search),
                    Song.singers.ilike(person_search),
                )
            )

        matching_songs = query.limit(top_k).all()
        if matching_songs:
            results = [
                RetrievedResult(
                    song_id=song.id,
                    title=song.title,
                    movie=song.movie,
                    chunk_text=_build_metadata_chunk_text(song),
                    score=1.0,
                    source_type="metadata",
                )
                for song in matching_songs
            ]
            return results, "metadata"

    # 3. Fall back to pgvector semantic search on lyric chunks
    from app.services.query_expansion import expand_query
    
    # Expand and transliterate query using LLM
    expanded_query = expand_query(question_clean)
    
    query_embedding = generate_embedding(expanded_query)
    if not query_embedding:
        return [], "semantic"

    # Calculate cosine distance using pgvector operator and compute similarity score
    chunks_with_dist = (
        db.query(
            LyricsChunk,
            LyricsChunk.embedding.cosine_distance(query_embedding).label("distance"),
        )
        .join(Song)
        .filter(LyricsChunk.embedding != None)
        .order_by("distance")
        .limit(top_k)
        .all()
    )

    results = []
    seen_chunks = set()
    for chunk, distance in chunks_with_dist:
        chunk_key = (chunk.song_id, chunk.chunk_text)
        if chunk_key in seen_chunks:
            continue
        seen_chunks.add(chunk_key)

        similarity_score = max(0.0, float(1.0 - (distance or 0.0)))
        results.append(
            RetrievedResult(
                song_id=chunk.song_id,
                title=chunk.song.title,
                movie=chunk.song.movie,
                chunk_text=chunk.chunk_text,
                score=round(similarity_score, 4),
                source_type="semantic",
            )
        )

    return results, "semantic"
