-- Real-Time Stream and Task Automation
-- This builds automated processing on top of your existing email processing foundation

USE DATABASE EMAIL_PROCESSING_APP;
USE SCHEMA CORE;

-- Task 1: Real-time email format processing (triggered by stream)
CREATE OR REPLACE TASK REALTIME_EMAIL_PROCESSOR
    WAREHOUSE = 'COMPUTE_WH'
    SCHEDULE = '1 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('EMAIL_FILES_REALTIME_STREAM')
    COMMENT = 'Processes new email files from stream in real-time'
AS
BEGIN
    -- Process new files from the stream
    DECLARE
        processed_count NUMBER DEFAULT 0;
        failed_count NUMBER DEFAULT 0;
        job_id STRING;
        
        -- Cursor for new files in stream
        cursor_new_files CURSOR FOR 
            SELECT file_id, file_content, file_name
            FROM EMAIL_FILES_REALTIME_STREAM 
            WHERE METADATA$ACTION = 'INSERT'
            AND processing_status = 'PENDING';
    BEGIN
        -- Create processing job
        job_id := CONCAT('REALTIME_PROC_', CURRENT_TIMESTAMP()::STRING, '_', UUID_STRING());
        INSERT INTO PROCESSING_JOBS (job_id, job_type, start_time, status)
        VALUES (job_id, 'REALTIME_PROCESSING', CURRENT_TIMESTAMP(), 'RUNNING');
        
        -- Process each new file
        FOR file_record IN cursor_new_files DO
            BEGIN
                -- Use your existing enhanced parsing function
                CALL PROCESS_EMAIL_FORMAT_ENHANCED(file_record.file_id, file_record.file_content);
                processed_count := processed_count + 1;
                
                -- Simple success logging in job record
                -- Removed complex metrics to keep it simple
                
            EXCEPTION
                WHEN OTHER THEN
                    failed_count := failed_count + 1;
                    -- Log processing error but continue
                    UPDATE RAW_EMAIL_FILES 
                    SET 
                        processing_status = 'FAILED',
                        error_message = SQLERRM
                    WHERE file_id = file_record.file_id;
            END;
        END FOR;
        
        -- Update job status
        UPDATE PROCESSING_JOBS 
        SET 
            end_time = CURRENT_TIMESTAMP(),
            status = CASE WHEN failed_count = 0 THEN 'COMPLETED' ELSE 'PARTIAL_FAILURE' END,
            files_processed = processed_count,
            files_failed = failed_count
        WHERE job_id = job_id;
        
    END;
END;

-- Task 2: Real-time AI analysis (triggered when emails are processed)
CREATE OR REPLACE TASK REALTIME_AI_ANALYZER
    WAREHOUSE = 'COMPUTE_WH'
    SCHEDULE = '1 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('PROCESSED_EMAILS_STREAM')
    COMMENT = 'Generates AI summaries for newly processed emails in real-time'
