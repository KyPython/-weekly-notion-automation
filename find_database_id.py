#!/usr/bin/env python3
"""
Helper script to find database IDs from Notion URLs.
Use this if you need to verify or find your database IDs.
"""

import os
import re
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

def extract_database_id_from_url(url):
    """Extract database ID from a Notion URL."""
    # Pattern: https://www.notion.so/{workspace}/{database_id}?v=...
    # Or: https://www.notion.so/{database_id}
    patterns = [
        r'notion\.so/[^/]+/([a-f0-9]{32})',
        r'notion\.so/([a-f0-9]{32})',
        r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            db_id = match.group(1)
            # Format as UUID if needed
            if len(db_id) == 32:
                db_id = f"{db_id[:8]}-{db_id[8:12]}-{db_id[12:16]}-{db_id[16:20]}-{db_id[20:]}"
            return db_id
    return None

def list_accessible_databases():
    """List all databases accessible to the integration."""
    api_key = os.getenv('NOTION_API_KEY')
    if not api_key:
        print("❌ NOTION_API_KEY not found in .env file")
        return
    
    try:
        client = Client(auth=api_key)
        
        print("=" * 60)
        print("Searching for accessible databases...")
        print("=" * 60)
        
        # Search for all accessible content (databases will be included)
        response = client.search(page_size=100)
        
        results = response.get('results', [])
        # Filter for databases
        databases = [r for r in results if r.get('object') == 'database']
        
        if not databases:
            print("\n❌ No databases found.")
            print("\nThis means:")
            print("1. Your integration hasn't been granted access to any databases yet")
            print("2. OR the databases are nested inside pages that aren't shared")
            print("\nTo fix:")
            print("- Go to each database in Notion")
            print("- Click '...' → 'Connections' → 'Add connections'")
            print("- Select your integration")
            return
        
        print(f"\n✅ Found {len(databases)} accessible database(s):\n")
        
        for i, db in enumerate(databases, 1):
            title = "Untitled"
            if db.get('title'):
                title_parts = db['title']
                if isinstance(title_parts, list) and len(title_parts) > 0:
                    title = title_parts[0].get('plain_text', 'Untitled')
            
            db_id = db['id']
            print(f"{i}. {title}")
            print(f"   ID: {db_id}")
            print()
        
        print("=" * 60)
        print("\nTo use a database ID, update your .env file or the script.")
        print("Current database IDs in use:")
        print(f"  Daily Metrics: 373f0ed0-4d5b-4e8a-9e90-9bc8d7b5a16a")
        print(f"  Weekly Success: 9e04bcc9-471d-4372-9e0f-5f0a9111e87b")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nMake sure:")
        print("1. Your NOTION_API_KEY is correct in .env")
        print("2. Your integration has been created at https://www.notion.so/my-integrations")

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Notion Database ID Finder")
    print("=" * 60)
    print("\nThis script lists all databases your integration can access.")
    print("If your databases don't appear, grant access in Notion first.\n")
    
    list_accessible_databases()
    
    print("\n" + "=" * 60)
    print("How to grant access:")
    print("=" * 60)
    print("1. Open your database in Notion")
    print("2. Click '...' (three dots) in the top right")
    print("3. Click 'Connections' → 'Add connections'")
    print("4. Select your integration")
    print("5. Run this script again to verify\n")

