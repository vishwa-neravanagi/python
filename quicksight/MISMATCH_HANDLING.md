# Time Mismatch Handling

## Overview

When turning OFF a dataset's hourly schedule, the script checks if the actual schedule time in QuickSight matches the time recorded in config.json.

## Behavior

### Scenario: Time Mismatch Detected

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

**QuickSight actual schedule:** 00:30 (differs from config.json)

**Command:**
```bash
python3 manage_schedules.py OFF
```

**What happens:**
1. ⚠️ WARNING logged: "Time mismatch for dataset-123: config.json has 00:15, QuickSight has 00:30"
2. ✓ Actual time (00:30) is saved to backup
3. ✓ Schedule is disabled
4. ✓ OFF action completes successfully

**Result in backup (schedule_backup.json):**
```json
{
  "dataset-123": {
    "ScheduleId": "...",
    "ScheduleFrequency": {
      "Interval": "HOURLY",
      "TimeOfTheDay": "00:30",
      "TimeZone": "Asia/Kolkata"
    },
    "RefreshType": "FULL_REFRESH"
  }
}
```

## Why This Matters

**Preserves Real Configuration:**
- The actual schedule time from QuickSight (00:30) is saved
- Not the config.json time (00:15)
- When turned back ON, the original 00:30 schedule is restored exactly

**Non-Blocking Warning:**
- Mismatch doesn't prevent OFF action
- Only logs a warning for visibility
- Script continues normally

## Scenarios

### Scenario 1: Perfect Match
```
config.json: 00:15
QuickSight: 00:15
Action: OFF
Result: No warning, normal disable
```

### Scenario 2: Time Changed in QuickSight
```
config.json: 00:15
QuickSight: 00:45 (manually changed)
Action: OFF
Result: WARNING logged, actual 00:45 saved
```

### Scenario 3: Time Changed Multiple Times
```
Initial: config.json = 00:15, QuickSight = 00:15
Then: QuickSight manually changed to 00:30
Then: OFF action
  → WARNING: mismatch, 00:30 saved to backup
Then: ON action
  → 00:30 restored (actual time preserved)
Then: QuickSight manually changed to 00:45
Then: OFF action
  → WARNING: mismatch (config still 00:15, actual 00:45)
  → 00:45 saved to backup
```

## Log Examples

### Matching Time
```
2024-05-28 10:30:00,123 - INFO - Turning OFF hourly schedule for dataset-123
2024-05-28 10:30:01,456 - INFO - DISABLED hourly schedule for dataset-123
```

### Mismatched Time
```
2024-05-28 10:30:00,123 - INFO - Turning OFF hourly schedule for dataset-123
2024-05-28 10:30:00,234 - WARNING - Time mismatch for dataset-123: config.json has 00:15, QuickSight has 00:30. Saving actual time from QuickSight.
2024-05-28 10:30:01,456 - INFO - DISABLED hourly schedule for dataset-123
```

## How to Sync config.json with Actual Schedules

If you want config.json to reflect actual times in QuickSight:

```bash
python3 init_config.py
```

This will:
1. Discover all hourly schedules in QuickSight
2. Update config.json with actual times
3. Back up old config.json to config.json.backup

## Summary

| Aspect | Behavior |
|--------|----------|
| Mismatch detection | ON (checks during OFF action) |
| Blocks OFF? | NO (warning only) |
| What gets saved | Actual time from QuickSight |
| What gets restored | Actual time from backup |
| Config.json | Not updated (remains unchanged) |
| User action needed | Optional - run init_config.py to sync if desired |
