-- Enhanced Email Parsing Procedures
-- This script provides advanced email parsing for multiple formats

USE DATABASE EMAIL_PROCESSING_APP;
USE SCHEMA CORE;

-- Enhanced email format processing procedure
CREATE OR REPLACE PROCEDURE PROCESS_EMAIL_FORMAT_ENHANCED(
    FILE_ID STRING,
    EMAIL_CONTENT VARIANT
)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    processed_count NUMBER DEFAULT 0;
    email_type STRING;
    result_message STRING;
BEGIN
    -- Determine email format type
    email_type := COALESCE(EMAIL_CONTENT:email_type::STRING, 'unknown');
    
    -- Process Gmail API format
    IF (email_type = 'gmail_api' OR EMAIL_CONTENT:payload IS NOT NULL) THEN
        INSERT INTO PROCESSED_EMAILS (
            file_id,
            sender_email,
            recipient_emails,
            subject,
            email_body,
            email_date,
            extracted_timestamp
        )
        SELECT 
            FILE_ID,
            -- Extract sender from headers
            (SELECT h.value::STRING 
             FROM TABLE(FLATTEN(EMAIL_CONTENT:payload.headers)) h
             WHERE h.value:name::STRING = 'From'),
            -- Extract recipients from headers  
            ARRAY_CONSTRUCT(
                (SELECT h.value::STRING 
                 FROM TABLE(FLATTEN(EMAIL_CONTENT:payload.headers)) h
                 WHERE h.value:name::STRING = 'To')
            ),
            -- Extract subject
            (SELECT h.value::STRING 
             FROM TABLE(FLATTEN(EMAIL_CONTENT:payload.headers)) h
             WHERE h.value:name::STRING = 'Subject'),
            -- Extract body content
            COALESCE(
                EMAIL_CONTENT:payload.parts[0].body.data::STRING,
                EMAIL_CONTENT:payload.body.data::STRING
            ),
            -- Convert internal date
            TRY_TO_TIMESTAMP_NTZ(EMAIL_CONTENT:internalDate::STRING, 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
            CURRENT_TIMESTAMP();
        
        processed_count := 1;
        result_message := 'Processed Gmail API format email';
        
    -- Process simple format
    ELSEIF (email_type = 'simple_format' OR EMAIL_CONTENT:email_text IS NOT NULL) THEN
        INSERT INTO PROCESSED_EMAILS (
            file_id,
            sender_email,
            recipient_emails,
            subject,
            email_body,
            email_date,
            attachments,
            extracted_timestamp
        )
        VALUES (
            FILE_ID,
            EMAIL_CONTENT:sender::STRING,
            EMAIL_CONTENT:recipients,
            EMAIL_CONTENT:subject::STRING,
            EMAIL_CONTENT:email_text::STRING,
            TRY_TO_TIMESTAMP_NTZ(EMAIL_CONTENT:email_date::STRING),
            EMAIL_CONTENT:attachments,
            CURRENT_TIMESTAMP()
        );
        
        processed_count := 1;
        result_message := 'Processed simple format email';
        
    -- Process marketing format
    ELSEIF (email_type = 'marketing') THEN
        INSERT INTO PROCESSED_EMAILS (
            file_id,
            sender_email,
            recipient_emails,
            subject,
            email_body,
            email_date,
            attachments,
            extracted_timestamp
        )
        VALUES (
            FILE_ID,
            EMAIL_CONTENT:sender::STRING,
            EMAIL_CONTENT:recipients,
            EMAIL_CONTENT:subject::STRING,
            EMAIL_CONTENT:email_text::STRING,
            TRY_TO_TIMESTAMP_NTZ(EMAIL_CONTENT:email_date::STRING),
            EMAIL_CONTENT:attachments,
            CURRENT_TIMESTAMP()
        );
        
        -- Set initial classification for marketing emails
        UPDATE PROCESSED_EMAILS 
        SET email_classification = 'MARKETING'
        WHERE file_id = FILE_ID;
        
        processed_count := 1;
        result_message := 'Processed marketing format email';
        
    -- Process Outlook/Exchange format
    ELSEIF (EMAIL_CONTENT:MessageClass IS NOT NULL) THEN
        INSERT INTO PROCESSED_EMAILS (
            file_id,
            sender_email,
            recipient_emails,
            subject,
            email_body,
            email_date,
            extracted_timestamp
        )
        VALUES (
            FILE_ID,
            EMAIL_CONTENT:SenderEmailAddress::STRING,
            ARRAY_CONSTRUCT(EMAIL_CONTENT:ToRecipients::STRING),
            EMAIL_CONTENT:Subject::STRING,
            EMAIL_CONTENT:Body::STRING,
            TRY_TO_TIMESTAMP_NTZ(EMAIL_CONTENT:DateTimeReceived::STRING),
            CURRENT_TIMESTAMP()
        );
        
        processed_count := 1;
        result_message := 'Processed Outlook/Exchange format email';
        
    -- Process raw text format
    ELSEIF (EMAIL_CONTENT:raw_text IS NOT NULL) THEN
        INSERT INTO PROCESSED_EMAILS (
            file_id,
            email_body,
            extracted_timestamp
        )
        VALUES (
            FILE_ID,
            EMAIL_CONTENT:raw_text::STRING,
            CURRENT_TIMESTAMP()
        );
        
        processed_count := 1;
        result_message := 'Processed raw text format email';
        
    ELSE
        -- Unknown format - store as raw content for manual review
        INSERT INTO PROCESSED_EMAILS (
            file_id,
            email_body,
            extracted_timestamp
        )
        VALUES (
            FILE_ID,
            EMAIL_CONTENT::STRING,
            CURRENT_TIMESTAMP()
        );
        
        processed_count := 1;
        result_message := 'Processed unknown format email as raw content';
    END IF;
    
    -- Update processing status
    UPDATE RAW_EMAIL_FILES 
    SET processing_status = 'COMPLETED'
    WHERE file_id = FILE_ID;
    
    RETURN result_message || ' (' || processed_count || ' email(s))';
    
EXCEPTION
    WHEN OTHER THEN
        UPDATE RAW_EMAIL_FILES 
        SET 
            processing_status = 'FAILED',
            error_message = SQLERRM
        WHERE file_id = FILE_ID;
        
        RETURN 'Processing failed for file ' || FILE_ID || ': ' || SQLERRM;
END;
$$;

-- Batch processing procedure with format detection
CREATE OR REPLACE PROCEDURE BATCH_PROCESS_EMAILS(
    LIMIT_COUNT NUMBER DEFAULT 50,
    FILE_PATTERN STRING DEFAULT '.*'
)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    processed_count NUMBER DEFAULT 0;
    failed_count NUMBER DEFAULT 0;
    job_id STRING;
    cursor_files CURSOR FOR 
        SELECT file_id, file_content, file_name
        FROM RAW_EMAIL_FILES 
        WHERE processing_status = 'PENDING'
        AND file_name RLIKE FILE_PATTERN
        LIMIT LIMIT_COUNT;
BEGIN
    -- Create processing job
    job_id := CONCAT('BATCH_PROC_', CURRENT_TIMESTAMP()::STRING, '_', UUID_STRING());
    INSERT INTO PROCESSING_JOBS (job_id, job_type, start_time, status)
    VALUES (job_id, 'BATCH_PROCESSING', CURRENT_TIMESTAMP(), 'RUNNING');
    
    -- Process files
    FOR file_record IN cursor_files DO
        BEGIN
            CALL PROCESS_EMAIL_FORMAT_ENHANCED(file_record.file_id, file_record.file_content);
            processed_count := processed_count + 1;
        EXCEPTION
            WHEN OTHER THEN
                failed_count := failed_count + 1;
                -- Log the error but continue processing
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
        status = 'COMPLETED',
        files_processed = processed_count,
        files_failed = failed_count
    WHERE job_id = job_id;
    
    RETURN 'Batch processing completed. Processed: ' || processed_count || 
           ', Failed: ' || failed_count || ', Job ID: ' || job_id;
END;
$$;

-- Email validation procedure
CREATE OR REPLACE PROCEDURE VALIDATE_EMAIL_DATA(email_id STRING)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    validation_errors ARRAY := ARRAY_CONSTRUCT();
    email_data OBJECT;
    result_message STRING;
BEGIN
    -- Get email data
    SELECT OBJECT_CONSTRUCT(
        'sender_email', sender_email,
        'subject', subject,
        'email_body', email_body,
        'email_date', email_date
    ) INTO email_data
    FROM PROCESSED_EMAILS 
    WHERE email_id = email_id;
    
    -- Validate sender email
    IF (email_data:sender_email IS NULL OR 
        NOT REGEXP_LIKE(email_data:sender_email::STRING, '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')) THEN
        validation_errors := ARRAY_APPEND(validation_errors, 'Invalid sender email format');
    END IF;
    
    -- Validate subject
    IF (email_data:subject IS NULL OR LENGTH(email_data:subject::STRING) = 0) THEN
        validation_errors := ARRAY_APPEND(validation_errors, 'Missing email subject');
    END IF;
    
    -- Validate body
    IF (email_data:email_body IS NULL OR LENGTH(email_data:email_body::STRING) < 10) THEN
        validation_errors := ARRAY_APPEND(validation_errors, 'Email body too short or missing');
    END IF;
    
    -- Validate date
    IF (email_data:email_date IS NULL) THEN
        validation_errors := ARRAY_APPEND(validation_errors, 'Missing email date');
    END IF;
    
    -- Update email with validation results
    UPDATE PROCESSED_EMAILS 
    SET validation_errors = validation_errors
    WHERE email_id = email_id;
    
    IF (ARRAY_SIZE(validation_errors) = 0) THEN
        result_message := 'Email validation passed';
    ELSE
        result_message := 'Email validation failed: ' || ARRAY_TO_STRING(validation_errors, ', ');
    END IF;
    
    RETURN result_message;
END;
$$;

-- Add validation errors column to processed emails table
ALTER TABLE PROCESSED_EMAILS 
ADD COLUMN IF NOT EXISTS validation_errors ARRAY;

-- Create procedure for email format detection and statistics
CREATE OR REPLACE PROCEDURE ANALYZE_EMAIL_FORMATS()
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    format_stats OBJECT;
    total_files NUMBER;
    result_message STRING;
BEGIN
    -- Get total files
    SELECT COUNT(*) INTO total_files FROM RAW_EMAIL_FILES;
    
    -- Analyze formats in raw files
    WITH format_analysis AS (
        SELECT 
            CASE 
                WHEN file_content:email_type IS NOT NULL THEN file_content:email_type::STRING
                WHEN file_content:payload IS NOT NULL THEN 'gmail_api'
                WHEN file_content:MessageClass IS NOT NULL THEN 'outlook_exchange'
                WHEN file_content:email_text IS NOT NULL THEN 'simple_text'
                WHEN file_content:raw_text IS NOT NULL THEN 'raw_text'
                ELSE 'unknown'
            END as detected_format,
            COUNT(*) as format_count
        FROM RAW_EMAIL_FILES
        WHERE file_content IS NOT NULL
        GROUP BY detected_format
    )
    SELECT OBJECT_AGG(detected_format, format_count) INTO format_stats
    FROM format_analysis;
    
    -- Store analysis results
    INSERT INTO PROCESSING_JOBS (job_id, job_type, start_time, status, error_details)
    VALUES (
        CONCAT('FORMAT_ANALYSIS_', CURRENT_TIMESTAMP()::STRING),
        'FORMAT_ANALYSIS',
        CURRENT_TIMESTAMP(),
        'COMPLETED',
        OBJECT_CONSTRUCT('total_files', total_files, 'format_breakdown', format_stats)
    );
    
    result_message := 'Format analysis completed. Total files: ' || total_files || 
                     ', Format breakdown: ' || format_stats::STRING;
    
    RETURN result_message;
END;
$$;

-- Create view for email processing statistics
CREATE OR REPLACE VIEW EMAIL_PROCESSING_STATS AS
SELECT 
    COUNT(*) as total_raw_files,
    COUNT(CASE WHEN processing_status = 'COMPLETED' THEN 1 END) as processed_files,
    COUNT(CASE WHEN processing_status = 'PENDING' THEN 1 END) as pending_files,
    COUNT(CASE WHEN processing_status = 'FAILED' THEN 1 END) as failed_files,
    ROUND(processed_files * 100.0 / total_raw_files, 2) as processing_success_rate
FROM RAW_EMAIL_FILES
WHERE file_content IS NOT NULL;

-- Create view for format distribution
CREATE OR REPLACE VIEW EMAIL_FORMAT_DISTRIBUTION AS
SELECT 
    CASE 
        WHEN file_content:email_type IS NOT NULL THEN file_content:email_type::STRING
        WHEN file_content:payload IS NOT NULL THEN 'gmail_api'
        WHEN file_content:MessageClass IS NOT NULL THEN 'outlook_exchange'
        WHEN file_content:email_text IS NOT NULL THEN 'simple_text'
        WHEN file_content:raw_text IS NOT NULL THEN 'raw_text'
        ELSE 'unknown'
    END as email_format,
    COUNT(*) as file_count,
    ROUND(file_count * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM RAW_EMAIL_FILES
WHERE file_content IS NOT NULL
GROUP BY email_format
ORDER BY file_count DESC;

-- Grant permissions
GRANT USAGE ON PROCEDURE PROCESS_EMAIL_FORMAT_ENHANCED(STRING, VARIANT) TO ROLE PUBLIC;
GRANT USAGE ON PROCEDURE BATCH_PROCESS_EMAILS(NUMBER, STRING) TO ROLE PUBLIC;
GRANT USAGE ON PROCEDURE VALIDATE_EMAIL_DATA(STRING) TO ROLE PUBLIC;
GRANT USAGE ON PROCEDURE ANALYZE_EMAIL_FORMATS() TO ROLE PUBLIC;
GRANT SELECT ON VIEW EMAIL_PROCESSING_STATS TO ROLE PUBLIC;
GRANT SELECT ON VIEW EMAIL_FORMAT_DISTRIBUTION TO ROLE PUBLIC;

-- Usage examples
/*
ENHANCED EMAIL PROCESSING EXAMPLES:

1. Process specific file with enhanced parsing:
   CALL PROCESS_EMAIL_FORMAT_ENHANCED('file_id_here', PARSE_JSON('{"email_type": "simple_format", ...}'));

2. Batch process emails with pattern matching:
   CALL BATCH_PROCESS_EMAILS(100, '.*\.json');

3. Validate processed email:
   CALL VALIDATE_EMAIL_DATA('email_id_here');

4. Analyze email format distribution:
   CALL ANALYZE_EMAIL_FORMATS();
   SELECT * FROM EMAIL_FORMAT_DISTRIBUTION;

5. Check processing statistics:
   SELECT * FROM EMAIL_PROCESSING_STATS;

6. Find emails with validation errors:
   SELECT email_id, subject, validation_errors 
   FROM PROCESSED_EMAILS 
   WHERE ARRAY_SIZE(validation_errors) > 0;
*/
