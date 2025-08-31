# 🚀 Demo → Production Extension: Gmail API Integration
# This shows how your existing sample_email_app.py extends to production

import streamlit as st
import pandas as pd
import json
from datetime import datetime

# Snowflake connection (works in both external and SiS)
if 'snowflake' in st.secrets:
    # External Streamlit (current demo)
    import snowflake.connector
    
    @st.cache_resource
    def init_connection():
        return snowflake.connector.connect(
            account=st.secrets["snowflake"]["account"],
            user=st.secrets["snowflake"]["user"],
            password=st.secrets["snowflake"]["password"],
            warehouse=st.secrets["snowflake"]["warehouse"],
            database=st.secrets["snowflake"]["database"],
            schema=st.secrets["snowflake"]["schema"]
        )
    
    def run_query(query, params=None):
        conn = init_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()

else:
    # Streamlit-in-Snowflake (production)
    def run_query(query, params=None):
        return st.connection("snowflake").query(query, params=params)

# =============================================================================
# 📧 GMAIL INTEGRATION LOGIC
# =============================================================================

def fetch_gmail_emails_production(domain="snowflake.com", max_emails=50):
    """
    Production Gmail fetching using Snowflake Python UDF
    """
    try:
        # Call Gmail UDF directly in Snowflake
        result = run_query(f"""
            SELECT FETCH_GMAIL_EMAILS('{domain}', {max_emails}) as gmail_emails
        """)
        
        if result and len(result) > 0:
            return json.loads(result[0][0])
        return []
        
    except Exception as e:
        st.error(f"Gmail API error: {str(e)}")
        return []

def fetch_gmail_emails_demo():
    """
    Demo simulation with realistic Gmail data
    """
    return [
        {
            "id": "gmail_prod_demo_1",
            "sender": "alerts@snowflake.com",
            "subject": "🚨 URGENT: Production Database Performance Alert",
            "body": "Critical performance degradation detected in PROD_DB. Query latency increased by 300%. Immediate attention required. Affected warehouses: LARGE_WH, XLARGE_WH. Impact: Customer-facing analytics dashboard.",
            "timestamp": datetime.now().isoformat(),
            "labels": ["INBOX", "IMPORTANT"],
            "source": "gmail_api_production_demo"
        },
        {
            "id": "gmail_prod_demo_2", 
            "sender": "security@snowflake.com",
            "subject": "Security Audit Completion - Q4 2024",
            "body": "Q4 security audit has been completed. Summary: 15 vulnerabilities identified, 12 resolved, 3 pending. Action items: Update access controls, review IAM policies, implement additional monitoring. Full report attached.",
            "timestamp": datetime.now().isoformat(),
            "labels": ["INBOX"],
            "source": "gmail_api_production_demo"
        }
    ]

# =============================================================================
# 🎯 PRODUCTION-READY STREAMLIT APP
# =============================================================================