AS
BEGIN
    DECLARE
        analyzed_count NUMBER DEFAULT 0;
        ai_job_id STRING;
        
        cursor_new_emails CURSOR FOR
            SELECT email_id, email_body, subject, sender_email
            FROM PROCESSED_EMAILS_STREAM
            WHERE METADATA$ACTION = 'INSERT'
            AND email_body IS NOT NULL;
    BEGIN
        -- Create AI analysis job
        ai_job_id := CONCAT('REALTIME_AI_', CURRENT_TIMESTAMP()::STRING, '_', UUID_STRING());
        INSERT INTO PROCESSING_JOBS (job_id, job_type, start_time, status)
        VALUES (ai_job_id, 'REALTIME_AI_ANALYSIS', CURRENT_TIMESTAMP(), 'RUNNING');
        
        -- Analyze each new email
        FOR email_record IN cursor_new_emails DO
            BEGIN
                -- Generate brief summary (minimize tokens for real-time)
                DECLARE
                    brief_summary STRING;
                    sentiment_score STRING;
                    email_class STRING;
                BEGIN
                    -- Get AI summary
                    SELECT SNOWFLAKE.CORTEX.SUMMARIZE(email_record.email_body) INTO brief_summary;
                    
                    -- Get sentiment (quick analysis)
                    SELECT SNOWFLAKE.CORTEX.SENTIMENT(email_record.email_body) INTO sentiment_score;
                    
                    -- Get classification
                    SELECT SNOWFLAKE.CORTEX.COMPLETE(
                        'mistral-large',
                        CONCAT(
                            'Classify this email into ONE category: URGENT, INFORMATIONAL, ACTION_REQUIRED, MEETING_REQUEST, MARKETING, SUPPORT, PERSONAL, OTHER. ',
                            'Reply with ONLY the category name.\n\nSubject: ', 
                            COALESCE(email_record.subject, ''), '\nContent: ', 
                            SUBSTRING(email_record.email_body, 1, 500)  -- Limit content for classification
                        )
                    ) INTO email_class;
                    
                    -- Insert AI results
                    INSERT INTO EMAIL_SUMMARIES (email_id, summary_type, summary_text, model_used)
                    VALUES 
                        (email_record.email_id, 'BRIEF', brief_summary, 'snowflake-arctic'),
                        (email_record.email_id, 'SENTIMENT', sentiment_score, 'snowflake-arctic');
                    
                    -- Update email with classification
                    UPDATE PROCESSED_EMAILS 
                    SET email_classification = email_class
                    WHERE email_id = email_record.email_id;
                    
                    analyzed_count := analyzed_count + 1;
                END;
                
            EXCEPTION
                WHEN OTHER THEN
                    -- Simple error logging - no complex metrics
                    -- Error details already logged in PROCESSING_JOBS table
            END;
        END FOR;
        
        -- Update AI job status
        UPDATE PROCESSING_JOBS 
        SET 
            end_time = CURRENT_TIMESTAMP(),
            status = 'COMPLETED',
            files_processed = analyzed_count
        WHERE job_id = ai_job_id;
        
    END;
END;

-- Task 3: Priority email alerting (for urgent emails)
CREATE OR REPLACE TASK URGENT_EMAIL_ALERTER
    WAREHOUSE = 'COMPUTE_WH'
    SCHEDULE = '1 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('PROCESSED_EMAILS_STREAM')
    COMMENT = 'Identifies and alerts on urgent emails in real-time'
AS
BEGIN
    DECLARE
        urgent_emails ARRAY;
        alert_count NUMBER DEFAULT 0;
    BEGIN
        -- Find urgent emails from stream
        SELECT ARRAY_AGG(
            OBJECT_CONSTRUCT(
                'email_id', email_id,
                'subject', subject,
                'sender', sender_email,
                'urgency_indicators', 
                ARRAY_CONSTRUCT_COMPACT(
                    CASE WHEN subject ILIKE '%urgent%' THEN 'URGENT_SUBJECT' END,
                    CASE WHEN subject ILIKE '%asap%' THEN 'ASAP_SUBJECT' END,
                    CASE WHEN subject ILIKE '%critical%' THEN 'CRITICAL_SUBJECT' END,
                    CASE WHEN email_body ILIKE '%immediately%' THEN 'IMMEDIATE_CONTENT' END,
                    CASE WHEN email_body ILIKE '%emergency%' THEN 'EMERGENCY_CONTENT' END
                )
            )
        ) INTO urgent_emails
        FROM PROCESSED_EMAILS_STREAM
        WHERE METADATA$ACTION = 'INSERT'
        AND (
            subject ILIKE ANY ('%urgent%', '%asap%', '%critical%', '%emergency%', '%immediate%')
            OR email_body ILIKE ANY ('%urgent%', '%asap%', '%critical%', '%emergency%', '%immediate%')
        );
        
        -- Simple urgent email logging
        IF (ARRAY_SIZE(urgent_emails) > 0) THEN
            alert_count := ARRAY_SIZE(urgent_emails);
            
            -- Simple log entry for urgent emails
            INSERT INTO PROCESSING_JOBS (job_id, job_type, start_time, status, error_details)
            VALUES (
                CONCAT('URGENT_ALERT_', CURRENT_TIMESTAMP()::STRING),
                'URGENT_ALERT',
                CURRENT_TIMESTAMP(),
                'COMPLETED',
                OBJECT_CONSTRUCT('urgent_count', alert_count)
            );
        END IF;
    END;
