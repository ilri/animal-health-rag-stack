"""
Citation Service for Academic References

Provides functionality to:
- Extract DOIs and metadata from documents
- Fetch proper academic citations from DOI APIs
- Format citations in standard academic formats
- Cache citations to avoid redundant API calls
"""

import re
import json
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class CitationMetadata:
    """Structured citation metadata."""
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None
    publisher: Optional[str] = None
    conference: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, filtering out None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}

class CitationService:
    """Service for handling academic citations and metadata."""
    
    # DOI API endpoints
    CROSSREF_API = "https://api.crossref.org/works/"
    DATACITE_API = "https://api.datacite.org/dois/"
    
    # Common DOI patterns
    DOI_PATTERNS = [
        r'10\.\d{4,}[^\s]*',  # Standard DOI format
        r'doi:\s*10\.\d{4,}[^\s]*',  # DOI with prefix
        r'DOI:\s*10\.\d{4,}[^\s]*',  # DOI with uppercase prefix
    ]
    
    def __init__(self):
        self.session = None
        self._citation_cache = {}  # Simple in-memory cache
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def extract_doi_from_filename(self, filename: str) -> Optional[str]:
        """Extract DOI from filename by converting first hyphen to forward slash."""
        if not filename:
            return None
        
        # Remove file extension and path
        import os
        base_name = os.path.splitext(os.path.basename(filename))[0]
        
        # Check if filename looks like a DOI (starts with 10. and has hyphens)
        if base_name.startswith('10.') and '-' in base_name:
            # Convert first hyphen to forward slash to create DOI
            doi = base_name.replace('-', '/', 1)
            # Validate DOI format
            import re
            if re.match(r'^10\.\d{4,}/', doi):
                return doi
        
        return None

    def extract_doi_from_text(self, text: str) -> Optional[str]:
        """Extract DOI from text content."""
        if not text:
            return None
            
        for pattern in self.DOI_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Clean up the DOI
                doi = matches[0].replace('doi:', '').replace('DOI:', '').strip()
                # Remove common trailing punctuation
                doi = re.sub(r'[.,;:\s]+$', '', doi)
                return doi
        return None
    
    def extract_basic_metadata_from_text(self, text: str, filename: str = None) -> CitationMetadata:
        """Extract basic metadata from document text."""
        metadata = CitationMetadata()
        
        # Try to extract DOI - prioritize filename-based DOI for this archive
        metadata.doi = self.extract_doi_from_filename(filename)
        if not metadata.doi:
            metadata.doi = self.extract_doi_from_text(text)
        
        # Try to extract title (first non-empty line or largest font text)
        lines = text.split('\n')
        for line in lines[:20]:  # Check first 20 lines
            clean_line = line.strip()
            if clean_line and len(clean_line) > 20:  # Potential title
                metadata.title = clean_line
                break
        
        # Try to extract year
        year_matches = re.findall(r'\b(19|20)\d{2}\b', text)
        if year_matches:
            years = [int(y) for y in year_matches if 1900 <= int(y) <= datetime.now().year]
            if years:
                metadata.year = max(years)  # Use the most recent year found
        
        # Use filename as fallback title if no title found
        if not metadata.title and filename:
            # Clean filename to make it more readable
            title = filename.replace('_', ' ').replace('-', ' ')
            title = re.sub(r'\.(pdf|docx?|txt)$', '', title, re.IGNORECASE)
            metadata.title = title.title()
            
        return metadata
    
    async def fetch_citation_from_doi(self, doi: str) -> Optional[str]:
        """Fetch APA-formatted citation from doi.org citation API."""
        if not doi or not self.session:
            return None
            
        # Check cache first
        if doi in self._citation_cache:
            cached_citation, timestamp = self._citation_cache[doi]
            # Cache for 24 hours
            if datetime.now() - timestamp < timedelta(hours=24):
                return cached_citation
        
        # Clean DOI
        clean_doi = doi.strip().replace('https://doi.org/', '')
        
        try:
            # Use doi.org citation API for APA format
            url = f"https://citation.crossref.org/format?doi={clean_doi}&style=apa&lang=en-US"
            headers = {'Accept': 'text/plain'}
            
            async with self.session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    citation = await response.text()
                    citation = citation.strip()
                    
                    if citation and not citation.startswith('DOI not found'):
                        # Cache the result
                        self._citation_cache[doi] = (citation, datetime.now())
                        return citation
                        
        except Exception as e:
            logger.warning(f"Error fetching citation for DOI {doi}: {e}")
            
        return None
    
    async def _fetch_from_crossref(self, doi: str) -> Optional[CitationMetadata]:
        """Fetch citation from CrossRef API."""
        try:
            url = f"{self.CROSSREF_API}{doi}"
            headers = {'Accept': 'application/json'}
            
            async with self.session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    work = data.get('message', {})
                    
                    metadata = CitationMetadata()
                    metadata.doi = doi
                    metadata.title = work.get('title', [None])[0] if work.get('title') else None
                    
                    # Extract authors
                    authors = work.get('author', [])
                    if authors:
                        metadata.authors = []
                        for author in authors:
                            given = author.get('given', '')
                            family = author.get('family', '')
                            if family:
                                full_name = f"{given} {family}".strip()
                                metadata.authors.append(full_name)
                    
                    # Journal information
                    metadata.journal = work.get('container-title', [None])[0] if work.get('container-title') else None
                    metadata.publisher = work.get('publisher')
                    
                    # Date information
                    published = work.get('published-print') or work.get('published-online')
                    if published and 'date-parts' in published:
                        date_parts = published['date-parts'][0]
                        if date_parts:
                            metadata.year = date_parts[0]
                    
                    # Volume/Issue/Pages
                    metadata.volume = work.get('volume')
                    metadata.issue = work.get('issue')
                    metadata.pages = work.get('page')
                    
                    # URL
                    metadata.url = work.get('URL') or f"https://doi.org/{doi}"
                    
                    return metadata
                    
        except Exception as e:
            logger.warning(f"CrossRef API error for {doi}: {e}")
            
        return None
    
    async def _fetch_from_datacite(self, doi: str) -> Optional[CitationMetadata]:
        """Fetch citation from DataCite API."""
        try:
            url = f"{self.DATACITE_API}{doi}"
            headers = {'Accept': 'application/json'}
            
            async with self.session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    work = data.get('data', {}).get('attributes', {})
                    
                    metadata = CitationMetadata()
                    metadata.doi = doi
                    metadata.title = work.get('title')
                    metadata.publisher = work.get('publisher')
                    
                    # Extract year from publication year
                    metadata.year = work.get('publicationYear')
                    
                    # Authors (creators)
                    creators = work.get('creators', [])
                    if creators:
                        metadata.authors = []
                        for creator in creators:
                            name = creator.get('name') or creator.get('givenName', '') + ' ' + creator.get('familyName', '')
                            if name.strip():
                                metadata.authors.append(name.strip())
                    
                    # URL
                    metadata.url = f"https://doi.org/{doi}"
                    
                    return metadata
                    
        except Exception as e:
            logger.warning(f"DataCite API error for {doi}: {e}")
            
        return None
    
    def format_citation(self, metadata: CitationMetadata, style: str = 'apa') -> str:
        """Format citation in specified academic style."""
        if not metadata:
            return "Unknown source"
            
        if style.lower() == 'apa':
            return self._format_apa(metadata)
        elif style.lower() == 'mla':
            return self._format_mla(metadata)
        elif style.lower() == 'chicago':
            return self._format_chicago(metadata)
        else:
            return self._format_apa(metadata)  # Default to APA
    
    def _format_apa(self, metadata: CitationMetadata) -> str:
        """Format citation in APA style."""
        parts = []
        
        # Authors
        if metadata.authors:
            if len(metadata.authors) == 1:
                parts.append(f"{metadata.authors[0]}.")
            elif len(metadata.authors) <= 7:
                author_list = ", ".join(metadata.authors[:-1]) + f", & {metadata.authors[-1]}"
                parts.append(f"{author_list}.")
            else:
                # More than 7 authors, use et al.
                parts.append(f"{metadata.authors[0]} et al.")
        
        # Year
        if metadata.year:
            parts.append(f"({metadata.year}).")
        
        # Title
        if metadata.title:
            parts.append(f"{metadata.title}.")
        
        # Journal/Publisher info
        if metadata.journal:
            journal_info = f"*{metadata.journal}*"
            if metadata.volume:
                journal_info += f", {metadata.volume}"
                if metadata.issue:
                    journal_info += f"({metadata.issue})"
            if metadata.pages:
                journal_info += f", {metadata.pages}"
            parts.append(f"{journal_info}.")
        elif metadata.publisher:
            parts.append(f"{metadata.publisher}.")
        
        # DOI or URL
        if metadata.doi:
            parts.append(f"https://doi.org/{metadata.doi}")
        elif metadata.url:
            parts.append(metadata.url)
        
        return " ".join(parts)
    
    def _format_mla(self, metadata: CitationMetadata) -> str:
        """Format citation in MLA style."""
        parts = []
        
        # Authors (Last, First)
        if metadata.authors:
            if len(metadata.authors) == 1:
                parts.append(f"{metadata.authors[0]}.")
            else:
                # First author last name first, others normal order
                first_author = metadata.authors[0]
                if ',' not in first_author:
                    # Assume "First Last" format, convert to "Last, First"
                    name_parts = first_author.split()
                    if len(name_parts) >= 2:
                        first_author = f"{name_parts[-1]}, {' '.join(name_parts[:-1])}"
                
                if len(metadata.authors) == 2:
                    parts.append(f"{first_author}, and {metadata.authors[1]}.")
                else:
                    parts.append(f"{first_author}, et al.")
        
        # Title in quotes
        if metadata.title:
            parts.append(f'"{metadata.title}."')
        
        # Journal in italics
        if metadata.journal:
            journal_info = f"*{metadata.journal}*"
            if metadata.volume:
                journal_info += f", vol. {metadata.volume}"
                if metadata.issue:
                    journal_info += f", no. {metadata.issue}"
            if metadata.year:
                journal_info += f", {metadata.year}"
            if metadata.pages:
                journal_info += f", pp. {metadata.pages}"
            parts.append(f"{journal_info}.")
        
        return " ".join(parts)
    
    def _format_chicago(self, metadata: CitationMetadata) -> str:
        """Format citation in Chicago style."""
        parts = []
        
        # Authors
        if metadata.authors:
            if len(metadata.authors) == 1:
                parts.append(f"{metadata.authors[0]}.")
            else:
                author_list = ", ".join(metadata.authors[:-1]) + f", and {metadata.authors[-1]}"
                parts.append(f"{author_list}.")
        
        # Title in quotes
        if metadata.title:
            parts.append(f'"{metadata.title}."')
        
        # Journal
        if metadata.journal:
            journal_info = f"*{metadata.journal}*"
            if metadata.volume:
                journal_info += f" {metadata.volume}"
                if metadata.issue:
                    journal_info += f", no. {metadata.issue}"
            if metadata.year:
                journal_info += f" ({metadata.year})"
            if metadata.pages:
                journal_info += f": {metadata.pages}"
            parts.append(f"{journal_info}.")
        
        # DOI
        if metadata.doi:
            parts.append(f"doi:{metadata.doi}.")
        
        return " ".join(parts)

    def format_references_list(self, metadata_list: List[CitationMetadata], style: str = 'apa') -> List[str]:
        """Format a list of citations."""
        references = []
        for metadata in metadata_list:
            citation = self.format_citation(metadata, style)
            if citation and citation != "Unknown source":
                references.append(citation)
        return references