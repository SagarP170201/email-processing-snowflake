import streamlit as st
import snowflake.connector
import pandas as pd
import plotly.express as px
from datetime import datetime
import json

# Page configuration
st.set_page_config(
    page_title="Simple Email Processing Monitor",
    page_icon="📧",
    layout="wide"
)

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

@st.cache_data(ttl=30)  # Refresh every 30 seconds
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

def main():
    st.title("📧 Simple Email Processing Monitor")
    st.markdown("*Basic monitoring for automated email processing*")
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Simple navigation
    page = st.sidebar.selectbox("Choose View", [
        "📋 System Status",
        "📧 Recent Emails", 
        "⚙️ Task Control"
    ])
    
    if page == "📋 System Status":
        show_simple_status()
    elif page == "📧 Recent Emails":
        show_recent_emails()
    elif page == "⚙️ Task Control":
        show_task_control()

def show_simple_status():
    st.header("📋 System Status")
    
    try:
        # Get basic health info
        health_query = "SELECT * FROM SIMPLE_SYSTEM_HEALTH"
        health_data, health_cols = run_query(health_query)
        
        if health_data:
            health = dict(zip(health_cols, health_data[0]))
            
            # Simple status indicator
            status = health['SYSTEM_STATUS']
            status_emoji = "✅" if status == "ACTIVE" else "💤"
            
            st.markdown(f"## {status_emoji} System Status: **{status}**")
            
            # Basic metrics in simple layout
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Files Uploaded (24h)", health['FILES_UPLOADED_24H'])
            
            with col2:
                st.metric("Emails Processed (24h)", health['EMAILS_PROCESSED_24H'])
            
            with col3:
                st.metric("Failed Files (24h)", health['FAILED_FILES_24H'])
            
            # Simple pipeline status
            st.subheader("📊 Pipeline Status")
            pipeline_query = "SELECT * FROM PIPELINE_STATUS"
            pipeline_data, pipeline_cols = run_query(pipeline_query)
            
            if pipeline_data:
                df_pipeline = pd.DataFrame(pipeline_data, columns=pipeline_cols)
                st.dataframe(df_pipeline, use_container_width=True)
            
            # Basic health check
            st.subheader("🔍 Health Check")
            if st.button("Run Health Check"):
                try:
                    health_result, _ = run_query("CALL CHECK_BASIC_HEALTH()")
                    health_msg = health_result[0][0] if health_result else "Unknown"
                    
                    if "WARNING" in health_msg:
                        st.warning(health_msg)
                    elif "HEALTHY" in health_msg:
                        st.success(health_msg)
                    else:
                        st.info(health_msg)
                except Exception as e:
                    st.error(f"Health check failed: {str(e)}")
        
    except Exception as e:
        st.error(f"Error loading system status: {str(e)}")

def show_recent_emails():
    st.header("📧 Recent Emails")
    
    try:
        # Recent processed emails
        recent_query = """
        SELECT 
            email_id,
            subject,
            sender_email,
            email_date,
            email_classification,
            extracted_timestamp
        FROM PROCESSED_EMAILS 
        ORDER BY extracted_timestamp DESC 
        LIMIT 20
        """
        
        recent_data, recent_cols = run_query(recent_query)
        if recent_data:
            df_recent = pd.DataFrame(recent_data, columns=recent_cols)
            st.dataframe(df_recent, use_container_width=True)
        else:
            st.info("No emails processed yet")
        
        # Show urgent emails
        st.subheader("🚨 Urgent Emails")
        urgent_query = "SELECT * FROM URGENT_EMAILS_SIMPLE LIMIT 10"
        urgent_data, urgent_cols = run_query(urgent_query)
        
        if urgent_data:
            df_urgent = pd.DataFrame(urgent_data, columns=urgent_cols)
            st.dataframe(df_urgent, use_container_width=True)
        else:
            st.success("No urgent emails detected")
        
        # Simple email stats
        st.subheader("📊 Basic Email Stats")
        stats_query = """
        SELECT 
            COUNT(*) as total_emails,
            COUNT(DISTINCT sender_email) as unique_senders,
            COUNT(CASE WHEN email_classification = 'URGENT' THEN 1 END) as urgent_count
        FROM PROCESSED_EMAILS
        WHERE extracted_timestamp >= DATEADD('day', -7, CURRENT_TIMESTAMP())
        """
        
        stats_data, stats_cols = run_query(stats_query)
        if stats_data:
            stats = dict(zip(stats_cols, stats_data[0]))
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Emails (7d)", stats['TOTAL_EMAILS'])
            with col2:
                st.metric("Unique Senders", stats['UNIQUE_SENDERS'])
            with col3:
                st.metric("Urgent Emails", stats['URGENT_COUNT'])
        
    except Exception as e:
        st.error(f"Error loading recent emails: {str(e)}")

def show_task_control():
    st.header("⚙️ Simple Task Control")
    
    try:
        # Task status
        task_query = "SELECT * FROM SIMPLE_TASK_STATUS"
        task_data, task_cols = run_query(task_query)
        
        if task_data:
            st.subheader("📋 Task Status")
            df_tasks = pd.DataFrame(task_data, columns=task_cols)
            
            for _, task in df_tasks.iterrows():
                status_emoji = "🟢" if task['STATE'] == 'Started' else "🔴"
                st.write(f"{status_emoji} **{task['TASK_NAME']}** - {task['STATE']}")
                st.write(f"   Last run: {task['LAST_COMMITTED_ON']}")
        
        # Simple task controls
        st.subheader("🎛️ Controls")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⏸️ Stop Automation"):
                try:
                    result, _ = run_query("CALL MANAGE_AUTOMATION_TASKS('SUSPEND', 'ALL')")
                    st.success("Automation stopped")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        with col2:
            if st.button("▶️ Start Automation"):
                try:
                    result, _ = run_query("CALL MANAGE_AUTOMATION_TASKS('RESUME', 'ALL')")
                    st.success("Automation started")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # Show any errors
        st.subheader("❌ Recent Errors")
        error_query = "SELECT * FROM RECENT_ERRORS"
        error_data, error_cols = run_query(error_query)
        
        if error_data:
            df_errors = pd.DataFrame(error_data, columns=error_cols)
            st.dataframe(df_errors, use_container_width=True)
        else:
            st.success("No recent errors detected")
        
    except Exception as e:
        st.error(f"Error loading task control: {str(e)}")

# Run the app
if __name__ == "__main__":
    main()
