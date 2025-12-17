#!/usr/bin/env python3
"""
Scheduler for Weekly Notion Automation
Runs weekly_aggregation.py every Friday at 8:00 AM
"""

import schedule
import time
import logging
import sys
from datetime import datetime
from weekly_aggregation import run_weekly_aggregation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def job():
    """Job function to run weekly aggregation."""
    logger.info("Scheduled job triggered - Running weekly aggregation")
    try:
        run_weekly_aggregation()
    except Exception as e:
        logger.error(f"Error in scheduled job: {str(e)}")


def main():
    """Main scheduler loop."""
    logger.info("Starting Weekly Notion Automation Scheduler")
    logger.info("Scheduled to run every Friday at 8:00 AM")
    
    # Schedule the job
    schedule.every().friday.at("08:00").do(job)
    
    # Optional: Run immediately for testing (comment out in production)
    # logger.info("Running immediately for testing...")
    # job()
    
    # Keep the script running
    logger.info("Scheduler running. Press Ctrl+C to stop.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
        sys.exit(0)


if __name__ == '__main__':
    main()

