from fastapi import APIRouter, HTTPException
from utils import get_db_connection

router = APIRouter(prefix="/retrieval/eval", tags=["Retrieval Eval"])

@router.get("/summary")
async def get_retrieval_eval_summary():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) FILTER (WHERE relevance_score = 1) AS relevant,
                        COUNT(*) AS total
                    FROM retrieval_evaluations
                    """
                )
                row = cursor.fetchone()
                relevant = row["relevant"] or 0
                total = row["total"] or 0
                precision = round(relevant / total, 3) if total else 0.0

                cursor.execute(
                    """
                    SELECT 
                        AVG(CASE WHEN rank_position <= 5 THEN relevance_score END)::float AS p5,
                        AVG(CASE WHEN rank_position <= 10 THEN relevance_score END)::float AS p10
                    FROM retrieval_evaluations
                    """
                )
                row2 = cursor.fetchone()
                return {
                    "overall_precision": precision,
                    "precision@5": float(row2["p5"]) if row2["p5"] is not None else 0.0,
                    "precision@10": float(row2["p10"]) if row2["p10"] is not None else 0.0,
                    "total_judgments": total,
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/query/{query_id}")
async def get_query_retrieval_eval(query_id: int):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT 
                        re.chunk_id,
                        re.relevance_score,
                        re.rank_position,
                        re.retrieval_method,
                        dc.text_content
                    FROM retrieval_evaluations re
                    JOIN document_chunks dc ON dc.id = re.chunk_id
                    WHERE re.query_id = %s
                    ORDER BY re.rank_position ASC
                    """,
                    (query_id,)
                )
                rows = cursor.fetchall()
                return {
                    "query_id": query_id,
                    "judgments": rows
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 