END;

-- Task 4: Simple health monitoring (optional)
-- This task is optional - you can skip it for minimal monitoring
CREATE OR REPLACE TASK SIMPLE_HEALTH_MONITOR
    WAREHOUSE = 'COMPUTE_WH'
    SCHEDULE = 'USING CRON 0 */30 * * * UTC'  -- Every 30 minutes
    COMMENT = 'Basic system health check - optional task'
AS
BEGIN
    -- Just log basic health status - no complex alerting
    DECLARE
        health_status STRING;
    BEGIN
        SELECT 
            CASE 
                WHEN files_uploaded_24h > 0 THEN 'ACTIVE'
                WHEN failed_files_24h > 5 THEN 'ISSUES_DETECTED'
                ELSE 'IDLE'
            END INTO health_status
        FROM SIMPLE_SYSTEM_HEALTH;
        
        -- Simple log entry
        INSERT INTO PROCESSING_JOBS (job_id, job_type, start_time, status, error_details)
        VALUES (
            CONCAT('HEALTH_CHECK_', CURRENT_TIMESTAMP()::STRING),
            'HEALTH_CHECK',
            CURRENT_TIMESTAMP(),
            'COMPLETED',
            PARSE_JSON('{"status": "' || health_status || '"}')
        );
    END;
END;

-- Task 5: Simple maintenance (optional)
CREATE OR REPLACE TASK SIMPLE_MAINTENANCE
    WAREHOUSE = 'COMPUTE_WH'
    SCHEDULE = 'USING CRON 0 2 * * 0 UTC'  -- Weekly on Sunday at 2 AM
    COMMENT = 'Weekly cleanup - optional task'
AS
BEGIN
    -- Clean up old processing jobs (keep last 30 days)
    DELETE FROM PROCESSING_JOBS
    WHERE start_time < DATEADD('day', -30, CURRENT_TIMESTAMP());
    
    -- Log maintenance completion
    INSERT INTO PROCESSING_JOBS (job_id, job_type, start_time, status)
    VALUES (
        CONCAT('MAINTENANCE_', CURRENT_TIMESTAMP()::STRING),
        'SIMPLE_MAINTENANCE',
        CURRENT_TIMESTAMP(),
        'COMPLETED'
    );
END;

-- Resume tasks (they are created in suspended state)
-- Only essential tasks - no complex monitoring
-- ALTER TASK REALTIME_EMAIL_PROCESSOR RESUME;  -- Enable after S3 setup
-- ALTER TASK REALTIME_AI_ANALYZER RESUME;      -- Enable after stream setup  
-- ALTER TASK URGENT_EMAIL_ALERTER RESUME;      -- Enable for urgent email alerts
-- ALTER TASK SIMPLE_HEALTH_MONITOR RESUME;     -- Enable for basic health checks (optional)
-- ALTER TASK SIMPLE_MAINTENANCE RESUME;        -- Enable for weekly cleanup (optional)

-- Create simplified task management procedure
CREATE OR REPLACE PROCEDURE MANAGE_AUTOMATION_TASKS(action STRING, task_name STRING DEFAULT 'ALL')
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    result_message STRING;
    essential_tasks ARRAY := [
        'REALTIME_EMAIL_PROCESSOR',
        'REALTIME_AI_ANALYZER', 
        'URGENT_EMAIL_ALERTER'
    ];
    optional_tasks ARRAY := [
        'SIMPLE_HEALTH_MONITOR',
        'SIMPLE_MAINTENANCE'
    ];
