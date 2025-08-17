-- Email Processing App - Automation Setup
-- This script sets up automated email processing workflows

USE DATABASE EMAIL_PROCESSING_APP;
USE SCHEMA CORE;

-- Create sequence for task ordering
CREATE OR REPLACE SEQUENCE TASK_SEQUENCE START = 1 INCREMENT = 1;

-- Create automated email ingestion task
CREATE OR REPLACE TASK AUTO_INGEST_EMAILS
    WAREHOUSE = 'COMPUTE_WH'  -- Replace with your warehouse
    SCHEDULE = 'USING CRON 0 */2 * * * UTC'  -- Every 2 hours
    COMMENT = 'Automated task to ingest new email files from S3 stage'
AS
BEGIN
    -- Call the ingestion procedure
    CALL INGEST_EMAIL_FILES('S3', '.*');
    
    -- Log the execution
    INSERT INTO PROCESSING_JOBS (job_id, job_type, start_time, status, files_processed)
    SELECT 
        CONCAT('AUTO_INGEST_', CURRENT_TIMESTAMP()::STRING, '_', TASK_SEQUENCE.NEXTVAL),
        'AUTO_INGESTION',
        CURRENT_TIMESTAMP(),
        'COMPLETED',
        (SELECT COUNT(*) FROM RAW_EMAIL_FILES WHERE processing_status = 'COMPLETED' 
         AND upload_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '2 HOURS');
END;

-- Create automated email processing task (depends on ingestion)
CREATE OR REPLACE TASK AUTO_PROCESS_EMAILS
    WAREHOUSE = 'COMPUTE_WH'  -- Replace with your warehouse
    AFTER AUTO_INGEST_EMAILS
    COMMENT = 'Automated task to process newly ingested emails'
AS
BEGIN
    -- Process pending emails
    DECLARE
        cursor_pending CURSOR FOR 
            SELECT file_id, file_content 
            FROM RAW_EMAIL_FILES 
            WHERE processing_status = 'PENDING'
            LIMIT 100;  -- Process in batches
    BEGIN
        FOR email_record IN cursor_pending DO
            CALL PROCESS_EMAIL_FORMAT(email_record.file_id, email_record.file_content);
        END FOR;
    END;
END;

-- Create automated AI analysis task (depends on processing)
CREATE OR REPLACE TASK AUTO_AI_ANALYSIS
    WAREHOUSE = 'COMPUTE_WH'  -- Replace with your warehouse
    AFTER AUTO_PROCESS_EMAILS
    COMMENT = 'Automated task to generate AI summaries for processed emails'
AS
BEGIN
    -- Analyze emails that don't have summaries yet
    CALL BATCH_ANALYZE_EMAILS(50, 'ALL');
END;

-- Create task for cleanup and maintenance
CREATE OR REPLACE TASK AUTO_MAINTENANCE
    WAREHOUSE = 'COMPUTE_WH'  -- Replace with your warehouse
    SCHEDULE = 'USING CRON 0 2 * * SUN UTC'  -- Weekly on Sunday at 2 AM
    COMMENT = 'Weekly maintenance task for email processing system'
AS
BEGIN
    -- Clean up old processing jobs (keep last 3 months)
    DELETE FROM PROCESSING_JOBS 
    WHERE start_time < CURRENT_TIMESTAMP() - INTERVAL '3 MONTHS';
    
    -- Archive old processed emails (optional)
    -- You might want to move very old emails to a separate archive table
    
    -- Update statistics
    ANALYZE TABLE RAW_EMAIL_FILES;
    ANALYZE TABLE PROCESSED_EMAILS;
    ANALYZE TABLE EMAIL_SUMMARIES;
    
    -- Log maintenance completion
    INSERT INTO PROCESSING_JOBS (job_id, job_type, start_time, status)
    VALUES (
        CONCAT('MAINTENANCE_', CURRENT_TIMESTAMP()::STRING),
        'MAINTENANCE',
        CURRENT_TIMESTAMP(),
        'COMPLETED'
    );
END;

-- Create notification task for failed jobs
CREATE OR REPLACE TASK AUTO_MONITOR_FAILURES
    WAREHOUSE = 'COMPUTE_WH'  -- Replace with your warehouse
    SCHEDULE = 'USING CRON 0 */6 * * * UTC'  -- Every 6 hours
    COMMENT = 'Monitor for failed processing jobs and send alerts'
AS
BEGIN
    -- Check for recent failures
    DECLARE
        failure_count NUMBER;
    BEGIN
        SELECT COUNT(*) INTO failure_count
        FROM PROCESSING_JOBS 
        WHERE status = 'FAILED' 
        AND start_time >= CURRENT_TIMESTAMP() - INTERVAL '6 HOURS';
        
        -- If failures detected, log for notification system
        IF (failure_count > 0) THEN
            INSERT INTO PROCESSING_JOBS (job_id, job_type, start_time, status, error_details)
            VALUES (
                CONCAT('ALERT_', CURRENT_TIMESTAMP()::STRING),
                'FAILURE_ALERT',
                CURRENT_TIMESTAMP(),
                'COMPLETED',
                PARSE_JSON(CONCAT('{"failure_count": ', failure_count, ', "time_period": "6_hours"}'))
            );
        END IF;
    END;
END;

-- Create stream for real-time processing (advanced)
CREATE OR REPLACE STREAM EMAIL_FILES_STREAM ON TABLE RAW_EMAIL_FILES
    APPEND_ONLY = TRUE
    COMMENT = 'Stream to track new email file insertions for real-time processing';

