#!/usr/bin/env python3
"""
Weekly Notion Automation
Aggregates data from EasyFlow Daily Metrics to Weekly Success Criteria database.
Runs every Friday at 8 AM.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from notion_client import Client
import pytz

# Load environment variables
load_dotenv()

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'weekly_aggregation_{datetime.now().strftime("%Y%m%d")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Database IDs
EASYFLOW_DAILY_METRICS_DB_ID = os.getenv('EASYFLOW_DAILY_METRICS_DB_ID', '373f0ed0-4d5b-4e8a-9e90-9bc8d7b5a16a')
WEEKLY_SUCCESS_CRITERIA_DB_ID = os.getenv('WEEKLY_SUCCESS_CRITERIA_DB_ID', '9e04bcc9-471d-4372-9e0f-5f0a9111e87b')

# Field IDs for EasyFlow Daily Metrics
DAILY_METRICS_FIELDS = {
    'date': 'dIHs',
    'mrr': 'R%60uR',
    'new_signups': 'kvo%3C',
    'visit_signup_pct': 'QtVP',
    'active_users_30d': 'hp%40%7D',
    'activated_users': 'NOQM',
    'activation_rate_pct': 'PFsb',
    'workflows_run': 'aJMX',
    'workflows_created_today': 'sTE~',
    'active_users_7d_avg': '%5B%7B%3FZ'
}

# Field IDs for Weekly Success Criteria
WEEKLY_FIELDS = {
    'title': 'title',
    'week_starting': 'WikD',
    'new_signups': '~%7BH~',
    'user_calls_booked': 'Ufki',
    'welcome_emails_sent': 'GVjV',
    'tier_achieved': 'tk%40n',
    'minimum_met': 'N_T%7B',
    'good_met': '%5COm%40',
    'great_met': '%5B%3DDh',
    'notes': '_Mhj'
}

# Tier IDs
TIER_IDS = {
    'below_minimum': '4f784ace-fca1-4da1-9c55-22cb23e08906',
    'minimum': '2462be85-3662-415e-819f-33b78fa31a8b',
    'good': 'e73e24e5-ae51-4939-891a-9b85c0424cd1',
    'great': '0244d663-3981-4c07-900e-e654896570b8'
}


def get_notion_client() -> Client:
    """Initialize and return Notion API client."""
    api_key = os.getenv('NOTION_API_KEY')
    if not api_key:
        raise ValueError("NOTION_API_KEY not found in environment variables")
    # Use a valid API version (2022-06-28 is stable and supports database queries)
    return Client(auth=api_key, notion_version='2022-06-28')


def get_week_range(date: Optional[datetime] = None) -> tuple[datetime, datetime]:
    """
    Get Monday-Sunday range for the week containing the given date.
    If no date provided, uses current date.
    """
    if date is None:
        date = datetime.now()
    
    # Get Monday of the week (weekday 0 = Monday)
    days_since_monday = date.weekday()
    monday = date - timedelta(days=days_since_monday)
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get Sunday of the week
    sunday = monday + timedelta(days=6)
    sunday = sunday.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    return monday, sunday


def query_daily_metrics(client: Client, monday: datetime, sunday: datetime) -> List[Dict[str, Any]]:
    """
    Query EasyFlow Daily Metrics database for entries in the week range.
    Returns list of page objects.
    """
    logger.info(f"Querying Daily Metrics from {monday.date()} to {sunday.date()}")
    
    try:
        # Query with date filter using direct API call
        response = client.request(
            path=f"databases/{EASYFLOW_DAILY_METRICS_DB_ID}/query",
            method="POST",
            body={
                "filter": {
                    "and": [
                        {
                            "property": DAILY_METRICS_FIELDS['date'],
                            "date": {
                                "on_or_after": monday.isoformat()
                            }
                        },
                        {
                            "property": DAILY_METRICS_FIELDS['date'],
                            "date": {
                                "on_or_before": sunday.isoformat()
                            }
                        }
                    ]
                },
                "sorts": [
                    {
                        "property": DAILY_METRICS_FIELDS['date'],
                        "direction": "descending"
                    }
                ]
            }
        )
        
        results = response.get('results', [])
        logger.info(f"Found {len(results)} daily metric entries for the week")
        return results
        
    except Exception as e:
        logger.error(f"Error querying Daily Metrics: {str(e)}")
        raise


def extract_number_property(page: Dict, field_id: str) -> Optional[float]:
    """Extract number value from a Notion page property."""
    try:
        prop = page.get('properties', {}).get(field_id, {})
        if prop.get('type') == 'number':
            return prop.get('number')
        return None
    except Exception as e:
        logger.warning(f"Error extracting property {field_id}: {str(e)}")
        return None


def extract_date_property(page: Dict, field_id: str) -> Optional[datetime]:
    """Extract date value from a Notion page property."""
    try:
        prop = page.get('properties', {}).get(field_id, {})
        if prop.get('type') == 'date':
            date_str = prop.get('date', {}).get('start')
            if date_str:
                # Parse ISO format date
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return None
    except Exception as e:
        logger.warning(f"Error extracting date property {field_id}: {str(e)}")
        return None


def aggregate_weekly_data(pages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate data from daily metrics pages.
    Returns aggregated metrics dictionary.
    """
    logger.info(f"Aggregating data from {len(pages)} pages")
    
    # Initialize aggregation variables
    new_signups_sum = 0
    workflows_run_sum = 0
    workflows_created_sum = 0
    
    active_users_30d_values = []
    activated_users_values = []
    visit_signup_pct_values = []
    active_users_7d_avg_values = []
    
    mrr_values = []
    
    for page in pages:
        # Sum fields
        new_signups = extract_number_property(page, DAILY_METRICS_FIELDS['new_signups'])
        if new_signups is not None:
            new_signups_sum += new_signups
        
        workflows_run = extract_number_property(page, DAILY_METRICS_FIELDS['workflows_run'])
        if workflows_run is not None:
            workflows_run_sum += workflows_run
        
        workflows_created = extract_number_property(page, DAILY_METRICS_FIELDS['workflows_created_today'])
        if workflows_created is not None:
            workflows_created_sum += workflows_created
        
        # Average fields
        active_users_30d = extract_number_property(page, DAILY_METRICS_FIELDS['active_users_30d'])
        if active_users_30d is not None:
            active_users_30d_values.append(active_users_30d)
        
        activated_users = extract_number_property(page, DAILY_METRICS_FIELDS['activated_users'])
        if activated_users is not None:
            activated_users_values.append(activated_users)
        
        visit_signup_pct = extract_number_property(page, DAILY_METRICS_FIELDS['visit_signup_pct'])
        if visit_signup_pct is not None:
            visit_signup_pct_values.append(visit_signup_pct)
        
        active_users_7d_avg = extract_number_property(page, DAILY_METRICS_FIELDS['active_users_7d_avg'])
        if active_users_7d_avg is not None:
            active_users_7d_avg_values.append(active_users_7d_avg)
        
        # Latest MRR
        mrr = extract_number_property(page, DAILY_METRICS_FIELDS['mrr'])
        if mrr is not None:
            mrr_values.append(mrr)
    
    # Calculate averages
    active_users_30d_avg = sum(active_users_30d_values) / len(active_users_30d_values) if active_users_30d_values else None
    activated_users_avg = sum(activated_users_values) / len(activated_users_values) if activated_users_values else None
    visit_signup_pct_avg = sum(visit_signup_pct_values) / len(visit_signup_pct_values) if visit_signup_pct_values else None
    active_users_7d_avg = sum(active_users_7d_avg_values) / len(active_users_7d_avg_values) if active_users_7d_avg_values else None
    
    # Get latest MRR (most recent non-null value)
    latest_mrr = mrr_values[0] if mrr_values else None
    
    aggregated = {
        'new_signups': int(new_signups_sum),
        'workflows_run': int(workflows_run_sum),
        'workflows_created': int(workflows_created_sum),
        'active_users_30d_avg': active_users_30d_avg,
        'activated_users_avg': activated_users_avg,
        'visit_signup_pct_avg': visit_signup_pct_avg,
        'active_users_7d_avg': active_users_7d_avg,
        'mrr': latest_mrr,
        # These fields don't exist in Daily Metrics - set to 0
        'user_calls_booked': 0,
        'welcome_emails_sent': 0
    }
    
    logger.info(f"Aggregated metrics: {aggregated}")
    return aggregated


