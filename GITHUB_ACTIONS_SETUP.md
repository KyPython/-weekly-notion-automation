# GitHub Actions Setup Guide

This automation runs automatically every Friday at 8:00 AM using GitHub Actions.

## Setup Steps

### 1. Add GitHub Secrets

Go to your repository: https://github.com/KyPython/-weekly-notion-automation

1. Click **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add these secrets:

#### Required Secrets:

**`NOTION_API_KEY`**
- Value: Your Notion API key (starts with `ntn_`)
- Same key you use for your daily metrics automation

**`EASYFLOW_DAILY_METRICS_DB_ID`** (Optional - defaults are set in code)
- Value: `373f0ed0-4d5b-4e8a-9e90-9bc8d7b5a16a`

**`WEEKLY_SUCCESS_CRITERIA_DB_ID`** (Optional - defaults are set in code)
- Value: `9e04bcc9-471d-4372-9e0f-5f0a9111e87b`

### 2. Adjust Schedule Time

The workflow runs every Friday at **1 PM UTC** (which is **8 AM EST**).

To change the time, edit `.github/workflows/weekly-aggregation.yml`:

```yaml
- cron: '0 13 * * 5'  # Friday at 1 PM UTC (8 AM EST)
```

**Cron format:** `minute hour day month weekday`
- `0 13 * * 5` = Friday at 1 PM UTC (8 AM EST)
- `0 16 * * 5` = Friday at 4 PM UTC (8 AM PST)
- `0 8 * * 5` = Friday at 8 AM UTC

**Time zone conversion:**
- EST (UTC-5): 8 AM EST = 1 PM UTC
- PST (UTC-8): 8 AM PST = 4 PM UTC
- CST (UTC-6): 8 AM CST = 2 PM UTC

### 3. Test the Workflow

After adding secrets, you can:

1. **Manual trigger:** Go to **Actions** tab → **Weekly Notion Aggregation** → **Run workflow**
2. **Wait for schedule:** It will run automatically every Friday

### 4. Monitor Runs

- Go to **Actions** tab to see workflow runs
- Click on a run to see logs
- If it fails, logs are uploaded as artifacts

## How It Works

1. **Schedule:** GitHub Actions triggers the workflow every Friday at the scheduled time
2. **Environment:** Sets up Python and installs dependencies
3. **Execution:** Runs `weekly_aggregation.py` with your API key from secrets
4. **Logging:** Logs are available in the Actions tab
5. **Error Handling:** If it fails, logs are saved as artifacts

## Advantages Over Local Scheduling

✅ **No server needed** - Runs in GitHub's cloud  
✅ **Reliable** - GitHub handles scheduling  
✅ **Logs** - View execution history in GitHub  
✅ **Manual trigger** - Can run on-demand from GitHub UI  
✅ **Notifications** - GitHub can email you on failures  

## Troubleshooting

**Workflow not running?**
- Check that secrets are set correctly
- Verify cron schedule syntax
- Check Actions tab for error messages

**Authentication errors?**
- Verify `NOTION_API_KEY` secret is correct
- Ensure integration has access to both databases

**Database errors?**
- Check that database IDs in secrets match your databases
- Verify integration permissions in Notion

## Manual Run

You can trigger manually anytime:
1. Go to **Actions** tab
2. Select **Weekly Notion Aggregation** workflow
3. Click **Run workflow** → **Run workflow**