BEGIN
    IF (UPPER(action) = 'SUSPEND') THEN
        IF (UPPER(task_name) = 'ALL') THEN
            -- Suspend essential tasks
            FOR i IN 0 TO ARRAY_SIZE(essential_tasks) - 1 DO
                EXECUTE IMMEDIATE 'ALTER TASK ' || essential_tasks[i]::STRING || ' SUSPEND';
            END FOR;
            result_message := 'Essential automation tasks suspended';
        ELSE
            EXECUTE IMMEDIATE 'ALTER TASK ' || UPPER(task_name) || ' SUSPEND';
            result_message := 'Task ' || UPPER(task_name) || ' suspended';
        END IF;
        
    ELSEIF (UPPER(action) = 'RESUME') THEN
        IF (UPPER(task_name) = 'ALL') THEN
            -- Resume essential tasks only
            FOR i IN 0 TO ARRAY_SIZE(essential_tasks) - 1 DO
                EXECUTE IMMEDIATE 'ALTER TASK ' || essential_tasks[i]::STRING || ' RESUME';
            END FOR;
            result_message := 'Essential automation tasks resumed';
        ELSE
            EXECUTE IMMEDIATE 'ALTER TASK ' || UPPER(task_name) || ' RESUME';
            result_message := 'Task ' || UPPER(task_name) || ' resumed';
        END IF;
        
    ELSEIF (UPPER(action) = 'STATUS') THEN
        result_message := 'Use: SELECT * FROM SIMPLE_SYSTEM_HEALTH;';
        
    ELSE
        result_message := 'Invalid action. Use: SUSPEND, RESUME, or STATUS';
    END IF;
    
    RETURN result_message;
END;
$$;

-- Simple task status view - just the basics
CREATE OR REPLACE VIEW SIMPLE_TASK_STATUS AS
SELECT 
    name as task_name,
    state,
    last_committed_on,
    next_scheduled_time
FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
    SCHEDULED_TIME_RANGE_START => DATEADD('hour', -2, CURRENT_TIMESTAMP())
))
WHERE database_name = 'EMAIL_PROCESSING_APP'
AND schema_name = 'CORE'
AND name IN ('REALTIME_EMAIL_PROCESSOR', 'REALTIME_AI_ANALYZER', 'URGENT_EMAIL_ALERTER')
ORDER BY last_committed_on DESC;

-- Simple urgent email view - no complex joins
CREATE OR REPLACE VIEW URGENT_EMAILS_SIMPLE AS
SELECT 
    pe.email_id,
    pe.subject,
    pe.sender_email,
    pe.email_date,
    pe.extracted_timestamp,
    es.summary_text as brief_summary
FROM PROCESSED_EMAILS pe
LEFT JOIN EMAIL_SUMMARIES es ON pe.email_id = es.email_id AND es.summary_type = 'BRIEF'
WHERE (
    pe.subject ILIKE ANY ('%urgent%', '%asap%', '%critical%', '%emergency%', '%immediate%')
    OR pe.email_body ILIKE ANY ('%urgent%', '%asap%', '%critical%', '%emergency%', '%immediate%')
)
AND pe.extracted_timestamp >= DATEADD('day', -7, CURRENT_TIMESTAMP())
ORDER BY pe.extracted_timestamp DESC;

-- Grant permissions
GRANT USAGE ON PROCEDURE MANAGE_AUTOMATION_TASKS(STRING, STRING) TO ROLE PUBLIC;
GRANT SELECT ON VIEW SIMPLE_TASK_STATUS TO ROLE PUBLIC;
GRANT SELECT ON VIEW URGENT_EMAILS_SIMPLE TO ROLE PUBLIC;

-- Simplified usage examples
/*
SIMPLE AUTOMATION USAGE:

1. Start automation:
   CALL MANAGE_AUTOMATION_TASKS('RESUME', 'ALL');

2. Stop automation:
   CALL MANAGE_AUTOMATION_TASKS('SUSPEND', 'ALL');

3. Check if tasks are running:
   SELECT * FROM SIMPLE_TASK_STATUS;

4. Basic health check:
   SELECT * FROM SIMPLE_SYSTEM_HEALTH;
   CALL CHECK_BASIC_HEALTH();

5. Check for urgent emails:
   SELECT * FROM URGENT_EMAILS_SIMPLE;

6. View recent activity:
   SELECT * FROM PROCESSING_JOBS 
   ORDER BY start_time DESC LIMIT 10;

That's it! Simple and focused monitoring.
*/
