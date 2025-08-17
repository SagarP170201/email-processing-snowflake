import streamlit as st
import snowflake.connector
import pandas as pd
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
import os

# Page configuration
st.set_page_config(
    page_title="Email Processing & AI Summarization",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-container {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .summary-box {
        background-color: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.25rem;
    }
    .action-item {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

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

# Helper functions
@st.cache_data(ttl=300)
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

def display_email_summary(email_data):
    """Display a formatted email summary"""
    st.markdown(f"""
    <div class="summary-box">
        <h4>📧 {email_data.get('SUBJECT', 'No Subject')}</h4>
        <p><strong>From:</strong> {email_data.get('SENDER_EMAIL', 'Unknown')}</p>
        <p><strong>Date:</strong> {email_data.get('EMAIL_DATE', 'Unknown')}</p>
        <p><strong>Classification:</strong> {email_data.get('EMAIL_CLASSIFICATION', 'Not classified')}</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    st.markdown('<h1 class="main-header">📧 Email Processing & AI Summarization</h1>', unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", [
        "📊 Dashboard", 
        "📤 Upload & Process", 
        "🔍 Search & Analyze", 
        "🤖 AI Insights",
        "⚙️ Settings"
    ])
    
    if page == "📊 Dashboard":
        show_dashboard()
    elif page == "📤 Upload & Process":
        show_upload_process()
    elif page == "🔍 Search & Analyze":
        show_search_analyze()
    elif page == "🤖 AI Insights":
        show_ai_insights()
    elif page == "⚙️ Settings":
        show_settings()

def show_dashboard():
    st.header("📊 Email Processing Dashboard")
    
    # Get metrics
    try:
        # Total emails processed
        total_emails_query = "SELECT COUNT(*) FROM PROCESSED_EMAILS"
        total_emails, _ = run_query(total_emails_query)
        total_count = total_emails[0][0] if total_emails else 0
        
        # Recent uploads
        recent_query = """
        SELECT COUNT(*) FROM RAW_EMAIL_FILES 
        WHERE upload_timestamp >= CURRENT_TIMESTAMP() - INTERVAL '24 HOURS'
        """
        recent_uploads, _ = run_query(recent_query)
        recent_count = recent_uploads[0][0] if recent_uploads else 0
        
        # Pending processing
        pending_query = "SELECT COUNT(*) FROM RAW_EMAIL_FILES WHERE processing_status = 'PENDING'"
        pending_emails, _ = run_query(pending_query)
        pending_count = pending_emails[0][0] if pending_emails else 0
        
        # AI summaries generated
        summaries_query = "SELECT COUNT(*) FROM EMAIL_SUMMARIES"
        summaries_data, _ = run_query(summaries_query)
        summaries_count = summaries_data[0][0] if summaries_data else 0
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Emails", total_count, delta=recent_count)
        
        with col2:
            st.metric("Recent Uploads (24h)", recent_count)
        
        with col3:
            st.metric("Pending Processing", pending_count)
        
        with col4:
            st.metric("AI Summaries", summaries_count)
        
        # Processing status chart
        status_query = """
        SELECT processing_status, COUNT(*) as count 
        FROM RAW_EMAIL_FILES 
        GROUP BY processing_status
        """
        status_data, status_cols = run_query(status_query)
        
        if status_data:
            df_status = pd.DataFrame(status_data, columns=status_cols)
            fig_status = px.pie(df_status, values='COUNT', names='PROCESSING_STATUS', 
                              title="Email Processing Status Distribution")
            st.plotly_chart(fig_status, use_container_width=True)
        
        # Recent activity
        st.subheader("📋 Recent Activity")
        recent_activity_query = """
        SELECT 
            ref.file_name,
            ref.upload_timestamp,
            ref.processing_status,
            pe.subject,
            pe.sender_email
        FROM RAW_EMAIL_FILES ref
        LEFT JOIN PROCESSED_EMAILS pe ON ref.file_id = pe.file_id
        ORDER BY ref.upload_timestamp DESC
        LIMIT 10
        """
        
        recent_data, recent_cols = run_query(recent_activity_query)
        if recent_data:
            df_recent = pd.DataFrame(recent_data, columns=recent_cols)
            st.dataframe(df_recent, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

def show_upload_process():
    st.header("📤 Upload & Process Emails")
    
    tab1, tab2, tab3 = st.tabs(["📁 File Upload", "🗂️ Stage Management", "⚡ Process Files"])
    
    with tab1:
        st.subheader("Upload Email Files")
        
        upload_type = st.radio("Choose upload method:", 
                              ["Manual File Upload", "Stage Files from S3", "Stage Files from Internal"])
        
        if upload_type == "Manual File Upload":
            uploaded_files = st.file_uploader("Choose email files", 
                                            accept_multiple_files=True,
                                            type=['json', 'eml', 'msg', 'txt'])
            
            if uploaded_files and st.button("Upload Files"):
                for uploaded_file in uploaded_files:
                    try:
                        # Here you would implement the logic to upload to Snowflake stage
                        st.success(f"Uploaded {uploaded_file.name}")
                    except Exception as e:
                        st.error(f"Error uploading {uploaded_file.name}: {str(e)}")
        
        elif upload_type == "Stage Files from S3":
            if st.button("List S3 Files"):
                try:
                    query = "CALL LIST_STAGED_FILES('S3')"
                    files_data, files_cols = run_query(query)
                    if files_data:
                        df_files = pd.DataFrame(files_data, columns=files_cols)
                        st.dataframe(df_files)
                except Exception as e:
                    st.error(f"Error listing S3 files: {str(e)}")
    
    with tab2:
        st.subheader("Stage Management")
        
        # List staged files
        stage_type = st.selectbox("Select stage:", ["Internal", "S3"])
        
        if st.button("Refresh File List"):
            try:
                query = f"CALL LIST_STAGED_FILES('{stage_type.upper()}')"
                files_data, files_cols = run_query(query)
                if files_data:
                    df_files = pd.DataFrame(files_data, columns=files_cols)
                    st.dataframe(df_files)
                    st.session_state['staged_files'] = df_files
            except Exception as e:
                st.error(f"Error listing staged files: {str(e)}")
    
    with tab3:
        st.subheader("Process Staged Files")
        
        col1, col2 = st.columns(2)
        
        with col1:
            process_stage = st.selectbox("Stage to process:", ["INTERNAL", "S3"])
            file_pattern = st.text_input("File pattern (regex):", value=".*")
        
        with col2:
            if st.button("🚀 Start Processing"):
                try:
                    with st.spinner("Processing files..."):
                        query = f"CALL INGEST_EMAIL_FILES('{process_stage}', '{file_pattern}')"
                        result, _ = run_query(query)
                        st.success(f"Processing result: {result[0][0] if result else 'Unknown'}")
                except Exception as e:
                    st.error(f"Error processing files: {str(e)}")

def show_search_analyze():
    st.header("🔍 Search & Analyze Emails")
    
    tab1, tab2 = st.tabs(["🔎 Semantic Search", "📈 Analytics"])
    
    with tab1:
        st.subheader("AI-Powered Email Search")
        
        search_query = st.text_input("Enter your search query:", 
                                   placeholder="e.g., 'meetings about budget planning'")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            limit_results = st.slider("Number of results:", 1, 50, 10)
        
        with col2:
            if st.button("🔍 Search"):
                if search_query:
                    try:
                        with st.spinner("Searching emails..."):
                            query = f"SELECT * FROM TABLE(SEARCH_EMAILS_SEMANTIC('{search_query}', {limit_results}))"
                            results, cols = run_query(query)
                            
                            if results:
                                df_results = pd.DataFrame(results, columns=cols)
                                
                                for idx, row in df_results.iterrows():
                                    with st.expander(f"📧 {row['SUBJECT']} (Relevance: {row['RELEVANCE_SCORE']:.2f})"):
                                        col_a, col_b = st.columns(2)
                                        with col_a:
                                            st.write(f"**From:** {row['SENDER_EMAIL']}")
                                            st.write(f"**Date:** {row['EMAIL_DATE']}")
                                        with col_b:
                                            st.write(f"**Relevance:** {row['RELEVANCE_SCORE']:.2f}")
                                        
                                        if row['BRIEF_SUMMARY']:
                                            st.markdown(f"""
                                            <div class="summary-box">
                                                <strong>Summary:</strong> {row['BRIEF_SUMMARY']}
                                            </div>
                                            """, unsafe_allow_html=True)
                            else:
                                st.info("No emails found matching your search.")
                                
                    except Exception as e:
                        st.error(f"Search error: {str(e)}")
    
    with tab2:
        st.subheader("Email Analytics")
        
        # Email classification distribution
        try:
            class_query = """
            SELECT email_classification, COUNT(*) as count 
            FROM PROCESSED_EMAILS 
            WHERE email_classification IS NOT NULL
            GROUP BY email_classification
            """
            class_data, class_cols = run_query(class_query)
            
            if class_data:
                df_class = pd.DataFrame(class_data, columns=class_cols)
                fig_class = px.bar(df_class, x='EMAIL_CLASSIFICATION', y='COUNT',
                                 title="Email Classification Distribution")
                st.plotly_chart(fig_class, use_container_width=True)
            
            # Sentiment analysis over time
            sentiment_query = """
            SELECT 
                DATE_TRUNC('day', pe.email_date) as email_day,
                AVG(TRY_CAST(es.summary_text AS FLOAT)) as avg_sentiment
            FROM PROCESSED_EMAILS pe
            JOIN EMAIL_SUMMARIES es ON pe.email_id = es.email_id
            WHERE es.summary_type = 'SENTIMENT' 
            AND TRY_CAST(es.summary_text AS FLOAT) IS NOT NULL
            GROUP BY DATE_TRUNC('day', pe.email_date)
            ORDER BY email_day
            """
            
            sentiment_data, sentiment_cols = run_query(sentiment_query)
            if sentiment_data:
                df_sentiment = pd.DataFrame(sentiment_data, columns=sentiment_cols)
                fig_sentiment = px.line(df_sentiment, x='EMAIL_DAY', y='AVG_SENTIMENT',
                                      title="Average Email Sentiment Over Time")
                st.plotly_chart(fig_sentiment, use_container_width=True)
                
        except Exception as e:
            st.error(f"Analytics error: {str(e)}")

def show_ai_insights():
    st.header("🤖 AI-Generated Insights")
    
    tab1, tab2, tab3 = st.tabs(["📝 Generate Summaries", "📊 View Insights", "🎯 Action Items"])
    
    with tab1:
        st.subheader("Generate AI Summaries")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Select email for analysis
            email_query = """
            SELECT email_id, subject, sender_email, email_date 
            FROM PROCESSED_EMAILS 
            ORDER BY email_date DESC 
            LIMIT 100
            """
            
            try:
                emails_data, emails_cols = run_query(email_query)
                if emails_data:
                    df_emails = pd.DataFrame(emails_data, columns=emails_cols)
                    
                    selected_email = st.selectbox("Select email to analyze:",
                                                options=df_emails['EMAIL_ID'].tolist(),
                                                format_func=lambda x: f"{df_emails[df_emails['EMAIL_ID']==x]['SUBJECT'].iloc[0]} - {df_emails[df_emails['EMAIL_ID']==x]['SENDER_EMAIL'].iloc[0]}")
                    
                    if st.button("🧠 Analyze Email"):
                        try:
                            with st.spinner("Generating AI insights..."):
                                query = f"CALL ANALYZE_EMAIL_WITH_AI('{selected_email}')"
                                result, _ = run_query(query)
                                st.success(f"Analysis complete: {result[0][0] if result else 'Unknown'}")
                        except Exception as e:
                            st.error(f"Analysis error: {str(e)}")
            
            except Exception as e:
                st.error(f"Error loading emails: {str(e)}")
        
        with col2:
            st.subheader("Batch Processing")
            
            batch_limit = st.number_input("Number of emails to process:", 1, 100, 10)
            
            if st.button("🚀 Batch Analyze"):
                try:
                    with st.spinner("Running batch analysis..."):
                        query = f"CALL BATCH_ANALYZE_EMAILS({batch_limit}, 'ALL')"
                        result, _ = run_query(query)
                        st.success(f"Batch analysis: {result[0][0] if result else 'Unknown'}")
                except Exception as e:
                    st.error(f"Batch analysis error: {str(e)}")
    
    with tab2:
        st.subheader("AI Insights Overview")
        
        try:
            insights_query = """
            SELECT * FROM EMAIL_AI_INSIGHTS 
            ORDER BY email_date DESC 
            LIMIT 20
            """
            
            insights_data, insights_cols = run_query(insights_query)
            if insights_data:
                df_insights = pd.DataFrame(insights_data, columns=insights_cols)
                
                for idx, row in df_insights.iterrows():
                    with st.expander(f"📧 {row['SUBJECT']} - {row['EMAIL_CLASSIFICATION']}"):
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.write(f"**From:** {row['SENDER_EMAIL']}")
                            st.write(f"**Date:** {row['EMAIL_DATE']}")
                            st.write(f"**Classification:** {row['EMAIL_CLASSIFICATION']}")
                        
                        with col_b:
                            st.write(f"**Sentiment:** {row['SENTIMENT_SCORE']}")
                            st.write(f"**Total Summaries:** {row['TOTAL_SUMMARIES']}")
                        
                        if row['BRIEF_SUMMARY']:
                            st.markdown(f"""
                            <div class="summary-box">
                                <strong>Brief Summary:</strong><br>
                                {row['BRIEF_SUMMARY']}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        if row['ACTION_ITEMS'] and 'No action items' not in str(row['ACTION_ITEMS']):
                            st.markdown(f"""
                            <div class="action-item">
                                <strong>Action Items:</strong><br>
                                {row['ACTION_ITEMS']}
                            </div>
                            """, unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"Error loading insights: {str(e)}")
    
    with tab3:
        st.subheader("📋 Action Items Dashboard")
        
        try:
            action_query = """
            SELECT 
                pe.email_id,
                pe.subject,
                pe.sender_email,
                pe.email_date,
                es.summary_text as action_items
            FROM PROCESSED_EMAILS pe
            JOIN EMAIL_SUMMARIES es ON pe.email_id = es.email_id
            WHERE es.summary_type = 'ACTION_ITEMS'
            AND es.summary_text NOT ILIKE '%No action items%'
            ORDER BY pe.email_date DESC
            """
            
            action_data, action_cols = run_query(action_query)
            if action_data:
                df_actions = pd.DataFrame(action_data, columns=action_cols)
                
                st.write(f"**Found {len(df_actions)} emails with action items**")
                
                for idx, row in df_actions.iterrows():
                    st.markdown(f"""
                    <div class="action-item">
                        <h5>📧 {row['SUBJECT']}</h5>
                        <p><strong>From:</strong> {row['SENDER_EMAIL']} | <strong>Date:</strong> {row['EMAIL_DATE']}</p>
                        <p><strong>Action Items:</strong></p>
                        <p>{row['ACTION_ITEMS']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No action items found in processed emails.")
        
        except Exception as e:
            st.error(f"Error loading action items: {str(e)}")

def show_settings():
    st.header("⚙️ Settings & Configuration")
    
    tab1, tab2 = st.tabs(["🔧 System Settings", "📊 Processing Jobs"])
    
    with tab1:
        st.subheader("Snowflake Configuration")
        
        # Display current connection info (without sensitive data)
        try:
            conn_query = "SELECT CURRENT_USER(), CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_WAREHOUSE()"
            conn_info, conn_cols = run_query(conn_query)
            if conn_info:
                st.info(f"Connected as: {conn_info[0][0]} | Database: {conn_info[0][1]} | Schema: {conn_info[0][2]} | Warehouse: {conn_info[0][3]}")
        except Exception as e:
            st.error(f"Connection error: {str(e)}")
        
        st.subheader("AI Model Settings")
        
        # Model selection options
        summarization_model = st.selectbox("Summarization Model:", 
                                         ["snowflake-arctic", "mistral-large", "llama2-70b-chat"])
        
        classification_model = st.selectbox("Classification Model:",
                                          ["mistral-large", "snowflake-arctic", "llama2-70b-chat"])
        
        st.info("Note: Model changes will affect future processing jobs.")
    
    with tab2:
        st.subheader("Processing Jobs History")
        
        try:
            jobs_query = """
            SELECT 
                job_id,
                job_type,
                start_time,
                end_time,
                status,
                files_processed,
                files_failed
            FROM PROCESSING_JOBS 
            ORDER BY start_time DESC 
            LIMIT 50
            """
            
            jobs_data, jobs_cols = run_query(jobs_query)
            if jobs_data:
                df_jobs = pd.DataFrame(jobs_data, columns=jobs_cols)
                st.dataframe(df_jobs, use_container_width=True)
                
                # Job status distribution
                fig_jobs = px.pie(df_jobs, values='FILES_PROCESSED', names='STATUS',
                                title="Processing Jobs Status Distribution")
                st.plotly_chart(fig_jobs, use_container_width=True)
        
        except Exception as e:
            st.error(f"Error loading jobs: {str(e)}")

if __name__ == "__main__":
    main()
