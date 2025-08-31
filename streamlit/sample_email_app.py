import streamlit as st
import snowflake.connector
import pandas as pd
import json

# Page configuration
st.set_page_config(
    page_title="Email Processing - Sample Emails",
    page_icon="📧",
    layout="wide"
)

st.title("📧 Gmail Integration - AI Email Processing")
st.markdown("*Live Gmail API integration demo with Snowflake Cortex AI automation*")

# Demo mode toggle
demo_mode = st.sidebar.checkbox("🎬 Demo Mode (Simulated Automation)", value=False)

if demo_mode:
    st.sidebar.markdown("""
    **🎯 Demo Mode Active**
    
    This simulates the production automation pipeline:
    - 📧 Gmail API fetching (Python UDF, every 5 min)
    - 📊 Streamlit-in-Snowflake processing (native)
    - 💾 Direct table ingestion (no external storage)
    - 🔄 Stream processing (real-time CDC)
    - 🤖 Cortex AI analysis (automatic)
    - 🚨 Urgent alerts (real-time)
    """)
    
    st.info("🎬 **DEMO MODE**: This simulates Gmail API automation. In production, this same app runs natively in Snowflake with real Gmail integration via Python UDFs.")
    
    # Gmail integration demo section
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📧 Live Gmail Integration**")
    st.sidebar.markdown("✅ Connected to: sagar.pawar@snowflake.com")
    st.sidebar.markdown("🎯 Domain filter: snowflake.com")
    st.sidebar.markdown("⚙️ Method: Python UDF (production)")
    st.sidebar.markdown("⏱️ Sync frequency: 5 minutes")
    st.sidebar.markdown("📊 Last demo sync: Just now")

# Snowflake connection with authentication refresh
@st.cache_resource
def init_connection():
    try:
        return snowflake.connector.connect(
            user=st.secrets["snowflake"]["user"],
            password=st.secrets["snowflake"]["password"],
            account=st.secrets["snowflake"]["account"],
            warehouse=st.secrets["snowflake"]["warehouse"],
            database="EMAIL_PROCESSING_APP",
            schema="CORE"
        )
    except Exception as e:
        st.error(f"Connection failed: {str(e)}")
        st.stop()

def get_fresh_connection():
    """Get a fresh connection, clearing cache if needed"""
    try:
        conn = init_connection()
        # Test the connection
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_USER()")
        cursor.fetchone()
        cursor.close()
        return conn
    except Exception as e:
        # Clear cache and retry
        st.cache_resource.clear()
        st.warning("🔄 Refreshing connection due to timeout...")
        return init_connection()

def run_query(query, params=None):
    conn = get_fresh_connection()  # Use fresh connection with auto-refresh
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall(), [desc[0] for desc in cursor.description]
    finally:
        cursor.close()

