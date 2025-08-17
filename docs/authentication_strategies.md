# Authentication Strategies for Snowflake Applications

## 🔐 **TOML Secrets File Explained**

### **What is secrets.toml?**
The `secrets.toml` file is Streamlit's secure way to store sensitive configuration data (passwords, API keys, connection strings) outside of your code.

```toml
[snowflake]
user = "your_username"
password = "your_password"  
account = "abc12345.snowflakecomputing.com"
warehouse = "COMPUTE_WH"
```

### **How it works:**
- **Local Development**: File stored in `.streamlit/secrets.toml`
- **Production**: Environment variables or secure vault
- **Access in Code**: `st.secrets["snowflake"]["user"]`
- **Security**: File is gitignored, never committed to repo

## 🏗️ **Authentication by Deployment Type**

### **1. Snowflake-Managed Streamlit (SiS)**
```python
# NO secrets.toml needed!
# Streamlit-in-Snowflake uses automatic authentication
import streamlit as st
import snowflake.snowpark.context as context

# Automatic authentication - no credentials needed
session = context.get_active_session()

# Direct access to Cortex
result = session.sql("SELECT SNOWFLAKE.CORTEX.SUMMARIZE('text')").collect()
```

**Advantages:**
- ✅ Zero credential management
- ✅ Automatic authentication  
- ✅ Built-in security
- ✅ No network latency

### **2. External Applications (Your Current Setup)**
```python
# Requires explicit credentials
import snowflake.connector

conn = snowflake.connector.connect(
    user=st.secrets["snowflake"]["user"],
    password=st.secrets["snowflake"]["password"],
    account=st.secrets["snowflake"]["account"]
)
```

**Authentication Options:**
- **Username/Password** (current approach)
- **Key Pair Authentication** (more secure)
- **OAuth** (enterprise integration)
- **JWT tokens** (for APIs)

### **3. Snowflake Container Services (SPCS)**
```python
# Similar to external, but with service accounts
import snowflake.connector
import os

conn = snowflake.connector.connect(
    user=os.environ['SNOWFLAKE_USER'],
    private_key=load_private_key(),  # From mounted secrets
    account=os.environ['SNOWFLAKE_ACCOUNT']
)
```

## 🚀 **Cortex Analyst REST API Integration**

### **For External Applications:**

```python
import requests
import jwt
import time

class SnowflakeCortexClient:
    def __init__(self, account, user, private_key):
        self.account = account
        self.user = user
        self.private_key = private_key
        self.base_url = f"https://{account}.snowflakecomputing.com"
    
    def get_jwt_token(self):
        # Generate JWT token for authentication
        payload = {
            'iss': f"{self.account}.{self.user}",
            'sub': f"{self.account}.{self.user}",
            'iat': int(time.time()),
            'exp': int(time.time()) + 3600
        }
        return jwt.encode(payload, self.private_key, algorithm='RS256')
    
    def call_cortex_analyst(self, question, semantic_model):
        headers = {
            'Authorization': f'Bearer {self.get_jwt_token()}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'question': question,
            'semantic_model': semantic_model
        }
        
        response = requests.post(
            f"{self.base_url}/api/v2/cortex/analyst",
            headers=headers,
            json=data
        )
        return response.json()

# Usage
client = SnowflakeCortexClient(
    account="your_account",
    user="your_user", 
    private_key=load_private_key()
)

result = client.call_cortex_analyst(
    question="What are the key insights from recent emails?",
    semantic_model="email_semantic_model"
)
```

### **For SPCS Containers:**

```yaml
# docker-compose.yml for SPCS
services:
  email-processor:
    image: your-registry/email-processor:latest
    environment:
      - SNOWFLAKE_ACCOUNT=${SNOWFLAKE_ACCOUNT}
      - SNOWFLAKE_USER=${SNOWFLAKE_USER}
    volumes:
      - snowflake-keys:/etc/snowflake/keys:ro
    secrets:
      - private_key
```

```python
# In container
def get_snowflake_connection():
    return snowflake.connector.connect(
        user=os.environ['SNOWFLAKE_USER'],
        private_key_path='/etc/snowflake/keys/private_key.p8',
        account=os.environ['SNOWFLAKE_ACCOUNT']
    )
```

## 🔄 **Migration Path: External → Snowflake-Managed**

### **Current (External Streamlit):**
```python
# Requires secrets.toml
conn = snowflake.connector.connect(
    user=st.secrets["snowflake"]["user"],
    password=st.secrets["snowflake"]["password"],
    account=st.secrets["snowflake"]["account"]
)
```

### **Migrated (Streamlit-in-Snowflake):**
```python
# No secrets needed!
session = context.get_active_session()
```

## 📊 **Comparison Matrix**

| Deployment Type | Auth Method | Secrets Mgmt | Cortex Access | Complexity |
|----------------|-------------|--------------|---------------|------------|
| **SiS** | Automatic | None | Direct SQL | Low |
| **External** | Manual | secrets.toml | REST API | Medium |
| **SPCS** | Service Account | K8s Secrets | REST API | High |

## 🎯 **Recommendations**

### **For Development/Testing:**
- Use external Streamlit with secrets.toml (your current setup)
- Easy to iterate and debug

### **For Production:**
- **Small/Medium Scale**: Migrate to Streamlit-in-Snowflake
- **Large Scale/Enterprise**: SPCS with proper secret management
- **API Integration**: External with JWT authentication

### **Security Best Practices:**
1. **Never commit secrets** to version control
2. **Use key-pair auth** over passwords
3. **Rotate credentials** regularly
4. **Implement proper RBAC** in Snowflake
5. **Use service accounts** for production
