-- Query to analyze citation fetch errors and failures

-- Count of different error types
SELECT 'ERROR ANALYSIS:' as section;
SELECT 
    CASE 
        WHEN citation_fetch_error IS NULL AND citation_fetched = FALSE THEN 'Not attempted'
        WHEN citation_fetch_error IS NOT NULL THEN 'Failed with error'
        WHEN citation_fetched = TRUE AND reference IS NULL THEN 'Fetched but no reference'
        WHEN citation_fetched = TRUE AND reference IS NOT NULL THEN 'Success'
        ELSE 'Unknown status'
    END as status,
    COUNT(*) as count
FROM document
GROUP BY 1
ORDER BY count DESC;

-- Specific error messages and their frequency
SELECT 'ERROR MESSAGES:' as section;
SELECT 
    citation_fetch_error,
    COUNT(*) as count,
    MIN(citation_fetch_attempted_at) as first_error,
    MAX(citation_fetch_attempted_at) as last_error
FROM document
WHERE citation_fetch_error IS NOT NULL
GROUP BY citation_fetch_error
ORDER BY count DESC;

-- Documents that failed (with details)
SELECT 'FAILED DOCUMENTS:' as section;
SELECT 
    filename,
    doi,
    citation_fetch_error,
    citation_fetch_attempted_at,
    CASE 
        WHEN doi IS NULL THEN 'No DOI extracted'
        WHEN doi IS NOT NULL AND citation_fetch_error IS NOT NULL THEN 'DOI exists but API failed'
        ELSE 'Unknown'
    END as failure_reason
FROM document
WHERE citation_fetch_error IS NOT NULL
ORDER BY citation_fetch_attempted_at DESC
LIMIT 10;

-- Documents with DOIs but no successful citation
SELECT 'DOI EXTRACTION VS CITATION SUCCESS:' as section;
SELECT 
    'Documents with DOIs:' as metric, 
    COUNT(*) as count 
FROM document WHERE doi IS NOT NULL
UNION ALL
SELECT 
    'DOIs with successful citations:', 
    COUNT(*) 
FROM document 
WHERE doi IS NOT NULL AND citation_fetched = TRUE AND reference IS NOT NULL
UNION ALL
SELECT 
    'DOIs with failed citations:', 
    COUNT(*) 
FROM document 
WHERE doi IS NOT NULL AND citation_fetch_error IS NOT NULL;

-- Recent errors (last 24 hours)
SELECT 'RECENT ERRORS (Last 24h):' as section;
SELECT 
    filename,
    doi,
    citation_fetch_error,
    citation_fetch_attempted_at
FROM document
WHERE citation_fetch_attempted_at > NOW() - INTERVAL '24 hours'
  AND citation_fetch_error IS NOT NULL
ORDER BY citation_fetch_attempted_at DESC;

-- Pattern analysis of failing DOIs
SELECT 'DOI PATTERN ANALYSIS:' as section;
SELECT 
    CASE 
        WHEN doi LIKE '10.1%' THEN '10.1xxx (Common academic)'
        WHEN doi LIKE '10.3389%' THEN '10.3389 (Frontiers)'
        WHEN doi LIKE '10.1371%' THEN '10.1371 (PLOS)'
        WHEN doi LIKE '10.1016%' THEN '10.1016 (Elsevier)'
        WHEN doi IS NULL THEN 'No DOI'
        ELSE 'Other DOI pattern'
    END as doi_pattern,
    COUNT(*) as total_count,
    SUM(CASE WHEN citation_fetched = TRUE AND reference IS NOT NULL THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN citation_fetch_error IS NOT NULL THEN 1 ELSE 0 END) as error_count
FROM document
GROUP BY 1
ORDER BY total_count DESC;