#!/bin/bash

# Minimal Email Processing App Deployment - Core Only
# This script deploys only the essential components for testing with minimal token usage

set -e

echo "🚀 Starting Minimal Email Processing App Deployment..."

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

# Deploy ONLY core components (no automation)
echo "🏗️  Deploying core database structure..."
execute_sql "setup/01_database_setup.sql" "Creating database, schemas, and tables"

echo "🗄️  Setting up basic staging..."
execute_sql "setup/02_staging_setup.sql" "Configuring internal stages only"

echo "🤖 Installing minimal AI functions..."
execute_sql "cortex/03_ai_summarization.sql" "Setting up AI summarization capabilities"

echo "🔧 Installing email parsing..."
execute_sql "setup/05_enhanced_email_parsing.sql" "Configuring email format support"

echo "🧪 Running single email test..."
execute_sql "minimal_test.sql" "Testing with one email to verify AI functionality"

echo ""
echo "🎉 Minimal deployment completed successfully!"
echo ""
echo "✅ What was deployed:"
echo "   ✓ Core database structure"
echo "   ✓ Basic email parsing"
echo "   ✓ AI summarization functions"
echo "   ✓ One test email processed"
echo ""
echo "❌ What was NOT deployed (to save tokens):"
echo "   ✗ Automation tasks"
echo "   ✗ Batch processing"
echo "   ✗ Real-time streaming"
echo ""
echo "🔍 Check your results in Snowflake:"
echo "   SELECT * FROM EMAIL_PROCESSING_OVERVIEW;"
echo ""
echo "📧 To process more emails manually:"
echo "   CALL ANALYZE_EMAIL_WITH_AI('email_id_here');"