def calculate_tier(signups: int, calls: int, emails: int) -> tuple[str, bool, bool, bool]:
    """
    Calculate tier based on signups, calls, and emails.
    Returns: (tier_id, minimum_met, good_met, great_met)
    """
    # Below Minimum: Less than 1 signup, 0 calls, 0 emails
    if signups < 1 and calls == 0 and emails == 0:
        return (TIER_IDS['below_minimum'], False, False, False)
    
    # Minimum: 1+ signup OR 1+ call OR 1+ email
    minimum_met = signups >= 1 or calls >= 1 or emails >= 1
    
    # Good: 3+ signups AND 2+ calls AND 2+ emails
    good_met = signups >= 3 and calls >= 2 and emails >= 2
    
    # Great: 5+ signups AND 5+ calls AND 5+ emails
    great_met = signups >= 5 and calls >= 5 and emails >= 5
    
    # Determine tier
    if great_met:
        tier_id = TIER_IDS['great']
    elif good_met:
        tier_id = TIER_IDS['good']
    elif minimum_met:
        tier_id = TIER_IDS['minimum']
    else:
        tier_id = TIER_IDS['below_minimum']
    
    return (tier_id, minimum_met, good_met, great_met)


def format_week_name(monday: datetime, sunday: datetime) -> str:
    """Format week name as 'Week of [Monday Date] - [Sunday Date], [Year]'."""
    monday_str = monday.strftime('%b %d')
    sunday_str = sunday.strftime('%b %d')
    year = monday.year
    
    # Handle year change
    if monday.year != sunday.year:
        return f"Week of {monday_str}, {monday.year} - {sunday_str}, {sunday.year}"
    else:
        return f"Week of {monday_str} - {sunday_str}, {year}"


