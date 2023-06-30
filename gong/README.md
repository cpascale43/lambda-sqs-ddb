# Gong -> Lambda + SQS + DDB

## Prereq: Create Panther schemas
- Fetch samples for each Gong log type ("AccessLog", "UserActivityLog", "UserCallPlay", "ExternallySharedCallAccess", "ExternallySharedCallPlay”):
```
curl -H "Authorization: Bearer YOUR_GONG_API_KEY" \\
     "<https://api.gong.io/v2/logs?logType=LOG_TYPE&limit=1000>" > output.json
```
- Replace YOUR_GONG_API_KEY with your Gong API key and LOG_TYPE with the desired log type.
- Follow the steps at [Generating a schema from sample logs](https://docs.panther.com/data-onboarding/custom-log-types#generating-a-schema-from-sample-logs)

## High level code steps:
- Set environment variables: `GONG_API_KEY`, `SQS_QUEUE_URL`, `DYNAMODB_TABLE`.
- Fetch logs from the last 24 hours, paging through API responses with a stored cursor.
- Deduplicate logs using the unique log ID.
- Send logs to the Panther AWS SQS queue - configure SQS log ingestion by following the steps here: [How to onboard SQS logs into Panther](https://docs.panther.com/data-onboarding/data-transports/aws/sqs#how-to-onboard-sqs-logs-into-panther)
- Update the cursor in DynamoDB for continuity in the next execution.

### Gotchas:
- Gong API rate limits. If encountered, add delays or break the task into smaller ones.
- Monitor the fetched data volume. The script uses 24 hours by default but you can adjust `from_date_time` to fetch logs from a shorter timeframe if necessary.
