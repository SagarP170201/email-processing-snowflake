# 🤖 Fully Automated Real-Time Email Processing with Snowflake Cortex AI

A **comprehensive real-time email processing system** that automatically ingests emails from Gmail, processes them instantly using Snowflake Streams and Tasks, and generates AI-powered insights using Snowflake Cortex AI functions.

## 🚀 Key Features

### 🔄 **Fully Automated Pipeline**
- **Real-time Ingestion**: Snowpipe + S3 event notifications for instant email processing (<1 minute latency)
- **Gmail API Integration**: Direct connection to Gmail for automatic domain-specific email fetching
- **Stream-based Processing**: Automatic email parsing triggered by new file arrivals using Snowflake Streams
- **Intelligent Task Orchestration**: Automated AI analysis with smart scheduling and resource management
- **Urgent Email Detection**: Automatic flagging and real-time alerting for time-sensitive emails

### 🎯 **AI-Powered Analysis** 
- **Multi-format Email Support**: Gmail API JSON, Outlook/Exchange, simple JSON, marketing emails, raw text
- **Snowflake Cortex AI**: Summarization, sentiment analysis, classification, and entity extraction
- **Token-Optimized Processing**: Smart content limits and batch processing for cost efficiency
- **Intelligent Classification**: Automatic categorization (urgent, informational, action required, etc.)

### 📊 **Comprehensive Monitoring**
- **Real-time Dashboard**: Live monitoring of ingestion, processing, and AI analysis
- **Intelligent Alerting**: Automated system health monitoring with customizable thresholds
- **Performance Analytics**: Processing latency, throughput, error rate, and token usage tracking
- **Pipeline Visualization**: End-to-end flow monitoring from Gmail to AI insights

## 📋 Prerequisites

- Snowflake account with Cortex AI enabled
- AWS S3 bucket (for external staging)
- Python 3.8+ (for Streamlit app)
- Appropriate Snowflake warehouse permissions

## 🏗️ Architecture Overview

```
Email Sources → S3 Staging → Snowflake Ingestion → AI Processing → Streamlit Dashboard
     ↓              ↓              ↓                    ↓              ↓
  Gmail API      External       Raw Email           Cortex AI      Interactive
  Outlook API    Stage          Files Table         Functions      Visualization
  .eml files     Internal       ↓                   ↓              ↓
  .msg files     Stage          Processed           Email          Search &
  .json files                   Emails Table        Summaries      Analytics
```

## 🛠️ Installation & Setup

### 1. Database Setup

Execute the SQL scripts in order:

```bash
# 1. Create database structure
snowsql -f setup/01_database_setup.sql

# 2. Set up staging areas
snowsql -f setup/02_staging_setup.sql

# 3. Configure AI summarization
snowsql -f cortex/03_ai_summarization.sql

# 4. Set up automation (optional)
snowsql -f automation/04_automation_setup.sql
```

### 2. Configure S3 Integration

Update the S3 stage configuration in `02_staging_setup.sql`:

```sql
CREATE OR REPLACE STAGE EMAIL_S3_STAGE
URL = 's3://your-email-bucket/email-files/'
CREDENTIALS = (AWS_KEY_ID = 'your_access_key' AWS_SECRET_KEY = 'your_secret_key')
-- OR use IAM role:
-- CREDENTIALS = (AWS_ROLE = 'arn:aws:iam::your-account:role/your-snowflake-role')
```

### 3. Streamlit App Setup

```bash
cd streamlit
pip install -r requirements.txt

# Configure Snowflake credentials
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
# Edit secrets.toml with your Snowflake credentials

# Run the app
streamlit run app.py
```

### 4. Configure Snowflake Secrets

Edit `.streamlit/secrets.toml`:

```toml
[snowflake]
user = "your_snowflake_username"
password = "your_snowflake_password"
account = "your_snowflake_account"
warehouse = "your_warehouse"
database = "EMAIL_PROCESSING_APP"
schema = "CORE"
```

## 📧 Supported Email Formats

The app supports multiple email formats:

### JSON Format (Gmail API)
```json
{
  "payload": {
    "headers": [
      {"name": "From", "value": "sender@example.com"},
      {"name": "Subject", "value": "Meeting Tomorrow"}
    ],
    "parts": [
      {"body": {"data": "Email content here..."}}
    ]
  },
  "internalDate": "1640995200000"
}
```

### Simple Text Format
```json
{
  "email_text": "Email content as plain text...",
  "metadata": {
    "sender": "sender@example.com",
    "subject": "Email subject"
  }
}
```

### EML/MSG Files
- Standard .eml and .msg files are supported
- Automatically parsed for headers and content

## 🤖 AI Features

### Summary Types

1. **Brief Summary**: 2-3 sentence overview
2. **Detailed Summary**: Comprehensive analysis
3. **Action Items**: Extracted tasks and deadlines
4. **Sentiment Analysis**: Emotional tone scoring

### Classification Categories

- URGENT
- INFORMATIONAL  
- ACTION_REQUIRED
- MEETING_REQUEST
- MARKETING
- SUPPORT
- PERSONAL
- OTHER

### Entity Extraction

Automatically identifies:
- Person names
- Company names
- Dates and deadlines
- Locations
- Monetary amounts
- Phone numbers
- Email addresses

## 📊 Usage Examples

