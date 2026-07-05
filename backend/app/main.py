from app.routes import lyrics
from app.routes import qa
from fastapi import FastAPI
from app.database import Base, engine
from app.models import Song
from app.routes import songs

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Tamil Song RAG Agent",
    description="A RAG-based Tamil song intelligence chatbot",
    version="0.1.0"
)

app.include_router(songs.router)
app.include_router(qa.router)
app.include_router(lyrics.router)

@app.get("/")
def root():
    return {
        "message": "Tamil Song RAG Agent API is running"
    }