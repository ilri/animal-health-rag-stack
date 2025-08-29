-- Query to count files that have had citations fetched

-- Basic count of documents with citations
SELECT 'Total documents with citations fetched:' as metric, COUNT(*) as count
FROM document 
WHERE citation_fetched = TRUE;

-- Count documents with actual reference text (not just flag set)
SELECT 'Documents with actual reference text:' as metric, COUNT(*) as count
FROM document 
WHERE citation_fetched = TRUE 
  AND reference IS NOT NULL 
  AND reference != '';

-- Count documents with DOIs
SELECT 'Documents with DOIs:' as metric, COUNT(*) as count
FROM document 
WHERE doi IS NOT NULL;

-- Count documents with DOIs that have been processed
SELECT 'Documents with DOIs and citations fetched:' as metric, COUNT(*) as count
FROM document 
WHERE doi IS NOT NULL 
  AND citation_fetched = TRUE;

-- Breakdown by processing status
SELECT 
    CASE 
        WHEN citation_fetched = TRUE AND reference IS NOT NULL THEN 'Successfully fetched'
        WHEN citation_fetched = TRUE AND reference IS NULL THEN 'Marked fetched but no reference'
        WHEN citation_fetch_attempted_at IS NOT NULL THEN 'Attempted but failed'
        ELSE 'Not processed'
    END as status,
    COUNT(*) as count
FROM document
GROUP BY 
    CASE 
        WHEN citation_fetched = TRUE AND reference IS NOT NULL THEN 'Successfully fetched'
        WHEN citation_fetched = TRUE AND reference IS NULL THEN 'Marked fetched but no reference'
        WHEN citation_fetch_attempted_at IS NOT NULL THEN 'Attempted but failed'
        ELSE 'Not processed'
    END
ORDER BY count DESC;

-- Sample of successfully fetched citations
SELECT 'SAMPLE CITATIONS:' as section;
SELECT filename, doi, LEFT(reference, 100) || '...' as citation_preview
FROM document 
WHERE citation_fetched = TRUE 
  AND reference IS NOT NULL 
ORDER BY created_at DESC 
LIMIT 5;