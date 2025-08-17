import snowflake.connector

# Common account identifier formats to try
account_formats = [
    "SPAWAR_AWSEAST1",
    "spawar-awseast1", 
    "SPAWAR_AWSEAST1.us-east-1.aws",
    "spawar-awseast1.us-east-1.aws",
    "SPAWAR.us-east-1.aws",
    "spawar.us-east-1.aws"
]

def test_account_format(account, user, password, warehouse):
    try:
        print(f"🧪 Testing account format: {account}")
        conn = snowflake.connector.connect(
            user=user,
            password=password,
            account=account,
            warehouse=warehouse,
            login_timeout=10  # Shorter timeout for testing
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_ACCOUNT()")
        result = cursor.fetchone()
        
        print(f"✅ SUCCESS! Correct account format: {account}")
        print(f"   Actual account name: {result[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed: {str(e)[:100]}...")
        return False

# Get credentials from user
print("Let's find your correct Snowflake account identifier!")
print("\nPlease provide your credentials:")
user = input("Username [SPAWAR]: ").strip() or "SPAWAR"
password = input("Password: ").strip()
warehouse = input("Warehouse [COMPUTE_WH]: ").strip() or "COMPUTE_WH"

if not password:
    print("❌ Password is required!")
    exit(1)

print(f"\n🔍 Testing different account formats for user: {user}")
print("=" * 60)

success = False
for account_format in account_formats:
    if test_account_format(account_format, user, password, warehouse):
        success = True
        print(f"\n🎉 Found working account format!")
        print(f"Update your secrets.toml with: account = \"{account_format}\"")
        break
    print()

if not success:
    print("\n❌ None of the common formats worked.")
    print("\nPlease check:")
    print("1. Your exact Snowflake login URL")
    print("2. Username and password are correct") 
    print("3. You have access to the specified warehouse")
    print("4. Your account has network connectivity")
    
    print("\nYour Snowflake URL should be something like:")
    print("- https://abc12345.snowflakecomputing.com")
    print("- https://abc12345.us-east-1.aws.snowflakecomputing.com")
    print("- https://abc12345.east-us-2.azure.snowflakecomputing.com")
    print("\nThe account identifier is everything before '.snowflakecomputing.com'")
