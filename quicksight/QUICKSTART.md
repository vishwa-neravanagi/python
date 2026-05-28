# Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies
```bash
pip3 install boto3
```

### Step 2: Configure AWS Credentials
```bash
export AWS_PROFILE=your-profile
# or use ~/.aws/credentials file
```

### Step 3: Auto-Populate Configuration
```bash
python3 init_config.py
```

This discovers all your QuickSight datasets and creates `config.json` with all datasets set to `auto_enable: false`.

### Step 4: Customize Configuration
Edit `config.json` and set `auto_enable: true` for datasets where you want hourly schedules to be automatically enabled every morning:

```json
{
  "execution_time": "08:00",
  "timezone": "Asia/Kolkata",
  "datasets": {
    "dataset-id-1": {
      "name": "Sales Data",
      "schedule_type": "HOURLY",
      "auto_enable": true      // ← Change this to true
    },
    "dataset-id-2": {
      "name": "Analytics",
      "schedule_type": "DAILY",
      "auto_enable": false
    }
  }
}
```

### Step 5: Test Manually
```bash
python3 manage_schedules.py
```

Check `schedule_changes.log` to see what actions were taken.

### Step 6: Set Up Automatic Execution
```bash
bash setup_cron.sh
```

Verify the cron job was installed:
```bash
crontab -l | grep manage_schedules
```

## Daily Operations

### View Current Schedules
```bash
python3 list_schedules.py
```

### View Changes Made
```bash
tail schedule_changes.log
```

### Manually Run Schedule Manager
```bash
python3 manage_schedules.py
```

## Configuration Details

### execution_time
Time of day to automatically enable/disable hourly schedules (24-hour format, HH:MM)
- Example: "08:00" for 8 AM
- Example: "20:30" for 8:30 PM

### timezone
IANA timezone identifier for scheduling
- "Asia/Kolkata" (IST)
- "UTC"
- "America/New_York"
- Full list: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

### auto_enable
- `true`: Enable hourly schedule every morning at execution_time
- `false`: Disable hourly schedule every morning at execution_time
- Only applies to HOURLY schedules; DAILY/WEEKLY/MONTHLY are never modified

## What Happens Each Morning

At the configured `execution_time`:

1. For each dataset with `auto_enable: true`:
   - If it has an HOURLY schedule → ensure it's enabled
   - If it has DAILY/WEEKLY/MONTHLY → skip (no change)

2. For each dataset with `auto_enable: false`:
   - If it has an HOURLY schedule → ensure it's disabled
   - If it has DAILY/WEEKLY/MONTHLY → skip (no change)

3. Log all actions to `schedule_changes.log`

## Troubleshooting

### "No datasets found"
- Verify AWS credentials are configured
- Check AWS IAM permissions for QuickSight

### "ModuleNotFoundError: No module named 'boto3'"
```bash
pip3 install boto3
```

### Cron job not running
- Check logs: `tail -f schedule_changes.log`
- Verify job exists: `crontab -l`
- Ensure AWS credentials available in cron environment

## More Information

See [README.md](README.md) for detailed documentation.