def main():
    st.title("📧 Email Processing Dashboard")
    
    # =================================================================
    # 🔧 GMAIL INTEGRATION SECTION
    # =================================================================
    
    st.header("📬 Gmail Integration")
    
    # Production vs Demo mode detection
    is_production = False
    try:
        # Try to call Gmail UDF (will fail in demo)
        run_query("SELECT CURRENT_USER()")  # Test connection
        test_udf = run_query("SHOW FUNCTIONS LIKE 'FETCH_GMAIL_EMAILS'")
        is_production = len(test_udf) > 0
    except:
        is_production = False
    
    if is_production:
        st.success("🚀 **PRODUCTION MODE**: Gmail API UDF detected")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            target_domain = st.selectbox(
                "Target Domain", 
                ["snowflake.com", "company.com", "all"]
            )
        
        with col2:
            max_emails = st.slider("Max Emails", 10, 100, 50)
        
        with col3:
            if st.button("🔄 Sync Gmail"):
                with st.spinner("Fetching from Gmail API..."):
                    # Production Gmail fetch
                    emails = fetch_gmail_emails_production(target_domain, max_emails)
                    
                    # Insert into pipeline
                    for email in emails:
                        run_query("""
                            INSERT INTO RAW_EMAIL_FILES (
                                file_name, file_content, processing_status
                            ) VALUES (?, ?, 'PENDING')
                        """, [f"gmail_{email['id']}.json", json.dumps(email)])
                    
                    st.success(f"✅ Processed {len(emails)} emails from Gmail!")
                    st.rerun()  # Refresh dashboard
    
    else:
        st.info("🎬 **DEMO MODE**: Simulating Gmail API integration")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write("**Simulated Gmail Source**: sagar.pawar@snowflake.com")
            st.write("**Target Domain**: snowflake.com")
        
        with col2:
            if st.button("🎬 Demo Gmail Sync"):
                with st.spinner("Simulating Gmail fetch..."):
                    # Demo Gmail simulation
                    emails = fetch_gmail_emails_demo()
                    
                    # Insert into pipeline (same code as production!)
                    for email in emails:
                        run_query("""
                            INSERT INTO RAW_EMAIL_FILES (
                                file_name, file_content, processing_status
                            ) VALUES (?, ?, 'PENDING')
                        """, [f"gmail_{email['id']}.json", json.dumps(email)])
                    
                    st.success(f"🎬 Demo: Processed {len(emails)} simulated emails!")
                    st.rerun()
    
    # =================================================================
    # 📊 ANALYTICS SECTION (Same for Demo + Production)
    # =================================================================
    
    st.header("📊 Email Analytics")
    
    # Recent emails
    recent_emails = run_query("""
        SELECT 
            sender,
            subject,
            ai_summary,
            urgency_level,
            created_timestamp
        FROM EMAIL_SUMMARIES 
        ORDER BY created_timestamp DESC 
        LIMIT 20
    """)
    
    if recent_emails:
        df = pd.DataFrame(
            recent_emails,
            columns=['Sender', 'Subject', 'AI Summary', 'Urgency', 'Timestamp']
        )
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No processed emails yet. Click 'Sync Gmail' or process sample emails.")
    
    # =================================================================
    # 🎯 AUTOMATION STATUS
    # =================================================================
    
    st.header("🤖 Automation Status")
    
    if is_production:
        # Production automation status
        tasks = run_query("""
            SELECT 
                name,
                state,
                last_committed_on,
                next_scheduled_time
            FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
            WHERE name LIKE '%EMAIL%'
            ORDER BY last_committed_on DESC
            LIMIT 5
        """)
        
        if tasks:
            st.subheader("🔄 Active Tasks")
            task_df = pd.DataFrame(
                tasks,
                columns=['Task', 'State', 'Last Run', 'Next Run']
            )
            st.dataframe(task_df)
        
        # Gmail sync status
        st.subheader("📧 Gmail Sync Status")
        last_sync = run_query("""
            SELECT MAX(upload_timestamp) as last_gmail_sync
            FROM RAW_EMAIL_FILES
            WHERE file_name LIKE 'gmail_%'
        """)
        
        if last_sync and last_sync[0][0]:
            st.success(f"✅ Last Gmail sync: {last_sync[0][0]}")
        else:
            st.warning("⚠️ No Gmail syncs detected")
    
    else:
        # Demo automation simulation
        st.info("""
        🎬 **Demo Automation Simulation**
        
        **Production would show:**
        - ✅ Gmail API sync task (every 5 minutes)
        - ✅ Email processing stream (real-time)
        - ✅ AI analysis task (1-minute lag)
        - ✅ Urgent alert monitoring (real-time)
        
        **Current demo**: Manual sync with realistic Gmail data
        """)

if __name__ == "__main__":
    main()

# =============================================================================
# 📋 PRODUCTION DEPLOYMENT NOTES
# =============================================================================

"""
🚀 PRODUCTION DEPLOYMENT STEPS:

1. **Upload App to Snowflake**:
   PUT file://demo_to_production_extension.py @EMAIL_APP_STAGE;

2. **Create Streamlit App**:
   CREATE STREAMLIT EMAIL_PROCESSING_APP
       ROOT_LOCATION = '@EMAIL_APP_STAGE'
       MAIN_FILE = 'demo_to_production_extension.py';

3. **Deploy Gmail UDF**:
   -- Upload credentials
   PUT file://gmail_service_account.json @EMAIL_APP_STAGE;
   
   -- Create UDF (see gmail_sis_integration.md)
   CREATE FUNCTION FETCH_GMAIL_EMAILS(...);

4. **Enable Automation**:
   ALTER TASK PRODUCTION_EMAIL_PIPELINE RESUME;

🎯 Result: Same UI, production Gmail integration, full automation!
"""
