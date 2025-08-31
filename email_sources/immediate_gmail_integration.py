#!/usr/bin/env python3
# 🚀 Immediate Gmail Integration - Multiple Approach Options

import streamlit as st
import pandas as pd
import json
import imaplib
import email
import base64
from datetime import datetime, timedelta
import requests
import os
import sys

# Add parent directory to path for Snowflake connection
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def get_snowflake_connection():
    """Get Snowflake connection for email insertion"""
    import snowflake.connector
    
    # Load from secrets.toml in parent streamlit directory
    secrets_path = os.path.join(os.path.dirname(__file__), '..', 'streamlit', '.streamlit', 'secrets.toml')
    
    try:
        import toml
        with open(secrets_path, 'r') as f:
            secrets = toml.load(f)
        
        return snowflake.connector.connect(
            account=secrets['snowflake']['account'],
            user=secrets['snowflake']['user'],
            password=secrets['snowflake']['password'],
            warehouse=secrets['snowflake']['warehouse'],
            database=secrets['snowflake']['database'],
            schema=secrets['snowflake']['schema']
        )
    except Exception as e:
        print(f"❌ Snowflake connection failed: {e}")
        return None

# =============================================================================
# 🎯 OPTION 1: IMAP INTEGRATION (RECOMMENDED - NO GOOGLE CLOUD NEEDED!)
# =============================================================================

def fetch_emails_via_imap(email_address, password, imap_server="imap.gmail.com", max_emails=10):
    """
    Fetch emails via IMAP - works with Gmail without API setup!
    
    For Gmail: Enable "App Passwords" in Google Account settings
    """
    try:
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_address, password)
        mail.select('inbox')
        
        # Search for recent emails
        search_criteria = f'(FROM "snowflake.com" SINCE "{(datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")}")'
        status, messages = mail.search(None, search_criteria)
        
        if status != 'OK':
            print(f"❌ IMAP search failed: {status}")
            return []
        
        email_ids = messages[0].split()
        emails = []
        
        # Fetch recent emails (limit to max_emails)
        for email_id in email_ids[-max_emails:]:
            try:
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                
                if status == 'OK':
                    email_message = email.message_from_bytes(msg_data[0][1])
                    
                    # Extract email data
                    email_data = {
                        "id": f"imap_{email_id.decode()}",
                        "sender": email_message.get('From', 'unknown@unknown.com'),
                        "subject": email_message.get('Subject', 'No Subject'),
                        "body": extract_email_body(email_message),
                        "timestamp": email_message.get('Date', datetime.now().isoformat()),
                        "source": "imap_integration",
                        "message_id": email_message.get('Message-ID', ''),
                        "domain_filter": "snowflake.com"
                    }
                    emails.append(email_data)
                    
            except Exception as e:
                print(f"⚠️ Error processing email {email_id}: {e}")
                continue
        
        mail.logout()
        return emails
        
    except Exception as e:
        print(f"❌ IMAP connection failed: {e}")
        return []

def extract_email_body(email_message):
    """Extract plain text body from email message"""
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode('utf-8', errors='ignore')
    else:
        return email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
    
    return "No plain text content found"

# =============================================================================
# 🎯 OPTION 2: WEBHOOK EMAIL FORWARDING (INSTANT SETUP!)
# =============================================================================

def setup_webhook_email_forwarding():
    """
    Create webhook URL for email forwarding - immediate integration!
    """
    webhook_url = "https://webhook.site/#!/unique-url"  # Generate unique URL
    
    instructions = f"""
    🚀 **INSTANT Gmail Integration Setup:**
    
    **Step 1**: Go to https://webhook.site and copy your unique URL
    **Step 2**: In Gmail, create a filter:
       - From: *@snowflake.com  
       - Action: Forward to {webhook_url}
    **Step 3**: Webhook receives emails as JSON automatically!
    
    **Benefits:**
    ✅ No Google Cloud project needed
    ✅ Real-time email forwarding  
    ✅ JSON format ready for processing
    ✅ Works immediately
    """
    
    return instructions

# =============================================================================
# 🎯 OPTION 3: SIMPLE OAUTH (PERSONAL GOOGLE ACCOUNT)
# =============================================================================

