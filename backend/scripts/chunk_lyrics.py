import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from app.database import SessionLocal, Base, engine
from app.models import Song, LyricsChunk


def split_lyrics_into_chunks(lyrics: str, max_lines_per_chunk: int = 4):
    """
    Groups lyrics into stanzas of up to `max_lines_per_chunk` lines.
    Respects empty lines as natural stanza breaks.
    """
    if not lyrics:
        return []

    chunks = []
    current_chunk_lines = []
    chunk_index = 0
    start_line_num = 1
    
    original_lines = lyrics.splitlines()
    
    for i, line in enumerate(original_lines):
        line_num = i + 1
        stripped_line = line.strip()
        
        if stripped_line:
            if not current_chunk_lines:
                start_line_num = line_num
            current_chunk_lines.append(stripped_line)
            
            # If we hit max lines, emit the chunk
            if len(current_chunk_lines) == max_lines_per_chunk:
                chunks.append({
                    "chunk_text": "\n".join(current_chunk_lines),
                    "chunk_index": chunk_index,
                    "start_line": start_line_num,
                    "end_line": line_num
                })
                chunk_index += 1
                current_chunk_lines = []
        else:
            # Empty line -> natural stanza break
            if current_chunk_lines:
                chunks.append({
                    "chunk_text": "\n".join(current_chunk_lines),
                    "chunk_index": chunk_index,
                    "start_line": start_line_num,
                    "end_line": line_num - 1
                })
                chunk_index += 1
                current_chunk_lines = []
                
    # Flush remaining lines
    if current_chunk_lines:
        chunks.append({
            "chunk_text": "\n".join(current_chunk_lines),
            "chunk_index": chunk_index,
            "start_line": start_line_num,
            "end_line": len(original_lines)
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