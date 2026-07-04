from sqlalchemy import Column, Integer, String, Text
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