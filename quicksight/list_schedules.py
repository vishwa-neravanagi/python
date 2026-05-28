#!/usr/bin/env python3
import boto3
import json
from datetime import datetime

# Read dataset IDs from file
dataset_ids = []
with open('dataset.txt', 'r') as f:
    for line in f:
        dataset_id = line.strip()
        if dataset_id:
            dataset_ids.append(dataset_id)

# Initialize QuickSight client with ap-south-1 region
client = boto3.client('quicksight', region_name='ap-south-1')

# Get AWS account ID
sts_client = boto3.client('sts')
account_id = sts_client.get_caller_identity()['Account']

# If no datasets in file, list all datasets
if not dataset_ids:
    print("No dataset IDs found in dataset.txt. Listing all datasets...\n")
    try:
        paginator = client.get_paginator('list_data_sets')
        pages = paginator.paginate(AwsAccountId=account_id)

        for page in pages:
            for ds in page.get('DataSetSummaries', []):
                dataset_ids.append(ds['DataSetId'])
    except Exception as e:
        print(f"Error listing datasets: {str(e)}")
        exit(1)

# Process each dataset
print(f"{'Dataset Name':<40} {'Dataset ID':<40} {'Schedule':<12} {'Time':<8} {'Enabled':<10}")
print("-" * 110)

for dataset_id in dataset_ids:
    try:
        # Describe dataset to get refresh properties
        response = client.describe_data_set(
            AwsAccountId=account_id,
            DataSetId=dataset_id
        )

        dataset = response['DataSet']
        name = dataset.get('Name', 'N/A')

        schedule = "Unknown"
        enabled = "N/A"

        # Get refresh schedules
        try:
            schedules_response = client.list_refresh_schedules(
                AwsAccountId=account_id,
                DataSetId=dataset_id
            )

            schedules = schedules_response.get('RefreshSchedules', [])

            if schedules:
                # Get interval from first schedule
                interval = schedules[0]['ScheduleFrequency'].get('Interval', 'Unknown')
                time_of_day = schedules[0]['ScheduleFrequency'].get('TimeOfTheDay', '')

                # Map interval to friendly names
                schedule_map = {
                    'HOURLY': 'Hourly',
                    'DAILY': 'Daily',
                    'WEEKLY': 'Weekly',
                    'MONTHLY': 'Monthly'
                }
                schedule = schedule_map.get(interval, interval)

                # Format time - for hourly, extract just the minute
                if interval == 'HOURLY' and time_of_day:
                    # TimeOfTheDay format is HH:MM, extract minute for hourly
                    time_display = f":{time_of_day.split(':')[1]}" if ':' in time_of_day else time_of_day
                else:
                    time_display = time_of_day if time_of_day else '-'

                enabled = "Yes"
            else:
                schedule = "None"
                time_display = "-"
                enabled = "No"

        except Exception as e:
            schedule = "Unknown"
            time_display = "-"
            enabled = "N/A"

        print(f"{name:<40} {dataset_id:<40} {schedule:<12} {time_display:<8} {enabled:<10}")

    except Exception as e:
        print(f"Error processing dataset {dataset_id}: {str(e)}")
