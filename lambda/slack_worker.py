import json
import logging
import os
from datetime import datetime

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")

# Get environment variables
JOBS_TABLE_NAME = os.environ["JOBS_TABLE_NAME"]

# Get table reference
jobs_table = dynamodb.Table(JOBS_TABLE_NAME)


def handler(event, context):
    """
    Slack worker Lambda that processes messages from the slack queue.
    """
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        for record in event["Records"]:
            # Parse the SQS message
            message_body = json.loads(record["body"])
            job_id = message_body["job_id"]
            instructions = message_body["instructions"]

            logger.info(f"Processing Slack job {job_id}")

            # Update job status to processing
            jobs_table.update_item(
                Key={"id": job_id},
                UpdateExpression=("SET #status = :status, updated_at = :updated_at"),
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": "processing",
                    ":updated_at": datetime.utcnow().isoformat(),
                },
            )

            # TODO: Add your Slack processing logic here
            # For now, we'll simulate some work
            result = process_slack_job(instructions)

            # Update job with result
            jobs_table.update_item(
                Key={"id": job_id},
                UpdateExpression=(
                    "SET #status = :status, " "#result = :result, " "updated_at = :updated_at"
                ),
                ExpressionAttributeNames={"#status": "status", "#result": "result"},
                ExpressionAttributeValues={
                    ":status": "completed",
                    ":result": result,
                    ":updated_at": datetime.utcnow().isoformat(),
                },
            )

            logger.info(f"Completed Slack job {job_id}")

        return {"statusCode": 200, "body": json.dumps("Successfully processed messages")}

    except Exception as e:
        logger.error(f"Error processing Slack job: {str(e)}", exc_info=True)

        # Try to update job status to failed
        if "job_id" in locals():
            try:
                jobs_table.update_item(
                    Key={"id": job_id},
                    UpdateExpression=(
                        "SET #status = :status, " "#result = :result, " "updated_at = :updated_at"
                    ),
                    ExpressionAttributeNames={"#status": "status", "#result": "result"},
                    ExpressionAttributeValues={
                        ":status": "failed",
                        ":result": f"Error: {str(e)}",
                        ":updated_at": datetime.utcnow().isoformat(),
                    },
                )
            except Exception as update_error:
                logger.error(f"Failed to update job status: {str(update_error)}")

        raise


def process_slack_job(instructions):
    """
    Process the Slack job based on instructions.
    This is a placeholder - implement your actual logic here.
    """
    logger.info(f"Processing Slack instructions: {instructions}")

    # TODO: Implement actual Slack integration logic
    # For example:
    # - Send notifications to Slack
    # - Post messages to channels
    # - Interact with Slack API

    result = {
        "message": "Slack job processed successfully",
        "instructions": instructions,
        "action": "Simulated Slack notification sent",
        "channels_notified": ["#general", "#notifications"],
    }

    return json.dumps(result)
