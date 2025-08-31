# 🚀 Production-Ready Email Processing App
# This is your sample_email_app.py extended for Gmail API integration

import streamlit as st
import pandas as pd
import json
from datetime import datetime

# =============================================================================
# 🔧 ENVIRONMENT DETECTION & CONNECTION SETUP
# =============================================================================

def detect_environment():
    """Detect if running in Streamlit-in-Snowflake or external"""
    try:
        # Check if we have native Snowflake connection
        conn = st.connection("snowflake")
        return "SiS"  # Streamlit-in-Snowflake
    except:
        return "External"  # External Streamlit

def setup_connection():
    """Setup connection based on environment"""
    env = detect_environment()
    
    if env == "SiS":
        # Streamlit-in-Snowflake (Production)
        return lambda query, params=None: st.connection("snowflake").query(query, params=params)
    
    else:
        # External Streamlit (Demo)
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
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
            finally:
                cursor.close()
        
        return run_query

# Initialize query function
run_query = setup_connection()
environment = detect_environment()

# =============================================================================
# 📧 GMAIL INTEGRATION FUNCTIONS
# =============================================================================

def check_gmail_udf_exists():
    """Check if Gmail UDF is deployed in production"""
    try:
        result = run_query("SHOW FUNCTIONS LIKE 'FETCH_GMAIL_EMAILS'")
        return len(result) > 0
    except:
        return False

def fetch_production_emails(domain="snowflake.com", max_emails=50):
    """Fetch emails using production Gmail UDF"""
    try:
        # Call the Gmail UDF
        result = run_query(f"""
            SELECT FETCH_GMAIL_EMAILS('{domain}', {max_emails}) as gmail_data
        """)
        
        if result and len(result) > 0:
            emails = json.loads(result[0][0]) if isinstance(result[0][0], str) else result[0][0]
            return emails if isinstance(emails, list) else [emails]
        
        return []
        
    except Exception as e:
        st.error(f"🚫 Gmail API Error: {str(e)}")
        return []

def simulate_gmail_fetch():
    """Demo simulation of Gmail API calls"""
    return [
        {
            "id": f"gmail_live_{datetime.now().strftime('%H%M%S')}",
            "sender": "john.doe@snowflake.com",
            "subject": "Q4 Budget Review - ACTION REQUIRED",
            "body": "Hi team, we need to finalize Q4 budget allocations. Key decisions: 1) Marketing spend increase (15%), 2) Engineering headcount (+8 FTE), 3) Infrastructure costs optimization. Meeting scheduled for Dec 15th. Please review attached spreadsheet and provide feedback by EOD.",
            "timestamp": datetime.now().isoformat(),
            "labels": ["INBOX", "IMPORTANT"],
            "source": "gmail_api_simulation",
            "domain": "snowflake.com"
        },
        {
            "id": f"gmail_urgent_{datetime.now().strftime('%H%M%S')}",
            "sender": "alerts@snowflake.com", 
            "subject": "🚨 CRITICAL: Production System Alert",
            "body": "URGENT: Production warehouse CRITICAL_WH experiencing high query queue times. Average wait: 45 seconds (SLA: <10s). Immediate investigation required. Impact: Customer dashboard loading delays. Auto-scaling initiated but manual review needed.",
            "timestamp": datetime.now().isoformat(),
            "labels": ["INBOX", "URGENT"],
            "source": "gmail_api_simulation",
            "domain": "snowflake.com"
        }
    ]

# =============================================================================
# 🎯 MAIN STREAMLIT APPLICATION
# =============================================================================

