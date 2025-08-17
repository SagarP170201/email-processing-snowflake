import snowflake.connector
import streamlit as st
import os
import sys

# Add streamlit directory to path to access secrets
sys.path.append('/Users/sagarvijaypawar/email_processing_app/streamlit')

# Mock streamlit secrets for testing
class MockSecrets:
    def __init__(self):
        # Try to read the actual secrets.toml file
        try:
            import toml
            with open('/Users/sagarvijaypawar/email_processing_app/streamlit/.streamlit/secrets.toml', 'r') as f:
                self.data = toml.load(f)
        except Exception as e:
            print(f"Error reading secrets.toml: {e}")
            print("Please make sure you've updated the credentials in secrets.toml")
            sys.exit(1)
    
    def __getitem__(self, key):
        return self.data[key]

# Test the connection
def test_snowflake_connection():
    secrets = MockSecrets()
    
    try:
        print("🔍 Testing Snowflake connection...")
        print(f"Account: {secrets['snowflake']['account']}")
        print(f"User: {secrets['snowflake']['user']}")
        print(f"Warehouse: {secrets['snowflake']['warehouse']}")
        
        # Try to connect
        if 'private_key_path' in secrets['snowflake'] and secrets['snowflake']['private_key_path']:
            # Key pair authentication
            print("Using key pair authentication...")
            conn = snowflake.connector.connect(
                user=secrets['snowflake']['user'],
                account=secrets['snowflake']['account'],
                private_key_path=secrets['snowflake']['private_key_path'],
                warehouse=secrets['snowflake']['warehouse']
            )
        else:
            # Username/password authentication
            print("Using username/password authentication...")
            conn = snowflake.connector.connect(
                user=secrets['snowflake']['user'],
                password=secrets['snowflake']['password'],
                account=secrets['snowflake']['account'],
                warehouse=secrets['snowflake']['warehouse']
            )
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_USER(), CURRENT_ACCOUNT(), CURRENT_WAREHOUSE()")
        result = cursor.fetchone()
        
        print("✅ Connection successful!")
        print(f"Connected as: {result[0]}")
        print(f"Account: {result[1]}")
        print(f"Warehouse: {result[2]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print("\nCommon issues:")
        print("- Check if your account identifier is correct")
        print("- Verify username and password")
        print("- Make sure the warehouse exists and you have access")
        print("- Check if your account has Cortex AI enabled")
        return False

if __name__ == "__main__":
    # Install toml if not available
    try:
        import toml
    except ImportError:
        print("Installing toml package...")
        os.system("pip install toml")
        import toml
    
    test_snowflake_connection()