def find_existing_week_entry(client: Client, monday: datetime) -> Optional[str]:
    """
    Find existing Weekly Success Criteria entry for the given week.
    Returns page ID if found, None otherwise.
    """
    try:
        # Query for entries with matching week_starting date
        response = client.request(
            path=f"databases/{WEEKLY_SUCCESS_CRITERIA_DB_ID}/query",
            method="POST",
            body={
                "filter": {
                    "property": WEEKLY_FIELDS['week_starting'],
                    "date": {
                        "equals": monday.date().isoformat()
                    }
                }
            }
        )
        
        results = response.get('results', [])
        if results:
            page_id = results[0]['id']
            logger.info(f"Found existing entry for week starting {monday.date()}: {page_id}")
            return page_id
        return None
        
    except Exception as e:
        logger.warning(f"Error finding existing week entry: {str(e)}")
        return None


def create_weekly_entry(client: Client, monday: datetime, sunday: datetime, 
                       aggregated: Dict[str, Any], tier_id: str, 
                       minimum_met: bool, good_met: bool, great_met: bool) -> str:
    """Create a new Weekly Success Criteria entry."""
    week_name = format_week_name(monday, sunday)
    
    logger.info(f"Creating new weekly entry: {week_name}")
    
    properties = {
        WEEKLY_FIELDS['title']: {
            'title': [{'text': {'content': week_name}}]
        },
        WEEKLY_FIELDS['week_starting']: {
            'date': {'start': monday.date().isoformat()}
        },
        WEEKLY_FIELDS['new_signups']: {
            'number': aggregated['new_signups']
        },
        WEEKLY_FIELDS['user_calls_booked']: {
            'number': aggregated['user_calls_booked']
        },
        WEEKLY_FIELDS['welcome_emails_sent']: {
            'number': aggregated['welcome_emails_sent']
        },
        WEEKLY_FIELDS['tier_achieved']: {
            'select': {'id': tier_id}
        },
        WEEKLY_FIELDS['minimum_met']: {
            'checkbox': minimum_met
        },
        WEEKLY_FIELDS['good_met']: {
            'checkbox': good_met
        },
        WEEKLY_FIELDS['great_met']: {
            'checkbox': great_met
        }
    }
    
    # Add notes with aggregated metrics summary
    notes_content = f"Aggregated from Daily Metrics:\n"
    notes_content += f"- Workflows Run: {aggregated['workflows_run']}\n"
    notes_content += f"- Workflows Created: {aggregated['workflows_created']}\n"
    if aggregated['mrr'] is not None:
        notes_content += f"- MRR: ${aggregated['mrr']:,.2f}\n"
    if aggregated['active_users_30d_avg'] is not None:
        notes_content += f"- Active Users (30d) Avg: {aggregated['active_users_30d_avg']:.2f}\n"
    if aggregated['activated_users_avg'] is not None:
        notes_content += f"- Activated Users Avg: {aggregated['activated_users_avg']:.2f}\n"
    
    properties[WEEKLY_FIELDS['notes']] = {
        'rich_text': [{'text': {'content': notes_content}}]
    }
    
    try:
        response = client.pages.create(
            parent={'database_id': WEEKLY_SUCCESS_CRITERIA_DB_ID},
            properties=properties
        )
        page_id = response['id']
        logger.info(f"Successfully created weekly entry: {page_id}")
        return page_id
        
    except Exception as e:
        logger.error(f"Error creating weekly entry: {str(e)}")
        raise


