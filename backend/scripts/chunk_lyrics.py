import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from app.database import SessionLocal, Base, engine
from app.models import Song, LyricsChunk


def split_lyrics_into_chunks(lyrics: str):
    """
    Simple version:
    - Split lyrics by line
    - Remove empty lines
    - Each line becomes one chunk

    Later we can improve this to group 2-4 lines together.
    """
    if not lyrics:
        return []

    lines = [
        line.strip()
        for line in lyrics.splitlines()
        if line.strip()
    ]

    chunks = []

    for index, line in enumerate(lines):
        chunks.append({
            "chunk_text": line,
            "chunk_index": index,
            "start_line": index + 1,
            "end_line": index + 1
        })

    return chunks


def chunk_all_songs():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        songs = db.query(Song).all()

        total_chunks = 0

        for song in songs:
            # Delete old chunks for this song so script can be re-run safely
            db.query(LyricsChunk).filter(
                LyricsChunk.song_id == song.id
            ).delete()

            chunks = split_lyrics_into_chunks(song.lyrics)

            for chunk in chunks:
                lyrics_chunk = LyricsChunk(
                    song_id=song.id,
                    chunk_text=chunk["chunk_text"],
                    chunk_index=chunk["chunk_index"],
                    start_line=chunk["start_line"],
                    end_line=chunk["end_line"]
                )

                db.add(lyrics_chunk)
                total_chunks += 1

        db.commit()

        print(f"Created {total_chunks} lyric chunks successfully.")

    except Exception as e:
        db.rollback()
        print("Error while chunking lyrics:")
        print(e)

    finally:
        db.close()


if __name__ == "__main__":
    chunk_all_songs()