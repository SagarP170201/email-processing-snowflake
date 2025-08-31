-- Simple Monitoring for Automated Email Processing
-- Essential health checks without over-engineering

USE DATABASE EMAIL_PROCESSING_APP;
USE SCHEMA CORE;

-- Simple system health view - just the basics
CREATE OR REPLACE VIEW SIMPLE_SYSTEM_HEALTH AS
SELECT 
    -- Basic counts for last 24 hours
    (SELECT COUNT(*) FROM RAW_EMAIL_FILES 
     WHERE upload_timestamp >= DATEADD('hour', -24, CURRENT_TIMESTAMP())) as files_uploaded_24h,
    
    (SELECT COUNT(*) FROM PROCESSED_EMAILS 
     WHERE extracted_timestamp >= DATEADD('hour', -24, CURRENT_TIMESTAMP())) as emails_processed_24h,
    
    (SELECT COUNT(*) FROM EMAIL_SUMMARIES 
     WHERE created_timestamp >= DATEADD('hour', -24, CURRENT_TIMESTAMP())) as summaries_created_24h,
    
    -- Error tracking
    (SELECT COUNT(*) FROM RAW_EMAIL_FILES 
     WHERE processing_status = 'FAILED' 
     AND upload_timestamp >= DATEADD('hour', -24, CURRENT_TIMESTAMP())) as failed_files_24h,
    
    -- Simple status check
    CASE 
        WHEN (SELECT COUNT(*) FROM RAW_EMAIL_FILES 
              WHERE upload_timestamp >= DATEADD('hour', -1, CURRENT_TIMESTAMP())) > 0 
        THEN 'ACTIVE'
        ELSE 'IDLE'
    END as system_status,
    
    CURRENT_TIMESTAMP() as last_check_time;

-- Simple task health check procedure
CREATE OR REPLACE PROCEDURE CHECK_BASIC_HEALTH()
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    task_count NUMBER;
    running_tasks NUMBER;
    health_message STRING;
BEGIN
    -- Count running tasks
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN state = 'Started' THEN 1 END) as running
    INTO task_count, running_tasks
    FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
        SCHEDULED_TIME_RANGE_START => DATEADD('hour', -1, CURRENT_TIMESTAMP())
    ))
    WHERE database_name = 'EMAIL_PROCESSING_APP'
    AND name LIKE 'REALTIME_%';
    
    -- Simple health assessment
    IF (running_tasks = 0) THEN
        health_message := '⚠️  WARNING: No automation tasks are running';
    ELSEIF (running_tasks < task_count) THEN
        health_message := '⚠️  PARTIAL: ' || running_tasks || ' of ' || task_count || ' tasks running';
    ELSE
        health_message := '✅ HEALTHY: All automation tasks are running';
    END IF;
    
    RETURN health_message;
END;
$$;

-- Simple error summary view
CREATE OR REPLACE VIEW RECENT_ERRORS AS
SELECT 
    'File Processing' as error_category,
    COUNT(*) as error_count,
    MAX(upload_timestamp) as latest_error,
    LISTAGG(DISTINCT error_message, '; ') as error_messages
FROM RAW_EMAIL_FILES 
WHERE processing_status = 'FAILED' 
AND upload_timestamp >= DATEADD('day', -7, CURRENT_TIMESTAMP())

UNION ALL

SELECT 
    'Job Processing' as error_category,
    COUNT(*) as error_count,
    MAX(start_time) as latest_error,
    LISTAGG(DISTINCT COALESCE(error_details:error::STRING, 'Unknown error'), '; ') as error_messages
FROM PROCESSING_JOBS 
WHERE status = 'FAILED'
AND start_time >= DATEADD('day', -7, CURRENT_TIMESTAMP());

-- Simple pipeline overview - just the key numbers
CREATE OR REPLACE VIEW PIPELINE_STATUS AS
SELECT 
    'Files in S3 Stage' as stage,
    (SELECT COUNT(*) FROM RAW_EMAIL_FILES 
     WHERE processing_status = 'PENDING') as pending_count,
    (SELECT COUNT(*) FROM RAW_EMAIL_FILES 
     WHERE upload_timestamp >= DATEADD('hour', -24, CURRENT_TIMESTAMP())) as last_24h
     
UNION ALL

SELECT 
    'Emails Processed' as stage,
    (SELECT COUNT(*) FROM PROCESSED_EMAILS) as pending_count,
    (SELECT COUNT(*) FROM PROCESSED_EMAILS 
     WHERE extracted_timestamp >= DATEADD('hour', -24, CURRENT_TIMESTAMP())) as last_24h
     
UNION ALL

SELECT 
    'AI Summaries Ready' as stage,
    (SELECT COUNT(*) FROM EMAIL_SUMMARIES) as pending_count,
    (SELECT COUNT(*) FROM EMAIL_SUMMARIES 
     WHERE created_timestamp >= DATEADD('hour', -24, CURRENT_TIMESTAMP())) as last_24h
     
ORDER BY 
    CASE stage 
        WHEN 'Files in S3 Stage' THEN 1
        WHEN 'Emails Processed' THEN 2
        WHEN 'AI Summaries Ready' THEN 3
    END;

-- Grant permissions
GRANT SELECT ON VIEW SIMPLE_SYSTEM_HEALTH TO ROLE PUBLIC;
GRANT SELECT ON VIEW RECENT_ERRORS TO ROLE PUBLIC;
GRANT SELECT ON VIEW PIPELINE_STATUS TO ROLE PUBLIC;
GRANT USAGE ON PROCEDURE CHECK_BASIC_HEALTH() TO ROLE PUBLIC;

-- Simple monitoring queries for quick checks
/*
SIMPLE MONITORING USAGE:

1. Quick health check:
   SELECT * FROM SIMPLE_SYSTEM_HEALTH;
   CALL CHECK_BASIC_HEALTH();

2. Check for errors:
   SELECT * FROM RECENT_ERRORS;

3. Pipeline status:
   SELECT * FROM PIPELINE_STATUS;

4. Task status:
   SELECT * FROM REALTIME_TASK_STATUS;

5. Recent activity:
   SELECT 
       file_name,
       processing_status,
       upload_timestamp
   FROM RAW_EMAIL_FILES 
   ORDER BY upload_timestamp DESC 
   LIMIT 10;

That's it! No complex alerting, just simple health checks.
*/
