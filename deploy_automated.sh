#!/bin/bash

# Automated Email Processing Pipeline Deployment Script
# Deploys complete real-time automation on top of existing foundation

set -e

echo "🚀 Starting Automated Email Processing Pipeline Deployment..."

# Check if snowsql is available
if ! command -v snowsql &> /dev/null; then
    echo "❌ snowsql CLI not found. Please install Snowflake CLI first."
    echo "   Visit: https://docs.snowflake.com/en/user-guide/snowsql-install-config.html"
    exit 1
fi

# Configuration
DEFAULT_CONNECTION="dev"
DEFAULT_WAREHOUSE="COMPUTE_WH"

# Get connection and warehouse from user or use defaults
read -p "Enter Snowflake connection name [$DEFAULT_CONNECTION]: " CONNECTION
CONNECTION=${CONNECTION:-$DEFAULT_CONNECTION}

read -p "Enter warehouse name [$DEFAULT_WAREHOUSE]: " WAREHOUSE
WAREHOUSE=${WAREHOUSE:-$DEFAULT_WAREHOUSE}

echo "📋 Using connection: $CONNECTION, warehouse: $WAREHOUSE"

# Function to execute SQL file
execute_sql() {
    local file=$1
    local description=$2
    
    echo "📝 $description..."
    if snowsql -c "$CONNECTION" -w "$WAREHOUSE" -f "$file"; then
        echo "✅ $description completed successfully"
    else
        echo "❌ $description failed"
        exit 1
    fi
}

echo "🏗️  Deploying Real-Time Automation Components..."

# Step 1: Deploy real-time ingestion (Snowpipe + Notifications)
echo "📡 Setting up real-time ingestion..."
execute_sql "automation/real_time_ingestion.sql" "Configuring Snowpipe and S3 notifications"

# Step 2: Deploy stream and task automation
echo "🔄 Setting up stream processing..."
execute_sql "automation/stream_task_automation.sql" "Creating streams and automated tasks"

# Step 3: Deploy simple monitoring
echo "📊 Setting up simple monitoring..."
execute_sql "monitoring/simple_monitoring.sql" "Configuring basic monitoring system"

# Configuration prompts
echo ""
echo "🔧 Configuration Required:"
echo ""

# S3 Configuration
echo "📦 S3 Configuration:"
read -p "Enter your S3 bucket name for email files: " S3_BUCKET
read -p "Enter AWS region [us-east-1]: " AWS_REGION
AWS_REGION=${AWS_REGION:-us-east-1}

# Update configuration files
echo "📝 Updating configuration files..."

# Update Gmail config with user inputs
sed -i.bak "s/your-email-processing-bucket/$S3_BUCKET/g" "email_sources/gmail_config.json"
sed -i.bak "s/us-east-1/$AWS_REGION/g" "email_sources/gmail_config.json"

# Email source configuration
echo ""
echo "📧 Email Source Configuration:"
read -p "Enter target domain(s) to monitor (comma separated) [company.com]: " TARGET_DOMAINS
TARGET_DOMAINS=${TARGET_DOMAINS:-company.com}

read -p "Enter max emails per run [50]: " MAX_EMAILS
MAX_EMAILS=${MAX_EMAILS:-50}

# Update Gmail config with email settings
cat > temp_config.json << EOF
{
  "target_domains": ["$(echo $TARGET_DOMAINS | sed 's/,/","/g')"],
  "max_emails_per_run": $MAX_EMAILS,
  "processing_interval_minutes": 5,
  "s3_bucket": "$S3_BUCKET",
  "aws_region": "$AWS_REGION",
  "snowflake_user": "SPAWAR",
  "snowflake_account": "SFSEAPAC-SPAWAR_AWSEAST1",
  "snowflake_warehouse": "COMPUTE_WH",
  "email_filters": {
    "include_keywords": ["budget", "meeting", "urgent", "action", "deadline"],
    "exclude_keywords": ["spam", "newsletter", "unsubscribe"],
    "date_range_days": 30,
    "include_attachments": true
  },
  "processing_options": {
    "enable_urgent_alerts": true,
    "enable_duplicate_detection": true,
    "max_content_length": 50000,
    "enable_sentiment_analysis": true,
    "enable_entity_extraction": false
  },
  "monitoring": {
    "enable_metrics_logging": true,
    "alert_thresholds": {
      "processing_latency_seconds": 300,
      "error_rate_percentage": 5,
      "queue_depth": 100
    }
  }
}
EOF

mv temp_config.json email_sources/gmail_config.json

# Install Python dependencies for automation
echo "📦 Installing Python dependencies..."
cd email_sources
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client boto3
cd ..

# Generate AWS setup instructions
echo ""
echo "🎉 Automated Pipeline Deployment Complete!"
echo ""
echo "📋 Next Steps Required:"
echo ""
echo "1. 📧 Gmail API Setup:"
echo "   - Go to: https://console.cloud.google.com/"
echo "   - Enable Gmail API"
echo "   - Create OAuth 2.0 credentials"
echo "   - Download credentials.json to email_sources/ folder"
echo ""
echo "2. 🛡️ AWS S3 Setup:"
echo "   - Create S3 bucket: $S3_BUCKET"
echo "   - Configure S3 Event Notifications → SQS"
echo "   - Get SQS ARN from: DESCRIBE NOTIFICATION INTEGRATION EMAIL_S3_NOTIFICATION;"
echo ""
echo "3. ⚡ Enable Real-Time Processing:"
echo "   snowsql -c $CONNECTION -q \"CALL MANAGE_AUTOMATION_TASKS('RESUME', 'ALL')\""
echo ""
echo "4. 🧪 Test Gmail Connector:"
echo "   cd email_sources"
echo "   python gmail_connector.py"
echo ""
echo "5. 📊 Launch Monitoring Dashboard:"
echo "   cd streamlit"
echo "   streamlit run realtime_monitoring_app.py"
echo ""
echo "📈 What You Now Have:"
echo "   ✅ Real-time S3 ingestion (Snowpipe)"
echo "   ✅ Stream-based processing (1-minute latency)"
echo "   ✅ Automated AI analysis"
echo "   ✅ Urgent email detection"
echo "   ✅ Gmail API connector"
echo "   ✅ Simple monitoring dashboard"
echo "   ✅ Basic error tracking"
echo ""
echo "🎯 Pipeline Flow:"
echo "   Gmail → Python Connector → S3 Upload → Snowpipe → Streams → Tasks → AI Analysis → Alerts"
echo ""
echo "💰 Token Usage:"
echo "   - Real-time processing: ~2-3 tokens per email"
echo "   - Batch optimization available for cost savings"
echo ""
echo "📚 Documentation:"
echo "   - README.md: Complete usage guide"
echo "   - monitoring/: SQL monitoring queries"
echo "   - email_sources/: Gmail connector and config"
echo ""
echo "Happy automated email processing! 📧🤖⚡"
