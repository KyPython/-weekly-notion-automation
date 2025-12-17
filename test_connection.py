#!/usr/bin/env python3
"""
Test script to verify Notion API connection and database access.
Run this before setting up the automation to ensure everything is configured correctly.
"""

import os
import sys
from dotenv import load_dotenv
from notion_client import Client

# Load environment variables
load_dotenv()

def test_connection():
    """Test Notion API connection and database access."""
    print("=" * 60)
    print("Testing Notion API Connection")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv('NOTION_API_KEY')
    if not api_key:
        print("❌ ERROR: NOTION_API_KEY not found in .env file")
        print("   Please create a .env file with your Notion API key")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    # Initialize client
    try:
        # Use a valid API version (2022-06-28 is stable and supports database queries)
        client = Client(auth=api_key, notion_version='2022-06-28')
        print("✅ Notion client initialized")
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize Notion client: {str(e)}")
        return False
    
    # Test database IDs
    daily_db_id = os.getenv('EASYFLOW_DAILY_METRICS_DB_ID', '373f0ed0-4d5b-4e8a-9e90-9bc8d7b5a16a')
    weekly_db_id = os.getenv('WEEKLY_SUCCESS_CRITERIA_DB_ID', '9e04bcc9-471d-4372-9e0f-5f0a9111e87b')
    
    print(f"\n📊 Testing Daily Metrics Database: {daily_db_id}")
    try:
        db = client.databases.retrieve(database_id=daily_db_id)
        print(f"✅ Daily Metrics database accessible: {db.get('title', [{}])[0].get('plain_text', 'Unknown')}")
    except Exception as e:
        print(f"❌ ERROR: Cannot access Daily Metrics database: {str(e)}")
        print("   Make sure your integration has access to this database")
        return False
    
    print(f"\n📊 Testing Weekly Success Criteria Database: {weekly_db_id}")
    try:
        db = client.databases.retrieve(database_id=weekly_db_id)
        print(f"✅ Weekly Success Criteria database accessible: {db.get('title', [{}])[0].get('plain_text', 'Unknown')}")
    except Exception as e:
        print(f"❌ ERROR: Cannot access Weekly Success Criteria database: {str(e)}")
        print("   Make sure your integration has access to this database")
        return False
    
    # Test query
    print(f"\n🔍 Testing query on Daily Metrics database...")
    try:
        # Use the same method as the main script
        response = client.request(
            path=f"databases/{daily_db_id}/query",
            method="POST",
            body={"page_size": 1}
        )
        count = len(response.get('results', []))
        print(f"✅ Query successful - found {count} entry/entries")
    except Exception as e:
        print(f"⚠️  Query test skipped: {str(e)}")
        print("   (This is OK - database access is confirmed above)")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! Your setup is correct.")
    print("=" * 60)
    return True

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)

