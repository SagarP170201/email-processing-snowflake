#!/bin/bash

# Email Processing App Deployment Script
# This script deploys the complete email processing application to Snowflake

set -e

echo "🚀 Starting Email Processing App Deployment..."

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

# Deploy core components
echo "🏗️  Deploying core database structure..."
execute_sql "setup/01_database_setup.sql" "Creating database, schemas, and tables"

echo "🗄️  Setting up staging areas..."
execute_sql "setup/02_staging_setup.sql" "Configuring S3 and internal stages"

echo "🤖 Installing Cortex AI functions..."
execute_sql "cortex/03_ai_summarization.sql" "Setting up AI summarization capabilities"

echo "🔧 Installing enhanced email parsing..."
execute_sql "setup/05_enhanced_email_parsing.sql" "Configuring advanced email format support"

echo "⏰ Setting up automation (optional)..."
read -p "Do you want to enable automation tasks? (y/N): " ENABLE_AUTOMATION
if [[ $ENABLE_AUTOMATION =~ ^[Yy]$ ]]; then
    execute_sql "automation/04_automation_setup.sql" "Configuring automated workflows"
    echo "✅ Automation enabled. Remember to configure warehouse settings for tasks."
else
    echo "⏭️  Skipping automation setup"
fi

# Test deployment with sample data
echo "🧪 Testing deployment with sample data..."
read -p "Do you want to load sample emails for testing? (y/N): " LOAD_SAMPLES
if [[ $LOAD_SAMPLES =~ ^[Yy]$ ]]; then
    echo "📧 Loading sample email data..."
    
    # Create temporary SQL script for sample data
    cat > temp_sample_load.sql << 'EOF'
USE DATABASE EMAIL_PROCESSING_APP;
USE SCHEMA CORE;

-- Load sample emails
INSERT INTO RAW_EMAIL_FILES (file_name, file_path, file_content, processing_status)
VALUES 
    ('sample_email_1.json', '@EMAIL_INTERNAL_STAGE/sample_email_1.json', 
     PARSE_JSON($${
       "email_type": "gmail_api",
       "payload": {
         "headers": [
           {"name": "From", "value": "john.smith@company.com"},
           {"name": "To", "value": "team@company.com"},
           {"name": "Subject", "value": "Q4 Budget Planning Meeting - Action Required"}
         ],
         "parts": [{"body": {"data": "Hi Team, I hope this email finds you well. I'm writing to schedule our Q4 budget planning meeting..."}}]
       },
       "internalDate": "1700083800000"
     }$$), 'PENDING'),
    ('sample_email_2.json', '@EMAIL_INTERNAL_STAGE/sample_email_2.json',
     PARSE_JSON($${
       "email_type": "simple_format",
       "sender": "sarah.johnson@clientcorp.com",
       "subject": "Urgent: System Outage Affecting Production",
       "email_text": "Dear Support Team, We are experiencing a critical system outage..."
     }$$), 'PENDING');

-- Process the sample emails
CALL BATCH_PROCESS_EMAILS(10, '.*');

-- Generate AI summaries
CALL BATCH_ANALYZE_EMAILS(10, 'ALL');

-- Display results
SELECT 'Sample data loaded and processed successfully' as status;
SELECT * FROM EMAIL_PROCESSING_OVERVIEW LIMIT 5;
EOF

    execute_sql "temp_sample_load.sql" "Loading and processing sample data"
    rm temp_sample_load.sql
    
    echo "✅ Sample data loaded and processed successfully"
else
    echo "⏭️  Skipping sample data loading"
fi

# Deployment verification
echo "🔍 Verifying deployment..."
cat > temp_verification.sql << 'EOF'
USE DATABASE EMAIL_PROCESSING_APP;
USE SCHEMA CORE;

-- Check tables
SELECT 'Tables created:' as check_type, COUNT(*) as count FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = 'CORE' AND TABLE_CATALOG = 'EMAIL_PROCESSING_APP';

-- Check procedures
SELECT 'Procedures created:' as check_type, COUNT(*) as count FROM INFORMATION_SCHEMA.PROCEDURES 
WHERE PROCEDURE_SCHEMA = 'CORE' AND PROCEDURE_CATALOG = 'EMAIL_PROCESSING_APP';

-- Check functions
SELECT 'Functions created:' as check_type, COUNT(*) as count FROM INFORMATION_SCHEMA.FUNCTIONS 
WHERE FUNCTION_SCHEMA = 'CORE' AND FUNCTION_CATALOG = 'EMAIL_PROCESSING_APP';

-- Check views
SELECT 'Views created:' as check_type, COUNT(*) as count FROM INFORMATION_SCHEMA.VIEWS 
WHERE TABLE_SCHEMA = 'CORE' AND TABLE_CATALOG = 'EMAIL_PROCESSING_APP';

-- Show processing stats
SELECT * FROM EMAIL_PROCESSING_STATS;
EOF

execute_sql "temp_verification.sql" "Verifying deployment"
rm temp_verification.sql

echo ""
echo "🎉 Email Processing App deployment completed successfully!"
echo ""
echo "📋 Next Steps:"
echo "   1. Configure your S3 credentials in the EMAIL_S3_STAGE"
echo "   2. Update Streamlit secrets.toml with your Snowflake credentials"
echo "   3. Start the Streamlit app: cd streamlit && streamlit run app.py"
echo "   4. Upload email files to test the processing pipeline"
echo ""
echo "📚 Documentation:"
echo "   - README.md: Complete usage guide"
echo "   - docs/sharepoint_connector_analysis.md: SharePoint connector analysis"
echo "   - sample_data/: Example email files for testing"
echo ""
echo "🔗 Useful Commands:"
echo "   - List stages: SHOW STAGES IN EMAIL_PROCESSING_APP.CORE;"
echo "   - Check processing: SELECT * FROM EMAIL_PROCESSING_OVERVIEW;"
echo "   - Monitor jobs: SELECT * FROM PROCESSING_JOBS ORDER BY start_time DESC;"
echo ""
echo "Happy email processing! 📧✨"
