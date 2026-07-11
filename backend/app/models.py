from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.database import Base


class Song(Base):
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(255), nullable=False, index=True)
    movie = Column(String(255), nullable=True, index=True)
    year = Column(Integer, nullable=True, index=True)

    singers = Column(Text, nullable=True)
    lyricist = Column(String(255), nullable=True, index=True)
    composer = Column(String(255), nullable=True, index=True)

    mood = Column(String(100), nullable=True, index=True)
    themes = Column(Text, nullable=True)

    lyrics = Column(Text, nullable=True)
    source_url = Column(Text, nullable=True)

    chunks = relationship(
        "LyricsChunk",
        back_populates="song",
        cascade="all, delete-orphan"
    )


class LyricsChunk(Base):
    __tablename__ = "lyrics_chunks"

    id = Column(Integer, primary_key=True, index=True)

    song_id = Column(Integer, ForeignKey("songs.id"), nullable=False, index=True)

    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)

    start_line = Column(Integer, nullable=True)
    end_line = Column(Integer, nullable=True)

    embedding = Column(Vector(3072), nullable=True)

    song = relationship("Song", back_populates="chunks")