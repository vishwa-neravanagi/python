# QuickSight Schedule Manager

Automated management of QuickSight dataset refresh schedules with support for enabling/disabling hourly schedules while leaving daily schedules unchanged.

## Files Overview

- **init_config.py** - Auto-discover datasets and generate config.json
- **list_schedules.py** - List all datasets with their current refresh schedules
- **manage_schedules.py** - Automatically enable/disable hourly schedules based on configuration
- **config.json** - Configuration file for datasets and execution settings
- **schedule_backup.json** - Backup of disabled schedules (auto-generated)
- **setup_cron.sh** - Helper script to set up cron job for automatic execution
- **schedule_changes.log** - Activity log of all schedule changes (auto-generated)

## Setup

### 1. Install Dependencies

```bash
pip3 install boto3
```

### 2. Configure AWS Credentials

Ensure AWS credentials are configured (via `~/.aws/credentials` or environment variables):
```bash
export AWS_PROFILE=your-profile
# or
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
```

### 3. Auto-Populate config.json

Run the initialization script to discover all datasets and auto-populate the configuration:

```bash
python3 init_config.py
```

This will:
- Discover all QuickSight datasets in your account
- Detect their current schedule types (Hourly/Daily/Weekly/Monthly)
- Generate `config.json` with all datasets set to `auto_enable: false`
- Backup any existing config to `config.json.backup`

Output example:
```
Discovering all QuickSight datasets...
  ✓ Sales Data (DAILY)
  ✓ Analytics Dataset (HOURLY)
  ✓ Customer Info (MONTHLY)

✓ Configuration saved to config.json
  Total datasets: 3
  Default auto_enable: false (change to true for datasets to auto-enable hourly schedules)
```

### 4. Update config.json (Optional)

After auto-population, edit `config.json` to customize settings:

- Change `execution_time` to desired morning time (HH:MM format)
- Change `timezone` if needed
- Set `auto_enable: true` for datasets where you want hourly schedules to be automatically enabled every morning

Example:

```json
{
  "execution_time": "08:00",
  "timezone": "Asia/Kolkata",
  "datasets": {
    "dataset-id-1": {
      "name": "Dataset Name",
      "auto_enable": true
    },
    "dataset-id-2": {
      "name": "Another Dataset",
      "auto_enable": false
    }
  }
}
```

**Settings:**
- `execution_time`: Time to run the schedule manager each morning (HH:MM format)
- `timezone`: Timezone for execution (e.g., Asia/Kolkata, UTC, America/New_York)
- `datasets`: Map of dataset IDs with their configuration
  - `name`: Human-readable dataset name
  - `auto_enable`: `true` to enable hourly schedules, `false` to disable

## Usage

### 0. Initialize Configuration (First Time Only)

Auto-populate config.json with all datasets:

```bash
python3 init_config.py
```

Then customize the generated config.json as needed (set `auto_enable: true` for datasets you want to manage).

### 1. List Current Schedules

View all datasets and their current refresh schedules:

```bash
python3 list_schedules.py
```

Output shows:
- Dataset Name
- Dataset ID
- Schedule Type (Hourly/Daily/Weekly/Monthly/None)
- Time (specific minute for hourly, HH:MM for others)
- Enabled status (Yes/No)

### 2. Manually Manage Schedules

Run the schedule manager manually to apply enable/disable changes immediately:

```bash
python3 manage_schedules.py
```

This will:
- Read configuration from config.json
- For datasets with HOURLY schedules:
  - Enable if `auto_enable: true` and currently disabled
  - Disable if `auto_enable: false` and currently enabled
- Skip DAILY/WEEKLY/MONTHLY schedules
- Log all actions to schedule_changes.log

### 3. Set Up Automatic Execution

Install a cron job to run the schedule manager every morning at the configured time:

```bash
bash setup_cron.sh
```

Verify the cron job was installed:
```bash
crontab -l | grep manage_schedules.py
```

## How It Works

### Enable/Disable Logic

- **When `auto_enable: true`**: 
  - If hourly schedule exists and is disabled → enable it
  - If hourly schedule exists and is already enabled → no action
  - If no hourly schedule exists → skip (create new schedules manually via QuickSight console)

- **When `auto_enable: false`**:
  - If hourly schedule exists and is enabled → disable it (save backup)
  - If hourly schedule exists and is already disabled → no action
  - If no hourly schedule exists → skip

- **Daily/Weekly/Monthly schedules**: Always skipped, never modified

### Schedule Backup

When a schedule is disabled, its full configuration is saved to `schedule_backup.json`:

```json
{
  "dataset-id": {
    "ScheduleId": "schedule-id",
    "ScheduleFrequency": {
      "Interval": "HOURLY",
      "TimeOfTheDay": "00:15",
      "TimeZone": "Asia/Kolkata"
    },
    "RefreshType": "FULL_REFRESH"
  }
}
```

When re-enabled, the schedule is restored with the exact same configuration.

### Activity Logging

All actions are logged to `schedule_changes.log`:

```
2024-05-28 08:00:00,123 - INFO - Starting schedule management
2024-05-28 08:00:01,456 - INFO - Enabling hourly schedule for Dataset Name
2024-05-28 08:00:02,789 - INFO - Skipping Another Dataset - schedule is DAILY, not HOURLY
2024-05-28 08:00:03,012 - INFO - Schedule management completed
```

## AWS Region

Default region: **ap-south-1** (Asia Pacific - Mumbai)

To use a different region, edit the script files and change:
```python
client = boto3.client('quicksight', region_name='your-region')
```

## Troubleshooting

### Scripts won't run - boto3 not installed

```bash
pip3 install boto3
```

### "No dataset IDs found in dataset.txt"

The list_schedules.py script reads from dataset.txt. Add dataset IDs there, or it will list all datasets in your account.

### Cron job not running

1. Verify it's installed: `crontab -l`
2. Check logs: `tail -f schedule_changes.log`
3. Ensure AWS credentials are available in the cron environment
4. Check system logs: `log stream --predicate 'eventMessage contains[cd] "manage_schedules"'`

### Schedule changes not applied

1. Check `schedule_changes.log` for errors
2. Verify AWS IAM permissions include:
   - `quicksight:ListRefreshSchedules`
   - `quicksight:CreateRefreshSchedule`
   - `quicksight:DeleteRefreshSchedule`
   - `quicksight:DescribeDataSet`

### Can't re-enable schedule

If you manually delete a schedule without using this script, the backup won't exist. Create a new schedule via QuickSight console or update schedule_backup.json with the correct configuration and run manage_schedules.py.

## API Reference

### QuickSight APIs Used

- `list_data_sets()` - List all datasets in account
- `describe_data_set()` - Get dataset details
- `list_refresh_schedules()` - Get all schedules for a dataset
- `delete_refresh_schedule()` - Disable (delete) a schedule
- `create_refresh_schedule()` - Enable (restore) a schedule

### Config JSON Schema

```json
{
  "execution_time": "string (HH:MM format)",
  "timezone": "string (IANA timezone)",
  "datasets": {
    "dataset-id": {
      "name": "string",
      "auto_enable": "boolean"
    }
  }
}
```
