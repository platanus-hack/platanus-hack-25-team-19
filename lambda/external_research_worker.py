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
    External Research worker Lambda that processes messages from the queue.
    """
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        for record in event["Records"]:
            # Parse the SQS message
            message_body = json.loads(record["body"])
            job_id = message_body["job_id"]
            instructions = message_body["instructions"]

            logger.info(f"Processing External Research job {job_id}")

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

            # TODO: Add your external research logic here
            # For now, we'll simulate some work
            result = process_external_research_job(instructions)

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

            logger.info(f"Completed External Research job {job_id}")

        return {"statusCode": 200, "body": json.dumps("Successfully processed messages")}

    except Exception as e:
        logger.error(f"Error processing External Research job: {str(e)}", exc_info=True)

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


def process_external_research_job(instructions):
    """
    Process the external research job based on instructions.
    This is a placeholder - implement your actual logic here.
    """
    logger.info(f"Processing external research instructions: {instructions}")

    # TODO: Implement actual external research logic
    # For example:
    # - Call external APIs
    # - Scrape websites for data
    # - Query external databases
    # - Aggregate data from multiple sources

    result = {
        "message": "External research job processed successfully",
        "instructions": instructions,
        "data_sources": ["External API 1", "External API 2", "Public Database"],
        "findings": {
            "key_insights": [
                "Insight 1 from external research",
                "Insight 2 from external research",
                "Insight 3 from external research",
            ],
            "data_points": {
                "metric_1": "42%",
                "metric_2": "1.5M users",
                "metric_3": "$250K average",
            },
        },
        "references": [
            "https://example.com/source1",
            "https://example.com/source2",
            "https://example.com/source3",
        ],
    }

    return json.dumps(result)
