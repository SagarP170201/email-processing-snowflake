# 📧 Minimal Email Processing Setup - Single Email Test

This guide helps you test the email processing app with **just ONE email** to minimize Snowflake Cortex AI token consumption.

## 🎯 **Token Usage**
- **1 email = ~1 token** (for brief summary only)
- Perfect for testing before scaling up
- No automation = no background token usage

## 🚀 **Quick Start (3 Steps)**

### **Step 1: Minimal Deployment**
```bash
cd /Users/sagarvijaypawar/email_processing_app
./minimal_deploy.sh
```
*This deploys core components + processes 1 test email*

### **Step 2: Configure Streamlit Credentials**
```bash
# Edit your Snowflake credentials
nano streamlit/.streamlit/secrets.toml
```

### **Step 3: Run Minimal App**
```bash
cd streamlit
pip install -r requirements.txt
streamlit run minimal_app.py
```

## 🧪 **What Gets Deployed**

### ✅ **Included (Minimal)**
- Core database structure
- Email parsing functions
- Basic AI summarization
- Single email test interface
- **1 test email processed automatically**

### ❌ **Excluded (Token Savers)**
- Automation tasks
- Batch processing
- Real-time streaming
- Multiple AI summary types
- Entity extraction
- Classification

## 📱 **Using the Minimal App**

1. **Access the Interface**: `http://localhost:8501`
2. **Enter Test Email**: Use the form to input a short email
3. **Process**: Click "Process with AI" (uses ~1 token)
4. **View Results**: See the AI-generated summary
5. **Clean Up**: Use the cleanup button to remove test data

## 🔍 **Manual Testing in Snowflake**

```sql
-- View processed emails
SELECT * FROM EMAIL_PROCESSING_OVERVIEW;

-- Check token usage (processing jobs)
SELECT * FROM PROCESSING_JOBS ORDER BY start_time DESC;

-- Process ONE more email manually
CALL ANALYZE_EMAIL_WITH_AI('email_id_here');
```

## 💰 **Token Conservation Tips**

1. **Test with short emails** (fewer tokens for summarization)
2. **Use BRIEF summaries only** (not DETAILED, ACTION_ITEMS, etc.)
3. **Process one at a time** (no batch operations)
4. **Clean up test data** regularly
5. **Avoid automation** until you're ready for production

## 🔄 **Scaling Up Later**

When ready for production:

```bash
# Deploy full version with automation
./deploy.sh

# Run full Streamlit app
streamlit run app.py
```

## 📊 **Expected Results**

After running the minimal deployment, you should see:
- 1 test email in `RAW_EMAIL_FILES`
- 1 processed email in `PROCESSED_EMAILS`
- 1 AI summary in `EMAIL_SUMMARIES`
- Total token usage: ~1 token

## 🆘 **Troubleshooting**

### **"Cortex functions not available"**
- Ensure your Snowflake account has Cortex enabled
- Check if your region supports Cortex AI

### **"Permission denied"**
- Verify warehouse permissions
- Check database and schema access rights

### **"Connection failed"**
- Update `secrets.toml` with correct credentials
- Test Snowflake connection with SnowSQL first

## 🎉 **Success Indicators**

You've successfully set up the minimal version when:
- ✅ Deployment script completes without errors
- ✅ Streamlit app loads at `localhost:8501`
- ✅ You can process a test email and see an AI summary
- ✅ Total token usage is minimal (1-2 tokens)

---

**Ready to test with minimal token usage!** 🚀

*Once you're satisfied with the functionality, you can scale up to the full version with batch processing and automation.*
