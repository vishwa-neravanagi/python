#!/usr/bin/env python3
import boto3
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(
    filename='schedule_changes.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

DATASET_FILE = 'dataset.txt'
CONFIG_FILE = 'config.json'
BACKUP_FILE = 'schedule_backup.json'

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def load_backup():
    backup_path = Path(BACKUP_FILE)
    if backup_path.exists():
        with open(backup_path, 'r') as f:
            return json.load(f)
    return {}

def save_backup(backup_data):
    with open(BACKUP_FILE, 'w') as f:
        json.dump(backup_data, f, indent=2)

def load_dataset_ids():
    dataset_ids = []
    with open(DATASET_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                dataset_ids.append(line)
    return dataset_ids

def get_schedule_info(dataset_id, account_id, client):
    try:
        response = client.list_refresh_schedules(
            AwsAccountId=account_id,
            DataSetId=dataset_id
        )
        schedules = response.get('RefreshSchedules', [])
        if schedules:
            return schedules[0].get('ScheduleId'), schedules[0]
        return None, None
    except Exception as e:
        logger.error(f"Error getting schedule for {dataset_id}: {str(e)}")
        return None, None

def disable_schedule(dataset_id, schedule_id, schedule_config, config_datasets, account_id, client):
    try:
        # Check if actual schedule time matches config.json
        actual_time = schedule_config.get('ScheduleFrequency', {}).get('TimeOfTheDay', 'unknown')
        config_time = config_datasets.get(dataset_id, {}).get('time', 'unknown')

        print(f"[DEBUG] Disabling: actual_time={actual_time}, config_time={config_time}")

        if actual_time != config_time:
            logger.warning(f"Time mismatch for {dataset_id}: config.json has {config_time}, QuickSight has {actual_time}. Saving actual time from QuickSight.")
            print(f"[WARNING] Time mismatch for {dataset_id}")

        print(f"[DEBUG] Calling delete_refresh_schedule with ScheduleId={schedule_id}")
        client.delete_refresh_schedule(
            AwsAccountId=account_id,
            DataSetId=dataset_id,
            ScheduleId=schedule_id
        )
        print(f"[DEBUG] delete_refresh_schedule succeeded")

        backup_data = load_backup()
        backup_data[dataset_id] = {
            'ScheduleId': schedule_id,
            'ScheduleFrequency': schedule_config.get('ScheduleFrequency', {}),
            'RefreshType': schedule_config.get('RefreshType', 'FULL_REFRESH')
        }
        save_backup(backup_data)
        print(f"[DEBUG] Backup saved")

        logger.info(f"DISABLED hourly schedule for {dataset_id}")
        print(f"[INFO] DISABLED hourly schedule for {dataset_id}")
        return True
    except Exception as e:
        logger.error(f"Error disabling schedule for {dataset_id}: {str(e)}")
        print(f"[ERROR] Error disabling schedule: {str(e)}")
        return False

def enable_schedule(dataset_id, config_time, account_id, client):
    backup_data = load_backup()

    if dataset_id in backup_data:
        # Restore from backup
        backup = backup_data[dataset_id]
        try:
            client.create_refresh_schedule(
                AwsAccountId=account_id,
                DataSetId=dataset_id,
                Schedule={
                    'ScheduleId': backup['ScheduleId'],
                    'ScheduleFrequency': backup['ScheduleFrequency'],
                    'RefreshType': backup.get('RefreshType', 'FULL_REFRESH')
                }
            )

            del backup_data[dataset_id]
            save_backup(backup_data)

            logger.info(f"ENABLED hourly schedule for {dataset_id} (restored from backup)")
            return True
        except Exception as e:
            logger.error(f"Error enabling schedule for {dataset_id}: {str(e)}")
            return False
    else:
        # No backup - create new schedule from config.json time
        try:
            client.create_refresh_schedule(
                AwsAccountId=account_id,
                DataSetId=dataset_id,
                Schedule={
                    'ScheduleId': f'hourly-{dataset_id}',
                    'ScheduleFrequency': {
                        'Interval': 'HOURLY',
                        'TimeOfTheDay': config_time,
                        'TimeZone': 'Asia/Kolkata'
                    },
                    'RefreshType': 'FULL_REFRESH'
                }
            )

            logger.info(f"ENABLED hourly schedule for {dataset_id} (created new at {config_time})")
            return True
        except Exception as e:
            logger.error(f"Error creating schedule for {dataset_id}: {str(e)}")
            return False

def manage_schedules(action):
    dataset_ids = load_dataset_ids()
    config = load_config()
    config_datasets = config.get('datasets', {})

    print(f"[DEBUG] Loaded dataset IDs: {dataset_ids}")
    print(f"[DEBUG] Config datasets: {list(config_datasets.keys())}")

    client = boto3.client('quicksight', region_name='ap-south-1')
    sts_client = boto3.client('sts')
    account_id = sts_client.get_caller_identity()['Account']

    print(f"[DEBUG] AWS Account ID: {account_id}")

    logger.info(f"Starting schedule management: action={action}, datasets={len(dataset_ids)}")

    for dataset_id in dataset_ids:
        try:
            if action.upper() == 'ON':
                config_time = config_datasets.get(dataset_id, {}).get('time', '00:00')
                schedule_id, schedule_config = get_schedule_info(dataset_id, account_id, client)

                if schedule_id:
                    logger.info(f"Schedule already ON for {dataset_id}, no action needed")
                else:
                    logger.info(f"Turning ON hourly schedule for {dataset_id}")
                    enable_schedule(dataset_id, config_time, account_id, client)

            elif action.upper() == 'OFF':
                print(f"[DEBUG] Processing OFF for {dataset_id}")
                print(f"[DEBUG] Dataset in config_datasets? {dataset_id in config_datasets}")

                if dataset_id not in config_datasets:
                    logger.error(f"Cannot turn OFF {dataset_id}: Not found in config.json. Skipping.")
                    print(f"[ERROR] {dataset_id} not in config.json, skipping")
                    continue

                print(f"[DEBUG] Getting schedule info for {dataset_id}")
                schedule_id, schedule_config = get_schedule_info(dataset_id, account_id, client)
                print(f"[DEBUG] Schedule ID: {schedule_id}, Config: {schedule_config}")

                if not schedule_id:
                    logger.info(f"Schedule already OFF for {dataset_id}, no action needed")
                    print(f"[INFO] Schedule already OFF for {dataset_id}")
                else:
                    logger.info(f"Turning OFF hourly schedule for {dataset_id}")
                    print(f"[INFO] Turning OFF hourly schedule for {dataset_id}")
                    disable_schedule(dataset_id, schedule_id, schedule_config, config_datasets, account_id, client)
            else:
                logger.error(f"Invalid action '{action}'. Use ON or OFF.")
                print(f"Error: Invalid action '{action}'. Use ON or OFF.")
                sys.exit(1)

        except Exception as e:
            logger.error(f"Error processing {dataset_id}: {str(e)}")

    logger.info(f"Schedule management completed for action={action}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 manage_schedules.py ON|OFF")
        print("  ON  - Enable hourly schedules for all datasets in dataset.txt")
        print("  OFF - Disable hourly schedules for all datasets in dataset.txt (requires config.json entry)")
        sys.exit(1)

    action = sys.argv[1]
    manage_schedules(action)
