# 🧪 Automated Pipeline Testing Guide

Complete end-to-end testing guide for the real-time automated email processing system.

## 🎯 Testing Overview

**What we're testing:**
- Real-time email ingestion via Snowpipe
- Stream-triggered automated processing
- AI analysis automation
- Monitoring and alerting system
- Gmail API integration

## 📋 Pre-Testing Checklist

### ✅ **Foundation Verification**
```sql
-- Verify existing foundation is working
USE DATABASE EMAIL_PROCESSING_APP;
USE SCHEMA CORE;

-- Check tables exist
SHOW TABLES;

-- Verify existing functions work
SELECT SNOWFLAKE.CORTEX.SUMMARIZE('Test email content for verification');
```

### ✅ **Automated Components Deployed**
```bash
# Deploy automation (if not done)
./deploy_automated.sh

# Verify deployment
snowsql -c dev -q "SELECT * FROM REALTIME_TASK_STATUS;"
```

## 🧪 Test Scenarios

### **Test 1: Manual S3 Upload → Snowpipe Ingestion**

**Purpose**: Verify Snowpipe automatically ingests files from S3

```bash
# 1. Upload test email to S3
aws s3 cp sample_data/sample_email_1.json s3://your-bucket/email-files/test_email_$(date +%s).json

# 2. Wait 1-2 minutes for Snowpipe
# 3. Check ingestion
snowsql -c dev -q "
SELECT * FROM RAW_EMAIL_FILES 
WHERE upload_timestamp >= DATEADD('minute', -5, CURRENT_TIMESTAMP())
ORDER BY upload_timestamp DESC;
"
```

**Expected Result**: ✅ New file appears in `RAW_EMAIL_FILES` with status `PENDING`

---

### **Test 2: Stream-Triggered Processing**

**Purpose**: Verify streams detect new files and trigger processing

```sql
-- 1. Check stream has data
SELECT SYSTEM$STREAM_HAS_DATA('EMAIL_FILES_REALTIME_STREAM');

-- 2. Manually trigger task (for testing)
EXECUTE TASK REALTIME_EMAIL_PROCESSOR;

-- 3. Verify processing
SELECT * FROM PROCESSED_EMAILS 
WHERE extracted_timestamp >= DATEADD('minute', -5, CURRENT_TIMESTAMP());
```

**Expected Result**: ✅ Email appears in `PROCESSED_EMAILS` with parsed content

---

### **Test 3: Automated AI Analysis**

**Purpose**: Verify AI analysis runs automatically on processed emails

```sql
-- 1. Check AI analysis stream
SELECT SYSTEM$STREAM_HAS_DATA('PROCESSED_EMAILS_STREAM');

-- 2. Manually trigger AI task
EXECUTE TASK REALTIME_AI_ANALYZER;

-- 3. Verify AI results
SELECT * FROM EMAIL_SUMMARIES 
WHERE created_timestamp >= DATEADD('minute', -5, CURRENT_TIMESTAMP());
```

**Expected Result**: ✅ AI summaries and classifications generated

---

### **Test 4: Gmail Connector Integration**

**Purpose**: Test automated email fetching from Gmail

```bash
# 1. Configure Gmail API credentials
cd email_sources
# Place credentials.json file here

# 2. Test Gmail connection
python gmail_connector.py

# 3. Check for new emails in S3
aws s3 ls s3://your-bucket/email-files/gmail-realtime/
```

**Expected Result**: ✅ Emails fetched from Gmail and uploaded to S3

---

### **Test 5: End-to-End Automated Flow**

**Purpose**: Complete pipeline test with real Gmail emails

```bash
# 1. Enable all automation tasks
snowsql -c dev -q "CALL MANAGE_REALTIME_TASKS('RESUME', 'ALL');"

# 2. Schedule Gmail fetching (every 5 minutes)
crontab -e
# Add: */5 * * * * cd /path/to/email_processing_app/email_sources && python gmail_connector.py

# 3. Monitor real-time processing
streamlit run streamlit/realtime_monitoring_app.py

# 4. Send test email to monitored domain
# 5. Watch dashboard for real-time processing
```

**Expected Result**: ✅ Email flows automatically through entire pipeline

---

### **Test 6: Urgent Email Detection**

**Purpose**: Test urgent email flagging and alerting

```sql
-- 1. Insert urgent email manually
INSERT INTO RAW_EMAIL_FILES (file_name, file_content, processing_status)
VALUES (
    'urgent_test.json',
    PARSE_JSON('{
        "email_type": "simple_format",
        "email_text": "URGENT: System outage affecting production systems. Immediate action required!",
        "metadata": {
            "sender": "admin@company.com",
            "subject": "URGENT: Production System Down"
        }
    }'),
    'PENDING'
);

-- 2. Wait for processing (1-2 minutes)
-- 3. Check urgent alerts
SELECT * FROM URGENT_EMAIL_ALERTS;
SELECT * FROM SYSTEM_ALERTS WHERE alert_category = 'AI_ANALYSIS';
```

**Expected Result**: ✅ Urgent email detected and alert generated

---

### **Test 7: System Health Monitoring**

**Purpose**: Verify monitoring and alerting system

