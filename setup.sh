#!/bin/bash
# Setup script for Weekly Notion Automation

set -e

echo "=========================================="
echo "Weekly Notion Automation - Setup"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Create a .env file with your NOTION_API_KEY"
echo "2. Run: python test_connection.py"
echo "3. Run: python weekly_aggregation.py"
echo ""
echo "See QUICK_START.md for detailed instructions."