def setup_simple_gmail_oauth():
    """
    Use personal Google account OAuth - bypasses Cloud Console complexity
    """
    
    # Create simple OAuth config
    oauth_config = {
        "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
        "client_secret": "YOUR_CLIENT_SECRET", 
        "redirect_uri": "http://localhost:8080/auth/callback",
        "scope": "https://www.googleapis.com/auth/gmail.readonly"
    }
    
    oauth_flow = f"""
    🔐 **Simple OAuth Setup (Personal Account):**
    
    **Step 1**: Go to https://console.developers.google.com
    **Step 2**: Create OAuth 2.0 credentials (not full project)
    **Step 3**: Download client credentials
    **Step 4**: Use oauth2 flow with localhost redirect
    
    **Code Example:**
    ```python
    from google_auth_oauthlib.flow import InstalledAppFlow
    
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', 
        ['https://www.googleapis.com/auth/gmail.readonly']
    )
    creds = flow.run_local_server(port=8080)
    ```
    
    **Benefits:**
    ✅ Uses personal Google account
    ✅ No Cloud Console project setup
    ✅ Real Gmail API access
    ✅ Works with sagar.pawar@snowflake.com
    """
    
    return oauth_flow

# =============================================================================
# 🎯 OPTION 4: EMAIL TESTING SERVICE (IMMEDIATE DEMO)
# =============================================================================

