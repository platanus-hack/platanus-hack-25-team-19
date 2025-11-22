import json
import logging
import os
import uuid
from datetime import datetime

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
sqs = boto3.client("sqs")

# Get environment variables
JOBS_TABLE_NAME = os.environ["JOBS_TABLE_NAME"]
SLACK_QUEUE_URL = os.environ["SLACK_QUEUE_URL"]
MARKET_RESEARCH_QUEUE_URL = os.environ["MARKET_RESEARCH_QUEUE_URL"]
EXTERNAL_RESEARCH_QUEUE_URL = os.environ["EXTERNAL_RESEARCH_QUEUE_URL"]

# Get table reference
jobs_table = dynamodb.Table(JOBS_TABLE_NAME)


def handler(event, context):
    """
    Orchestrator Lambda function that processes job requests.
    Creates 3 jobs (one for each queue) and returns the job IDs.
    """
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # Parse the request body
        if "body" in event:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
        else:
            body = event

        # Extract the problem parameter
        problem = body.get("problem")

        if not problem:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps(
                    {
                        "error": "Missing required parameter: problem",
                        "message": 'Please provide a "problem" field',
                    }
                ),
            }

        logger.info(f"Processing problem: {problem}")

        # Create 3 jobs, one for each queue
        job_types = [
            {"type": "slack", "queue_url": SLACK_QUEUE_URL},
            {"type": "market_research", "queue_url": MARKET_RESEARCH_QUEUE_URL},
            {"type": "external_research", "queue_url": EXTERNAL_RESEARCH_QUEUE_URL},
        ]

        created_jobs = []

        for job_config in job_types:
            job_id = str(uuid.uuid4())
            job_type = job_config["type"]
            queue_url = job_config["queue_url"]

            # Create entry in DynamoDB
            job_item = {
                "id": job_id,
                "status": "pending",
                "instructions": problem,
                "type": job_type,
                "result": "",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            jobs_table.put_item(Item=job_item)
            logger.info(f"Created job {job_id} in DynamoDB")

            # Send message to SQS queue
            message_body = {"job_id": job_id, "instructions": problem, "type": job_type}

            sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(message_body))
            logger.info(f"Sent message for job {job_id} to {job_type} queue")

            created_jobs.append({"job_id": job_id, "type": job_type, "status": "pending"})

        response = {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps(
                {
                    "message": "Jobs created successfully",
                    "jobs": created_jobs,
                    "job_ids": [job["job_id"] for job in created_jobs],
                }
            ),
        }

        logger.info(f"Successfully created {len(created_jobs)} jobs")
        return response

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request body: {str(e)}")
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": "Invalid JSON", "message": str(e)}),
        }
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": "Internal server error", "message": str(e)}),
        }
