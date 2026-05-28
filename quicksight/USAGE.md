# QuickSight Schedule Manager - Usage Guide

## Simple Workflow

### Step 1: Initialize Configuration (One-time)

Auto-discover all hourly schedules and populate config.json:

```bash
python3 init_config.py
```

This creates `config.json` with all datasets that have HOURLY schedules and their refresh times.

### Step 2: Add Dataset IDs to dataset.txt

Edit `dataset.txt` and add dataset IDs (one per line):

```
fd01471931-e63c-4427-b89c-8af98c3472c3
another-dataset-id
third-dataset-id
```

### Step 3: Execute Schedule Changes with Action

Run the script with ON or OFF action:

```bash
# Enable hourly schedules for all datasets in dataset.txt
python3 manage_schedules.py ON

# Disable hourly schedules for all datasets in dataset.txt
python3 manage_schedules.py OFF
```

This will:
- For `ON`: Enable the hourly schedule for each dataset
- For `OFF`: Disable the hourly schedule (after validating it exists in config.json)
- Log all actions to `schedule_changes.log`

### Step 4: Verify Changes

View all datasets and their current schedules:

```bash
python3 list_schedules.py
```

View what actions were taken:

```bash
cat schedule_changes.log
```

## How It Works

### config.json
Stores the hourly schedule times for each dataset (auto-populated by init_config.py):

```json
{
  "datasets": {
    "dataset-id-1": {
      "time": "00:15"
    },
    "dataset-id-2": {
      "time": "00:30"
    }
  }
}
```

### dataset.txt
Lists the dataset IDs to manage (you edit this):

```
dataset-id-1
dataset-id-2
dataset-id-3
```

### manage_schedules.py Logic

**Action: ON**
- Reads all dataset IDs from dataset.txt
- For each dataset: Enable the hourly schedule
- Three scenarios:
  1. Has backup entry → Restore from backup (original schedule config)
  2. No backup, schedule exists → No action needed (already ON)
  3. No backup, no schedule → Create new schedule using time from config.json

**Action: OFF**
- Reads all dataset IDs from dataset.txt
- For each dataset:
  - Gets schedule info from QuickSight
  - If no schedule found: logs "already OFF" and skips
  - If schedule found:
    - If dataset in config.json: checks for time mismatch, logs warning if found
    - If dataset NOT in config.json: logs warning, captures info from QuickSight
    - Disables the hourly schedule (saves backup for later restore)

## Examples

### Enable all datasets' hourly schedules

dataset.txt:
```
dataset-1
dataset-2
dataset-3
```

Run:
```bash
python3 manage_schedules.py ON
```

All three datasets will have their hourly schedules enabled.

### Disable specific datasets' hourly schedules

dataset.txt:
```
dataset-1
dataset-2
```

Run:
```bash
python3 manage_schedules.py OFF
```

Both datasets will have their hourly schedules disabled (only if they exist in config.json).

## File Formats

### dataset.txt Format
```
dataset-id
dataset-id
dataset-id
```

Each line contains one dataset ID
- Blank lines are ignored
- Whitespace is trimmed

### config.json Format
```json
{
  "datasets": {
    "dataset-id": {
      "time": "HH:MM"
    }
  }
}
```

Only contains datasets with HOURLY schedules.

## Validation Rules

✅ **Turn ON:**
- Dataset ID is in dataset.txt
- If has backup: Restore from backup
- If no backup but schedule exists: No action (already ON)
- If no backup and no schedule: Create new schedule from config.json time
- All scenarios succeed

✅ **Turn OFF:**
- Dataset ID is in dataset.txt
- Schedule exists in QuickSight
- If in config.json: validates time match (warns if mismatch)
- If NOT in config.json: captures schedule info from QuickSight
- Schedule is disabled and backed up

⚠️ **Turn OFF dataset not in config.json:**
- Allowed - will capture schedule info from QuickSight
- Logged as warning for visibility
- Schedule info saved to backup with actual details

## Usage Examples

### Example 1: Enable two datasets

**dataset.txt:**
```
dataset-123
dataset-456
```

**Command:**
```bash
python3 manage_schedules.py ON
```

**Result:**
- Both datasets will have hourly schedules enabled
- Logs: "ENABLED hourly schedule for dataset-123" and "dataset-456"

### Example 2: Disable with validation

**dataset.txt:**
```
dataset-123
dataset-unknown
```

**config.json:**
```json
{
  "datasets": {
    "dataset-123": {
      "time": "00:15"
    }
  }
}
```

