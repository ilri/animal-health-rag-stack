"""
Enhanced Metadata Extraction for Academic Documents

Extracts comprehensive metadata including:
- DOIs from various locations in documents
- Author names and affiliations
- Publication titles and abstracts
- Journal information
- Publication dates
- Keywords and subjects
"""

import re
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging

# Import PDF processing libraries with fallbacks
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

logger = logging.getLogger(__name__)

class MetadataExtractor:
    """Enhanced metadata extraction for academic documents."""
    
    # DOI patterns (more comprehensive)
    DOI_PATTERNS = [
        r'10\.\d{4,}[^\s<>\[\]\"\']*',  # Standard DOI format
        r'doi:\s*10\.\d{4,}[^\s<>\[\]\"\']*',  # DOI with prefix
        r'DOI:\s*10\.\d{4,}[^\s<>\[\]\"\']*',  # DOI with uppercase prefix
        r'https?://doi\.org/10\.\d{4,}[^\s<>\[\]\"\']*',  # DOI URLs
        r'dx\.doi\.org/10\.\d{4,}[^\s<>\[\]\"\']*',  # dx.doi.org URLs
    ]
    
    # Author patterns
    AUTHOR_PATTERNS = [
        r'(?:Authors?|By):\s*([^\n\r]+)',
        r'(?:^|\n)\s*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)*[A-Z][a-z]+(?:\s*,\s*[A-Z][a-z]+(?:\s+[A-Z]\.?\s*)*[A-Z][a-z]+)*)',
    ]
    
    # Title patterns (for extracting potential titles)
    TITLE_INDICATORS = [
        'title', 'heading', 'h1', 'h2'
    ]
    
    def __init__(self):
        self.pdf_available = PDF_AVAILABLE
        self.bs4_available = BS4_AVAILABLE
    
    def extract_metadata_from_text(self, text: str, filename: str = None) -> Dict[str, Any]:
        """Extract comprehensive metadata from document text."""
        metadata = {
            'source': filename or 'Unknown source',
            'content_length': len(text),
            'extracted_at': None  # Will be set by the calling function
        }
        
        # Extract DOI - prioritize filename-based DOI for this archive
        doi = self.extract_doi_from_filename(filename)
        if not doi:
            # Fallback to text-based DOI extraction
            doi = self.extract_doi(text)
        if doi:
            metadata['doi'] = doi
        
        # Extract title
        title = self.extract_title(text, filename)
        if title:
            metadata['title'] = title
        
        # Extract authors
        authors = self.extract_authors(text)
        if authors:
            metadata['authors'] = authors
        
        # Extract publication year
        year = self.extract_publication_year(text)
        if year:
            metadata['year'] = year
        
        # Extract abstract
        abstract = self.extract_abstract(text)
        if abstract:
            metadata['abstract'] = abstract
        
        # Extract keywords
        keywords = self.extract_keywords(text)
        if keywords:
            metadata['keywords'] = keywords
        
        # Extract journal information
        journal_info = self.extract_journal_info(text)
        if journal_info:
            metadata.update(journal_info)
        
        return metadata
    
    def extract_doi_from_filename(self, filename: str) -> Optional[str]:
        """Extract DOI from filename by converting first hyphen to forward slash."""
        if not filename:
            return None
        
        # Remove file extension
        base_name = Path(filename).stem
        
        # Check if filename looks like a DOI (starts with 10. and has hyphens)
        if base_name.startswith('10.') and '-' in base_name:
            # Convert first hyphen to forward slash to create DOI
            doi = base_name.replace('-', '/', 1)
            # Validate DOI format
            if re.match(r'^10\.\d{4,}/', doi):
                return doi
        
        return None
    
    def extract_doi(self, text: str) -> Optional[str]:
        """Extract DOI from text with multiple patterns."""
        if not text:
            return None
        
        # Look in the first part of the document (more likely to contain DOI)
        search_text = text[:5000]  # First 5000 characters
        
        for pattern in self.DOI_PATTERNS:
            matches = re.findall(pattern, search_text, re.IGNORECASE | re.MULTILINE)
            if matches:
                # Clean up the DOI
                doi = matches[0]
                # Remove prefixes
                doi = re.sub(r'^(doi:?|DOI:?)\s*', '', doi, flags=re.IGNORECASE)
                doi = re.sub(r'^https?://(?:dx\.)?doi\.org/', '', doi, flags=re.IGNORECASE)
                # Remove common trailing punctuation and whitespace
                doi = re.sub(r'[.,;:\s\[\]\"\'<>]+$', '', doi)
                # Validate DOI format
                if re.match(r'^10\.\d{4,}/', doi):
                    return doi
        
        return None
    
    def extract_title(self, text: str, filename: str = None) -> Optional[str]:
        """Extract document title using multiple strategies."""
        if not text:
            return None
        
        lines = text.split('\n')
        potential_titles = []
        
        # Strategy 1: Look for lines that might be titles (early in document, proper length)
        for i, line in enumerate(lines[:20]):  # Check first 20 lines
            clean_line = line.strip()
            # Skip very short lines, page numbers, headers
            if (20 <= len(clean_line) <= 200 and 
                not re.match(r'^\d+$', clean_line) and  # Not just a number
                not re.match(r'^page\s+\d+', clean_line, re.IGNORECASE) and  # Not page number
                not clean_line.isupper() and  # Not all caps (likely header)
                '.' not in clean_line[:10]):  # Doesn't start with enumeration
                potential_titles.append((clean_line, i))
        
        # Strategy 2: Look for "Title:" patterns
        title_match = re.search(r'(?:^|\n)\s*(?:Title|TITLE):\s*([^\n\r]+)', text, re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()
        
        # Strategy 3: Use the first substantial line as title
        if potential_titles:
            # Prefer titles that appear earlier in the document
            potential_titles.sort(key=lambda x: x[1])  # Sort by line number
            return potential_titles[0][0]
        
        # Strategy 4: Clean up filename as fallback
        if filename:
            title = Path(filename).stem
            # Clean filename to make it more readable
            title = re.sub(r'[_-]+', ' ', title)
            title = re.sub(r'\s+', ' ', title)
            # Remove common academic paper patterns from filename
            title = re.sub(r'\d{4}[a-zA-Z]*\s*', '', title)  # Remove years
            return title.strip().title() if title.strip() else None
        
        return None
    
    def extract_authors(self, text: str) -> Optional[List[str]]:
        """Extract author names from text."""
        if not text:
            return None
        
        authors = []
        
        # Look in the first part of the document
        search_text = text[:3000]
        
        # Strategy 1: Look for "Author(s):" patterns
        for pattern in self.AUTHOR_PATTERNS:
            matches = re.findall(pattern, search_text, re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    if not match:
                        continue
                    match = match[0]
                
                # Clean and split authors
                author_line = match.strip()
                if len(author_line) > 5 and len(author_line) < 300:  # Reasonable length
                    # Split by common delimiters
                    potential_authors = re.split(r',\s*(?:and\s+)?|;\s*|\s+and\s+', author_line)
                    for author in potential_authors:
                        clean_author = author.strip()
                        # Basic validation: has at least first and last name
                        if (len(clean_author) > 3 and 
                            ' ' in clean_author and 
                            re.match(r'^[A-Za-z\s\.\-\']+$', clean_author)):
                            authors.append(clean_author)
        
        # Strategy 2: Look for name patterns early in document
        # This is more heuristic and might have false positives
        lines = search_text.split('\n')
        for i, line in enumerate(lines[:15]):  # First 15 lines
            line = line.strip()
            # Look for lines that might contain author names
            if (10 <= len(line) <= 100 and
                not re.search(r'\b(?:abstract|introduction|keywords|doi)\b', line, re.IGNORECASE) and
                re.search(r'^[A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+', line)):
                # Could be an author line
                potential_authors = re.split(r',\s*(?:and\s+)?|\s+and\s+', line)
                for author in potential_authors[:3]:  # Limit to 3 to avoid false positives
                    clean_author = author.strip()
                    if (len(clean_author) > 3 and 
                        ' ' in clean_author and
                        re.match(r'^[A-Za-z\s\.\-\']+$', clean_author)):
                        authors.append(clean_author)
                break  # Only check the first potential author line
        
        # Remove duplicates while preserving order
        unique_authors = []
        seen = set()
        for author in authors:
            if author.lower() not in seen:
                unique_authors.append(author)
                seen.add(author.lower())
        
        return unique_authors if unique_authors else None
    
    def extract_publication_year(self, text: str) -> Optional[int]:
        """Extract publication year from text."""
        if not text:
            return None
        
        # Look in the first part of the document
        search_text = text[:2000]
        
        # Look for year patterns near publication-related keywords
        patterns = [
            r'(?:published|copyright|©)\s*(?:in\s*)?(\d{4})',
            r'(\d{4})\s*(?:all rights reserved|copyright|©)',
            r'(?:^|\n)\s*(\d{4})\s*(?:\n|$)',  # Year on its own line
            r'\b(19\d{2}|20[0-2]\d)\b',  # General 4-digit year pattern
        ]
        
        years = []
        for pattern in patterns:
            matches = re.findall(pattern, search_text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                try:
                    year = int(match)
                    if 1900 <= year <= 2030:  # Reasonable year range
                        years.append(year)
                except ValueError:
                    continue
        
        if years:
            # Return the most recent reasonable year
            return max(years)
        
        return None
    
    def extract_abstract(self, text: str) -> Optional[str]:
        """Extract abstract from text."""
        if not text:
            return None
        
        # Look for abstract section
        abstract_patterns = [
            r'(?:^|\n)\s*ABSTRACT\s*:?\s*\n(.*?)(?:\n\s*(?:Keywords?|Introduction|1\.|I\.|\n\s*\n))',
            r'(?:^|\n)\s*Abstract\s*:?\s*\n(.*?)(?:\n\s*(?:Keywords?|Introduction|1\.|I\.|\n\s*\n))',
            r'(?:^|\n)\s*abstract\s*:?\s*\n(.*?)(?:\n\s*(?:keywords?|introduction|1\.|i\.|\n\s*\n))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                abstract = match.group(1).strip()
                # Clean up the abstract
                abstract = re.sub(r'\s+', ' ', abstract)  # Normalize whitespace
                if 50 <= len(abstract) <= 2000:  # Reasonable abstract length
                    return abstract
        
        return None
    
    def extract_keywords(self, text: str) -> Optional[List[str]]:
        """Extract keywords from text."""
        if not text:
            return None
        
        # Look for keywords section
        keyword_patterns = [
            r'(?:^|\n)\s*KEYWORDS?\s*:?\s*([^\n]+)',
            r'(?:^|\n)\s*Keywords?\s*:?\s*([^\n]+)',
            r'(?:^|\n)\s*Key\s*words?\s*:?\s*([^\n]+)',
        ]
        
        for pattern in keyword_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                keywords_text = match.group(1).strip()
                # Split keywords by common delimiters
                keywords = re.split(r'[,;]\s*', keywords_text)
                # Clean keywords
                clean_keywords = []
                for keyword in keywords:
                    clean_keyword = keyword.strip()
                    if clean_keyword and len(clean_keyword) > 2:
                        clean_keywords.append(clean_keyword)
                
                return clean_keywords if clean_keywords else None
        
        return None
    
    def extract_journal_info(self, text: str) -> Dict[str, Any]:
        """Extract journal information from text."""
        journal_info = {}
        
        if not text:
            return journal_info
        
        # Look in first part of document
        search_text = text[:2000]
        
        # Journal name patterns
        journal_patterns = [
            r'(?:^|\n)\s*([A-Z][^.\n]+Journal[^.\n]*)',
            r'(?:^|\n)\s*([A-Z][^.\n]+Review[^.\n]*)',
            r'(?:^|\n)\s*([A-Z][^.\n]+Proceedings[^.\n]*)',
            r'(?:Published in|Appears in):\s*([^\n]+)',
        ]
        
        for pattern in journal_patterns:
            match = re.search(pattern, search_text, re.IGNORECASE | re.MULTILINE)
            if match:
                journal_name = match.group(1).strip()
                if 10 <= len(journal_name) <= 100:  # Reasonable length
                    journal_info['journal'] = journal_name
                break
        
        # Volume, issue, pages patterns
        volume_match = re.search(r'(?:Vol\.|Volume)\s*(\d+)', search_text, re.IGNORECASE)
        if volume_match:
            journal_info['volume'] = volume_match.group(1)
        
        issue_match = re.search(r'(?:No\.|Issue)\s*(\d+)', search_text, re.IGNORECASE)
        if issue_match:
            journal_info['issue'] = issue_match.group(1)
        
        pages_match = re.search(r'(?:pp\.|pages?)\s*(\d+(?:-\d+)?)', search_text, re.IGNORECASE)
        if pages_match:
            journal_info['pages'] = pages_match.group(1)
        
        return journal_info
    
    def extract_metadata_from_pdf_properties(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from PDF properties if available."""
        metadata = {}
        
        if not self.pdf_available or not file_path.lower().endswith('.pdf'):
            return metadata
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                if pdf_reader.metadata:
                    info = pdf_reader.metadata
                    
                    # Extract standard PDF metadata
                    if info.get('/Title'):
                        metadata['pdf_title'] = str(info['/Title'])
                    
                    if info.get('/Author'):
                        metadata['pdf_author'] = str(info['/Author'])
                    
                    if info.get('/Subject'):
                        metadata['pdf_subject'] = str(info['/Subject'])
                    
                    if info.get('/Keywords'):
                        keywords = str(info['/Keywords'])
                        metadata['pdf_keywords'] = [k.strip() for k in keywords.split(',') if k.strip()]
                    
                    if info.get('/CreationDate'):
                        creation_date = str(info['/CreationDate'])
                        # Try to extract year from creation date
                        year_match = re.search(r'(\d{4})', creation_date)
                        if year_match:
                            metadata['pdf_creation_year'] = int(year_match.group(1))
        
        except Exception as e:
            logger.warning(f"Could not extract PDF metadata from {file_path}: {e}")
        
        return metadata