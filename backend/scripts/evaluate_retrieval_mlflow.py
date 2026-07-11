import sys
from pathlib import Path

import mlflow
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

from app.database import SessionLocal
from app.models import LyricsChunk, Song
from app.services.embedding_service import generate_embedding
from app.services.query_expansion import expand_query


EVALUATION_FILE = BASE_DIR / "data" / "evaluation_queries.csv"
TOP_K = 5

EXPERIMENT_NAME = "Tamil Song Lyric Retrieval"

CONCEPT_DICTIONARY = BASE_DIR / "config" / "concept_dictionary.json"




def parse_expected_titles(value):
    if pd.isna(value) or not str(value).strip():
        return []

    return [
        title.strip().lower()
        for title in str(value).split("|")
        if title.strip()
    ]


def semantic_search(db, query, top_k=5):
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

    return [
        {
            "song_title": chunk.song.title,
            "movie": chunk.song.movie,
            "line": chunk.chunk_text,
            "line_number": chunk.start_line,
        }
        for chunk in chunks
    ]


def calculate_hit_at_k(retrieved_titles, expected_titles):
    if not expected_titles:
        return None

    return int(any(title in expected_titles for title in retrieved_titles))


def calculate_precision_at_k(retrieved_titles, expected_titles, k):
    if not expected_titles:
        return None

    relevant = sum(
        1 for title in retrieved_titles[:k]
        if title in expected_titles
    )

    return relevant / k


def calculate_mrr(retrieved_titles, expected_titles):
    if not expected_titles:
        return None

    for index, title in enumerate(retrieved_titles):
        if title in expected_titles:
            return 1 / (index + 1)

    return 0


def evaluate_retrieval(use_query_expansion: bool):
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
            original_query = row.get("query")
            query_type = row.get("query_type")
            expected_titles = parse_expected_titles(row.get("expected_song_titles"))

            if not expected_titles:
                continue

            final_query = (
                expand_query(original_query)
                if use_query_expansion
                else original_query
            )

            results = semantic_search(db, final_query, top_k=TOP_K)

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
                "query": original_query,
                "final_query": final_query,
                "query_type": query_type,
                "expected_titles": " | ".join(expected_titles),
                "retrieved_titles": " | ".join(retrieved_titles),
                f"hit@{TOP_K}": hit_at_k,
                f"precision@{TOP_K}": precision_at_k,
                "mrr": mrr,
            })

        avg_hit = total_hit / evaluated_count
        avg_precision = total_precision / evaluated_count
        avg_mrr = total_mrr / evaluated_count

        results_df = pd.DataFrame(all_results)

        output_name = (
            "semantic_expanded_results.csv"
            if use_query_expansion
            else "semantic_baseline_results.csv"
        )

        output_path = BASE_DIR / "data" / output_name
        results_df.to_csv(output_path, index=False, encoding="utf-8-sig")

        return {
            "evaluated_count": evaluated_count,
            f"hit@{TOP_K}": avg_hit,
            f"precision@{TOP_K}": avg_precision,
            "mrr": avg_mrr,
            "results_path": output_path,
        }

    finally:
        db.close()


def run_experiment(use_query_expansion: bool):
    mlflow.set_experiment(EXPERIMENT_NAME)

    run_name = (
        "semantic_search_with_query_expansion"
        if use_query_expansion
        else "semantic_search_baseline"
    )

    with mlflow.start_run(run_name=run_name):
        mlflow.log_param("retrieval_method", "semantic_search")
        mlflow.log_param("embedding_model", "text-embedding-3-large")
        mlflow.log_param("embedding_dimensions", 3072)
        mlflow.log_param("top_k", TOP_K)
        mlflow.log_param("query_expansion", use_query_expansion)
        mlflow.log_param("chunking_strategy", "line_level_chunks")
        mlflow.log_param("vector_database", "supabase_postgres_pgvector")

        metrics = evaluate_retrieval(use_query_expansion)

        mlflow.log_metric(f"hit_at_{TOP_K}", metrics[f"hit@{TOP_K}"])
        mlflow.log_metric(f"precision_at_{TOP_K}", metrics[f"precision@{TOP_K}"])
        mlflow.log_metric("mrr", metrics["mrr"])
        mlflow.log_metric("evaluated_queries", metrics["evaluated_count"])

        mlflow.log_artifact(str(EVALUATION_FILE), artifact_path="evaluation")
        mlflow.log_artifact(str(metrics["results_path"]), artifact_path="results")
        mlflow.log_artifact(str(CONCEPT_DICTIONARY), artifact_path="config")

        print("MLflow run completed.")
        print(f"Run name: {run_name}")
        print(f"Hit@{TOP_K}: {metrics[f'hit@{TOP_K}']:.3f}")
        print(f"Precision@{TOP_K}: {metrics[f'precision@{TOP_K}']:.3f}")
        print(f"MRR: {metrics['mrr']:.3f}")


if __name__ == "__main__":
    run_experiment(use_query_expansion=False)
    run_experiment(use_query_expansion=True)