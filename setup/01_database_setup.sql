-- Email Processing App - Database Setup
-- This script sets up the core database structure for email ingestion and AI summarization

-- Create database and schema
CREATE DATABASE IF NOT EXISTS EMAIL_PROCESSING_APP;
USE DATABASE EMAIL_PROCESSING_APP;

CREATE SCHEMA IF NOT EXISTS CORE;
USE SCHEMA CORE;

-- Create table for storing raw email files
CREATE OR REPLACE TABLE RAW_EMAIL_FILES (
    file_id STRING DEFAULT CONCAT('EMAIL_', CURRENT_TIMESTAMP()::STRING, '_', UUID_STRING()),
    file_name STRING NOT NULL,
    file_path STRING,
    file_size NUMBER,
    upload_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    file_content VARIANT,
    processing_status STRING DEFAULT 'PENDING', -- PENDING, PROCESSING, COMPLETED, FAILED
    error_message STRING,
    PRIMARY KEY (file_id)
);

-- Create table for processed email data
CREATE OR REPLACE TABLE PROCESSED_EMAILS (
    email_id STRING DEFAULT CONCAT('PROC_', CURRENT_TIMESTAMP()::STRING, '_', UUID_STRING()),
    file_id STRING,
    sender_email STRING,
    recipient_emails ARRAY,
    subject STRING,
    email_body STRING,
    email_date TIMESTAMP_NTZ,
    attachments ARRAY,
    extracted_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (email_id),
    FOREIGN KEY (file_id) REFERENCES RAW_EMAIL_FILES(file_id)
);

-- Create table for AI-generated summaries
CREATE OR REPLACE TABLE EMAIL_SUMMARIES (
    summary_id STRING DEFAULT CONCAT('SUMM_', CURRENT_TIMESTAMP()::STRING, '_', UUID_STRING()),
    email_id STRING,
    summary_type STRING, -- 'BRIEF', 'DETAILED', 'ACTION_ITEMS', 'SENTIMENT'
    summary_text STRING,
    confidence_score FLOAT,
    created_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    model_used STRING DEFAULT 'snowflake-arctic',
    PRIMARY KEY (summary_id),
    FOREIGN KEY (email_id) REFERENCES PROCESSED_EMAILS(email_id)
);

-- Create table for tracking processing jobs
CREATE OR REPLACE TABLE PROCESSING_JOBS (
    job_id STRING DEFAULT CONCAT('JOB_', CURRENT_TIMESTAMP()::STRING, '_', UUID_STRING()),
    job_type STRING, -- 'INGESTION', 'SUMMARIZATION', 'BATCH_PROCESS'
    start_time TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    end_time TIMESTAMP_NTZ,
    status STRING DEFAULT 'RUNNING', -- RUNNING, COMPLETED, FAILED
    files_processed NUMBER DEFAULT 0,
    files_failed NUMBER DEFAULT 0,
    error_details VARIANT,
    PRIMARY KEY (job_id)
);

-- Create views for easier data access
CREATE OR REPLACE VIEW EMAIL_PROCESSING_OVERVIEW AS
SELECT 
    pf.file_name,
    pf.upload_timestamp,
    pf.processing_status,
    pe.subject,
    pe.sender_email,
    pe.email_date,
    es.summary_text as brief_summary,
    es.confidence_score
FROM RAW_EMAIL_FILES pf
LEFT JOIN PROCESSED_EMAILS pe ON pf.file_id = pe.file_id
LEFT JOIN EMAIL_SUMMARIES es ON pe.email_id = es.email_id 
    AND es.summary_type = 'BRIEF'
ORDER BY pf.upload_timestamp DESC;

-- Grant necessary permissions (adjust as needed)
GRANT USAGE ON DATABASE EMAIL_PROCESSING_APP TO ROLE PUBLIC;
GRANT USAGE ON SCHEMA EMAIL_PROCESSING_APP.CORE TO ROLE PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA EMAIL_PROCESSING_APP.CORE TO ROLE PUBLIC;
GRANT SELECT ON ALL VIEWS IN SCHEMA EMAIL_PROCESSING_APP.CORE TO ROLE PUBLIC;

-- Create file formats for email ingestion
CREATE OR REPLACE FILE FORMAT EMAIL_FILE_FORMAT
TYPE = 'JSON'
STRIP_OUTER_ARRAY = FALSE
COMMENT = 'File format for email JSON files';

CREATE OR REPLACE FILE FORMAT EMAIL_TEXT_FORMAT
TYPE = 'CSV'
FIELD_DELIMITER = NONE
RECORD_DELIMITER = NONE
SKIP_HEADER = 0
COMMENT = 'File format for plain text email files';
