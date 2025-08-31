# 📧 Gmail API Integration with Streamlit-in-Snowflake (SiS)

## 🎯 **Current Demo → Production Migration Path**

### **Your Current Demo Architecture:**
```
📊 External Streamlit App
     ↓ (snowflake-connector-python)
💾 Snowflake Tables
     ↓ (Tasks/Streams)
🤖 Cortex AI Analysis
```

### **Production SiS Architecture:**
```
📧 Gmail API (Python UDF) → 📊 Streamlit-in-Snowflake → 💾 Internal Tables → 🤖 Cortex AI
```

---

## 🔧 **Technical Implementation Details**

### **1. Gmail API Integration Options in SiS**

#### **Option A: Python UDF Approach (Recommended)**
```sql
-- Create Gmail fetching function inside Snowflake
CREATE OR REPLACE FUNCTION FETCH_GMAIL_EMAILS(
    target_domain STRING DEFAULT 'snowflake.com',
    max_emails INT DEFAULT 50
)
RETURNS ARRAY
LANGUAGE PYTHON
RUNTIME_VERSION = '3.9'
PACKAGES = ('google-api-python-client==2.108.0', 'google-auth==2.23.4')
IMPORTS = ('@EMAIL_APP_STAGE/gmail_credentials.json')
HANDLER = 'fetch_emails_handler'
AS
$$
import json
import base64
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

def fetch_emails_handler(target_domain, max_emails):
    # Load service account credentials
    with open('/tmp/gmail_credentials.json', 'r') as f:
        creds_info = json.load(f)
    
    credentials = Credentials.from_service_account_info(creds_info)
    service = build('gmail', 'v1', credentials=credentials)
    
    # Fetch emails from specific domain
    query = f'from:{target_domain}'
    results = service.users().messages().list(
        userId='me', 
        q=query, 
        maxResults=max_emails
    ).execute()
    
    emails = []
    for msg in results.get('messages', []):
        # Get full message
        message = service.users().messages().get(
            userId='me', 
            id=msg['id']
        ).execute()
        
        # Parse email content
        email_data = {
            'id': message['id'],
            'thread_id': message['threadId'],
            'sender': extract_sender(message),
            'subject': extract_subject(message),
            'body': extract_body(message),
            'timestamp': message['internalDate'],
            'labels': message.get('labelIds', [])
        }
        emails.append(email_data)
    
    return emails

def extract_sender(message):
    # Extract sender from headers
    headers = message['payload'].get('headers', [])
    for header in headers:
        if header['name'] == 'From':
            return header['value']
    return 'unknown@unknown.com'

def extract_subject(message):
    # Extract subject from headers
    headers = message['payload'].get('headers', [])
    for header in headers:
        if header['name'] == 'Subject':
            return header['value']
    return 'No Subject'

def extract_body(message):
    # Extract body from message parts
    payload = message['payload']
    body = ''
    
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
                break
    else:
        if payload['mimeType'] == 'text/plain':
            data = payload['body']['data']
            body = base64.urlsafe_b64decode(data).decode('utf-8')
    
    return body
$$;
```

#### **Option B: External Service + REST API**
```sql
-- Call external Gmail service via HTTP
CREATE OR REPLACE FUNCTION CALL_GMAIL_SERVICE(domain STRING)
RETURNS ARRAY
LANGUAGE SQL
AS
$$
    SELECT PARSE_JSON(
        SYSTEM$REST_API_CALL(
            'GET',
            'https://your-gmail-service.com/fetch',
            OBJECT_CONSTRUCT('domain', domain)
        )
    )
$$;
```

### **2. Streamlit-in-Snowflake App Structure**

#### **Production Streamlit App (streamlit_production.py)**
```python
import streamlit as st
import pandas as pd
from datetime import datetime

# Snowflake connection (built-in for SiS)
conn = st.connection("snowflake")

def main():
    st.title("📧 Email Processing Dashboard")
    
    # Gmail integration section
    st.header("📬 Gmail Integration")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        target_domain = st.selectbox(
            "Target Domain", 
            ["snowflake.com", "company.com", "all"]
        )
        max_emails = st.slider("Max Emails to Fetch", 10, 100, 50)
    
    with col2:
        if st.button("🔄 Fetch New Emails"):
            with st.spinner("Fetching emails from Gmail..."):
                # Call Gmail UDF directly
                result = conn.query(f"""
                    SELECT FETCH_GMAIL_EMAILS('{target_domain}', {max_emails}) as emails
                """)
                
                # Process results
                emails = result.iloc[0]['EMAILS']
                
                # Insert into processing pipeline
                for email in emails:
                    conn.query("""
                        INSERT INTO RAW_EMAIL_FILES (
                            file_name, file_content, processing_status
                        ) VALUES (?, ?, 'PENDING')
                    """, params=[f"gmail_{email['id']}.json", json.dumps(email)])
                
                st.success(f"✅ Fetched {len(emails)} emails!")
    
    # Rest of your existing dashboard code...
    st.header("📊 Email Analytics")
    
    # Your existing charts and analysis
    summaries = conn.query("SELECT * FROM EMAIL_SUMMARIES ORDER BY created_timestamp DESC LIMIT 10")
    st.dataframe(summaries)

if __name__ == "__main__":
    main()
```