**Command:**
```bash
python3 manage_schedules.py OFF
```

**Result:**
- dataset-123: Disabled successfully
- dataset-unknown: Error logged - "Not found in config.json. Skipping."

## Logging

All actions are logged to `schedule_changes.log`:

```
2024-05-28 10:30:00,123 - INFO - Starting schedule management: action=ON, datasets=2
2024-05-28 10:30:01,456 - INFO - Turning ON hourly schedule for dataset-1
2024-05-28 10:30:02,789 - INFO - ENABLED hourly schedule for dataset-1
2024-05-28 10:30:03,012 - INFO - Schedule already ON for dataset-2, no action needed
2024-05-28 10:30:04,345 - INFO - Schedule management completed for action=ON
```

### Time Mismatch Detection (OFF action)

If schedule time in QuickSight differs from config.json:

```
2024-05-28 10:30:00,123 - WARNING - Time mismatch for dataset-1: config.json has 00:15, QuickSight has 00:30. Saving actual time from QuickSight.
2024-05-28 10:30:01,456 - INFO - DISABLED hourly schedule for dataset-1
```

The actual time from QuickSight is saved to backup, preserving the real configuration.

## Backup & Restore

When a schedule is disabled (OFF action), it's saved to `schedule_backup.json`:

```json
{
  "dataset-id": {
    "ScheduleId": "schedule-uuid",
    "ScheduleFrequency": {
      "Interval": "HOURLY",
      "TimeOfTheDay": "00:15",
      "TimeZone": "Asia/Kolkata"
    },
    "RefreshType": "FULL_REFRESH"
  }
}
```

When you turn it back ON, the exact same schedule is restored from the backup.

## Time Mismatch Handling

### What happens if schedule time in QuickSight differs from config.json?

When turning OFF, if the actual schedule time in QuickSight doesn't match config.json:

1. **Warning is logged** about the mismatch
2. **Actual time from QuickSight is saved** to backup (preserves real config)
3. **Schedule is disabled** normally
4. **When turned back ON**, original schedule is restored (with actual time)

**Example:**
```
config.json: dataset-1 has time "00:15"
QuickSight: dataset-1 actually has "00:30" 

python3 manage_schedules.py OFF
→ WARNING: Time mismatch detected
→ Saves actual 00:30 to backup
→ DISABLED schedule

python3 manage_schedules.py ON
→ Restores 00:30 (actual time, not config.json time)
```

This ensures the real schedule configuration is always preserved and restored.

## Troubleshooting

### "Cannot turn OFF dataset-x: Not found in config.json"

**Reason:** The dataset doesn't have an hourly schedule in config.json.

**Solution:** 
- Only datasets with HOURLY schedules are in config.json
- Check if the dataset actually has an hourly schedule using `list_schedules.py`
- If it does, run `init_config.py` again to refresh config.json

### "Time mismatch" warning in logs

**Reason:** Schedule time in QuickSight doesn't match config.json entry.

**Solution:**
- This is logged as a warning but doesn't prevent the OFF action
- The actual time from QuickSight is saved (correct behavior)
- Update config.json to match if you want consistency: `python3 init_config.py`

### "Usage: python3 manage_schedules.py ON|OFF"

**Reason:** Missing action argument.

**Solution:** 
- Always provide ON or OFF: `python3 manage_schedules.py ON`

### "Can I turn ON a dataset with no backup?"

**Yes!** If no backup exists:
- A new hourly schedule will be created using the time from config.json
- The schedule will refresh hourly at the specified time
- Next time you turn OFF, it will be backed up for future restores

**Example:**
```
config.json: dataset-123 with time "00:15"
schedule_backup.json: empty (no entry for dataset-123)

python3 manage_schedules.py ON
→ Creates new hourly schedule at 00:15 for dataset-123
```

### Script won't run - "ModuleNotFoundError: No module named 'boto3'"

```bash
pip3 install boto3
```

### AWS credentials error

Ensure AWS credentials are configured:
```bash
export AWS_PROFILE=your-profile
# or
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
```

## Cron Integration (Optional)

To automatically enable/disable at a specific time each morning:

```bash
# Edit crontab
crontab -e

# Example: Enable at 8:00 AM
0 8 * * * cd /path/to/quicksight && python3 manage_schedules.py ON

# Example: Disable at 6:00 PM
0 18 * * * cd /path/to/quicksight && python3 manage_schedules.py OFF
```

Then update dataset.txt with the datasets you want to manage.
