import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from app.database import SessionLocal
from app.models import LyricsChunk, Song
from app.services.embedding_service import generate_embedding


EVALUATION_FILE = BASE_DIR / "data" / "evaluation_queries.csv"
TOP_K = 5


def parse_expected_titles(value):
    """
    Convert:
    'Song A|Song B'
    into:
    ['song a', 'song b']
    """
    if pd.isna(value) or not str(value).strip():
        return []

    return [
        title.strip().lower()
        for title in str(value).split("|")
        if title.strip()
    ]


def semantic_search(db, query, top_k=5):
    """
    Search lyric chunks using vector similarity.
    Returns a list of result dictionaries.
    """
    query_embedding = generate_embedding(query)

    if not query_embedding:
        return []

    chunks = (
        db.query(LyricsChunk)
        .join(Song)
        .filter(LyricsChunk.embedding != None)
        .order_by(LyricsChunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
        .all()
    )

    results = []

    for chunk in chunks:
        results.append({
            "song_title": chunk.song.title,
            "movie": chunk.song.movie,
            "line": chunk.chunk_text,
            "line_number": chunk.start_line
        })

    return results


def calculate_hit_at_k(retrieved_titles, expected_titles):
    """
    Hit@K = 1 if at least one expected title appears in retrieved titles.
    """
    if not expected_titles:
        return None

    for title in retrieved_titles:
        if title in expected_titles:
            return 1

    return 0


def calculate_precision_at_k(retrieved_titles, expected_titles, k):
    """
    Precision@K = relevant retrieved results / K
    """
    if not expected_titles:
        return None

    if not retrieved_titles:
        return 0

    relevant = 0

    for title in retrieved_titles[:k]:
        if title in expected_titles:
            relevant += 1

    return relevant / k


def calculate_mrr(retrieved_titles, expected_titles):
    """
    MRR = reciprocal rank of first relevant result.
    Example:
    correct result at rank 1 → 1.0
    correct result at rank 2 → 0.5
    correct result at rank 5 → 0.2
    no correct result → 0
    """
    if not expected_titles:
        return None

    for index, title in enumerate(retrieved_titles):
        if title in expected_titles:
            rank = index + 1
            return 1 / rank

    return 0


def evaluate():
    db = SessionLocal()

    try:
        df = pd.read_csv(EVALUATION_FILE)

        all_results = []

        total_hit = 0
        total_precision = 0
        total_mrr = 0
        evaluated_count = 0

        for _, row in df.iterrows():
            query_id = row.get("query_id")
            query = row.get("query")
            query_type = row.get("query_type")
            expected_titles = parse_expected_titles(row.get("expected_song_titles"))

            # Skip rows where expected title is empty
            # Example: negative test cases
            if not expected_titles:
                continue

            results = semantic_search(db, query, top_k=TOP_K)

            retrieved_titles = [
                result["song_title"].strip().lower()
                for result in results
            ]

            hit_at_k = calculate_hit_at_k(retrieved_titles, expected_titles)
            precision_at_k = calculate_precision_at_k(
                retrieved_titles,
                expected_titles,
                TOP_K
            )
            mrr = calculate_mrr(retrieved_titles, expected_titles)

            total_hit += hit_at_k
            total_precision += precision_at_k
            total_mrr += mrr
            evaluated_count += 1

            all_results.append({
                "query_id": query_id,
                "query": query,
                "query_type": query_type,
                "expected_titles": " | ".join(expected_titles),
                "retrieved_titles": " | ".join(retrieved_titles),
                f"hit@{TOP_K}": hit_at_k,
                f"precision@{TOP_K}": precision_at_k,
                "mrr": mrr
            })

        if evaluated_count == 0:
            print("No evaluatable rows found.")
            return

        avg_hit = total_hit / evaluated_count
        avg_precision = total_precision / evaluated_count
        avg_mrr = total_mrr / evaluated_count

        results_df = pd.DataFrame(all_results)

        output_path = BASE_DIR / "data" / "semantic_evaluation_results.csv"
        results_df.to_csv(output_path, index=False, encoding="utf-8-sig")

        print("\nEvaluation completed.")
        print(f"Evaluated queries: {evaluated_count}")
        print(f"Hit@{TOP_K}: {avg_hit:.3f}")
        print(f"Precision@{TOP_K}: {avg_precision:.3f}")
        print(f"MRR: {avg_mrr:.3f}")
        print(f"\nDetailed results saved to: {output_path}")

    except Exception as e:
        print("Error during evaluation:")
        print(e)

    finally:
        db.close()


if __name__ == "__main__":
    evaluate()