"""
Database operations for document metadata and citations.
"""

import psycopg2
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from .config import Config


def get_db_connection():
    """Get a database connection."""
    return psycopg2.connect(Config.DB_URL)


def get_documents_without_citations(limit: int = 50) -> List[Dict[str, Any]]:
    """Get documents that haven't had their citations fetched yet."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, filename, doi, file_path, created_at
                FROM document 
                WHERE citation_fetched = FALSE 
                   AND (citation_fetch_error IS NULL OR citation_fetch_attempted_at < NOW() - INTERVAL '24 hours')
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,)
            )
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]


def update_document_citation_metadata(
    document_id: int,
    citation_reference: str
) -> bool:
    """Update document with fetched citation reference."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    UPDATE document SET
                        reference = %s,
                        citation_fetched = TRUE,
                        citation_fetch_attempted_at = NOW(),
                        citation_fetch_error = NULL,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (citation_reference, document_id)
                )
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                print(f"Error updating document {document_id}: {e}")
                conn.rollback()
                return False


def mark_citation_fetch_failed(document_id: int, error_message: str) -> bool:
    """Mark a document as having failed citation fetch."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    UPDATE document SET
                        citation_fetch_attempted_at = NOW(),
                        citation_fetch_error = %s
                    WHERE id = %s
                    """,
                    (error_message, document_id)
                )
                conn.commit()
                return cursor.rowcount > 0
            except Exception as e:
                print(f"Error marking citation fetch failed for document {document_id}: {e}")
                conn.rollback()
                return False


def get_document_by_chunk_id(chunk_id: int) -> Optional[Dict[str, Any]]:
    """Get document metadata by chunk ID."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT d.id, d.filename, d.doi, d.reference, d.citation_fetched
                FROM document d
                JOIN document_chunks dc ON dc.document_id = d.id
                WHERE dc.id = %s
                """,
                (chunk_id,)
            )
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None


def get_documents_for_chunks(chunk_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    """Get document metadata for multiple chunk IDs."""
    if not chunk_ids:
        return {}
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT dc.id as chunk_id, d.id, d.filename, d.doi, d.reference, d.citation_fetched
                FROM document d
                JOIN document_chunks dc ON dc.document_id = d.id
                WHERE dc.id = ANY(%s)
                """,
                (chunk_ids,)
            )
            
            results = {}
            columns = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                chunk_id = row_dict.pop('chunk_id')
                results[chunk_id] = row_dict
            
            return results


def get_citation_for_source(source_filename: str) -> Optional[str]:
    """Get formatted citation for a source filename."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT reference
                FROM document 
                WHERE filename = %s AND citation_fetched = TRUE
                LIMIT 1
                """,
                (source_filename,)
            )
            row = cursor.fetchone()
            if row:
                return row[0]  # Return the reference (APA citation from doi.org)
            
            return None