```sql
-- 1. Check system health
CALL GET_SYSTEM_STATUS();
SELECT * FROM SYSTEM_HEALTH_DASHBOARD;

-- 2. Generate test alerts
CALL GENERATE_SMART_ALERTS();

-- 3. View alerts
SELECT * FROM SYSTEM_ALERTS WHERE resolved = FALSE;

-- 4. Test alert resolution
CALL RESOLVE_ALERT('alert_id_here', 'TEST_USER');
```

**Expected Result**: ✅ System health accurately reported, alerts generated and resolved

---

### **Test 8: Performance Under Load**

**Purpose**: Test system performance with multiple emails

```bash
# 1. Upload multiple test files to S3
for i in {1..10}; do
    aws s3 cp sample_data/sample_email_1.json s3://your-bucket/email-files/load_test_$i.json
done

# 2. Monitor processing metrics
snowsql -c dev -q "
SELECT 
    COUNT(*) as total_files,
    COUNT(CASE WHEN processing_status = 'COMPLETED' THEN 1 END) as processed,
    COUNT(CASE WHEN processing_status = 'FAILED' THEN 1 END) as failed,
    AVG(DATEDIFF('second', upload_timestamp, 
        COALESCE((SELECT MAX(extracted_timestamp) FROM PROCESSED_EMAILS pe 
                  WHERE pe.file_reference = rf.file_id), CURRENT_TIMESTAMP()))) as avg_latency
FROM RAW_EMAIL_FILES rf
WHERE upload_timestamp >= DATEADD('minute', -10, CURRENT_TIMESTAMP());
"
```

**Expected Result**: ✅ All files processed with acceptable latency (<2 minutes)

---

## 🚨 Troubleshooting Common Issues

### **Issue 1: Snowpipe Not Processing Files**

```sql
-- Check pipe status
SELECT * FROM SNOWPIPE_STATUS;
CALL CHECK_PIPE_HEALTH();

-- Common fixes:
-- 1. Verify S3 event notifications configured correctly
-- 2. Check SQS queue permissions
-- 3. Restart pipe: ALTER PIPE EMAIL_REALTIME_PIPE REFRESH;
```

### **Issue 2: Tasks Not Executing**

```sql
-- Check task status
SELECT * FROM REALTIME_TASK_STATUS;

-- Common fixes:
-- 1. Resume tasks: CALL MANAGE_REALTIME_TASKS('RESUME', 'ALL');
-- 2. Check warehouse availability
-- 3. Verify stream has data: SELECT SYSTEM$STREAM_HAS_DATA('EMAIL_FILES_REALTIME_STREAM');
```

### **Issue 3: Gmail Connector Errors**

```bash
# Check authentication
cd email_sources
python -c "from gmail_connector import GmailConnector; print('✅ Imports OK')"

# Common fixes:
# 1. Refresh OAuth token: rm token.json && python gmail_connector.py
# 2. Check credentials.json file exists
# 3. Verify Gmail API enabled in Google Cloud Console
```

### **Issue 4: High Token Usage**

```sql
-- Check token usage patterns
SELECT 
    DATE_TRUNC('hour', created_timestamp) as hour,
    COUNT(*) as summaries_generated,
    summary_type,
    AVG(LENGTH(summary_text)) as avg_summary_length
FROM EMAIL_SUMMARIES 
WHERE created_timestamp >= DATEADD('day', -1, CURRENT_TIMESTAMP())
GROUP BY hour, summary_type
ORDER BY hour DESC;

-- Optimization options:
-- 1. Reduce max_content_length in config
-- 2. Enable batch processing for non-urgent emails
-- 3. Use brief summaries only for automated processing
```

## ✅ Success Criteria

### **Real-Time Processing**
- [ ] New emails appear in dashboard within 2 minutes
- [ ] Processing latency < 60 seconds end-to-end
- [ ] Zero failed files under normal conditions

### **AI Analysis Quality**
- [ ] Summaries are coherent and accurate
- [ ] Email classification matches content
- [ ] Urgent emails correctly identified
- [ ] Sentiment analysis reasonable

### **System Reliability**
- [ ] Tasks execute on schedule without manual intervention
- [ ] Error rate < 5% under normal load
- [ ] System recovers automatically from temporary failures
- [ ] Monitoring dashboard shows green status

### **Performance Benchmarks**
- [ ] Process 100 emails/hour with minimal latency
- [ ] Token usage < 5 per email (optimized mode)
- [ ] System handles 500+ emails/day
- [ ] Alerts trigger within 1 minute of issues

## 🎉 Deployment Completion Checklist

- [ ] All SQL scripts deployed successfully
- [ ] Snowpipe configured and active
- [ ] Tasks resumed and executing
- [ ] Gmail API credentials configured
- [ ] S3 bucket and notifications set up
- [ ] Monitoring dashboard accessible
- [ ] Test emails processed successfully
- [ ] Performance meets benchmarks

## 📞 Support & Next Steps

**If all tests pass**: 🎉 Your automated email processing pipeline is ready for production!

**If issues found**: 
1. Review troubleshooting section
2. Check Snowflake task history: `SELECT * FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())`
3. Examine error logs in `SYSTEM_ALERTS` and `PROCESSING_JOBS`
4. Use monitoring dashboard for real-time debugging