# Sample emails data
sample_emails = [
    {
        "id": "sample_1",
        "title": "📊 Q4 Budget Planning Meeting",
        "sender": "john.smith@company.com",
        "subject": "Q4 Budget Planning Meeting - Action Required",
        "content": """Hi Team,

I hope this email finds you well. I'm writing to schedule our Q4 budget planning meeting.

Key agenda items:
- Review Q3 spending analysis
- Discuss Q4 budget allocations
- Approve new project funding
- Set 2024 preliminary budget targets

Meeting Details:
- Date: November 22, 2023
- Time: 2:00 PM - 4:00 PM PST
- Location: Conference Room A
- Virtual link: https://company.zoom.us/j/123456789

Please prepare:
1. Your department's Q3 spending report
2. Q4 budget requests with justifications
3. Preliminary 2024 goals and resource needs

Deadlines:
- Send budget requests by November 20th
- Complete Q3 reports by November 19th

This is a critical meeting for our financial planning. Please confirm your attendance by responding to this email.

Best regards,
John Smith
Finance Director"""
    },
    {
        "id": "sample_2", 
        "title": "🚨 Urgent: System Outage",
        "sender": "sarah.johnson@clientcorp.com",
        "subject": "Urgent: System Outage Affecting Production",
        "content": """Dear Support Team,

We are experiencing a critical system outage that is affecting our production environment. The issue started at approximately 8:45 AM EST this morning.

Impact:
- All customer-facing applications are down
- Payment processing is offline
- Customer data access is limited
- Estimated revenue loss: $10,000 per hour

Immediate actions needed:
1. Activate emergency response protocol
2. Engage senior technical team
3. Provide hourly status updates
4. Prepare customer communication

Priority Level: CRITICAL
Expected Resolution: Within 2 hours

Please call me immediately at (555) 987-6543 or email me back with your action plan.

This is causing significant business disruption and needs immediate attention.

Urgently,
Sarah Johnson
IT Operations Manager"""
    },
    {
        "id": "sample_3",
        "title": "🎉 New Product Launch",
        "sender": "marketing@techsolutions.com", 
        "subject": "New Product Launch: AI Analytics Platform - Special Pricing",
        "content": """Hello!

We're excited to announce the launch of our revolutionary AI Analytics Platform!

Key Features:
✓ Real-time data processing
✓ Advanced machine learning algorithms
✓ Interactive dashboards
✓ Seamless integration with existing systems
✓ 99.9% uptime guarantee

Special Launch Pricing:
- Starter Plan: $99/month (was $149)
- Professional Plan: $299/month (was $399)
- Enterprise Plan: $799/month (was $999)

Limited time offer - expires December 31, 2023!

What our beta customers are saying:
"This platform has transformed how we analyze our data. The insights are incredible!" - TechCorp CEO

"Implementation was seamless and support is outstanding." - DataFlow CTO

Ready to revolutionize your analytics?

[CLAIM YOUR DISCOUNT] - Use code LAUNCH50 for additional 50% off first month

Questions? Reply to this email or call our sales team at 1-800-ANALYTICS.

Best regards,
The TechSolutions Marketing Team"""
    },
    {
        "id": "gmail_demo_1",
        "title": "📧 Gmail API: Q4 Budget Planning (Snowflake)",
        "sender": "john.smith@snowflake.com",
        "subject": "Q4 Budget Planning Meeting - Action Required",
        "content": """Hi Sagar, I hope this email finds you well. We need to schedule our Q4 budget planning meeting. Key agenda items include reviewing Q3 spending analysis, discussing Q4 budget allocations, and approving new project funding. The meeting is scheduled for November 22, 2024, at 2:00 PM PST in Conference Room A. Please prepare your department's Q3 spending report and Q4 budget requests. This is critical for our financial planning. Please confirm your attendance. Best regards, John Smith, Finance Director""",
        "source": "gmail_api_demo"
    },
    {
        "id": "gmail_demo_2", 
        "title": "📧 Gmail API: URGENT System Issue (Snowflake)",
        "sender": "sarah.johnson@snowflake.com",
        "subject": "URGENT: System Performance Issue - Immediate Review Needed",
        "content": """Hi Team, We're experiencing performance degradation in our production systems. Database query times have increased by 40% since this morning. Need immediate review of recent changes and resource allocation. Please join emergency call at 5:00 PM today. Critical systems affected: Customer portal, analytics dashboard, reporting pipeline. Escalation to management if not resolved by EOD. Thanks, Sarah Johnson, DevOps Lead""",
        "source": "gmail_api_demo"
    },
    {
        "id": "gmail_demo_3",
        "title": "📧 Gmail API: Summit Registration (Snowflake)",
        "sender": "marketing@snowflake.com", 
        "subject": "Snowflake Summit 2024 - Registration Now Open",
        "content": """Dear Snowflake Community, We're excited to announce that registration for Snowflake Summit 2024 is now open! Join us for three days of innovation, learning, and networking. Featured sessions include AI/ML advances, data governance best practices, and hands-on workshops. Early bird pricing available until September 15th. Register now at summit.snowflake.com. Looking forward to seeing you there! Best regards, Snowflake Events Team""",
        "source": "gmail_api_demo"
    }
]

# Main interface
st.header("📧 Gmail Email Processing Demo")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 Choose Email (Gmail Integration)")
    
    selected_email = st.selectbox(
        "Select an email to process:",
        options=[email["id"] for email in sample_emails],
        format_func=lambda x: next(email["title"] for email in sample_emails if email["id"] == x)
    )
    
    # Show selected email details
    email_data = next(email for email in sample_emails if email["id"] == selected_email)
    
    st.markdown(f"**From:** {email_data['sender']}")
    st.markdown(f"**Subject:** {email_data['subject']}")
    
    with st.expander("📄 View Email Content"):
        st.text(email_data['content'])
    
    if st.button("🧠 Process with AI (Uses ~1 Token)", key="process_btn"):
        with st.spinner("Processing email with AI..."):
            try:
                # Insert into processed emails
                insert_query = """
                INSERT INTO PROCESSED_EMAILS (sender_email, subject, email_body, extracted_timestamp)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP())
                """
                run_query(insert_query, (
                    email_data['sender'], 
                    email_data['subject'], 
                    email_data['content']
                ))
                
                # Get the email ID
                get_email_query = """
                SELECT email_id FROM PROCESSED_EMAILS 
                WHERE sender_email = %s AND subject = %s 
                ORDER BY extracted_timestamp DESC LIMIT 1
                """
                email_result, _ = run_query(get_email_query, (email_data['sender'], email_data['subject']))
                email_id = email_result[0][0]
                
                # Generate AI summary - First get the summary, then insert it
                get_summary_query = """
                SELECT SNOWFLAKE.CORTEX.SUMMARIZE(%s) as summary
                """
                summary_result, _ = run_query(get_summary_query, (email_data['content'],))
                ai_summary = summary_result[0][0]
                
                # Now insert the summary
                insert_summary_query = """
                INSERT INTO EMAIL_SUMMARIES (email_id, summary_type, summary_text, model_used)
                VALUES (%s, 'BRIEF', %s, 'snowflake-arctic')
                """
                run_query(insert_summary_query, (email_id, ai_summary))
                
                st.success("✅ Email processed successfully!")
                st.session_state['last_processed'] = {
                    'email_id': email_id,
                    'email_data': email_data
                }
                
            except Exception as e:
                st.error(f"Error processing email: {str(e)}")

