import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from app.database import SessionLocal, Base, engine
from app.models import Song


CSV_PATH = BASE_DIR / "data" / "sample_songs.csv"


def seed_songs():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        df = pd.read_csv(CSV_PATH)

        inserted = 0

        for _, row in df.iterrows():
            title = str(row.get("title", "")).strip()
            movie = str(row.get("movie", "")).strip()

            existing_song = (
                db.query(Song)
                .filter(Song.title == title, Song.movie == movie)
                .first()
            )

            if existing_song:
                continue

            song = Song(
                title=title,
                movie=movie,
                year=int(row["year"]) if not pd.isna(row.get("year")) else None,
                singers=str(row.get("singers", "")).strip(),
                lyricist=str(row.get("lyricist", "")).strip(),
                composer=str(row.get("composer", "")).strip(),
                mood=str(row.get("mood", "")).strip(),
                themes=str(row.get("themes", "")).strip(),
                lyrics=str(row.get("lyrics", "")).strip(),
                source_url=str(row.get("source_url", "")).strip(),
            )

            db.add(song)
            inserted += 1

        db.commit()

        print(f"Inserted {inserted} songs successfully.")

    except Exception as e:
        db.rollback()
        print("Error while seeding songs:")
        print(e)

    finally:
        db.close()


if __name__ == "__main__":
    seed_songs()