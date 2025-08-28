-- Create document table for storing document metadata
CREATE TABLE IF NOT EXISTS document (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL UNIQUE,
    file_path TEXT NOT NULL,
    content_hash VARCHAR(64) UNIQUE,  -- SHA-256 hash for deduplication
    file_size BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Citation metadata (populated by DOI fetcher)
    doi VARCHAR(255),
    reference TEXT,  -- APA-formatted citation from doi.org citation API
    
    -- Processing status
    citation_fetched BOOLEAN DEFAULT FALSE,
    citation_fetch_attempted_at TIMESTAMP,
    citation_fetch_error TEXT,
    
    CONSTRAINT valid_doi CHECK (doi IS NULL OR doi ~ '^10\.\d{4,}/.*$')
);

-- Add document_id foreign key to document_chunks table
ALTER TABLE document_chunks 
ADD COLUMN IF NOT EXISTS document_id INTEGER REFERENCES document(id) ON DELETE CASCADE;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_document_filename ON document(filename);
CREATE INDEX IF NOT EXISTS idx_document_doi ON document(doi);
CREATE INDEX IF NOT EXISTS idx_document_content_hash ON document(content_hash);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_document_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_document_updated_at
    BEFORE UPDATE ON document
    FOR EACH ROW
    EXECUTE FUNCTION update_document_updated_at();