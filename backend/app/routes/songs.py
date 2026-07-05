from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import Song

router = APIRouter(
    prefix="/songs",
    tags=["Songs"]
)


@router.get("/")
def get_songs(db: Session = Depends(get_db)):
    songs = db.query(Song).all()

    return {
        "count": len(songs),
        "songs": songs
    }


@router.get("/search")
def search_songs(
    q: str = Query(..., description="Search by title, movie, singer, lyricist, composer, mood, or theme"),
    db: Session = Depends(get_db)
):
    search_text = f"%{q}%"

    songs = (
        db.query(Song)
        .filter(
            or_(
                Song.title.ilike(search_text),
                Song.movie.ilike(search_text),
                Song.singers.ilike(search_text),
                Song.lyricist.ilike(search_text),
                Song.composer.ilike(search_text),
                Song.mood.ilike(search_text),
                Song.themes.ilike(search_text),
            )
        )
        .all()
    )

    return {
        "query": q,
        "count": len(songs),
        "songs": songs
    }

@router.get("/filter")
def filter_songs(
    mood: str | None = None,
    year: int | None = None,
    lyricist: str | None = None,
    composer: str | None = None,
    singer: str | None = None,
    theme: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(Song)

    if mood:
        query = query.filter(Song.mood.ilike(f"%{mood}%"))

    if year:
        query = query.filter(Song.year == year)

    if lyricist:
        query = query.filter(Song.lyricist.ilike(f"%{lyricist}%"))

    if composer:
        query = query.filter(Song.composer.ilike(f"%{composer}%"))

    if singer:
        query = query.filter(Song.singers.ilike(f"%{singer}%"))

    if theme:
        query = query.filter(Song.themes.ilike(f"%{theme}%"))

    songs = query.all()

    return {
        "filters": {
            "mood": mood,
            "year": year,
            "lyricist": lyricist,
            "composer": composer,
            "singer": singer,
            "theme": theme
        },
        "count": len(songs),
        "songs": songs
    }

@router.get("/{song_id}")
def get_song(song_id: int, db: Session = Depends(get_db)):
    song = db.query(Song).filter(Song.id == song_id).first()

    if not song:
        return {
            "error": "Song not found"
        }

    return song