### Manual Processing

```sql
-- Ingest files from S3
CALL INGEST_EMAIL_FILES('S3', '.*\.json');

-- Process specific email
CALL ANALYZE_EMAIL_WITH_AI('email_id_here');

-- Batch analyze emails
CALL BATCH_ANALYZE_EMAILS(10, 'ALL');
```

### Search and Analytics

```sql
-- Semantic search
SELECT * FROM TABLE(SEARCH_EMAILS_SEMANTIC('budget planning meetings', 5));

-- View comprehensive insights
SELECT * FROM EMAIL_AI_INSIGHTS 
WHERE email_classification = 'ACTION_REQUIRED'
ORDER BY email_date DESC;
```

### Automation Management

```sql
-- Suspend all automation
CALL MANAGE_AUTOMATION('SUSPEND', 'ALL');

-- Resume specific task
CALL MANAGE_AUTOMATION('RESUME', 'AUTO_INGEST_EMAILS');

-- Check automation status
SELECT * FROM AUTOMATION_MONITORING;
```

## 🔄 Automation Features

### Available Tasks

1. **AUTO_INGEST_EMAILS**: Ingests new files every 2 hours
2. **AUTO_PROCESS_EMAILS**: Processes newly ingested emails
3. **AUTO_AI_ANALYSIS**: Generates AI summaries
4. **AUTO_MAINTENANCE**: Weekly cleanup and optimization
5. **AUTO_MONITOR_FAILURES**: Monitors for failed jobs
6. **REALTIME_EMAIL_PROCESSOR**: Stream-based real-time processing

### Scheduling Options

- **Time-based**: CRON expressions for regular intervals
- **Event-based**: Stream triggers for real-time processing
- **Dependency-based**: Tasks that run after other tasks complete

## 📈 Monitoring & Analytics

### Key Metrics Dashboard

- Total emails processed
- Recent uploads (24h)
- Pending processing count
- AI summaries generated
- Processing status distribution
- Sentiment trends over time

### Processing Jobs Tracking

All operations are logged in the `PROCESSING_JOBS` table:

```sql
SELECT 
    job_type,
    COUNT(*) as total_jobs,
    AVG(files_processed) as avg_files_per_job,
    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed_jobs
FROM PROCESSING_JOBS 
WHERE start_time >= CURRENT_TIMESTAMP() - INTERVAL '7 DAYS'
GROUP BY job_type;
```

## 🔍 SharePoint Connector Analysis

We've evaluated the Snowflake OpenFlow SharePoint Connector for this use case:

### When to Use SharePoint Connector:
- Emails already stored in SharePoint
- Microsoft 365 ecosystem integration
- Need SharePoint metadata preservation

### When to Use S3 Approach (Recommended):
- Multiple email sources
- Various email formats
- Cost-effective large-scale processing
- Custom preprocessing requirements

**Recommendation**: The S3-based approach provides better flexibility and cost-effectiveness for most email processing scenarios.

## 🚨 Troubleshooting

### Common Issues

1. **Cortex AI Functions Not Available**
   - Ensure your Snowflake account has Cortex enabled
   - Check region availability for Cortex services

2. **S3 Access Errors**
   - Verify IAM permissions
   - Check storage integration configuration
   - Validate S3 bucket and file paths

3. **Task Execution Failures**
   - Check warehouse availability and size
   - Review task dependencies
   - Monitor resource usage

### Performance Optimization

1. **Warehouse Sizing**
   - Use larger warehouses for batch processing
   - Consider auto-suspend/resume settings

2. **Batch Processing**
   - Process emails in batches of 50-100
   - Use pagination for large datasets

3. **Storage Optimization**
   - Archive old processed emails
   - Clean up intermediate files
   - Use appropriate data types

## 📝 API Reference

### Key Stored Procedures

- `INGEST_EMAIL_FILES(stage_name, file_pattern)`
- `PROCESS_EMAIL_FORMAT(file_id, email_content)`
- `ANALYZE_EMAIL_WITH_AI(email_id)`
- `BATCH_ANALYZE_EMAILS(limit_count, status_filter)`
- `MANAGE_AUTOMATION(action, task_name)`

### Key Functions

- `SUMMARIZE_EMAIL(email_content, summary_type)`
- `CLASSIFY_EMAIL(email_content, subject)`
- `EXTRACT_EMAIL_ENTITIES(email_content)`
- `SEARCH_EMAILS_SEMANTIC(search_query, limit_count)`

### Key Views

- `EMAIL_PROCESSING_OVERVIEW`: High-level processing status
- `EMAIL_AI_INSIGHTS`: Comprehensive AI analysis results
- `AUTOMATION_MONITORING`: Task execution monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test your changes thoroughly
4. Submit a pull request with detailed description

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
1. Check the troubleshooting section
2. Review Snowflake Cortex documentation
3. Open an issue in the repository
4. Contact your Snowflake support team for account-specific issues

## 🔮 Future Enhancements

- **Multi-language Support**: Process emails in different languages
- **Advanced Analytics**: Trend analysis and predictive insights  
- **Integration APIs**: REST APIs for external system integration
- **Custom AI Models**: Fine-tuned models for specific use cases
- **Real-time Notifications**: Slack/Teams integration for alerts
- **Email Response Generation**: AI-powered email drafting
