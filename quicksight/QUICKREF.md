# Quick Reference

## Setup (First Time)

```bash
# 1. Install dependencies
pip3 install boto3

# 2. Configure AWS credentials
export AWS_PROFILE=your-profile

# 3. Initialize config.json
python3 init_config.py
```

## Basic Usage

### Turn ON hourly schedules

**dataset.txt:**
```
dataset-id-1
dataset-id-2
```

**Command:**
```bash
python3 manage_schedules.py ON
```

### Turn OFF hourly schedules

**dataset.txt:**
```
dataset-id-1
dataset-id-2
```

**Command:**
```bash
python3 manage_schedules.py OFF
```

Note: Requires each dataset ID to exist in config.json

## File Summary

| File | Purpose | You Edit? |
|------|---------|-----------|
| `dataset.txt` | List of dataset IDs to manage | YES |
| `config.json` | Schedule times (auto-populated) | NO |
| `manage_schedules.py` | Main script (requires ON/OFF arg) | NO |
| `list_schedules.py` | View all schedules | NO |
| `init_config.py` | Auto-discover datasets (one-time) | NO |
| `schedule_backup.json` | Backup of disabled schedules | NO |
| `schedule_changes.log` | Activity log | NO |

## Commands

```bash
# Initialize configuration (first time only)
python3 init_config.py

# Enable hourly schedules for datasets in dataset.txt
python3 manage_schedules.py ON

# Disable hourly schedules for datasets in dataset.txt
python3 manage_schedules.py OFF

# View all datasets and current schedules
python3 list_schedules.py

# View what changes were made
cat schedule_changes.log
```

## Validation

**Before turning OFF:**
- Each dataset in dataset.txt must exist in config.json
- If not found: Error logged, dataset skipped

**Turning ON:**
- Dataset must have been previously known (in backup or config)
- If no backup: Error logged

## Example Workflow

```bash
# 1. Initialize (discovers all hourly datasets)
python3 init_config.py

# 2. Edit dataset.txt to add datasets you want to manage
# dataset-123
# dataset-456

# 3. Enable them
python3 manage_schedules.py ON

# 4. Check what happened
tail schedule_changes.log

# 5. Later, disable them
python3 manage_schedules.py OFF

# 6. Verify current state
python3 list_schedules.py
```

## Troubleshooting

**boto3 not installed:**
```bash
pip3 install boto3
```

**AWS credentials missing:**
```bash
export AWS_PROFILE=your-profile
```

**"Not found in config.json" error when turning OFF:**
- Run `python3 init_config.py` to refresh config.json
- Verify dataset actually has hourly schedule: `python3 list_schedules.py`

**View detailed logs:**
```bash
cat schedule_changes.log
```
