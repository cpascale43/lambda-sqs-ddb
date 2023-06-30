## Discord audit log puller

The `discord.Client` class is used as a context manager in `fetch_and_upload_audit_logs`, which runs every minute via a Lambda. 

The Lambda relies on async methods from `discord.py`, and the Lambda handler uses `asyncio` so that asynchronous code can be run inside the Lambda (see: https://discordpy.readthedocs.io/en/async/faq.html#coroutines)

### Code overview: 
- [fetch_guild](https://discordpy.readthedocs.io/en/latest/api.html#discord.Client.fetch_guild)
- [guild.audit_logs](https://discordpy.readthedocs.io/en/latest/api.html#audit-log-data)
- [run_until_complete](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.run_until_complete)
- Handles deduplication via a dynamoDB store
- Writes new logs to S3


### Config steps:
- Create an S3 bucket and dynamoDB table with partition key `config_key` 
- Create Lamba using lambda_function.py
- Add `dynamodb:GetItem`, `dynamodb:PutItem`, and `dynamodb:UpdateItem` permissions to Lambda role
- Set up ingestion to Panther via instructions at [S3 Source](https://docs.panther.com/data-onboarding/data-transports/aws/s3)