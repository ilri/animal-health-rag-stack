from typing import Dict, List
import math

class RetrievalRelevanceEvaluator:
    """Binary relevance evaluator.
    Starts with a cosine similarity threshold heuristic using existing similarity scores.
    Can be extended to LLM-based judgments later.
    """

    def __init__(self, similarity_threshold: float = 0.35):
        self.similarity_threshold = similarity_threshold

    def evaluate_retrieval(self, query: str, chunk: Dict) -> Dict[str, object]:
        # Expect chunk dict to include 'similarity' and 'text_content'
        similarity = float(chunk.get('similarity', 0.0))
        is_relevant = int(similarity >= self.similarity_threshold)
        explanation = f"similarity={similarity:.3f} threshold={self.similarity_threshold}"
        return {
            "relevance_score": is_relevant,
            "explanation": explanation,
            "retrieval_method": "vector",
        }

    def evaluate_ranked_list(self, query: str, chunks: List[Dict]) -> List[Dict]:
        results = []
        for rank, ch in enumerate(chunks, start=1):
            res = self.evaluate_retrieval(query, ch)
            res["rank_position"] = rank
            res["chunk_id"] = ch.get("id")
            results.append(res)
        return results 