-- Create task for stream-based real-time processing
CREATE OR REPLACE TASK REALTIME_EMAIL_PROCESSOR
    WAREHOUSE = 'COMPUTE_WH'  -- Replace with your warehouse
    SCHEDULE = '1 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('EMAIL_FILES_STREAM')
    COMMENT = 'Real-time processor for newly inserted email files'
AS
BEGIN
    -- Process new files from stream
    DECLARE
        cursor_new_files CURSOR FOR 
            SELECT file_id, file_content 
            FROM EMAIL_FILES_STREAM 
            WHERE METADATA$ACTION = 'INSERT';
    BEGIN
        FOR new_file IN cursor_new_files DO
            -- Process the email format
            CALL PROCESS_EMAIL_FORMAT(new_file.file_id, new_file.file_content);
            
            -- Immediately analyze with AI if content is ready
            DECLARE
                email_ids ARRAY;
            BEGIN
                SELECT ARRAY_AGG(email_id) INTO email_ids
                FROM PROCESSED_EMAILS 
                WHERE file_id = new_file.file_id;
                
                FOR i IN 0 TO ARRAY_SIZE(email_ids) - 1 DO
                    CALL ANALYZE_EMAIL_WITH_AI(email_ids[i]::STRING);
                END FOR;
            END;
        END FOR;
    END;
END;

-- Resume all tasks (they are created in suspended state)
ALTER TASK AUTO_INGEST_EMAILS RESUME;
ALTER TASK AUTO_PROCESS_EMAILS RESUME;
ALTER TASK AUTO_AI_ANALYSIS RESUME;
ALTER TASK AUTO_MAINTENANCE RESUME;
ALTER TASK AUTO_MONITOR_FAILURES RESUME;
-- ALTER TASK REALTIME_EMAIL_PROCESSOR RESUME;  -- Enable for real-time processing

-- Create procedure to manage task states
CREATE OR REPLACE PROCEDURE MANAGE_AUTOMATION(action STRING, task_name STRING DEFAULT 'ALL')
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    result_message STRING;
    task_list ARRAY := ['AUTO_INGEST_EMAILS', 'AUTO_PROCESS_EMAILS', 'AUTO_AI_ANALYSIS', 
                       'AUTO_MAINTENANCE', 'AUTO_MONITOR_FAILURES'];
BEGIN
    IF (UPPER(action) = 'SUSPEND') THEN
        IF (UPPER(task_name) = 'ALL') THEN
            FOR i IN 0 TO ARRAY_SIZE(task_list) - 1 DO
                EXECUTE IMMEDIATE 'ALTER TASK ' || task_list[i]::STRING || ' SUSPEND';
            END FOR;
            result_message := 'All automation tasks suspended';
        ELSE
            EXECUTE IMMEDIATE 'ALTER TASK ' || UPPER(task_name) || ' SUSPEND';
            result_message := 'Task ' || UPPER(task_name) || ' suspended';
        END IF;
        
    ELSEIF (UPPER(action) = 'RESUME') THEN
        IF (UPPER(task_name) = 'ALL') THEN
            FOR i IN 0 TO ARRAY_SIZE(task_list) - 1 DO
                EXECUTE IMMEDIATE 'ALTER TASK ' || task_list[i]::STRING || ' RESUME';
            END FOR;
            result_message := 'All automation tasks resumed';
        ELSE
            EXECUTE IMMEDIATE 'ALTER TASK ' || UPPER(task_name) || ' RESUME';
            result_message := 'Task ' || UPPER(task_name) || ' resumed';
        END IF;
        
    ELSEIF (UPPER(action) = 'STATUS') THEN
        -- Return status of all tasks
        result_message := 'Use SHOW TASKS to see current status';
        
    ELSE
        result_message := 'Invalid action. Use: SUSPEND, RESUME, or STATUS';
    END IF;
    
    RETURN result_message;
END;
$$;

-- Create monitoring view for automation
CREATE OR REPLACE VIEW AUTOMATION_MONITORING AS
SELECT 
    name as task_name,
    state,
    schedule,
    last_committed_on,
    next_scheduled_time,
    warehouse,
    comment
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
WHERE database_name = 'EMAIL_PROCESSING_APP'
AND schema_name = 'CORE'
ORDER BY last_committed_on DESC;

-- Grant permissions
GRANT USAGE ON PROCEDURE MANAGE_AUTOMATION(STRING, STRING) TO ROLE PUBLIC;
GRANT SELECT ON VIEW AUTOMATION_MONITORING TO ROLE PUBLIC;

-- Usage examples and documentation
/*
AUTOMATION USAGE EXAMPLES:

1. Suspend all automation:
   CALL MANAGE_AUTOMATION('SUSPEND', 'ALL');

2. Resume specific task:
   CALL MANAGE_AUTOMATION('RESUME', 'AUTO_INGEST_EMAILS');

3. Check task status:
   SELECT * FROM AUTOMATION_MONITORING;

4. Manual trigger for testing:
   EXECUTE TASK AUTO_INGEST_EMAILS;

5. View task history:
   SELECT * FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY()) 
   WHERE name = 'AUTO_INGEST_EMAILS';

MONITORING QUERIES:

-- Check processing volumes
SELECT 
    DATE_TRUNC('hour', start_time) as hour,
    job_type,
    COUNT(*) as job_count,
    SUM(files_processed) as total_files
FROM PROCESSING_JOBS 
WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL '24 HOURS'
GROUP BY DATE_TRUNC('hour', start_time), job_type
ORDER BY hour DESC;

-- Check failure rates
SELECT 
    job_type,
    COUNT(*) as total_jobs,
    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed_jobs,
    ROUND(failed_jobs * 100.0 / total_jobs, 2) as failure_rate_pct
FROM PROCESSING_JOBS 
WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL '7 DAYS'
GROUP BY job_type;
*/
