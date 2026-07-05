from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import Song


router = APIRouter(
    prefix="/qa",
    tags=["Question Answering"]
)


class QuestionRequest(BaseModel):
    question: str


def find_song_by_title(question: str, db: Session):
    songs = db.query(Song).all()

    question_lower = question.lower()

    for song in songs:
        if song.title and song.title.lower() in question_lower:
            return song

    return None


@router.post("/ask")
def ask_question(request: QuestionRequest, db: Session = Depends(get_db)):
    question = request.question.strip()
    question_lower = question.lower()

    song = find_song_by_title(question, db)

    if not song:
        return {
            "question": question,
            "answer": "I could not find the song in the database.",
            "matched_song": None
        }

    # who wrote / lyricist question
    if (
        "who wrote" in question_lower
        or "lyricist" in question_lower
        or "written by" in question_lower
        or "lyrics by" in question_lower
    ):
        return {
            "question": question,
            "answer": f"{song.title} was written by {song.lyricist}.",
            "matched_song": {
                "title": song.title,
                "movie": song.movie,
                "year": song.year,
                "lyricist": song.lyricist
            }
        }

    # composer question
    if (
        "composer" in question_lower
        or "music director" in question_lower
        or "music by" in question_lower
        or "composed" in question_lower
    ):
        return {
            "question": question,
            "answer": f"{song.title} was composed by {song.composer}.",
            "matched_song": {
                "title": song.title,
                "movie": song.movie,
                "year": song.year,
                "composer": song.composer
            }
        }

    # singer question
    if (
        "singer" in question_lower
        or "sung by" in question_lower
        or "who sang" in question_lower
    ):
        return {
            "question": question,
            "answer": f"{song.title} was sung by {song.singers}.",
            "matched_song": {
                "title": song.title,
                "movie": song.movie,
                "year": song.year,
                "singers": song.singers
            }
        }

    # movie question
    if (
        "movie" in question_lower
        or "film" in question_lower
        or "which film" in question_lower
    ):
        return {
            "question": question,
            "answer": f"{song.title} is from the movie {song.movie}.",
            "matched_song": {
                "title": song.title,
                "movie": song.movie,
                "year": song.year
            }
        }

    # default song summary
    return {
        "question": question,
        "answer": (
            f"{song.title} is a {song.mood} song from {song.movie}. "
            f"It was written by {song.lyricist}, composed by {song.composer}, "
            f"and sung by {song.singers}."
        ),
        "matched_song": {
            "title": song.title,
            "movie": song.movie,
            "year": song.year,
            "singers": song.singers,
            "lyricist": song.lyricist,
            "composer": song.composer,
            "mood": song.mood,
            "themes": song.themes
        }
    }