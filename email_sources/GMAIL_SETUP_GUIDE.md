# 📧 Gmail API Setup Guide for Automated Email Processing

**Target**: Monitor emails from **snowflake.com** domain for automatic processing

## 🎯 **Step-by-Step Gmail API Setup**

### **1. Google Cloud Console Setup (5 minutes)**

**A. Create/Select Project**
1. Go to: **https://console.cloud.google.com/**
2. Click **"Select a project"** → **"NEW PROJECT"**
3. Project name: **"Email Processing App"**
4. Click **"CREATE"**

**B. Enable Gmail API**
1. In the search bar, type: **"Gmail API"**
2. Click **"Gmail API"** → **"ENABLE"**
3. Wait for activation (30 seconds)

**C. Create OAuth 2.0 Credentials**
1. Go to: **APIs & Services** → **Credentials**
2. Click **"+ CREATE CREDENTIALS"**
3. Choose: **"OAuth 2.0 Client IDs"**
4. If prompted, configure **OAuth consent screen**:
   - User Type: **External**
   - App name: **"Email Processing App"**
   - User support email: **sagar.pawar@snowflake.com**
   - Scopes: **Add Gmail read scope**
5. Application type: **"Desktop application"**
6. Name: **"Email Processing Desktop"**
7. Click **"CREATE"**

**D. Download Credentials**
1. Click the **Download** icon (⬇️) next to your new credential
2. **Rename** the downloaded file to: **`credentials.json`**
3. **Move** it to: `/Users/sagarvijaypawar/email_processing_app/email_sources/`

---

### **2. Test Gmail Connection**

Run the test script to verify OAuth setup:

```bash
cd /Users/sagarvijaypawar/email_processing_app/email_sources
python test_gmail_connection.py
```

**Expected flow:**
1. Browser opens for Google OAuth
2. Login with: **sagar.pawar@snowflake.com**
3. Grant permissions to read Gmail
4. Script shows emails from snowflake.com domain

---

### **3. Your Current Configuration**

✅ **Target Domain**: `snowflake.com`
✅ **Max emails per run**: 10 (for testing)
✅ **Keywords**: meeting, urgent, action, deadline, project, client, demo
✅ **Date range**: Last 7 days

---

## 🔧 **Troubleshooting**

### **"credentials.json not found"**
- Download from Google Cloud Console
- Check file is in correct directory
- Verify filename is exactly `credentials.json`

### **"OAuth consent screen required"**
- Go to: APIs & Services → OAuth consent screen
- Choose "External" user type
- Fill required fields with your Snowflake email

### **"Gmail API not enabled"**
- Go to: APIs & Services → Library
- Search "Gmail API" → Enable

### **"Permission denied" in OAuth**
- Add your email to test users in OAuth consent screen
- Or publish the app (for production use)

---

## 🎯 **Next Steps After OAuth Setup**

1. **Test connection**: `python test_gmail_connection.py`
2. **Run Gmail connector**: `python gmail_connector.py`
3. **Monitor processing**: Launch Streamlit dashboard
4. **Configure S3**: For full automation pipeline

---

## 📋 **Ready to Start?**

**Current status**: Waiting for `credentials.json` file from Google Cloud Console

**Once you have the file**, the Gmail integration will automatically:
- 📧 Fetch emails from snowflake.com every 5 minutes
- 📤 Upload to S3 for Snowpipe processing  
- 🤖 Trigger automated AI analysis
- 🚨 Alert on urgent emails

Let me know when you've **downloaded the credentials.json** file!