def update_weekly_entry(client: Client, page_id: str, monday: datetime, sunday: datetime,
                       aggregated: Dict[str, Any], tier_id: str,
                       minimum_met: bool, good_met: bool, great_met: bool) -> None:
    """Update an existing Weekly Success Criteria entry."""
    week_name = format_week_name(monday, sunday)
    
    logger.info(f"Updating existing weekly entry: {week_name}")
    
    properties = {
        WEEKLY_FIELDS['title']: {
            'title': [{'text': {'content': week_name}}]
        },
        WEEKLY_FIELDS['new_signups']: {
            'number': aggregated['new_signups']
        },
        WEEKLY_FIELDS['user_calls_booked']: {
            'number': aggregated['user_calls_booked']
        },
        WEEKLY_FIELDS['welcome_emails_sent']: {
            'number': aggregated['welcome_emails_sent']
        },
        WEEKLY_FIELDS['tier_achieved']: {
            'select': {'id': tier_id}
        },
        WEEKLY_FIELDS['minimum_met']: {
            'checkbox': minimum_met
        },
        WEEKLY_FIELDS['good_met']: {
            'checkbox': good_met
        },
        WEEKLY_FIELDS['great_met']: {
            'checkbox': great_met
        }
    }
    
    # Update notes
    notes_content = f"Aggregated from Daily Metrics:\n"
    notes_content += f"- Workflows Run: {aggregated['workflows_run']}\n"
    notes_content += f"- Workflows Created: {aggregated['workflows_created']}\n"
    if aggregated['mrr'] is not None:
        notes_content += f"- MRR: ${aggregated['mrr']:,.2f}\n"
    if aggregated['active_users_30d_avg'] is not None:
        notes_content += f"- Active Users (30d) Avg: {aggregated['active_users_30d_avg']:.2f}\n"
    if aggregated['activated_users_avg'] is not None:
        notes_content += f"- Activated Users Avg: {aggregated['activated_users_avg']:.2f}\n"
    
    properties[WEEKLY_FIELDS['notes']] = {
        'rich_text': [{'text': {'content': notes_content}}]
    }
    
    try:
        client.pages.update(page_id=page_id, properties=properties)
        logger.info(f"Successfully updated weekly entry: {page_id}")
        
    except Exception as e:
        logger.error(f"Error updating weekly entry: {str(e)}")
        raise


def run_weekly_aggregation(date: Optional[datetime] = None) -> None:
    """
    Main function to run weekly aggregation.
    If date is provided, aggregates for that week. Otherwise uses current week.
    """
    logger.info("=" * 60)
    logger.info("Starting Weekly Aggregation")
    logger.info("=" * 60)
    
    try:
        # Get week range
        monday, sunday = get_week_range(date)
        logger.info(f"Week range: {monday.date()} to {sunday.date()}")
        
        # Initialize Notion client
        client = get_notion_client()
        
        # Query daily metrics
        daily_pages = query_daily_metrics(client, monday, sunday)
        
        if not daily_pages:
            logger.warning(f"No daily metrics found for week {monday.date()} to {sunday.date()}")
            logger.warning("Creating entry with zero values")
            aggregated = {
                'new_signups': 0,
                'workflows_run': 0,
                'workflows_created': 0,
                'active_users_30d_avg': None,
                'activated_users_avg': None,
                'visit_signup_pct_avg': None,
                'active_users_7d_avg': None,
                'mrr': None,
                'user_calls_booked': 0,
                'welcome_emails_sent': 0
            }
        else:
            # Aggregate data
            aggregated = aggregate_weekly_data(daily_pages)
        
        # Calculate tier
        tier_id, minimum_met, good_met, great_met = calculate_tier(
            aggregated['new_signups'],
            aggregated['user_calls_booked'],
            aggregated['welcome_emails_sent']
        )
        
        logger.info(f"Tier calculation: minimum_met={minimum_met}, good_met={good_met}, great_met={great_met}")
        
        # Check if entry already exists
        existing_page_id = find_existing_week_entry(client, monday)
        
        if existing_page_id:
            # Update existing entry
            update_weekly_entry(
                client, existing_page_id, monday, sunday,
                aggregated, tier_id, minimum_met, good_met, great_met
            )
        else:
            # Create new entry
            create_weekly_entry(
                client, monday, sunday,
                aggregated, tier_id, minimum_met, good_met, great_met
            )
        
        logger.info("=" * 60)
        logger.info("Weekly Aggregation Completed Successfully")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"Weekly Aggregation Failed: {str(e)}")
        logger.error("=" * 60)
        raise


if __name__ == '__main__':
    try:
        run_weekly_aggregation()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)