def main():
    st.title("📧 Email Processing Dashboard")
    
    # Environment indicator
    env_color = "🚀" if environment == "SiS" else "🎬"
    st.markdown(f"**{env_color} Running in {environment} Mode**")
    
    # =================================================================
    # 📬 GMAIL INTEGRATION SECTION
    # =================================================================
    
    st.header("📬 Gmail Integration")
    
    # Check production capabilities
    has_gmail_udf = check_gmail_udf_exists() if environment == "SiS" else False
    
    if environment == "SiS" and has_gmail_udf:
        # 🚀 PRODUCTION MODE
        st.success("✅ **PRODUCTION**: Gmail API UDF ready")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            target_domain = st.selectbox(
                "📧 Target Domain", 
                ["snowflake.com", "all"],
                help="Domain to fetch emails from"
            )
        
        with col2:
            max_emails = st.slider(
                "📊 Max Emails", 
                min_value=10, 
                max_value=100, 
                value=50,
                help="Maximum emails per sync"
            )
        
        with col3:
            st.write("")  # Spacing
            if st.button("🔄 **Sync Gmail**", type="primary"):
                with st.spinner("🔄 Fetching emails from Gmail API..."):
                    # Production Gmail integration
                    emails = fetch_production_emails(target_domain, max_emails)
                    
                    if emails:
                        # Insert into processing pipeline
                        success_count = 0
                        for email in emails:
                            try:
                                run_query("""
                                    INSERT INTO RAW_EMAIL_FILES (
                                        file_name, file_content, processing_status, upload_timestamp
                                    ) VALUES (%s, %s, 'PENDING', CURRENT_TIMESTAMP())
                                """, [f"gmail_{email['id']}.json", json.dumps(email)])
                                success_count += 1
                            except Exception as e:
                                st.warning(f"⚠️ Failed to process email {email['id']}: {str(e)}")
                        
                        st.success(f"✅ **Gmail Sync Complete**: {success_count}/{len(emails)} emails processed!")
                        
                        # Trigger processing
                        with st.spinner("🤖 Running AI analysis..."):
                            run_query("CALL PROCESS_PENDING_EMAILS()")
                        
                        st.rerun()  # Refresh dashboard
                    else:
                        st.warning("📭 No new emails found")
        
        # Show last sync status
        last_sync = run_query("""
            SELECT 
                COUNT(*) as gmail_emails,
                MAX(upload_timestamp) as last_sync
            FROM RAW_EMAIL_FILES 
            WHERE file_name LIKE 'gmail_%'
            AND upload_timestamp >= DATEADD('hour', -24, CURRENT_TIMESTAMP())
        """)
        
        if last_sync and last_sync[0][1]:
            st.info(f"📊 **Last 24h**: {last_sync[0][0]} Gmail emails | Last sync: {last_sync[0][1]}")
    
    else:
        # 🎬 DEMO MODE
        st.info("🎬 **DEMO MODE**: Simulating Gmail API integration")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("""
            **📧 Simulated Gmail Connection**
            - **Account**: sagar.pawar@snowflake.com  
            - **Domain Filter**: snowflake.com
            - **Sync Frequency**: Every 5 minutes (production)
            """)
        
        with col2:
            if st.button("🎬 **Demo Sync**", type="primary"):
                with st.spinner("🎬 Simulating Gmail API call..."):
                    # Demo Gmail simulation
                    emails = simulate_gmail_fetch()
                    
                    # Insert using same production code path
                    success_count = 0
                    for email in emails:
                        try:
                            run_query("""
                                INSERT INTO RAW_EMAIL_FILES (
                                    file_name, file_content, processing_status, upload_timestamp
                                ) VALUES (%s, %s, 'PENDING', CURRENT_TIMESTAMP())
                            """, [f"gmail_{email['id']}.json", json.dumps(email)])
                            success_count += 1
                        except Exception as e:
                            st.warning(f"⚠️ Demo error: {str(e)}")
                    
                    st.success(f"🎬 **Demo Complete**: {success_count} simulated emails processed!")
                    
                    # Trigger processing (same as production)
                    with st.spinner("🤖 Running AI analysis..."):
                        run_query("CALL PROCESS_PENDING_EMAILS()")
                    
                    st.rerun()
        
        # Production preview
        st.markdown("""
        **🚀 Production Would Show:**
        - ✅ Real Gmail API connection status
        - 📊 Actual sync metrics and timing
        - 🔄 Live task execution status
        - 🚨 Real-time alert monitoring
        """)
    
    # =================================================================
    # 📊 EMAIL ANALYTICS (SAME FOR DEMO + PRODUCTION)
    # =================================================================
    
    st.header("📊 Email Analytics Dashboard")
    
    # Fetch recent summaries
    try:
        summaries = run_query("""
            SELECT 
                sender,
                subject,
                ai_summary,
                urgency_level,
                sentiment_score,
                created_timestamp
            FROM EMAIL_SUMMARIES 
            ORDER BY created_timestamp DESC 
            LIMIT 15
        """)
        
        if summaries:
            df = pd.DataFrame(
                summaries,
                columns=['Sender', 'Subject', 'AI Summary', 'Urgency', 'Sentiment', 'Timestamp']
            )
            
            # Add urgency color coding
            def color_urgency(val):
                if val == 'HIGH':
                    return 'background-color: #ffcdd2'
                elif val == 'MEDIUM':
                    return 'background-color: #fff3e0'
                else:
                    return 'background-color: #e8f5e8'
            
            styled_df = df.style.applymap(color_urgency, subset=['Urgency'])
            st.dataframe(styled_df, use_container_width=True)
            
            # Quick stats
            st.subheader("📈 Quick Stats")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_emails = len(df)
                st.metric("📧 Total Emails", total_emails)
            
            with col2:
                urgent_emails = len(df[df['Urgency'] == 'HIGH'])
                st.metric("🚨 Urgent", urgent_emails, delta=urgent_emails-1 if urgent_emails > 0 else 0)
            
            with col3:
                avg_sentiment = df['Sentiment'].mean() if 'Sentiment' in df.columns else 0
                st.metric("😊 Avg Sentiment", f"{avg_sentiment:.2f}")
            
            with col4:
                recent_emails = len(df[pd.to_datetime(df['Timestamp']) >= pd.Timestamp.now() - pd.Timedelta(hours=1)])
                st.metric("⏰ Last Hour", recent_emails)
        
        else:
            st.info("📭 No processed emails yet. Use Gmail sync above to fetch emails.")
            
            # Show sample data option
            if st.button("📝 **Load Sample Data**"):
                # Your existing sample email processing code
                sample_emails = [
                    {
                        "id": "sample_1",
                        "sender": "demo@snowflake.com",
                        "subject": "Sample Email for Testing",
                        "body": "This is a sample email to test the Cortex AI functionality.",
                        "timestamp": datetime.now().isoformat()
                    }
                ]
                
                for email in sample_emails:
                    run_query("""
                        INSERT INTO RAW_EMAIL_FILES (
                            file_name, file_content, processing_status, upload_timestamp
                        ) VALUES (%s, %s, 'PENDING', CURRENT_TIMESTAMP())
                    """, [f"sample_{email['id']}.json", json.dumps(email)])
                
                # Process immediately
                run_query("CALL PROCESS_PENDING_EMAILS()")
                st.success("✅ Sample data loaded and processed!")
                st.rerun()
    
    except Exception as e:
        st.error(f"📊 Dashboard Error: {str(e)}")
    
    # =================================================================
    # 🤖 AUTOMATION MONITORING
    # =================================================================
    
    st.header("🤖 Automation Status")
    
    if environment == "SiS":
        # Production automation monitoring
        try:
            # Check task status
            task_status = run_query("""
                SELECT 
                    name,
                    state,
                    CASE 
                        WHEN state = 'STARTED' THEN '✅'
                        WHEN state = 'SUSPENDED' THEN '⏸️'
                        ELSE '❌'
                    END as status_icon,
                    last_committed_on,
                    next_scheduled_time
                FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY())
                WHERE name LIKE '%EMAIL%' OR name LIKE '%GMAIL%'
                ORDER BY last_committed_on DESC
                LIMIT 10
            """)
            
            if task_status:
                st.subheader("🔄 Active Email Tasks")
                task_df = pd.DataFrame(
                    task_status,
                    columns=['Task Name', 'State', 'Status', 'Last Run', 'Next Run']
                )
                st.dataframe(task_df, use_container_width=True)
            
            # Gmail sync health
            gmail_health = run_query("""
                SELECT 
                    COUNT(*) as emails_24h,
                    MAX(upload_timestamp) as last_gmail_sync,
                    COUNT(CASE WHEN processing_status = 'FAILED' THEN 1 END) as failed_emails
                FROM RAW_EMAIL_FILES
                WHERE file_name LIKE 'gmail_%'
                AND upload_timestamp >= DATEADD('hour', -24, CURRENT_TIMESTAMP())
            """)
            
            if gmail_health:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📧 Gmail Emails (24h)", gmail_health[0][0])
                with col2:
                    last_sync = gmail_health[0][1]
                    sync_status = "✅ Active" if last_sync else "⚠️ No sync"
                    st.metric("🔄 Last Sync", sync_status)
                with col3:
                    failed = gmail_health[0][2]
                    st.metric("❌ Failed", failed, delta=-failed if failed == 0 else None)
        
        except Exception as e:
            st.warning(f"⚠️ Automation monitoring unavailable: {str(e)}")
    
    else:
        # Demo automation simulation
        st.info("""
        🎬 **Demo Automation Simulation**
        
        **In Production (Streamlit-in-Snowflake):**
        - 🔄 **Gmail Sync Task**: `FETCH_GMAIL_EMAILS()` every 5 minutes
        - 📧 **Processing Stream**: Real-time email detection
        - 🤖 **AI Analysis Task**: Cortex AI processing (1-min cycles)
        - 🚨 **Alert Task**: Urgent email notifications
        - 📊 **This Dashboard**: Native in Snowflake with SSO auth
        
        **Current Demo**: Manual simulation with realistic data
        """)
        
        # Simulated metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🔄 Sync Status", "🎬 Demo Mode")
        with col2:
            st.metric("📧 Queue", "2 pending")
        with col3:
            st.metric("🤖 AI Status", "✅ Active")

