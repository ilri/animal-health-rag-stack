#!/usr/bin/env python3
import argparse
import json
from typing import List

from api_service.utils import get_db_connection, Config
from api_service.services.qa_service import RetrievalEvaluator
from api_service.services.query_service import QueryService


def fetch_recent_query_cache(limit: int) -> List[dict]:
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, query_text 
                FROM query_cache 
                ORDER BY created_at DESC 
                LIMIT %s
                """,
                (limit,)
            )
            return cursor.fetchall()


def backfill(limit: int, max_results: int, use_llm: bool):
    evaluator = RetrievalEvaluator()
    q = QueryService()

    entries = fetch_recent_query_cache(limit)
    for entry in entries:
        query_id = entry["id"]
        query_text = entry["query_text"]
        print(f"Backfilling retrieval evals for query_id={query_id}")

        # Re-run vector retrieval for reproducible ranking
        embedding = q.create_embedding(query_text)
        chunks = q.vector_search(embedding, max_results)

        # Vector judgments
        judgments = evaluator.relevance.evaluate_ranked_list(query_text, chunks)
        evaluator.persist_retrieval_evaluations(query_id, judgments)

        # Optional LLM judgments
        if use_llm:
            import asyncio
            llm_judgments = asyncio.run(evaluator.evaluate_llm_retrieval(query_text, chunks))
            evaluator.persist_retrieval_evaluations(query_id, llm_judgments)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill retrieval evaluations for recent query_cache entries")
    parser.add_argument("--limit", type=int, default=50, help="Number of recent query_cache entries")
    parser.add_argument("--max_results", type=int, default=10, help="Top-N chunks to evaluate")
    parser.add_argument("--use-llm", action="store_true", help="Include LLM-based judgments")
    args = parser.parse_args()

    backfill(args.limit, args.max_results, args.use_llm) 