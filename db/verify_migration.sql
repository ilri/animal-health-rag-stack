-- Verification script to check migration results
-- Run this after the migration to ensure everything worked correctly

-- Basic counts
SELECT 'MIGRATION VERIFICATION REPORT' as report;
SELECT '================================' as separator;

-- 1. Document table statistics
SELECT 'Documents created:' as metric, COUNT(*) as value FROM document;
SELECT 'Documents with DOIs:' as metric, COUNT(*) as value FROM document WHERE doi IS NOT NULL;
SELECT 'Documents with file paths:' as metric, COUNT(*) as value FROM document WHERE file_path IS NOT NULL;
SELECT 'Documents with content hashes:' as metric, COUNT(*) as value FROM document WHERE content_hash IS NOT NULL;

-- 2. Document chunks linking
SELECT 'Total document chunks:' as metric, COUNT(*) as value FROM document_chunks;
SELECT 'Chunks with document_id:' as metric, COUNT(*) as value FROM document_chunks WHERE document_id IS NOT NULL;
SELECT 'Chunks without document_id:' as metric, COUNT(*) as value FROM document_chunks WHERE document_id IS NULL;

-- 3. Sample of created documents
SELECT 'SAMPLE DOCUMENTS:' as section;
SELECT id, filename, doi, citation_fetched, created_at 
FROM document 
ORDER BY created_at DESC 
LIMIT 5;

-- 4. Sample DOI extractions
SELECT 'SAMPLE DOI EXTRACTIONS:' as section;
SELECT filename, doi
FROM document 
WHERE doi IS NOT NULL 
LIMIT 5;

-- 5. Check for orphaned chunks (should be 0)
SELECT 'ORPHANED CHUNKS CHECK:' as section;
SELECT COUNT(*) as orphaned_chunks
FROM document_chunks dc
LEFT JOIN document d ON d.id = dc.document_id
WHERE dc.document_id IS NOT NULL AND d.id IS NULL;

-- 6. Check for missing mappings
SELECT 'UNMAPPED CHUNKS:' as section;
SELECT 
    source_metadata->>'source' as filename,
    COUNT(*) as chunk_count
FROM document_chunks 
WHERE document_id IS NULL
GROUP BY source_metadata->>'source'
LIMIT 5;

-- 7. Duplicate filename check (should be 0)
SELECT 'DUPLICATE FILENAME CHECK:' as section;
SELECT filename, COUNT(*) as count
FROM document
GROUP BY filename
HAVING COUNT(*) > 1;

SELECT 'Migration verification complete!' as status;