#!/usr/bin/env python3
"""
Direct Gmail to Snowflake Integration (No S3 Required)
For testing Gmail integration before full automation setup
"""

import os
import json
from datetime import datetime
from simple_gmail_test import SimpleGmailTest
import snowflake.connector

class DirectGmailProcessor:
    def __init__(self):
        self.gmail_test = SimpleGmailTest()
        self.snowflake_conn = None
    
    def connect_snowflake(self):
        """Connect to Snowflake using same credentials as Streamlit"""
        try:
            # Load from config or use direct credentials
            self.snowflake_conn = snowflake.connector.connect(
                user='SPAWAR',
                password='Applemylove@12345',
                account='SFSEAPAC-SPAWAR_AWSEAST1',
                warehouse='COMPUTE_WH',
                database='EMAIL_PROCESSING_APP',
                schema='CORE'
            )
            print("✅ Snowflake connection established")
            return True
        except Exception as e:
            print(f"❌ Snowflake connection failed: {str(e)}")
            return False
    
    def process_gmail_emails_direct(self, max_emails=3):
        """Fetch Gmail emails and insert directly into Snowflake"""
        
        print("🚀 Starting Direct Gmail → Snowflake Processing")
        print("=" * 50)
        
        # Step 1: Authenticate Gmail
        if not self.gmail_test.authenticate():
            return False
        
        # Step 2: Connect to Snowflake
        if not self.connect_snowflake():
            return False
        
        # Step 3: Fetch emails
        emails = self.gmail_test.fetch_snowflake_emails(max_emails)
        if not emails:
            print("📭 No emails to process")
            return False
        
        # Step 4: Insert directly into Snowflake
        processed_count = 0
        for i, email in enumerate(emails, 1):
            try:
                print(f"💾 Inserting email {i} into Snowflake...")
                
                # Insert into RAW_EMAIL_FILES
                cursor = self.snowflake_conn.cursor()
                
                file_name = f"gmail_direct_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.json"
                
                cursor.execute("""
                    INSERT INTO RAW_EMAIL_FILES (file_name, file_path, file_size, file_content, processing_status)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    file_name,
                    f"gmail_direct/{file_name}",
                    len(json.dumps(email)),
                    email,
                    'PENDING'
                ))
                
                processed_count += 1
                cursor.close()
                
                # Show preview
                headers = {h['name']: h['value'] for h in email['payload']['headers']}
                subject = headers.get('Subject', 'No subject')[:50]
                sender = headers.get('From', 'Unknown sender')[:30]
                print(f"   ✅ {subject}... from {sender}")
                
            except Exception as e:
                print(f"   ❌ Failed to insert email {i}: {str(e)}")
        
        print(f"\n🎉 Successfully processed {processed_count} emails!")
        
        # Step 5: Trigger processing using existing functions
        if processed_count > 0:
            print("🤖 Triggering AI processing...")
            try:
                cursor = self.snowflake_conn.cursor()
                
                # Get the file IDs we just inserted
                cursor.execute("""
                    SELECT file_id, file_content 
                    FROM RAW_EMAIL_FILES 
                    WHERE file_path LIKE 'gmail_direct/%'
                    AND processing_status = 'PENDING'
                    ORDER BY upload_timestamp DESC
                    LIMIT %s
                """, (processed_count,))
                
                pending_files = cursor.fetchall()
                
                for file_id, file_content in pending_files:
                    try:
                        # Use your existing email processing function
                        cursor.execute("CALL PROCESS_EMAIL_FORMAT_ENHANCED(%s, %s)", (file_id, file_content))
                        print(f"   ✅ Processed file_id: {file_id}")
                    except Exception as e:
                        print(f"   ⚠️  Processing failed for {file_id}: {str(e)}")
                
                cursor.close()
                
            except Exception as e:
                print(f"⚠️  AI processing setup failed: {str(e)}")
        
        return True
    
    def check_results(self):
        """Check processing results in Snowflake"""
        try:
            cursor = self.snowflake_conn.cursor()
            
            # Check processed emails
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_processed,
                    COUNT(CASE WHEN subject IS NOT NULL THEN 1 END) as emails_with_subjects
                FROM PROCESSED_EMAILS 
                WHERE extracted_timestamp >= DATEADD('hour', -1, CURRENT_TIMESTAMP())
            """)
            
            result = cursor.fetchone()
            if result:
                print(f"📊 Processed emails (last hour): {result[0]}")
                print(f"📧 Emails with subjects: {result[1]}")
            
            # Check AI summaries
            cursor.execute("""
                SELECT COUNT(*) 
                FROM EMAIL_SUMMARIES 
                WHERE created_timestamp >= DATEADD('hour', -1, CURRENT_TIMESTAMP())
            """)
            
            summaries = cursor.fetchone()[0]
            print(f"🤖 AI summaries generated: {summaries}")
            
            cursor.close()
            
        except Exception as e:
            print(f"❌ Error checking results: {str(e)}")

def main():
    """Main execution"""
    processor = DirectGmailProcessor()
    
    # Process emails directly
    if processor.process_gmail_emails_direct(max_emails=3):
        print("\n📊 Checking results...")
        processor.check_results()
        
        print(f"\n🎯 View results in Streamlit:")
        print(f"   cd ../streamlit")
        print(f"   streamlit run sample_email_app.py")
    else:
        print("\n❌ Direct processing failed")

if __name__ == "__main__":
    main()
