"""
Database operations for document metadata and citations.
"""

import psycopg2
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from .config import DB_URL


def get_db_connection():
    """Get a database connection."""
    return psycopg2.connect(DB_URL)


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
    citation_metadata: Dict[str, Any],
    citation_apa: str = None,
    citation_mla: str = None,
    citation_chicago: str = None
) -> bool:
    """Update document with fetched citation metadata."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    UPDATE document SET
                        title = %s,
                        authors = %s,
                        journal = %s,
                        publication_year = %s,
                        volume = %s,
                        issue = %s,
                        pages = %s,
                        publisher = %s,
                        abstract = %s,
                        keywords = %s,
                        citation_apa = %s,
                        citation_mla = %s,
                        citation_chicago = %s,
                        citation_fetched = TRUE,
                        citation_fetch_attempted_at = NOW(),
                        citation_fetch_error = NULL,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (
                        citation_metadata.get('title'),
                        json.dumps(citation_metadata.get('authors')) if citation_metadata.get('authors') else None,
                        citation_metadata.get('journal'),
                        citation_metadata.get('year'),
                        citation_metadata.get('volume'),
                        citation_metadata.get('issue'),
                        citation_metadata.get('pages'),
                        citation_metadata.get('publisher'),
                        citation_metadata.get('abstract'),
                        json.dumps(citation_metadata.get('keywords')) if citation_metadata.get('keywords') else None,
                        citation_apa,
                        citation_mla,
                        citation_chicago,
                        document_id
                    )
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
                SELECT citation_apa, citation_mla, citation_chicago, title, authors, 
                       journal, publication_year, doi
                FROM document 
                WHERE filename = %s AND citation_fetched = TRUE
                LIMIT 1
                """,
                (source_filename,)
            )
            row = cursor.fetchone()
            if row:
                apa, mla, chicago, title, authors_json, journal, year, doi = row
                
                # Return the best available citation format
                if apa:
                    return apa
                elif mla:
                    return mla
                elif chicago:
                    return chicago
                else:
                    # Fallback to basic formatting
                    citation_parts = []
                    if authors_json:
                        try:
                            authors = json.loads(authors_json)
                            if authors:
                                citation_parts.append(f"{authors[0]} et al." if len(authors) > 1 else authors[0])
                        except:
                            pass
                    
                    if year:
                        citation_parts.append(f"({year})")
                    
                    if title:
                        citation_parts.append(title)
                    
                    if journal:
                        citation_parts.append(f"*{journal}*")
                    
                    if doi:
                        citation_parts.append(f"https://doi.org/{doi}")
                    
                    return ". ".join(filter(None, citation_parts))
            
            return None