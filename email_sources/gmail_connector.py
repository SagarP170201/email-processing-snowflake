#!/usr/bin/env python3
"""
Gmail API Connector for Real-Time Email Processing
Automatically fetches emails and triggers Snowflake processing pipeline
"""

import os
import json
import boto3
import time
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional

# Gmail API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Snowflake imports
import snowflake.connector

# Configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gmail_connector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GmailConnector:
    def __init__(self, config: Dict):
        """
        Initialize Gmail connector with configuration
        """
        self.config = config
        self.service = None
        self.s3_client = None
        self.snowflake_conn = None
        
    def authenticate_gmail(self) -> bool:
        """
        Authenticate with Gmail API using OAuth 2.0
        """
        try:
            creds = None
            
            # Load existing token
            if os.path.exists(TOKEN_FILE):
                creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            
            # Refresh or get new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("✅ Gmail API authenticated successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Gmail authentication failed: {str(e)}")
            return False
    
    def setup_aws_s3(self) -> bool:
        """
        Setup AWS S3 client for file uploads
        """
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.config.get('aws_access_key'),
                aws_secret_access_key=self.config.get('aws_secret_key'),
                region_name=self.config.get('aws_region', 'us-east-1')
            )
            
            # Test S3 connection
            self.s3_client.head_bucket(Bucket=self.config['s3_bucket'])
            logger.info("✅ S3 connection established")
            return True
            
        except Exception as e:
            logger.error(f"❌ S3 setup failed: {str(e)}")
            return False
    
    def setup_snowflake(self) -> bool:
        """
        Setup Snowflake connection for monitoring
        """
        try:
            self.snowflake_conn = snowflake.connector.connect(
                user=self.config['snowflake_user'],
                password=self.config['snowflake_password'],
                account=self.config['snowflake_account'],
                warehouse=self.config['snowflake_warehouse'],
                database='EMAIL_PROCESSING_APP',
                schema='CORE'
            )
            logger.info("✅ Snowflake connection established")
            return True
            
        except Exception as e:
            logger.error(f"❌ Snowflake setup failed: {str(e)}")
            return False
    
    def get_last_processed_timestamp(self) -> Optional[str]:
        """
        Get timestamp of last processed email from Snowflake
        """
        try:
            cursor = self.snowflake_conn.cursor()
            cursor.execute("""
                SELECT MAX(email_date) 
                FROM PROCESSED_EMAILS 
                WHERE email_date IS NOT NULL
            """)
            
            result = cursor.fetchone()
            cursor.close()
            
            if result and result[0]:
                # Convert to Gmail API format
                timestamp = result[0]
                return timestamp.strftime('%Y/%m/%d')
            else:
                # If no emails processed yet, get emails from last 7 days
                from datetime import timedelta
                week_ago = datetime.now() - timedelta(days=7)
                return week_ago.strftime('%Y/%m/%d')
                
        except Exception as e:
            logger.error(f"Error getting last processed timestamp: {str(e)}")
            return None
    
    def fetch_emails_from_domain(self, domain: str, max_results: int = 100) -> List[Dict]:
        """
        Fetch emails from specific domain using incremental approach
        """
        try:
            # Build query with incremental processing
            last_processed = self.get_last_processed_timestamp()
            
            if last_processed:
                query = f'from:{domain} after:{last_processed}'
            else:
                query = f'from:{domain}'
            
            logger.info(f"🔍 Fetching emails with query: {query}")
            
            # Search for messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            logger.info(f"📧 Found {len(messages)} new emails from {domain}")
            
            # Get detailed email data
            detailed_emails = []
            for msg in messages:
                email_details = self.get_email_details(msg['id'])
                if email_details:
                    detailed_emails.append(email_details)
            
            return detailed_emails
            
        except HttpError as e:
            logger.error(f"Gmail API error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error fetching emails: {str(e)}")
            return []
    
    def get_email_details(self, msg_id: str) -> Optional[Dict]:
        """
        Extract detailed email information from Gmail API
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = {}
            payload = message.get('payload', {})
            for header in payload.get('headers', []):
                headers[header['name']] = header['value']
            
            # Extract body content
            body_content = self.extract_body_content(payload)
            
            # Convert to your existing format
            email_data = {
                "email_type": "gmail_api",
                "payload": {
                    "headers": [
                        {"name": k, "value": v} for k, v in headers.items()
                    ],
                    "parts": [
                        {"body": {"data": body_content}}
                    ]
                },
                "internalDate": message.get('internalDate'),
                "threadId": message.get('threadId'),
                "messageId": msg_id,
                "fetched_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            return email_data
            
        except Exception as e:
            logger.error(f"Error getting email details for {msg_id}: {str(e)}")
            return None
    
    def extract_body_content(self, payload: Dict) -> str:
        """
        Extract text content from Gmail API payload
        """
        def decode_data(data: str) -> str:
            import base64
            return base64.urlsafe_b64decode(data + '===').decode('utf-8')
        
        try:
            # Handle multipart messages
            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain':
                        if 'data' in part.get('body', {}):
                            return decode_data(part['body']['data'])
                    elif 'parts' in part:  # Nested parts
                        content = self.extract_body_content(part)
                        if content:
                            return content
            
            # Handle single part messages
            elif payload.get('body', {}).get('data'):
                return decode_data(payload['body']['data'])
            
            return "No readable content found"
            
        except Exception as e:
            logger.error(f"Error extracting body content: {str(e)}")
            return "Content extraction failed"
    
    def upload_emails_to_s3(self, emails: List[Dict], batch_name: str) -> bool:
        """
        Upload email batch to S3 for Snowpipe processing
        """
        try:
            if not emails:
                logger.info("No emails to upload")
                return True
            
            # Create batch file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            s3_key = f"email-files/gmail-realtime/{batch_name}_{timestamp}.json"
            
            # Upload each email as separate JSON lines for easier processing
            email_batch = []
            for email in emails:
                email_batch.append(email)
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.config['s3_bucket'],
                Key=s3_key,
                Body=json.dumps(email_batch, indent=2),
                ContentType='application/json',
                Metadata={
                    'email_count': str(len(emails)),
                    'batch_name': batch_name,
                    'upload_timestamp': timestamp
                }
            )
            
            logger.info(f"✅ Uploaded {len(emails)} emails to s3://{self.config['s3_bucket']}/{s3_key}")
            return True
            
        except Exception as e:
            logger.error(f"❌ S3 upload failed: {str(e)}")
            return False
    
    def log_processing_metrics(self, emails_fetched: int, processing_time: float):
        """
        Log metrics to Snowflake for monitoring
        """
        try:
            cursor = self.snowflake_conn.cursor()
            
            # Log fetch metrics
            cursor.execute("""
                INSERT INTO REALTIME_METRICS (metric_type, metric_value, additional_data)
                VALUES 
                    ('GMAIL_FETCH_COUNT', %s, PARSE_JSON(%s)),
                    ('GMAIL_FETCH_LATENCY', %s, PARSE_JSON(%s))
            """, (
                emails_fetched,
                json.dumps({"source": "gmail_api", "timestamp": datetime.now().isoformat()}),
                processing_time,
                json.dumps({"source": "gmail_connector", "emails_processed": emails_fetched})
            ))
            
            cursor.close()
            logger.info(f"📊 Logged metrics: {emails_fetched} emails, {processing_time:.2f}s processing time")
            
        except Exception as e:
            logger.error(f"Error logging metrics: {str(e)}")
    
    def process_domain_emails(self, domain: str) -> Dict:
        """
        Main processing function - fetch emails from domain and upload to S3
        """
        start_time = time.time()
        
        try:
            logger.info(f"🚀 Starting automated email processing for domain: {domain}")
            
            # Fetch emails from Gmail
            emails = self.fetch_emails_from_domain(domain, self.config.get('max_emails_per_run', 50))
            
            if not emails:
                logger.info(f"📭 No new emails found for domain: {domain}")
                return {
                    'status': 'success',
                    'emails_processed': 0,
                    'message': 'No new emails to process'
                }
            
            # Upload to S3 (triggers Snowpipe)
            batch_name = f"gmail_{domain.replace('.', '_')}"
            upload_success = self.upload_emails_to_s3(emails, batch_name)
            
            if not upload_success:
                return {
                    'status': 'error',
                    'message': 'Failed to upload emails to S3'
                }
            
            # Log metrics
            processing_time = time.time() - start_time
            self.log_processing_metrics(len(emails), processing_time)
            
            logger.info(f"✅ Successfully processed {len(emails)} emails in {processing_time:.2f}s")
            
            return {
                'status': 'success',
                'emails_processed': len(emails),
                'processing_time': processing_time,
                'message': f'Successfully uploaded {len(emails)} emails to S3'
            }
            
        except Exception as e:
            logger.error(f"❌ Processing failed: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

def load_config() -> Dict:
    """
    Load configuration from environment variables or config file
    """
    # Try to load from config file first
    config_file = 'gmail_config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        # Load from environment variables
        config = {
            'target_domains': os.environ.get('TARGET_DOMAINS', 'company.com').split(','),
            'max_emails_per_run': int(os.environ.get('MAX_EMAILS_PER_RUN', '50')),
            's3_bucket': os.environ.get('S3_BUCKET', 'your-email-bucket'),
            'aws_access_key': os.environ.get('AWS_ACCESS_KEY_ID'),
            'aws_secret_key': os.environ.get('AWS_SECRET_ACCESS_KEY'),
            'aws_region': os.environ.get('AWS_REGION', 'us-east-1'),
            'snowflake_user': os.environ.get('SNOWFLAKE_USER'),
            'snowflake_password': os.environ.get('SNOWFLAKE_PASSWORD'),
            'snowflake_account': os.environ.get('SNOWFLAKE_ACCOUNT'),
            'snowflake_warehouse': os.environ.get('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH')
        }
    
    return config

def main():
    """
    Main execution function for automated email processing
    """
    logger.info("🚀 Starting Gmail Connector for Real-Time Email Processing")
    
    # Load configuration
    config = load_config()
    
    # Initialize connector
    connector = GmailConnector(config)
    
    # Setup connections
    if not connector.authenticate_gmail():
        logger.error("❌ Failed to authenticate with Gmail API")
        return
    
    if not connector.setup_aws_s3():
        logger.error("❌ Failed to setup S3 connection")
        return
        
    if not connector.setup_snowflake():
        logger.error("❌ Failed to setup Snowflake connection") 
        return
    
    # Process emails for each configured domain
    total_processed = 0
    for domain in config['target_domains']:
        logger.info(f"📧 Processing domain: {domain}")
        
        result = connector.process_domain_emails(domain)
        
        if result['status'] == 'success':
            total_processed += result['emails_processed']
            logger.info(f"✅ Domain {domain}: {result['emails_processed']} emails processed")
        else:
            logger.error(f"❌ Domain {domain} failed: {result['message']}")
    
    logger.info(f"🎉 Automation cycle complete! Total emails processed: {total_processed}")

if __name__ == "__main__":
    main()
