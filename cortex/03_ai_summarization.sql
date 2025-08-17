-- Email Processing App - Cortex AI Summarization
-- This script implements AI-powered email summarization using Snowflake Cortex

USE DATABASE EMAIL_PROCESSING_APP;
USE SCHEMA CORE;

-- Create function for basic email summarization
CREATE OR REPLACE FUNCTION SUMMARIZE_EMAIL(email_content STRING, summary_type STRING)
RETURNS STRING
LANGUAGE SQL
AS
$$
    CASE 
        WHEN UPPER(summary_type) = 'BRIEF' THEN
            SNOWFLAKE.CORTEX.SUMMARIZE(
                email_content,
                'Provide a brief 2-3 sentence summary of this email focusing on the main purpose and key points.'
            )
        WHEN UPPER(summary_type) = 'DETAILED' THEN
            SNOWFLAKE.CORTEX.SUMMARIZE(
                email_content,
                'Provide a detailed summary of this email including all important points, decisions made, and context provided.'
            )
        WHEN UPPER(summary_type) = 'ACTION_ITEMS' THEN
            SNOWFLAKE.CORTEX.COMPLETE(
                'mistral-large',
                CONCAT(
                    'Extract and list all action items, tasks, deadlines, and follow-ups from this email. ',
                    'Format as bullet points. If no action items exist, respond with "No action items found."\n\n',
                    'Email content:\n', email_content
                )
            )
        WHEN UPPER(summary_type) = 'SENTIMENT' THEN
            SNOWFLAKE.CORTEX.SENTIMENT(email_content)
        ELSE
            'Invalid summary type. Use: BRIEF, DETAILED, ACTION_ITEMS, or SENTIMENT'
    END
$$;

-- Create function for email classification
CREATE OR REPLACE FUNCTION CLASSIFY_EMAIL(email_content STRING, subject STRING)
RETURNS STRING
LANGUAGE SQL
AS
$$
    SNOWFLAKE.CORTEX.COMPLETE(
        'mistral-large',
        CONCAT(
            'Classify this email into one of these categories: ',
            'URGENT, INFORMATIONAL, ACTION_REQUIRED, MEETING_REQUEST, MARKETING, SUPPORT, PERSONAL, OTHER. ',
            'Respond with only the category name.\n\n',
            'Subject: ', COALESCE(subject, 'No subject'), '\n',
            'Content: ', email_content
        )
    )
$$;

-- Create function to extract key entities from emails
CREATE OR REPLACE FUNCTION EXTRACT_EMAIL_ENTITIES(email_content STRING)
RETURNS VARIANT
LANGUAGE SQL
AS
$$
    PARSE_JSON(
        SNOWFLAKE.CORTEX.COMPLETE(
            'mistral-large',
            CONCAT(
                'Extract the following entities from this email and return as JSON: ',
                '{"people": ["list of person names"], ',
                '"companies": ["list of company names"], ',
                '"dates": ["list of dates mentioned"], ',
                '"locations": ["list of locations"], ',
                '"amounts": ["list of monetary amounts"], ',
                '"phone_numbers": ["list of phone numbers"], ',
                '"email_addresses": ["list of email addresses"]}. ',
                'Return only valid JSON.\n\nEmail content:\n', email_content
            )
        )
    )
$$;

-- Create comprehensive email analysis procedure
CREATE OR REPLACE PROCEDURE ANALYZE_EMAIL_WITH_AI(email_id STRING)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    email_content STRING;
    email_subject STRING;
    analysis_results VARIANT;
    summary_count NUMBER DEFAULT 0;
BEGIN
    -- Get email content
    SELECT email_body, subject 
    INTO email_content, email_subject
    FROM PROCESSED_EMAILS 
    WHERE email_id = email_id;
    
    IF (email_content IS NULL) THEN
        RETURN 'Email not found with ID: ' || email_id;
    END IF;
    
    -- Generate different types of summaries
    INSERT INTO EMAIL_SUMMARIES (email_id, summary_type, summary_text, model_used)
    VALUES 
        (email_id, 'BRIEF', SUMMARIZE_EMAIL(email_content, 'BRIEF'), 'snowflake-arctic'),
        (email_id, 'DETAILED', SUMMARIZE_EMAIL(email_content, 'DETAILED'), 'snowflake-arctic'),
        (email_id, 'ACTION_ITEMS', SUMMARIZE_EMAIL(email_content, 'ACTION_ITEMS'), 'mistral-large'),
        (email_id, 'SENTIMENT', SUMMARIZE_EMAIL(email_content, 'SENTIMENT'), 'snowflake-arctic');
    
    summary_count := 4;
    
    -- Add classification and entity extraction to processed emails table
    UPDATE PROCESSED_EMAILS 
    SET 
        email_classification = CLASSIFY_EMAIL(email_content, email_subject),
        extracted_entities = EXTRACT_EMAIL_ENTITIES(email_content)
    WHERE email_id = email_id;
    
    RETURN 'Successfully analyzed email ' || email_id || ' with ' || summary_count || ' AI-generated insights';
    
EXCEPTION
    WHEN OTHER THEN
        RETURN 'Analysis failed for email ' || email_id || ': ' || SQLERRM;
END;
$$;

