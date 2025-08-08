from fastapi import APIRouter, HTTPException
from utils import get_db_connection

router = APIRouter(prefix="/ingestion/quality", tags=["Ingestion Quality"])

@router.get("/{document_id}")
async def get_document_quality(document_id: int):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) FILTER (WHERE ce.score = 1) AS good_chunks,
                        COUNT(*) AS total_chunks
                    FROM chunk_evaluations ce
                    JOIN document_chunks dc ON dc.id = ce.chunk_id
                    WHERE (dc.source_metadata->>'content_hash') = (
                        SELECT source_metadata->>'content_hash' 
                        FROM document_chunks 
                        WHERE id = %s
                        LIMIT 1
                    )
                """,
                    (document_id,)
                )
                row = cursor.fetchone()
                good = row["good_chunks"] or 0
                total = row["total_chunks"] or 0
                pct = round((good / total) * 100, 1) if total else 0.0

                cursor.execute(
                    """
                    SELECT 
                        (SELECT COUNT(DISTINCT source_metadata->>'source') FROM document_chunks WHERE source_metadata->>'ocr_applied' = 'true') AS ocr_docs,
                        (SELECT COUNT(DISTINCT source_metadata->>'source') FROM document_chunks) AS all_docs
                """
                )
                ocr_stats = cursor.fetchone()
                return {
                    "document_id": document_id,
                    "chunk_quality": {"good": good, "total": total, "percentage": pct},
                    "ocr": {
                        "documents_with_ocr": ocr_stats["ocr_docs"] or 0,
                        "total_documents": ocr_stats["all_docs"] or 0
                    }
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_ingestion_quality_summary():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) FILTER (WHERE score = 1) AS good,
                        COUNT(*) AS total
                    FROM chunk_evaluations
                """
                )
                row = cursor.fetchone()
                good = row["good"] or 0
                total = row["total"] or 0
                pct = round((good / total) * 100, 1) if total else 0.0

                cursor.execute(
                    """
                    SELECT 
                        COUNT(DISTINCT source_metadata->>'source') as unique_documents,
                        COUNT(*) as total_chunks
                    FROM document_chunks
                    """
                )
                overall = cursor.fetchone()

                return {
                    "chunk_quality": {"good": good, "total": total, "percentage": pct},
                    "overall": overall
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 