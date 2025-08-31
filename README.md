# 📧 Gmail Integration with Snowflake Cortex AI

A **native Snowflake email processing system** that integrates Gmail API via Python UDFs, processes emails using Streamlit-in-Snowflake, and generates AI-powered insights with Snowflake Cortex functions.

## 🚀 Key Features

### 🔄 **Native Snowflake Architecture**
- **Gmail API Integration**: Python UDF-based email fetching (no external infrastructure)
- **Streamlit-in-Snowflake**: Native dashboard with built-in enterprise authentication
- **Direct Table Processing**: Real-time email ingestion without external staging
- **Stream-based Analysis**: Automatic AI processing triggered by new emails
- **Urgent Email Detection**: Intelligent priority flagging and real-time alerting

### 🎯 **AI-Powered Analysis** 
- **Snowflake Cortex AI**: Summarization, sentiment analysis, and classification
- **Token-Optimized Processing**: Smart content limits for cost efficiency
- **Multi-format Support**: Gmail API JSON, simple JSON, raw text
- **Intelligent Classification**: Automatic urgency detection and prioritization

### 📊 **Real-time Dashboard**
- **Live Email Analytics**: Real-time processing metrics and insights
- **Gmail Integration Status**: Connection health and sync monitoring
- **AI Analysis Results**: Summaries, sentiment scores, and urgency levels
- **System Health Monitoring**: Pipeline status and error tracking

## 📋 Prerequisites

- Snowflake account with Cortex AI enabled
- Gmail API access (for production) or demo simulation  
- Python 3.8+ (for local development/testing)
- Appropriate Snowflake warehouse permissions

## 🏗️ Native Snowflake Architecture

```
Gmail API → Python UDF → Snowflake Tables → Cortex AI → Streamlit-in-Snowflake
     ↓           ↓              ↓              ↓              ↓
sagar.pawar@  FETCH_GMAIL    Raw Email      AI Analysis    Native Dashboard
snowflake.com  EMAILS()      Files Table    Functions      Built-in Auth
Domain Filter      ↓              ↓              ↓              ↓
5-min Sync    Direct Insert  Processed      Email          Interactive
Automation    (No S3 needed) Emails Table   Summaries      Analytics
```

**Benefits of Native Approach:**
- ✅ **No external infrastructure** (S3, Lambda, etc.)
- ✅ **Built-in authentication** (no secrets.toml in production)
- ✅ **Cost efficient** (only warehouse compute)
- ✅ **Enterprise security** (native Snowflake)

## 🛠️ Quick Start

### 1. Database Setup
```bash
# Deploy core Snowflake objects
snowsql -f setup/01_database_setup.sql
snowsql -f cortex/03_ai_summarization.sql
snowsql -f automation/stream_task_automation.sql
```

### 2. Demo Setup (Immediate)
```bash
cd streamlit
pip install -r requirements.txt

# Configure Snowflake credentials in .streamlit/secrets.toml
streamlit run sample_email_app.py
```

### 3. Production Deployment (Streamlit-in-Snowflake)
```sql
-- Upload your Streamlit app
PUT file://sample_email_app.py @EMAIL_APP_STAGE;

-- Create native Streamlit app
CREATE STREAMLIT EMAIL_PROCESSING_APP
    ROOT_LOCATION = '@EMAIL_APP_STAGE'
    MAIN_FILE = 'sample_email_app.py'
    QUERY_WAREHOUSE = COMPUTE_WH;

-- Deploy Gmail API UDF (see production/gmail_sis_integration.md)
CREATE FUNCTION FETCH_GMAIL_EMAILS(domain STRING) ...;

-- Enable automation
ALTER TASK GMAIL_PROCESSING_TASK RESUME;
```

## 📧 Gmail Integration Methods

### 🎯 **Production (Recommended)**
- **Python UDF**: Gmail API calls inside Snowflake
- **Streamlit-in-Snowflake**: Native deployment
- **Task Automation**: Scheduled email fetching

### 🎬 **Demo (Current Implementation)**
- **Simulated Gmail**: Realistic email data
- **External Streamlit**: Local development
- **Manual Processing**: Interactive demo workflow

### 🔄 **Alternative Approaches**
- **IMAP Integration**: Direct Gmail IMAP access (no API setup)
- **Webhook Forwarding**: Real-time email forwarding to Snowflake
- **Email Simulation**: Realistic test data for demonstrations

## 🤖 AI Processing Features

### Cortex AI Functions Used
1. **SUMMARIZE**: Email content summarization
2. **SENTIMENT**: Emotional tone analysis
3. **CLASSIFY**: Urgency level detection

### Intelligent Processing
- **Priority Detection**: HIGH/MEDIUM/LOW urgency classification
- **Domain Filtering**: Focus on specific email domains (e.g., snowflake.com)
- **Real-time Analysis**: Immediate AI processing of new emails

## 📊 Demo Usage

### Current Demo Features
```bash
# Run the Gmail integration demo
cd streamlit
streamlit run sample_email_app.py

# Features available:
- Gmail API simulation with realistic emails
- Live Cortex AI processing
- Interactive dashboard with analytics
- Production architecture demonstration
```

