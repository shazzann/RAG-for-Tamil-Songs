from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import LyricsChunk, Song


router = APIRouter(
    prefix="/lyrics",
    tags=["Lyrics"]
)


@router.get("/chunks")
def get_chunks(db: Session = Depends(get_db)):
    chunks = (
        db.query(LyricsChunk)
        .join(Song)
        .limit(50)
        .all()
    )

    return {
        "count": len(chunks),
        "chunks": [
            {
                "id": chunk.id,
                "song_title": chunk.song.title,
                "movie": chunk.song.movie,
                "year": chunk.song.year,
                "line": chunk.chunk_text,
                "line_number": chunk.start_line
            }
            for chunk in chunks
        ]
    }


@router.get("/search")
def search_lyrics(
    q: str = Query(..., description="Keyword to search inside lyrics"),
    db: Session = Depends(get_db)
):
    search_text = f"%{q}%"

    chunks = (
        db.query(LyricsChunk)
        .join(Song)
        .filter(LyricsChunk.chunk_text.ilike(search_text))
        .limit(50)
        .all()
    )

    return {
        "query": q,
        "count": len(chunks),
        "results": [
            {
                "song_title": chunk.song.title,
                "movie": chunk.song.movie,
                "year": chunk.song.year,
                "lyricist": chunk.song.lyricist,
                "composer": chunk.song.composer,
                "line": chunk.chunk_text,
                "line_number": chunk.start_line,
                "source_url": chunk.song.source_url
            }
            for chunk in chunks
        ]
    }


THEME_KEYWORDS = {
    "eyes": ["eyes", "eye", "kan", "கண்", "vizhi", "விழி", "paarvai", "பார்வை", "nayanam"],
    "rain": ["rain", "mazhai", "மழை"],
    "love": ["love", "kadhal", "காதல்"],
    "separation": ["separation", "pirivu", "பிரிவு", "missing", "longing"],
    "mother": ["mother", "amma", "அம்மா"],
    "heart": ["heart", "idhayam", "இதயம்"]
}


@router.get("/theme/{theme}")
def search_lyrics_by_theme(
    theme: str,
    db: Session = Depends(get_db)
):
    keywords = THEME_KEYWORDS.get(theme.lower())

    if not keywords:
        return {
            "theme": theme,
            "error": "Unknown theme",
            "available_themes": list(THEME_KEYWORDS.keys())
        }

    filters = [
        LyricsChunk.chunk_text.ilike(f"%{keyword}%")
        for keyword in keywords
    ]

    chunks = (
        db.query(LyricsChunk)
        .join(Song)
        .filter(or_(*filters))
        .limit(50)
        .all()
    )

    return {
        "theme": theme,
        "keywords_used": keywords,
        "count": len(chunks),
        "results": [
            {
                "song_title": chunk.song.title,
                "movie": chunk.song.movie,
                "year": chunk.song.year,
                "lyricist": chunk.song.lyricist,
                "line": chunk.chunk_text,
                "line_number": chunk.start_line,
                "source_url": chunk.song.source_url
            }
            for chunk in chunks
        ]
    }