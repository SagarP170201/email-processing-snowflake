import streamlit as st
import snowflake.connector
import pandas as pd
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Email Processing - Minimal Test",
    page_icon="📧",
    layout="wide"
)

st.title("📧 Email Processing - Single Email Test")
st.markdown("*Minimal version to test AI functionality with minimal token usage*")

# Snowflake connection
@st.cache_resource
def init_connection():
    return snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database="EMAIL_PROCESSING_APP",
        schema="CORE"
    )

def run_query(query, params=None):
    conn = init_connection()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall(), [desc[0] for desc in cursor.description]
    finally:
        cursor.close()

# Main interface
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📝 Test Single Email")
    
    # Input form for single email
    with st.form("single_email_form"):
        sender = st.text_input("From:", value="test@example.com")
        subject = st.text_input("Subject:", value="Test Email - Quick Meeting")
        email_body = st.text_area("Email Content:", 
                                 value="Hi! This is a test email about our quick meeting tomorrow at 2 PM. Please prepare the quarterly reports. Thanks!",
                                 height=150)
        
        submitted = st.form_submit_button("🧠 Process with AI (Uses ~1 Token)")
        
        if submitted and email_body:
            with st.spinner("Processing email with AI..."):
                try:
                    # Create email JSON
                    email_json = {
                        "email_type": "simple_format",
                        "sender": sender,
                        "recipients": ["you@company.com"],
                        "subject": subject,
                        "email_date": datetime.now().isoformat() + "Z",
                        "email_text": email_body
                    }
                    
                    # Insert raw email directly into processed emails table
                    file_name = f"test_email_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    
                    # Insert directly into PROCESSED_EMAILS table (skip the complex parsing)
                    insert_query = """
                    INSERT INTO PROCESSED_EMAILS (sender_email, subject, email_body, email_date, extracted_timestamp)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP())
                    """
                    run_query(insert_query, (sender, subject, email_body, datetime.now().isoformat()))
                    
                    # Get the email ID we just inserted
                    get_email_query = """
                    SELECT email_id FROM PROCESSED_EMAILS 
                    WHERE sender_email = %s AND subject = %s 
                    ORDER BY extracted_timestamp DESC LIMIT 1
                    """
                    email_result, _ = run_query(get_email_query, (sender, subject))
                    email_id = email_result[0][0]
                    
                    # Generate AI summary - First get the summary, then insert it
                    get_summary_query = """
                    SELECT SNOWFLAKE.CORTEX.SUMMARIZE(%s) as summary
                    """
                    summary_result, _ = run_query(get_summary_query, (email_body,))
                    ai_summary = summary_result[0][0]
                    
                    # Now insert the summary
                    insert_summary_query = """
                    INSERT INTO EMAIL_SUMMARIES (email_id, summary_type, summary_text, model_used)
                    VALUES (%s, 'BRIEF', %s, 'snowflake-arctic')
                    """
                    run_query(insert_summary_query, (email_id, ai_summary))
                    
                    st.success("✅ Email processed successfully!")
                    st.session_state['last_email_id'] = email_id
                    
                except Exception as e:
                    st.error(f"Error processing email: {str(e)}")

with col2:
    st.header("📊 Results")
    
    # Show recent results
    if 'last_email_id' in st.session_state:
        try:
            results_query = """
            SELECT 
                pe.subject,
                pe.sender_email,
                pe.email_body,
                es.summary_text,
                es.created_timestamp
            FROM PROCESSED_EMAILS pe
            JOIN EMAIL_SUMMARIES es ON pe.email_id = es.email_id
            WHERE pe.email_id = %s
            AND es.summary_type = 'BRIEF'
            """
            
            results, cols = run_query(results_query, (st.session_state['last_email_id'],))
            
            if results:
                result = results[0]
                st.subheader("📧 Processed Email")
                st.write(f"**Subject:** {result[0]}")
                st.write(f"**From:** {result[1]}")
                
                st.subheader("🤖 AI Summary")
                st.info(result[3])
                
                st.subheader("📝 Original Content")
                with st.expander("View original email content"):
                    st.text(result[2])
                    
                st.write(f"*Processed at: {result[4]}*")
        
        except Exception as e:
            st.error(f"Error loading results: {str(e)}")
    
    else:
        st.info("👆 Process an email above to see AI-generated results here")

# Quick stats
st.header("📈 Quick Stats")
try:
    stats_query = """
    SELECT 
        COUNT(*) as total_emails,
        COUNT(CASE WHEN processing_status = 'COMPLETED' THEN 1 END) as processed,
        (SELECT COUNT(*) FROM EMAIL_SUMMARIES) as ai_summaries
    FROM RAW_EMAIL_FILES
    """
    
    stats, _ = run_query(stats_query)
    if stats:
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Total Emails", stats[0][0])
        with col_b:
            st.metric("Processed", stats[0][1])
        with col_c:
            st.metric("AI Summaries", stats[0][2])

except Exception as e:
    st.error(f"Error loading stats: {str(e)}")

# Instructions
st.markdown("---")
st.markdown("""
### 💡 **Token-Saving Tips:**
- This app processes **ONE email at a time** to minimize Cortex AI token usage
- Each email uses approximately **1 token** for a brief summary
- Use this for testing before processing larger batches
- For production, use the full app with batch processing

### 🔍 **Manual Testing in Snowflake:**
```sql
-- View all processed emails
SELECT * FROM EMAIL_PROCESSING_OVERVIEW;

-- Generate additional summaries for existing emails (uses more tokens)
CALL ANALYZE_EMAIL_WITH_AI('email_id_here');
```
""")

# Cleanup option
st.markdown("---")
if st.button("🧹 Clean Up Test Data"):
    try:
        cleanup_query = """
        DELETE FROM EMAIL_SUMMARIES 
        WHERE email_id IN (
            SELECT email_id FROM PROCESSED_EMAILS 
            WHERE sender_email = 'test@example.com'
            OR subject LIKE 'Test Email%'
        );
        
        DELETE FROM PROCESSED_EMAILS 
        WHERE sender_email = 'test@example.com'
        OR subject LIKE 'Test Email%';
        """
        
        run_query(cleanup_query)
        st.success("✅ Test data cleaned up!")
        if 'last_email_id' in st.session_state:
            del st.session_state['last_email_id']
        st.experimental_rerun()
        
    except Exception as e:
        st.error(f"Error cleaning up: {str(e)}")
