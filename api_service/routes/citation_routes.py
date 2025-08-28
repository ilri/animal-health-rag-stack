"""
Citation management routes.
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from typing import Dict, Any, Optional
import asyncio
import logging

from services.citation_fetcher import run_citation_fetcher_once
from utils.document_db import get_documents_without_citations
from utils.admin import AdminManager

router = APIRouter()
logger = logging.getLogger(__name__)
admin_manager = AdminManager()


@router.get("/citations/status")
async def get_citation_status():
    """Get status of citation fetching process."""
    try:
        pending_documents = get_documents_without_citations(limit=100)
        total_pending = len(pending_documents)
        
        return {
            "status": "success",
            "pending_citations": total_pending,
            "next_documents": [
                {
                    "id": doc["id"],
                    "filename": doc["filename"],
                    "doi": doc["doi"],
                    "created_at": doc["created_at"].isoformat() if doc["created_at"] else None
                }
                for doc in pending_documents[:10]  # Show next 10
            ]
        }
    except Exception as e:
        logger.error(f"Error getting citation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/citations/fetch")
async def trigger_citation_fetch(request: Request, background_tasks: BackgroundTasks):
    """Trigger citation fetching for pending documents."""
    admin_manager.require_admin(request, "trigger citation fetch")
    
    try:
        # Run citation fetcher in background
        background_tasks.add_task(run_citation_fetcher_once)
        
        return {
            "status": "success",
            "message": "Citation fetch process started in background"
        }
    except Exception as e:
        logger.error(f"Error triggering citation fetch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/citations/fetch-sync")
async def fetch_citations_sync(request: Request, limit: Optional[int] = 10):
    """Fetch citations synchronously (for testing)."""
    admin_manager.require_admin(request, "synchronous citation fetch")
    
    try:
        from services.citation_fetcher import CitationFetcher
        
        fetcher = CitationFetcher(batch_size=limit)
        processed = await fetcher.fetch_citations_batch()
        
        return {
            "status": "success",
            "processed_count": processed,
            "message": f"Processed {processed} documents"
        }
    except Exception as e:
        logger.error(f"Error in synchronous citation fetch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/citations/documents/{document_id}")
async def get_document_citation(document_id: int):
    """Get citation information for a specific document."""
    try:
        from utils.document_db import get_db_connection
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, filename, doi, reference, citation_fetched, 
                           citation_fetch_attempted_at, citation_fetch_error
                    FROM document 
                    WHERE id = %s
                    """,
                    (document_id,)
                )
                row = cursor.fetchone()
                
                if not row:
                    raise HTTPException(status_code=404, detail="Document not found")
                
                columns = [desc[0] for desc in cursor.description]
                document = dict(zip(columns, row))
                
                return {
                    "status": "success",
                    "document": document
                }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document citation: {e}")
        raise HTTPException(status_code=500, detail=str(e))