-- Minimal Email Processing Test - Single Email Only
-- This script processes just ONE email to test the system without using many tokens

USE DATABASE EMAIL_PROCESSING_APP;
USE SCHEMA CORE;

-- Insert one sample email for testing
INSERT INTO RAW_EMAIL_FILES (file_name, file_content, processing_status)
VALUES (
    'test_email.json',
    PARSE_JSON('{
        "email_type": "simple_format",
        "sender": "test@example.com",
        "recipients": ["you@company.com"],
        "subject": "Test Email - Budget Meeting",
        "email_date": "2023-11-16T10:00:00Z",
        "email_text": "Hi there! This is a short test email about our budget meeting scheduled for next week. Please prepare your quarterly reports and budget proposals. The meeting will be on Tuesday at 2 PM. Thanks!"
    }'),
    'PENDING'
);

-- Process the email (convert from raw to structured format)
DECLARE
    test_file_id STRING;
    test_email_id STRING;
BEGIN
    -- Get the file ID we just inserted
    SELECT file_id INTO test_file_id 
    FROM RAW_EMAIL_FILES 
    WHERE file_name = 'test_email.json'
    ORDER BY upload_timestamp DESC 
    LIMIT 1;
    
    -- Process the email format
    CALL PROCESS_EMAIL_FORMAT_ENHANCED(test_file_id, PARSE_JSON('{
        "email_type": "simple_format",
        "sender": "test@example.com",
        "recipients": ["you@company.com"],
        "subject": "Test Email - Budget Meeting",
        "email_date": "2023-11-16T10:00:00Z",
        "email_text": "Hi there! This is a short test email about our budget meeting scheduled for next week. Please prepare your quarterly reports and budget proposals. The meeting will be on Tuesday at 2 PM. Thanks!"
    }'));
    
    -- Get the processed email ID
    SELECT email_id INTO test_email_id 
    FROM PROCESSED_EMAILS 
    WHERE file_id = test_file_id
    LIMIT 1;
    
    -- Generate ONLY ONE AI summary (brief) to minimize token usage
    INSERT INTO EMAIL_SUMMARIES (email_id, summary_type, summary_text, model_used)
    VALUES (
        test_email_id,
        'BRIEF',
        SUMMARIZE_EMAIL(
            (SELECT email_body FROM PROCESSED_EMAILS WHERE email_id = test_email_id),
            'BRIEF'
        ),
        'snowflake-arctic'
    );
    
    -- Show the results
    SELECT 'SUCCESS: Test email processed with AI summary!' as result;
    
    -- Display the processed email and summary
    SELECT 
        pe.subject,
        pe.sender_email,
        pe.email_body,
        es.summary_text as ai_summary,
        es.summary_type
    FROM PROCESSED_EMAILS pe
    JOIN EMAIL_SUMMARIES es ON pe.email_id = es.email_id
    WHERE pe.email_id = test_email_id;
    
END;

-- Clean up the test data (optional)
-- DELETE FROM EMAIL_SUMMARIES WHERE email_id IN (SELECT email_id FROM PROCESSED_EMAILS WHERE file_id IN (SELECT file_id FROM RAW_EMAIL_FILES WHERE file_name = 'test_email.json'));
-- DELETE FROM PROCESSED_EMAILS WHERE file_id IN (SELECT file_id FROM RAW_EMAIL_FILES WHERE file_name = 'test_email.json');
-- DELETE FROM RAW_EMAIL_FILES WHERE file_name = 'test_email.json';