### Demo Talk Track
> "This demonstrates Gmail API integration pulling emails from sagar.pawar@snowflake.com, filtering for snowflake.com domain emails, automatically detecting urgency levels, and processing everything with Cortex AI in real-time. In production, this same Streamlit app deploys natively to Snowflake with Python UDF Gmail integration and automated task scheduling."

## 🚀 Production Deployment

### Streamlit-in-Snowflake Approach
```sql
-- 1. Deploy Gmail UDF
CREATE FUNCTION FETCH_GMAIL_EMAILS(domain STRING)
RETURNS ARRAY
LANGUAGE PYTHON
RUNTIME_VERSION = '3.9'
PACKAGES = ('google-api-python-client')
HANDLER = 'gmail_fetch_handler'
AS $$ ... $$;

-- 2. Deploy Streamlit app
PUT file://sample_email_app.py @EMAIL_APP_STAGE;
CREATE STREAMLIT EMAIL_PROCESSING_APP
    ROOT_LOCATION = '@EMAIL_APP_STAGE'
    MAIN_FILE = 'sample_email_app.py';

-- 3. Automate email fetching
CREATE TASK GMAIL_AUTOMATION
    SCHEDULE = 'USING CRON 0 */5 * * * UTC'
AS SELECT FETCH_GMAIL_EMAILS('snowflake.com');
```

### Production Benefits
- ✅ **Same code** as demo (no rewrite needed)
- ✅ **Enterprise authentication** (built-in Snowflake SSO)
- ✅ **Auto-scaling compute** (warehouse management)
- ✅ **Zero external infrastructure** (no S3, Lambda, containers)

## 📁 Repository Structure

```
email_processing_app/
├── streamlit/
│   ├── sample_email_app.py          # Main demo application
│   ├── simple_monitoring_app.py     # System monitoring dashboard
│   └── requirements.txt             # Python dependencies
├── setup/
│   ├── 01_database_setup.sql        # Core database objects
│   └── 05_enhanced_email_parsing.sql # Email processing functions
├── cortex/
│   └── 03_ai_summarization.sql      # Cortex AI functions
├── automation/
│   ├── stream_task_automation.sql   # Automated processing tasks
│   └── 04_automation_setup.sql      # Task scheduling setup
├── email_sources/
│   ├── gmail_connector.py           # Production Gmail integration
│   ├── gmail_workarounds.py         # Demo Gmail implementation
│   └── gmail_config.json           # Gmail API configuration
├── production/
│   ├── gmail_sis_integration.md     # Production deployment guide
│   ├── streamlit_native_approach.md # Why Streamlit > SPCS
│   └── production_ready_app.py      # Production app template
└── sample_data/
    ├── gmail_demo_1.json           # Sample Gmail format emails
    ├── gmail_demo_2.json
    └── gmail_demo_3.json
```

## 🔍 Why Native Snowflake Over S3?

### ✅ **Native Snowflake Advantages:**
- **Simpler**: No external storage management
- **Cheaper**: Only warehouse compute costs
- **Faster**: Direct table access, no staging delays  
- **Secure**: Everything stays in Snowflake ecosystem

### ❌ **S3 Approach Drawbacks:**
- **Complex**: S3 + Snowpipe + IAM roles + SQS
- **Expensive**: Storage + transfer + compute costs
- **Slower**: File upload → event → processing lag
- **More failure points**: External dependencies

**Result**: Native approach is optimal for email processing workflows.

## 🚨 Troubleshooting

### Common Issues

1. **Connection Timeout**
   - App auto-refreshes expired Snowflake connections
   - Clear Streamlit cache if needed: `st.cache_resource.clear()`

2. **Gmail Integration**
   - **Demo**: Uses realistic email simulation
   - **Production**: Requires Gmail API UDF deployment
   - **Alternative**: IMAP integration available

3. **Cortex AI Processing**
   - Ensure Cortex AI is enabled in your Snowflake account
   - Check token usage limits for your account tier

## 🎯 Demo Instructions

### Run the Demo
```bash
# Navigate to project
cd email_processing_app/streamlit

# Install dependencies
pip install -r requirements.txt

# Configure Snowflake credentials in .streamlit/secrets.toml
# Run the app
streamlit run sample_email_app.py
```

### Demo Features
- **Gmail API Simulation**: Realistic email processing workflow
- **Live Cortex AI**: Real AI summarization and sentiment analysis
- **Interactive Dashboard**: Process emails and view results instantly
- **Production Preview**: Shows exactly what production deployment looks like

## 📈 Future Enhancements

- **Real Gmail API**: Production Python UDF integration
- **Advanced Analytics**: Email trend analysis and insights
- **Multi-domain Support**: Process emails from multiple domains
- **Alert Notifications**: Slack/Teams integration for urgent emails
- **Email Response AI**: Cortex-powered email drafting assistance

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch  
3. Test changes with the demo app
4. Submit pull request with demo screenshots

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- **Demo Issues**: Check Streamlit app logs and Snowflake connection
- **Production Questions**: See `production/gmail_sis_integration.md`
- **Architecture Questions**: See `production/why_streamlit_not_spcs.md`

---

**🎯 Perfect for demonstrating Gmail integration with Snowflake Cortex AI!** ✅