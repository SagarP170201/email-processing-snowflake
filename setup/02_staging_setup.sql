-- Email Processing App - Staging Setup
-- This script sets up staging areas for email file ingestion

USE DATABASE EMAIL_PROCESSING_APP;
USE SCHEMA CORE;

-- Create internal directory stage for manual file uploads
CREATE OR REPLACE STAGE EMAIL_INTERNAL_STAGE
DIRECTORY = ( ENABLE = TRUE )
COMMENT = 'Internal stage for manual email file uploads';

-- Create external S3 stage (you'll need to configure with your AWS credentials)
-- Note: Replace with your actual S3 bucket details
CREATE OR REPLACE STAGE EMAIL_S3_STAGE
URL = 's3://your-email-bucket/email-files/'
-- CREDENTIALS = (AWS_KEY_ID = 'your_access_key' AWS_SECRET_KEY = 'your_secret_key')
-- OR use IAM role: 
-- CREDENTIALS = (AWS_ROLE = 'arn:aws:iam::your-account:role/your-snowflake-role')
FILE_FORMAT = EMAIL_FILE_FORMAT
DIRECTORY = ( ENABLE = TRUE )
COMMENT = 'External S3 stage for automated email file ingestion';

-- Create a more flexible stage for different email formats
CREATE OR REPLACE STAGE EMAIL_MULTI_FORMAT_STAGE
DIRECTORY = ( ENABLE = TRUE )
COMMENT = 'Internal stage supporting multiple email formats (.eml, .msg, .txt, .json)';

-- Create stored procedure to list files in stages
CREATE OR REPLACE PROCEDURE LIST_STAGED_FILES(STAGE_NAME STRING)
RETURNS TABLE (file_name STRING, file_size NUMBER, last_modified TIMESTAMP_NTZ)
LANGUAGE SQL
AS
$$
BEGIN
    CASE 
        WHEN UPPER(STAGE_NAME) = 'S3' THEN
            RETURN TABLE(
                SELECT 
                    METADATA$FILENAME as file_name,
                    METADATA$FILE_SIZE as file_size, 
                    METADATA$FILE_LAST_MODIFIED as last_modified
                FROM @EMAIL_S3_STAGE
            );
        WHEN UPPER(STAGE_NAME) = 'INTERNAL' THEN
            RETURN TABLE(
                SELECT 
                    METADATA$FILENAME as file_name,
                    METADATA$FILE_SIZE as file_size,
                    METADATA$FILE_LAST_MODIFIED as last_modified
                FROM @EMAIL_INTERNAL_STAGE
            );
        ELSE
            RETURN TABLE(
                SELECT 
                    'Invalid stage name' as file_name,
                    0 as file_size,
                    CURRENT_TIMESTAMP() as last_modified
            );
    END CASE;
END;
$$;

-- Create stored procedure for manual file ingestion
CREATE OR REPLACE PROCEDURE INGEST_EMAIL_FILES(
    STAGE_NAME STRING DEFAULT 'INTERNAL',
    FILE_PATTERN STRING DEFAULT '.*'
)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    job_id STRING;
    files_processed NUMBER DEFAULT 0;
    files_failed NUMBER DEFAULT 0;
    result_message STRING;
BEGIN
    -- Create new processing job
    job_id := CONCAT('JOB_', CURRENT_TIMESTAMP()::STRING, '_', UUID_STRING());
    
    INSERT INTO PROCESSING_JOBS (job_id, job_type, start_time, status)
    VALUES (job_id, 'INGESTION', CURRENT_TIMESTAMP(), 'RUNNING');
    
    -- Process files based on stage
    IF (UPPER(STAGE_NAME) = 'S3') THEN
        INSERT INTO RAW_EMAIL_FILES (file_name, file_path, file_size, file_content, processing_status)
        SELECT 
            METADATA$FILENAME,
            '@EMAIL_S3_STAGE/' || METADATA$FILENAME,
            METADATA$FILE_SIZE,
            PARSE_JSON($1),
            'PENDING'
        FROM @EMAIL_S3_STAGE
        WHERE METADATA$FILENAME RLIKE FILE_PATTERN;
        
    ELSEIF (UPPER(STAGE_NAME) = 'INTERNAL') THEN
        INSERT INTO RAW_EMAIL_FILES (file_name, file_path, file_size, file_content, processing_status)
        SELECT 
            METADATA$FILENAME,
            '@EMAIL_INTERNAL_STAGE/' || METADATA$FILENAME,
            METADATA$FILE_SIZE,
            PARSE_JSON($1),
            'PENDING'
        FROM @EMAIL_INTERNAL_STAGE
        WHERE METADATA$FILENAME RLIKE FILE_PATTERN;
    END IF;
    
    files_processed := SQLROWCOUNT;
    
    -- Update job status
    UPDATE PROCESSING_JOBS 
    SET 
        end_time = CURRENT_TIMESTAMP(),
        status = 'COMPLETED',
        files_processed = files_processed
    WHERE job_id = job_id;
    
    result_message := 'Successfully ingested ' || files_processed || ' files with job ID: ' || job_id;
    RETURN result_message;
    
EXCEPTION
    WHEN OTHER THEN
        UPDATE PROCESSING_JOBS 
        SET 
            end_time = CURRENT_TIMESTAMP(),
            status = 'FAILED',
            files_failed = files_processed,
            error_details = PARSE_JSON('{"error": "' || SQLERRM || '"}')
        WHERE job_id = job_id;
        
        RETURN 'Ingestion failed: ' || SQLERRM;
END;
$$;

-- Create procedure to process different email file formats
CREATE OR REPLACE PROCEDURE PROCESS_EMAIL_FORMAT(
    FILE_ID STRING,
    EMAIL_CONTENT VARIANT
)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    processed_count NUMBER DEFAULT 0;
BEGIN
    -- Process JSON format emails (like from Gmail API)
    IF (EMAIL_CONTENT:payload IS NOT NULL) THEN
        INSERT INTO PROCESSED_EMAILS (
            file_id,
            sender_email,
            recipient_emails,
            subject,
            email_body,
            email_date
        )
        SELECT 
            FILE_ID,
            EMAIL_CONTENT:payload.headers[0]:value::STRING as sender,
            PARSE_JSON(EMAIL_CONTENT:payload.headers[1]:value::STRING) as recipients,
            EMAIL_CONTENT:payload.headers[2]:value::STRING as subject,
            EMAIL_CONTENT:payload.parts[0]:body.data::STRING as body,
            TO_TIMESTAMP_NTZ(EMAIL_CONTENT:internalDate::STRING);
        processed_count := 1;
        
    -- Process simple text format
    ELSEIF (EMAIL_CONTENT:email_text IS NOT NULL) THEN
        INSERT INTO PROCESSED_EMAILS (
            file_id,
            email_body,
            extracted_timestamp
        )
        VALUES (
            FILE_ID,
            EMAIL_CONTENT:email_text::STRING,
            CURRENT_TIMESTAMP()
        );
        processed_count := 1;
    END IF;
    
    -- Update processing status
    UPDATE RAW_EMAIL_FILES 
    SET processing_status = 'COMPLETED'
    WHERE file_id = FILE_ID;
    
    RETURN 'Processed ' || processed_count || ' email(s) from file: ' || FILE_ID;
    
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

-- Grant execute permissions on procedures
GRANT USAGE ON PROCEDURE LIST_STAGED_FILES(STRING) TO ROLE PUBLIC;
GRANT USAGE ON PROCEDURE INGEST_EMAIL_FILES(STRING, STRING) TO ROLE PUBLIC;
GRANT USAGE ON PROCEDURE PROCESS_EMAIL_FORMAT(STRING, VARIANT) TO ROLE PUBLIC;