with col2:
    st.subheader("📊 AI Analysis Results")
    
    if 'last_processed' in st.session_state:
        try:
            email_id = st.session_state['last_processed']['email_id']
            email_data = st.session_state['last_processed']['email_data']
            
            # Get AI summary
            results_query = """
            SELECT summary_text, created_timestamp
            FROM EMAIL_SUMMARIES 
            WHERE email_id = %s AND summary_type = 'BRIEF'
            ORDER BY created_timestamp DESC LIMIT 1
            """
            results, _ = run_query(results_query, (email_id,))
            
            if results:
                summary = results[0][0]
                timestamp = results[0][1]
                
                st.markdown(f"### 📧 {email_data['title']}")
                st.markdown(f"**From:** {email_data['sender']}")
                
                st.markdown("### 🤖 AI Summary")
                st.info(summary)
                
                st.markdown(f"*Processed at: {timestamp}*")
                
                # Show token usage estimate
                word_count = len(email_data['content'].split())
                estimated_tokens = max(1, word_count // 100)
                st.markdown(f"📊 **Estimated tokens used:** ~{estimated_tokens}")
            
        except Exception as e:
            st.error(f"Error loading results: {str(e)}")
    else:
        st.info("👆 Process a sample email above to see AI-generated results here")

# Statistics
st.header("📈 Processing Statistics")
try:
    stats_query = """
    SELECT 
        COUNT(*) as total_emails,
        (SELECT COUNT(*) FROM EMAIL_SUMMARIES) as ai_summaries
    FROM PROCESSED_EMAILS
    """
    
    stats, _ = run_query(stats_query)
    if stats:
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Total Emails Processed", stats[0][0])
        with col_b:
            st.metric("AI Summaries Generated", stats[0][1])

except Exception as e:
    st.error(f"Error loading stats: {str(e)}")

# View all processed emails
if st.button("📋 View All Processed Emails"):
    try:
        all_emails_query = """
        SELECT 
            pe.subject,
            pe.sender_email,
            es.summary_text,
            pe.extracted_timestamp
        FROM PROCESSED_EMAILS pe
        LEFT JOIN EMAIL_SUMMARIES es ON pe.email_id = es.email_id AND es.summary_type = 'BRIEF'
        ORDER BY pe.extracted_timestamp DESC
        LIMIT 10
        """
        
        all_results, cols = run_query(all_emails_query)
        if all_results:
            df = pd.DataFrame(all_results, columns=['Subject', 'Sender', 'AI Summary', 'Processed'])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No processed emails found.")
            
    except Exception as e:
        st.error(f"Error loading email history: {str(e)}")

# Cleanup option
st.markdown("---")
if st.button("🧹 Clean Up All Test Data"):
    try:
        cleanup_queries = [
            "DELETE FROM EMAIL_SUMMARIES",
            "DELETE FROM PROCESSED_EMAILS"
        ]
        
        for query in cleanup_queries:
            run_query(query)
        
        st.success("✅ All test data cleaned up!")
        if 'last_processed' in st.session_state:
            del st.session_state['last_processed']
        st.experimental_rerun()
        
    except Exception as e:
        st.error(f"Error cleaning up: {str(e)}")

st.markdown("---")
st.markdown("""
### 💡 **About This Gmail Integration Demo:**
- **Gmail API**: Simulated real-time email fetching from sagar.pawar@snowflake.com
- **Domain Filter**: Monitoring snowflake.com emails for business intelligence
- **AI Processing**: Snowflake Cortex for summarization and sentiment analysis
- **Production Architecture**: Streamlit-in-Snowflake with Python UDF integration
- **Automation**: Real-time processing via Streams and Tasks (5-minute sync cycles)
- **Token Efficiency**: ~1 token per email for AI summarization
""")
