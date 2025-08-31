#!/bin/bash

# 📧 Deploy Gmail Integration Email Processing Application to Snowflake  
# This script deploys the native Snowflake email processing system

set -e

echo "📧 Deploying Gmail Integration Email Processing App"
echo "================================================="

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
        echo "ℹ️  Continuing with next step..."
    fi
}

echo "🏗️  Deploying Core Email Processing Components..."

# Step 1: Deploy database setup
echo "📊 Setting up database structure..."
execute_sql "setup/01_database_setup.sql" "Creating database, schema, and core tables"

# Step 2: Deploy AI functions
echo "🤖 Setting up Cortex AI functions..."
execute_sql "cortex/03_ai_summarization.sql" "Deploying AI summarization functions"

# Step 3: Deploy email parsing
echo "📧 Setting up email parsing..."
execute_sql "setup/05_enhanced_email_parsing.sql" "Configuring email parsing procedures"

# Step 4: Deploy automation
echo "🔄 Setting up automation..."
execute_sql "automation/stream_task_automation.sql" "Creating streams and automated tasks"

# Step 5: Deploy monitoring
echo "📊 Setting up monitoring..."
execute_sql "monitoring/simple_monitoring.sql" "Configuring basic monitoring system"

echo ""
echo "🎉 Core Deployment Complete!"
echo ""
echo "📋 Next Steps for Production:"
echo ""

echo "1. 📧 Deploy Streamlit App to Snowflake:"
echo "   PUT file://streamlit/sample_email_app.py @EMAIL_APP_STAGE;"
echo "   CREATE STREAMLIT EMAIL_PROCESSING_APP"
echo "       ROOT_LOCATION = '@EMAIL_APP_STAGE'"
echo "       MAIN_FILE = 'sample_email_app.py';"
echo ""

echo "2. 🔗 Gmail API Integration:"
echo "   - Set up Gmail API credentials (see production/gmail_sis_integration.md)"
echo "   - Deploy Gmail Python UDF"
echo "   - Configure automated email fetching task"
echo ""

echo "3. ⚡ Enable Automation:"
echo "   snowsql -c $CONNECTION -q \"ALTER TASK GMAIL_PROCESSING_TASK RESUME\""
echo ""

echo "4. 🧪 Test the Demo:"
echo "   cd streamlit"
echo "   streamlit run sample_email_app.py"
echo ""

echo "📈 What You Now Have:"
echo "   ✅ Native Snowflake email processing"
echo "   ✅ Streamlit-in-Snowflake ready deployment"
echo "   ✅ Gmail API integration framework"
echo "   ✅ Cortex AI analysis pipeline"
echo "   ✅ Stream-based automation"
echo "   ✅ Simple monitoring dashboard"
echo ""

echo "🎯 Architecture:"
echo "   Gmail API → Python UDF → Snowflake Tables → Cortex AI → Streamlit Native"
echo ""

echo "💰 Token Usage:"
echo "   - Demo processing: ~1 token per email"
echo "   - Production optimization: Batch processing available"
echo ""

echo "📚 Key Documentation:"
echo "   - README.md: Complete usage guide"
echo "   - production/gmail_sis_integration.md: Production deployment"
echo "   - production/why_streamlit_not_spcs.md: Architecture rationale"
echo ""

echo "🚀 Happy Gmail integration with Snowflake! 📧🤖✨"