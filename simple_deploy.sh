#!/bin/bash

# Simple Email Processing App Deployment
# This script deploys using direct credentials (no named connections needed)

set -e

echo "🚀 Starting Simple Email Processing App Deployment..."

# Get credentials
echo "Please provide your Snowflake credentials:"
read -p "Account [SFSEAPAC-SPAWAR_AWSEAST1]: " ACCOUNT
ACCOUNT=${ACCOUNT:-SFSEAPAC-SPAWAR_AWSEAST1}

read -p "Username [SPAWAR]: " USERNAME
USERNAME=${USERNAME:-SPAWAR}

read -s -p "Password: " PASSWORD
echo ""

read -p "Warehouse [COMPUTE_WH]: " WAREHOUSE
WAREHOUSE=${WAREHOUSE:-COMPUTE_WH}

echo "📋 Using Account: $ACCOUNT, User: $USERNAME, Warehouse: $WAREHOUSE"

# Function to execute SQL file with direct credentials
execute_sql() {
    local file=$1
    local description=$2
    
    echo "📝 $description..."
    if snowsql -a "$ACCOUNT" -u "$USERNAME" -w "$WAREHOUSE" -f "$file" <<< "$PASSWORD"; then
        echo "✅ $description completed successfully"
    else
        echo "❌ $description failed"
        exit 1
    fi
}

# Deploy core components
echo "🏗️  Deploying core database structure..."
execute_sql "setup/01_database_setup.sql" "Creating database, schemas, and tables"

echo "🗄️  Setting up basic staging..."
execute_sql "setup/02_staging_setup.sql" "Configuring internal stages"

echo "🤖 Installing AI functions..."
execute_sql "cortex/03_ai_summarization.sql" "Setting up AI summarization capabilities"

echo "🔧 Installing email parsing..."
execute_sql "setup/05_enhanced_email_parsing.sql" "Configuring email format support"

echo "🧪 Running single email test..."
execute_sql "minimal_test.sql" "Testing with one email to verify AI functionality"

echo ""
echo "🎉 Simple deployment completed successfully!"
echo ""
echo "✅ What was deployed:"
echo "   ✓ Core database structure"
echo "   ✓ Email parsing functions"
echo "   ✓ AI summarization capabilities"
echo "   ✓ One test email processed"
echo ""
echo "🔍 Next steps:"
echo "   1. cd streamlit"
echo "   2. streamlit run minimal_app.py"
echo ""
echo "📧 Check your results in Snowflake:"
echo "   SELECT * FROM EMAIL_PROCESSING_OVERVIEW;"
