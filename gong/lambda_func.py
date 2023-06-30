# import necessary libraries
import os
import json
import boto3
import requests
from datetime import datetime, timedelta

# Define environment variables (Gong API Key, SQS URL, DynamoDB table)
GONG_API_KEY = os.environ["GONG_API_KEY"]
SQS_QUEUE_URL = os.environ["SQS_QUEUE_URL"]
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE_NAME"]

# Create S3 and DynamoDB clients
sqs_client = boto3.client("sqs")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE)


# Define fetch_and_upload_audit_logs function:
def fetch_and_upload_audit_logs():
    # Set headers for Gong API, including API key
    headers = {"Authorization": f"Bearer {GONG_API_KEY}"}

    # Fetch the last cursor from DynamoDB
    response = table.get_item(Key={"config_key": "cursor"})
    cursor = response["Item"]["value"] if "Item" in response else None

    # Define an empty list for the logs
    logs = []
    # Get all log types and set time range
    log_types = [
        "AccessLog",
        "UserActivityLog",
        "UserCallPlay",
        "ExternallySharedCallAccess",
        "ExternallySharedCallPlay",
    ]
    from_date_time = (
        datetime.utcnow() - timedelta(days=1)
    ).isoformat() + "Z"  # Fetch logs from last 24 hours

    for log_type in log_types:
        has_more_data = True
        # While there is more data to fetch:
        while has_more_data:
            # Fetch logs after the cursor from Gong API
            if cursor is not None:
                response = requests.get(
                    f"https://api.gong.io/v2/logs?logType={log_type}&fromDateTime={from_date_time}&cursor={cursor}",
                    headers=headers,
                )
            else:
                # Fetch logs from Gong API
                response = requests.get(
                    f"https://api.gong.io/v2/logs?logType={log_type}&fromDateTime={from_date_time}",
                    headers=headers,
                )

            data = response.json()
            # Extract new logs from the response
            new_logs = data.get("logEntries", [])

            # Append logs to the main list
            logs.extend(new_logs)

            # Update cursor with new cursor from response
            cursor = data.get("records", {}).get("cursor", None)

            # Check if more data exists (currentPageSize equals the length of new_logs)
            has_more_data = len(new_logs) == data.get("records", {}).get(
                "currentPageSize", 0
            )

            # Deduplicate logs by 'id'
            seen_ids = set()
            unique_logs = []
            for log in logs:
                if log["id"] not in seen_ids:
                    seen_ids.add(log["id"])
                    unique_logs.append(log)

            # Send logs to SQS queue
            if unique_logs:
                for log in unique_logs:
                    sqs_client.send_message(
                        QueueUrl=SQS_QUEUE_URL, MessageBody=json.dumps(log)
                    )

                # Save the latest cursor back into the DynamoDB table
                table.put_item(Item={"config_key": "cursor", "value": cursor})


# Define lambda_handler function
def lambda_handler(event, context):
    fetch_and_upload_audit_logs()


# """
# Gong audit log object
# {
#   "requestId": "4al018gzaztcr8nbukw",
#   "records": {
#     "totalRecords": 263,
#     "currentPageSize": 100,
#     "currentPageNumber": 0,
#     "cursor": "eyJhbGciOiJIUzI1NiJ9.eyJjYWxsSWQiM1M30.6qKwpOcvnuweTZmFRzYdtjs_YwJphJU4QIwWFM"
#   },
#   "logEntries": [
#     {
#       "userId": "234599484848423",
#       "userEmailAddress": "test@test.com",
#       "userFullName": "Jon Snow",
#       "impersonatorUserId": "234599484848423",
#       "impersonatorEmailAddress": "test@test.com",
#       "impersonatorFullName": "Jon Snow",
#       "impersonatorCompanyId": "234599484848423",
#       "eventTime": "2018-02-17T02:30:00-08:00",
#       "logRecord": {}
#     }
#   ]
# }
# """
