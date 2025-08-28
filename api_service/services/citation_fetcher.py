"""
Background service for fetching and updating document citations.
"""

import asyncio
import logging
from typing import List
from datetime import datetime

from .citation_service import CitationService, CitationMetadata
from ..utils.document_db import (
    get_documents_without_citations,
    update_document_citation_metadata,
    mark_citation_fetch_failed
)

logger = logging.getLogger(__name__)


class CitationFetcher:
    """Background service to fetch citations for documents with DOIs."""
    
    def __init__(self, batch_size: int = 10, delay_between_batches: float = 1.0):
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches
        self.is_running = False
    
    async def _update_document_doi(self, document_id: int, doi: str) -> bool:
        """Update document table with extracted DOI."""
        try:
            from ..utils.document_db import get_db_connection
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE document SET doi = %s, updated_at = NOW() WHERE id = %s",
                        (doi, document_id)
                    )
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating DOI for document {document_id}: {e}")
            return False
    
    async def _update_document_reference(self, document_id: int, citation: str) -> bool:
        """Update document table with formatted citation."""
        try:
            from ..utils.document_db import get_db_connection
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
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
                        (citation, document_id)
                    )
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating citation for document {document_id}: {e}")
            return False
    
    async def fetch_citations_batch(self) -> int:
        """Fetch citations for a batch of documents. Returns number processed."""
        documents = get_documents_without_citations(self.batch_size)
        if not documents:
            return 0
        
        processed_count = 0
        
        async with CitationService() as citation_service:
            for doc in documents:
                doc_id = doc['id']
                filename = doc['filename']
                doi = doc['doi']
                
                logger.info(f"Processing document {doc_id}: {filename}")
                
                try:
                    # Extract DOI if not already present
                    if not doi:
                        doi = citation_service.extract_doi_from_filename(filename)
                        if not doi:
                            logger.info(f"No DOI found for {filename}, skipping")
                            mark_citation_fetch_failed(doc_id, "No DOI found")
                            continue
                        else:
                            # Update document table with extracted DOI
                            logger.info(f"Extracted DOI {doi} from filename {filename}")
                            await self._update_document_doi(doc_id, doi)
                    
                    # Fetch citation using DOI (returns formatted APA citation)
                    citation = await citation_service.fetch_citation_from_doi(doi)
                    
                    if citation:
                        # Update database with formatted citation
                        success = await self._update_document_reference(doc_id, citation)
                        
                        if success:
                            logger.info(f"Successfully updated citation for {filename}")
                            processed_count += 1
                        else:
                            logger.error(f"Failed to update database for {filename}")
                            mark_citation_fetch_failed(doc_id, "Database update failed")
                    else:
                        logger.warning(f"No citation found for DOI {doi} (file: {filename})")
                        mark_citation_fetch_failed(doc_id, f"No citation found for DOI {doi}")
                
                except Exception as e:
                    logger.error(f"Error processing document {filename}: {e}")
                    mark_citation_fetch_failed(doc_id, str(e))
                
                # Small delay between documents to be respectful to APIs
                await asyncio.sleep(0.5)
        
        return processed_count
    
    async def run_continuous(self, max_iterations: int = None):
        """Run the citation fetcher continuously."""
        self.is_running = True
        iteration = 0
        
        logger.info("Starting citation fetcher service")
        
        try:
            while self.is_running:
                if max_iterations and iteration >= max_iterations:
                    break
                
                try:
                    processed = await self.fetch_citations_batch()
                    
                    if processed > 0:
                        logger.info(f"Processed {processed} documents in iteration {iteration + 1}")
                    else:
                        logger.debug(f"No documents to process in iteration {iteration + 1}")
                    
                    # Wait before next batch
                    await asyncio.sleep(self.delay_between_batches)
                    iteration += 1
                    
                except Exception as e:
                    logger.error(f"Error in citation fetcher iteration {iteration + 1}: {e}")
                    await asyncio.sleep(5.0)  # Longer delay on errors
                    
        except asyncio.CancelledError:
            logger.info("Citation fetcher cancelled")
        except Exception as e:
            logger.error(f"Fatal error in citation fetcher: {e}")
        finally:
            self.is_running = False
            logger.info("Citation fetcher service stopped")
    
    def stop(self):
        """Stop the citation fetcher."""
        self.is_running = False


async def run_citation_fetcher_once():
    """Run citation fetcher once (useful for testing or manual runs)."""
    fetcher = CitationFetcher()
    processed = await fetcher.fetch_citations_batch()
    logger.info(f"Citation fetch completed: {processed} documents processed")
    return processed


if __name__ == "__main__":
    # For testing - run once
    import sys
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        asyncio.run(run_citation_fetcher_once())
    else:
        # Run continuously
        async def main():
            fetcher = CitationFetcher()
            await fetcher.run_continuous()
        
        asyncio.run(main())