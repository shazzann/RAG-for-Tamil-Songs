import logging
from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.routes import songs, qa, lyrics, chat

logger = logging.getLogger(__name__)

# Attempt to create tables, but do not crash the application if Supabase is temporarily unreachable
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logger.warning(f"Could not connect to database on startup (Supabase may be offline/unreachable): {e}")

app = FastAPI(
    title="Tamil Song RAG Agent",
    description="A RAG-based Tamil song intelligence chatbot",
    version="0.1.0"
)

app.include_router(songs.router)
app.include_router(qa.router)
app.include_router(lyrics.router)
app.include_router(chat.router)


@app.get("/")
def root(db: Session = Depends(get_db)):
    """Health check endpoint reporting API and database status."""
    db_status = "available"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unavailable"

    return {
        "api": "healthy",
        "database": db_status
    }