# =============================================================================
# 🚀 MAIN APPLICATION
# =============================================================================

if __name__ == "__main__":
    st.set_page_config(
        page_title="Email Processing Dashboard",
        page_icon="📧",
        layout="wide"
    )
    
    # Sidebar with environment info
    st.sidebar.markdown(f"**🏗️ Environment**: {environment}")
    
    if environment == "SiS":
        st.sidebar.success("🚀 **Production Ready**")
        st.sidebar.markdown("""
        **Production Features:**
        - ✅ Native Snowflake auth
        - ✅ Gmail API UDF integration  
        - ✅ Automated task scheduling
        - ✅ Enterprise security
        - ✅ Auto-scaling compute
        """)
    else:
        st.sidebar.info("🎬 **Demo Mode**")
        st.sidebar.markdown("""
        **Demo Features:**
        - 🎬 Simulated Gmail API calls
        - 📊 Real Cortex AI analysis
        - 🔄 Manual trigger workflow
        - 📈 Live analytics dashboard
        """)
    
    # Run main app
    main()

# =============================================================================
# 📋 PRODUCTION DEPLOYMENT NOTES
# =============================================================================

"""
🚀 PRODUCTION DEPLOYMENT CHECKLIST:

□ 1. Upload Gmail credentials to Snowflake stage
□ 2. Deploy FETCH_GMAIL_EMAILS UDF  
□ 3. Upload this app file to Snowflake stage
□ 4. Create Streamlit app in Snowflake
□ 5. Create automated Gmail sync task
□ 6. Test Gmail API connectivity
□ 7. Enable task automation
□ 8. Configure monitoring alerts

🎯 RESULT: Same UI, production Gmail integration!

📧 GMAIL API FLOW IN PRODUCTION:
Snowflake Task → Python UDF → Gmail API → Email JSON → RAW_EMAIL_FILES → Streams → AI Analysis → Dashboard

✅ NO SPCS CONTAINERS NEEDED!
"""
