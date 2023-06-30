import asyncio
import os
import json
import boto3
import discord
from datetime import datetime

TOKEN = os.environ["DISCORD_BOT_TOKEN"]
S3_BUCKET = os.environ["S3_BUCKET_NAME"]
GUILD_ID = int(os.environ["GUILD_ID"])
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE_NAME"]

s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE)


async def fetch_and_upload_audit_logs():
    async with discord.Client(intents=discord.Intents.default()) as client:
        await client.login(TOKEN)
        guild = await client.fetch_guild(GUILD_ID)

        response = table.get_item(Key={"config_key": "last_audit_log_id"})
        last_audit_log_id = response["Item"]["value"] if "Item" in response else None

        after_entry = None
        if last_audit_log_id is not None:
            after_entry = discord.Object(id=int(last_audit_log_id))

        logs = []
        async for entry in guild.audit_logs(limit=100, after=after_entry):
            logs.append(entry)
            if last_audit_log_id is None or entry.id > int(last_audit_log_id):
                last_audit_log_id = str(entry.id)

        log_data = [
            {
                "id": entry.id,
                "action": entry.action.name,
                "user_id": entry.user.id,
                "created_at": entry.created_at.timestamp(),
            }
            for entry in logs
        ]

        if log_data:
            current_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
            file_name = f"audit_logs_{current_time}.json"

            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=file_name,
                Body=json.dumps(log_data),
                ContentType="application/json",
            )

            table.put_item(
                Item={"config_key": "last_audit_log_id", "value": last_audit_log_id}
            )

        await client.close()


def lambda_handler(event, context):
    asyncio.run(fetch_and_upload_audit_logs())
