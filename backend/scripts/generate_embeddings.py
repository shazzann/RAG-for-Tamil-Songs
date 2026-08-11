import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from app.database import SessionLocal
from app.models import LyricsChunk
from app.services.embedding_service import generate_embedding


def generate_missing_embeddings():
    db = SessionLocal()

    try:
        chunks = (
            db.query(LyricsChunk)
            .filter(LyricsChunk.embedding == None)
            .all()
        )

        print(f"Found {len(chunks)} chunks without embeddings.")

        updated = 0

        for chunk in chunks:
            safe_text = chunk.chunk_text[:50].encode("ascii", "replace").decode("ascii")
            print(f"Embedding chunk {chunk.id}: {safe_text}")

            embedding = generate_embedding(chunk.chunk_text)

            if embedding:
                chunk.embedding = embedding
                updated += 1

        db.commit()

        print(f"Generated embeddings for {updated} chunks.")

    except Exception as e:
        db.rollback()
        print("Error while generating embeddings:")
        print(e)

    finally:
        db.close()


if __name__ == "__main__":
    generate_missing_embeddings()