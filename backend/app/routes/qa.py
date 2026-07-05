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


MOOD_KEYWORDS = {
    "sad": ["sad", "sogam", "சோகம்", "துயரம்", "melancholy"],
    "romantic": ["romantic", "love", "kadhal", "காதல்", "romance"],
    "happy": ["happy", "joy", "celebration", "fun"],
    "devotional": ["devotional", "god", "prayer", "bhakti", "பக்தி"],
    "energetic": ["energetic", "mass", "dance", "fast"]
}


THEME_KEYWORDS = {
    "eyes": ["eyes", "eye", "kan", "கண்", "vizhi", "விழி", "paarvai", "பார்வை"],
    "rain": ["rain", "mazhai", "மழை"],
    "love": ["love", "kadhal", "காதல்"],
    "separation": ["separation", "pirivu", "பிரிவு", "missing", "longing"],
    "mother": ["mother", "amma", "அம்மா"]
}


def find_song_by_title(question: str, db: Session):
    songs = db.query(Song).all()
    question_lower = question.lower()

    for song in songs:
        if song.title and song.title.lower() in question_lower:
            return song

    return None


def detect_mood(question_lower: str):
    for mood, keywords in MOOD_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in question_lower:
                return mood
    return None


def detect_theme(question_lower: str):
    for theme, keywords in THEME_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in question_lower:
                return theme
    return None


def detect_year(question_lower: str):
    words = question_lower.replace("?", "").split()

    for word in words:
        if word.isdigit() and len(word) == 4:
            year = int(word)
            if 1900 <= year <= 2100:
                return year

    return None


def find_person_name(question: str, db: Session):
    """
    Simple matching against lyricist, composer, and singers.
    Later we can replace this with better entity extraction.
    """
    songs = db.query(Song).all()
    question_lower = question.lower()

    for song in songs:
        possible_people = [
            song.lyricist,
            song.composer,
            song.singers
        ]

        for person_text in possible_people:
            if not person_text:
                continue

            names = [name.strip() for name in person_text.split(",")]

            for name in names:
                if name and name.lower() in question_lower:
                    return name

    return None


def format_song_list(songs):
    if not songs:
        return "I could not find matching songs in the database."

    lines = []

    for song in songs:
        line = f"- {song.title}"
        if song.movie:
            line += f" from {song.movie}"
        if song.year:
            line += f" ({song.year})"
        if song.lyricist:
            line += f", lyrics by {song.lyricist}"
        lines.append(line)

    return "\n".join(lines)


@router.post("/ask")
def ask_question(request: QuestionRequest, db: Session = Depends(get_db)):
    question = request.question.strip()
    question_lower = question.lower()

    # 1. First, try direct song-title factual QA
    song = find_song_by_title(question, db)

    if song:
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

    # 2. Analytical search questions
    mood = detect_mood(question_lower)
    theme = detect_theme(question_lower)
    year = detect_year(question_lower)
    person = find_person_name(question, db)

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
                Song.singers.ilike(person_search)
            )
        )

    songs = query.all()

    if mood or theme or year or person:
        return {
            "question": question,
            "detected_filters": {
                "mood": mood,
                "theme": theme,
                "year": year,
                "person": person
            },
            "count": len(songs),
            "answer": format_song_list(songs),
            "songs": songs
        }

    return {
        "question": question,
        "answer": "I could not understand the question yet. Try asking about song title, lyricist, composer, singer, mood, theme, or year.",
        "matched_song": None
    }