-- Create batch analysis procedure
CREATE OR REPLACE PROCEDURE BATCH_ANALYZE_EMAILS(
    limit_count NUMBER DEFAULT 10,
    status_filter STRING DEFAULT 'ALL'
)
RETURNS STRING
LANGUAGE SQL
AS
$$
DECLARE
    processed_count NUMBER DEFAULT 0;
    failed_count NUMBER DEFAULT 0;
    job_id STRING;
    cursor_emails CURSOR FOR 
        SELECT email_id 
        FROM PROCESSED_EMAILS pe
        WHERE NOT EXISTS (
            SELECT 1 FROM EMAIL_SUMMARIES es 
            WHERE es.email_id = pe.email_id 
            AND es.summary_type = 'BRIEF'
        )
        AND (status_filter = 'ALL' OR pe.processing_status = status_filter)
        LIMIT limit_count;
BEGIN
    -- Create processing job
    job_id := CONCAT('JOB_', CURRENT_TIMESTAMP()::STRING, '_', UUID_STRING());
    INSERT INTO PROCESSING_JOBS (job_id, job_type, start_time, status)
    VALUES (job_id, 'SUMMARIZATION', CURRENT_TIMESTAMP(), 'RUNNING');
    
    -- Process emails
    FOR email_record IN cursor_emails DO
        BEGIN
            CALL ANALYZE_EMAIL_WITH_AI(email_record.email_id);
            processed_count := processed_count + 1;
        EXCEPTION
            WHEN OTHER THEN
                failed_count := failed_count + 1;
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
    
    RETURN 'Batch analysis completed. Processed: ' || processed_count || ', Failed: ' || failed_count || ', Job ID: ' || job_id;
END;
$$;

-- Create intelligent email search function
CREATE OR REPLACE FUNCTION SEARCH_EMAILS_SEMANTIC(search_query STRING, limit_count NUMBER DEFAULT 10)
RETURNS TABLE (
    email_id STRING,
    subject STRING,
    sender_email STRING,
    email_date TIMESTAMP_NTZ,
    relevance_score FLOAT,
    brief_summary STRING
)
LANGUAGE SQL
AS
$$
    SELECT 
        pe.email_id,
        pe.subject,
        pe.sender_email,
        pe.email_date,
        SNOWFLAKE.CORTEX.COMPLETE(
            'mistral-large',
            CONCAT(
                'Rate the relevance of this email to the query "', search_query, '" on a scale of 0-1. ',
                'Return only the numeric score.\n\nEmail: ', 
                COALESCE(pe.subject, ''), ' ', COALESCE(pe.email_body, '')
            )
        )::FLOAT as relevance_score,
        es.summary_text as brief_summary
    FROM PROCESSED_EMAILS pe
    LEFT JOIN EMAIL_SUMMARIES es ON pe.email_id = es.email_id AND es.summary_type = 'BRIEF'
    WHERE pe.email_body IS NOT NULL
    ORDER BY relevance_score DESC
    LIMIT limit_count
$$;

-- Add new columns to processed emails table for AI insights
ALTER TABLE PROCESSED_EMAILS 
ADD COLUMN IF NOT EXISTS email_classification STRING,
ADD COLUMN IF NOT EXISTS extracted_entities VARIANT,
ADD COLUMN IF NOT EXISTS priority_score FLOAT;

-- Create view for comprehensive email insights
CREATE OR REPLACE VIEW EMAIL_AI_INSIGHTS AS
SELECT 
    pe.email_id,
    pe.subject,
    pe.sender_email,
    pe.email_date,
    pe.email_classification,
    pe.extracted_entities,
    MAX(CASE WHEN es.summary_type = 'BRIEF' THEN es.summary_text END) as brief_summary,
    MAX(CASE WHEN es.summary_type = 'DETAILED' THEN es.summary_text END) as detailed_summary,
    MAX(CASE WHEN es.summary_type = 'ACTION_ITEMS' THEN es.summary_text END) as action_items,
    MAX(CASE WHEN es.summary_type = 'SENTIMENT' THEN es.summary_text END) as sentiment_score,
    COUNT(es.summary_id) as total_summaries
FROM PROCESSED_EMAILS pe
LEFT JOIN EMAIL_SUMMARIES es ON pe.email_id = es.email_id
GROUP BY pe.email_id, pe.subject, pe.sender_email, pe.email_date, pe.email_classification, pe.extracted_entities;

-- Grant permissions
GRANT USAGE ON FUNCTION SUMMARIZE_EMAIL(STRING, STRING) TO ROLE PUBLIC;
GRANT USAGE ON FUNCTION CLASSIFY_EMAIL(STRING, STRING) TO ROLE PUBLIC;
GRANT USAGE ON FUNCTION EXTRACT_EMAIL_ENTITIES(STRING) TO ROLE PUBLIC;
GRANT USAGE ON FUNCTION SEARCH_EMAILS_SEMANTIC(STRING, NUMBER) TO ROLE PUBLIC;
GRANT USAGE ON PROCEDURE ANALYZE_EMAIL_WITH_AI(STRING) TO ROLE PUBLIC;
GRANT USAGE ON PROCEDURE BATCH_ANALYZE_EMAILS(NUMBER, STRING) TO ROLE PUBLIC;
GRANT SELECT ON VIEW EMAIL_AI_INSIGHTS TO ROLE PUBLIC;