### **3. Automated Production Workflow**

#### **Complete Production Task Chain:**
```sql
-- Master automation task
CREATE OR REPLACE TASK PRODUCTION_EMAIL_PIPELINE
    WAREHOUSE = COMPUTE_WH
    SCHEDULE = 'USING CRON 0 */5 * * * UTC'  -- Every 5 minutes
COMMENT = 'Production email processing pipeline'
AS
BEGIN
    -- Step 1: Fetch emails from Gmail
    LET new_emails ARRAY := FETCH_GMAIL_EMAILS('snowflake.com', 50);
    
    -- Step 2: Insert raw emails
    FOR email IN new_emails DO
        INSERT INTO RAW_EMAIL_FILES (file_name, file_content, processing_status)
        VALUES ('gmail_' || email:id::STRING || '.json', email, 'PENDING');
    END FOR;
    
    -- Step 3: Process pending emails
    CALL PROCESS_PENDING_EMAILS();
    
    -- Step 4: Run AI analysis
    CALL ANALYZE_NEW_EMAILS();
    
    -- Step 5: Check for urgent emails
    CALL CHECK_URGENT_EMAILS();
END;
```

---

## 🔄 **Demo → Production Extension Strategy**

### **Phase 1: Current Demo (✅ DONE)**
- External Streamlit with simulated Gmail data
- Manual email processing
- Cortex AI analysis
- Basic monitoring

### **Phase 2: Production Ready (🎯 YOUR TARGET)**
```sql
-- Deploy your existing Streamlit app to Snowflake
CREATE STREAMLIT EMAIL_PROCESSING_APP
    ROOT_LOCATION = '@EMAIL_APP_STAGE'
    MAIN_FILE = 'sample_email_app.py'  -- Your existing app!
    QUERY_WAREHOUSE = COMPUTE_WH;
```

### **Phase 3: Gmail Integration**
```python
# Add to your existing Streamlit app
if st.button("🔄 Sync with Gmail"):
    # This calls the UDF inside Snowflake
    emails = st.connection("snowflake").query(
        "SELECT FETCH_GMAIL_EMAILS('snowflake.com') as gmail_data"
    )
    st.success("✅ Gmail sync complete!")
```

### **Phase 4: Full Automation**
```sql
-- Schedule the automation
ALTER TASK PRODUCTION_EMAIL_PIPELINE RESUME;
```

---

## 🎯 **Key Benefits of SiS vs SPCS**

### **Streamlit-in-Snowflake Advantages:**

1. **🔐 Zero Auth Complexity**
   - No `secrets.toml` needed
   - Built-in Snowflake authentication
   - Enterprise SSO integration

2. **💰 Cost Efficient**
   - No container compute costs
   - Pay only for warehouse time
   - Auto-suspend when idle

3. **🛠️ Simple Deployment**
   - Upload Python file
   - CREATE STREAMLIT command
   - That's it!

4. **🔄 Code Reuse**
   - Your existing `sample_email_app.py` works as-is
   - Just add Gmail UDF calls
   - Same UI, same logic

### **SPCS Use Cases (When You'd Actually Need It):**
- 🐳 **Multi-container applications**
- 🌐 **Complex external API integrations**
- 🔄 **Heavy background processing**
- 🛠️ **Custom runtimes/dependencies**

**Your email app doesn't need any of these!** ✅

---

## 🚀 **Production Migration Roadmap**

### **Step 1: Prepare Gmail Credentials**
```bash
# Upload service account JSON to Snowflake stage
snowsql -c dev -q "PUT file://gmail_service_account.json @EMAIL_APP_STAGE"
```

### **Step 2: Deploy UDF**
```sql
-- Deploy Gmail fetching function
CREATE OR REPLACE FUNCTION FETCH_GMAIL_EMAILS(domain STRING)
RETURNS ARRAY
LANGUAGE PYTHON
-- (implementation as shown above)
```

### **Step 3: Deploy Streamlit App**
```sql
-- Upload and create Streamlit app
PUT file://sample_email_app.py @EMAIL_APP_STAGE;
CREATE STREAMLIT EMAIL_PROCESSING_APP
    ROOT_LOCATION = '@EMAIL_APP_STAGE'
    MAIN_FILE = 'sample_email_app.py';
```

### **Step 4: Enable Automation**
```sql
-- Start automated pipeline
ALTER TASK PRODUCTION_EMAIL_PIPELINE RESUME;
```

**Result**: Your demo becomes production with minimal changes! 🎯

---

## 💡 **Demo Talk Track for Production**

> **"What you see here is production-ready architecture. This same Streamlit dashboard deploys natively to Snowflake, where Gmail API calls happen through secure Python UDFs, all processing stays internal with enterprise authentication, and we get automatic scaling and cost optimization built-in. No containers, no external infrastructure - just pure Snowflake."**

**Your instinct was spot-on - SPCS is overkill for this use case!** ✅