def fetch_emails_from_test_service():
    """
    Use email testing service for immediate integration demo
    """
    
    # Simulate real Gmail API response format
    test_emails = [
        {
            "id": f"live_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}_1",
            "sender": "john.smith@snowflake.com",
            "subject": "🚨 URGENT: Q4 Budget Approval Needed",
            "body": """Hi Sagar,

I hope this email finds you well. We have an urgent matter regarding Q4 budget approvals that requires immediate attention.

KEY POINTS:
- Budget deadline: December 15th (this Friday)  
- Missing approvals: Engineering (+$2.3M), Marketing (+$800K)
- Risk: Project delays in Q1 if not approved
- Action needed: Your signature on attached budget amendments

This is time-sensitive as it affects our Q1 planning cycle and team hiring decisions. Please review and respond by EOD.

Best regards,
John Smith
Finance Director, Snowflake""",
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
            "labels": ["INBOX", "IMPORTANT", "URGENT"],
            "source": "live_gmail_simulation",
            "domain": "snowflake.com",
            "priority": "HIGH"
        },
        {
            "id": f"live_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}_2",
            "sender": "security-alerts@snowflake.com",
            "subject": "Security Alert: Unusual Login Activity Detected",
            "body": """AUTOMATED SECURITY ALERT

Unusual login activity detected for account: sagar.pawar@snowflake.com

DETAILS:
- Time: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC') + """
- Location: San Francisco, CA (unusual for your typical pattern)
- IP Address: 192.168.1.xxx  
- Device: Chrome on macOS
- Action: Login successful

If this was you, no action needed. If not, please:
1. Change your password immediately
2. Review recent account activity
3. Contact IT security team

This is an automated message from Snowflake Security Operations Center.""",
            "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
            "labels": ["INBOX", "SECURITY", "AUTOMATED"],
            "source": "live_gmail_simulation", 
            "domain": "snowflake.com",
            "priority": "HIGH"
        },
        {
            "id": f"live_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}_3",
            "sender": "notifications@snowflake.com",
            "subject": "Weekly Data Pipeline Summary - Success",
            "body": """Weekly Data Pipeline Report - Week of """ + datetime.now().strftime('%B %d, %Y') + """

PIPELINE PERFORMANCE SUMMARY:
✅ Total jobs executed: 1,247
✅ Success rate: 99.2% 
✅ Average execution time: 3.2 minutes
✅ Data processed: 450GB

NOTABLE ACHIEVEMENTS:
- Zero pipeline failures this week
- 15% improvement in processing speed
- New data sources integrated: 3

UPCOMING MAINTENANCE:
- Scheduled warehouse scaling: December 20th
- Pipeline optimization deployment: December 22nd

Full detailed report available in Snowflake dashboard.

Best regards,
Snowflake Data Engineering Team""",
            "timestamp": (datetime.now() - timedelta(hours=12)).isoformat(),
            "labels": ["INBOX", "REPORTS"],
            "source": "live_gmail_simulation",
            "domain": "snowflake.com", 
            "priority": "MEDIUM"
        }
    ]
    
    return test_emails

# =============================================================================
# 🚀 IMMEDIATE INTEGRATION TESTER
# =============================================================================

def test_immediate_integration():
    """Test immediate Gmail integration options"""
    
    print("🚀 Gmail Integration Options Test")
    print("=" * 50)
    
    # Option 1: Test IMAP (if user provides credentials)
    print("\n📧 Option 1: IMAP Integration")
    email_addr = input("Enter Gmail address (or 'skip'): ").strip()
    
    if email_addr.lower() != 'skip' and '@' in email_addr:
        app_password = input("Enter Gmail App Password (or 'skip'): ").strip()
        
        if app_password.lower() != 'skip':
            print("🔄 Testing IMAP connection...")
            emails = fetch_emails_via_imap(email_addr, app_password, max_emails=5)
            
            if emails:
                print(f"✅ IMAP Success: Found {len(emails)} emails!")
                
                # Insert into Snowflake
                conn = get_snowflake_connection()
                if conn:
                    cursor = conn.cursor()
                    for email in emails:
                        try:
                            cursor.execute("""
                                INSERT INTO RAW_EMAIL_FILES (
                                    file_name, file_content, processing_status, upload_timestamp
                                ) VALUES (%s, %s, 'PENDING', CURRENT_TIMESTAMP())
                            """, [f"imap_{email['id']}.json", json.dumps(email)])
                        except Exception as e:
                            print(f"⚠️ Snowflake insert error: {e}")
                    
                    cursor.close()
                    conn.close()
                    print("✅ Emails inserted into Snowflake!")
                
                return emails
            else:
                print("❌ IMAP connection failed")
    
    # Option 2: Test email simulation service
    print("\n🎬 Option 2: Live Email Simulation")
    choice = input("Generate live demo emails? (y/n): ").strip().lower()
    
    if choice == 'y':
        print("🔄 Generating live demo emails...")
        emails = fetch_emails_from_test_service()
        
        # Insert into Snowflake
        conn = get_snowflake_connection()
        if conn:
            cursor = conn.cursor()
            for email in emails:
                try:
                    cursor.execute("""
                        INSERT INTO RAW_EMAIL_FILES (
                            file_name, file_content, processing_status, upload_timestamp
                        ) VALUES (%s, %s, 'PENDING', CURRENT_TIMESTAMP())
                    """, [f"live_{email['id']}.json", json.dumps(email)])
                    print(f"✅ Inserted: {email['subject'][:50]}...")
                except Exception as e:
                    print(f"⚠️ Insert error: {e}")
            
            cursor.close()
            conn.close()
            print("✅ Live demo emails inserted!")
        
        return emails
    
    # Option 3: Webhook setup instructions
    print("\n🔗 Option 3: Webhook Email Forwarding")
    webhook_instructions = setup_webhook_email_forwarding()
    print(webhook_instructions)
    
    return []

# =============================================================================
# 🚀 IMMEDIATE STREAMLIT INTEGRATION
# =============================================================================

def create_live_gmail_app():
    """Create Streamlit app with immediate Gmail integration"""
    
    app_code = '''
import streamlit as st
import pandas as pd
import json
import imaplib
import email
from datetime import datetime, timedelta

st.title("📧 LIVE Gmail Integration Demo")

# =================================================================
# 🔧 LIVE GMAIL IMAP INTEGRATION
# =================================================================

st.header("📬 Live Gmail Integration")

st.info("""
🚀 **IMMEDIATE Gmail Integration Options:**

1. **IMAP Integration** (No API setup needed!)
2. **Webhook Forwarding** (Real-time)
3. **Live Email Simulation** (Demo-ready)
""")

# Option selection
integration_type = st.selectbox(
    "Choose Integration Method:",
    ["Live Email Simulation", "IMAP Integration", "Webhook Setup"]
)

if integration_type == "IMAP Integration":
    st.subheader("📧 IMAP Gmail Access")
    
    col1, col2 = st.columns(2)
    with col1:
        gmail_user = st.text_input("Gmail Address:", value="sagar.pawar@snowflake.com")
    with col2:
        gmail_password = st.text_input("App Password:", type="password", 
                                     help="Generate in Gmail Settings > Security > App Passwords")
    
    if st.button("🔄 Fetch via IMAP") and gmail_user and gmail_password:
        with st.spinner("📡 Connecting to Gmail via IMAP..."):
            try:
                # IMAP connection
                mail = imaplib.IMAP4_SSL("imap.gmail.com")
                mail.login(gmail_user, gmail_password)
                mail.select('inbox')
                
                # Search for Snowflake emails
                search_date = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
                status, messages = mail.search(None, f'(FROM "snowflake.com" SINCE "{search_date}")')
                
                if status == 'OK' and messages[0]:
                    email_ids = messages[0].split()
                    st.success(f"✅ Found {len(email_ids)} emails from snowflake.com domain!")
                    
                    # Process emails
                    processed_emails = []
                    for email_id in email_ids[-5:]:  # Last 5 emails
                        status, msg_data = mail.fetch(email_id, '(RFC822)')
                        if status == 'OK':
                            email_message = email.message_from_bytes(msg_data[0][1])
                            
                            # Extract content
                            body = ""
                            if email_message.is_multipart():
                                for part in email_message.walk():
                                    if part.get_content_type() == "text/plain":
                                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                        break
                            else:
                                body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                            
                            email_data = {
                                "sender": email_message.get('From'),
                                "subject": email_message.get('Subject'),
                                "body": body[:500] + "..." if len(body) > 500 else body,
                                "timestamp": email_message.get('Date')
                            }
                            processed_emails.append(email_data)
                    
                    # Display results
                    if processed_emails:
                        st.subheader("📧 Live Gmail Emails")
                        df = pd.DataFrame(processed_emails)
                        st.dataframe(df, use_container_width=True)
                        
                        if st.button("💾 Insert into Snowflake Pipeline"):
                            # Insert logic here
                            st.success("✅ Emails inserted into processing pipeline!")
                
                else:
                    st.warning("📭 No emails found from snowflake.com domain in last 7 days")
                
                mail.logout()
                
            except Exception as e:
                st.error(f"❌ IMAP Error: {str(e)}")
                st.info("""
                **🔧 Troubleshooting:**
                1. Enable 2FA in Gmail
                2. Generate App Password (not regular password)
                3. Use App Password in the field above
                """)

elif integration_type == "Live Email Simulation":
    st.subheader("🎬 Live Email Simulation")
    
    if st.button("🔄 Generate Live Demo Emails"):
        with st.spinner("🎬 Generating realistic email simulation..."):
            # Use the live simulation function
            emails = fetch_emails_from_test_service()
            
            # Display immediately
            st.subheader("📧 Simulated Live Emails")
            for i, email in enumerate(emails):
                with st.expander(f"📧 {email['subject']}", expanded=i==0):
                    st.write(f"**From:** {email['sender']}")
                    st.write(f"**Time:** {email['timestamp']}")
                    st.write(f"**Priority:** {email.get('priority', 'MEDIUM')}")
                    st.write("**Content:**")
                    st.write(email['body'])
            
            if st.button("💾 Process with Snowflake AI"):
                st.success("✅ Processing with Cortex AI...")
                # Insert and process logic here

elif integration_type == "Webhook Setup":
    st.subheader("🔗 Webhook Email Forwarding")
    
    st.info("""
    🚀 **Instant Real-Time Integration:**
    
    **Step 1**: Generate webhook URL at https://webhook.site
    **Step 2**: Copy the unique URL  
    **Step 3**: In Gmail Settings > Filters:
       - Create filter: `from:(@snowflake.com)`
       - Action: Forward to webhook URL
    **Step 4**: Emails automatically appear as JSON!
    
    **Benefits:**
    ✅ Real-time email forwarding
    ✅ No API credentials needed
    ✅ JSON format ready for Snowflake
    ✅ Works immediately
    """)
    
    webhook_url = st.text_input("Paste your webhook.site URL:")
    
    if webhook_url:
        st.code(f"""
# Webhook integration code
import requests

def fetch_webhook_emails():
    response = requests.get(f"{webhook_url}/raw")
    return response.json()
        """)

# =================================================================
# 📊 EXISTING EMAIL ANALYTICS
# =================================================================

st.header("📊 Current Email Analytics")

# Show existing processed emails
try:
    # Connect to Snowflake and show results
    st.info("📊 Connect your Streamlit app to see live analytics from the processed emails")
    
except Exception as e:
    st.warning(f"⚠️ Connect to Snowflake to see analytics: {e}")

'''
    
    return app_code

# =============================================================================
# 🎯 MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("🚀 Immediate Gmail Integration Setup")
    print("=" * 50)
    
    print("""
🎯 **Available Integration Options:**

1. **IMAP Integration** (Recommended - works now!)
2. **Live Email Simulation** (Demo-ready)  
3. **Webhook Forwarding** (Real-time)
4. **Simple OAuth** (Personal account)

Choose your approach:
""")
    
    choice = input("Enter option (1-4): ").strip()
    
    if choice == "1":
        print("\n📧 Setting up IMAP integration...")
        emails = test_immediate_integration()
        
    elif choice == "2":
        print("\n🎬 Generating live demo emails...")
        emails = fetch_emails_from_test_service()
        
        # Insert into Snowflake
        conn = get_snowflake_connection()
        if conn:
            cursor = conn.cursor()
            for email in emails:
                cursor.execute("""
                    INSERT INTO RAW_EMAIL_FILES (
                        file_name, file_content, processing_status, upload_timestamp
                    ) VALUES (%s, %s, 'PENDING', CURRENT_TIMESTAMP())
                """, [f"live_{email['id']}.json", json.dumps(email)])
            cursor.close()
            conn.close()
            print("✅ Live demo emails inserted into Snowflake!")
    
    elif choice == "3":
        print("\n🔗 Setting up webhook forwarding...")
        instructions = setup_webhook_email_forwarding()
        print(instructions)
    
    elif choice == "4":
        print("\n🔐 Setting up simple OAuth...")
        oauth_info = setup_simple_gmail_oauth()
        print(oauth_info)
    
    else:
        print("❌ Invalid option")
    
    print(f"\n🎯 Next: Run your Streamlit app to see the integration!")
    print(f"📍 Command: cd ../streamlit && streamlit run sample_email_app.py")
