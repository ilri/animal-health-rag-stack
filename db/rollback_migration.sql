-- Rollback script for document table migration
-- Use this if the migration fails or you need to revert changes

BEGIN;

-- Step 1: Remove document_id foreign key constraint and column from document_chunks
-- (This preserves all existing chunk data)
ALTER TABLE document_chunks DROP CONSTRAINT IF EXISTS document_chunks_document_id_fkey;
ALTER TABLE document_chunks DROP COLUMN IF EXISTS document_id;

-- Step 2: Drop the document table entirely
DROP TABLE IF EXISTS document;

-- Step 3: Drop the update trigger and function
DROP TRIGGER IF EXISTS update_document_updated_at ON document;
DROP FUNCTION IF EXISTS update_document_updated_at();

-- Step 4: Clean up any indexes that were created
DROP INDEX IF EXISTS idx_document_filename;
DROP INDEX IF EXISTS idx_document_doi;
DROP INDEX IF EXISTS idx_document_content_hash;
DROP INDEX IF EXISTS idx_document_chunks_document_id;

-- Verification
SELECT 'document_chunks table structure after rollback:' as info;
\d document_chunks;

SELECT 'Total chunks preserved:' as info, COUNT(*) as count FROM document_chunks;

COMMIT;

-- Note: This rollback preserves all your original document_chunks data
-- You can safely re-run the migration script after fixing any issues