#!/usr/bin/env python3
import boto3
import json
from pathlib import Path

CONFIG_FILE = 'config.json'

def generate_config():
    client = boto3.client('quicksight', region_name='ap-south-1')
    sts_client = boto3.client('sts')
    account_id = sts_client.get_caller_identity()['Account']

    print("Discovering all HOURLY QuickSight datasets...\n")

    datasets = {}
    paginator = client.get_paginator('list_data_sets')
    pages = paginator.paginate(AwsAccountId=account_id)

    hourly_count = 0
    for page in pages:
        for ds in page.get('DataSetSummaries', []):
            dataset_id = ds['DataSetId']
            dataset_name = ds.get('Name', dataset_id)

            try:
                # Get schedule info
                schedules_response = client.list_refresh_schedules(
                    AwsAccountId=account_id,
                    DataSetId=dataset_id
                )
                schedules = schedules_response.get('RefreshSchedules', [])

                if schedules:
                    interval = schedules[0]['ScheduleFrequency'].get('Interval', 'Unknown')
                    time_of_day = schedules[0]['ScheduleFrequency'].get('TimeOfTheDay', '00:00')
                else:
                    interval = None
                    time_of_day = None

                # Only add HOURLY schedules
                if interval == 'HOURLY':
                    datasets[dataset_id] = {
                        "time": time_of_day
                    }
                    print(f"  ✓ {dataset_name} (Hourly at {time_of_day})")
                    hourly_count += 1
            except Exception as e:
                print(f"  ✗ Error getting schedule for {dataset_name}: {str(e)}")

    config = {
        "datasets": datasets
    }

    # Backup existing config if it exists
    config_path = Path(CONFIG_FILE)
    if config_path.exists():
        backup_path = Path(f"{CONFIG_FILE}.backup")
        config_path.rename(backup_path)
        print(f"\nExisting config backed up to {backup_path}")

    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"\n✓ Configuration saved to {CONFIG_FILE}")
    print(f"  Total HOURLY datasets: {hourly_count}")
    print(f"\nUsage:")
    print(f"  - Add 'dataset-id,ON' to dataset.txt to enable a dataset")
    print(f"  - Add 'dataset-id,OFF' to dataset.txt to disable a dataset")
    print(f"  - Run: python3 manage_schedules.py")

if __name__ == '__main__':
    try:
        generate_config()
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)
