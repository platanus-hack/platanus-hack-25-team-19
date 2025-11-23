import json
import logging
import os
import boto3
from typing import Dict, Any
from shared.job_model import JobHandler
from shared.conversation_model import ConversationHandler

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
sqs = boto3.client("sqs")

# Get environment variables
job_handler = JobHandler(os.environ["JOBS_TABLE_NAME"])
conversation_handler = ConversationHandler(os.environ['CONVERSATIONS_TABLE_NAME'])

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to handle problem declarations, create jobs, and fan out to SQS queues.
    """
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # 1. Input Parsing and Validation
        body = event.get('body', event)
        if isinstance(body, str):
            body = json.loads(body)

        type = body['type']

        if type == 'url_verification':
            print("URL Verification event received, skipping.")
            
            return {
                "statusCode": 200,
                "body": json.dumps({"challenge": body.get("challenge")}),
            }

        slack_event = body.get('event', {})
        slack_channel = slack_event['channel']
        target_user_id = slack_event['user']
        message = slack_event['text']

        # Search for existing conversation
        existing_conversation = conversation_handler.find_one(
            slack_channel=slack_channel,
            target_user_id=target_user_id
        )

        if existing_conversation is None:
            logger.info("Missing conversation, ignoring")
            return {
                'statusCode': 200,
            }

        job = job_handler.find_one(
            session_id=existing_conversation.session_id,
            job_id=existing_conversation.job_id
        )

        if job is None:
            logger.info("Missing job, ignoring")
            return {
                'statusCode': 200,
            }

        if job.status == 'CREATED':
            logger.info("Job not in IN_PROGRESS state, ignoring")
            return {
                'statusCode': 200,
            }

        job_handler.mark_completed(
            session_id=job.session_id,
            job_id=job.id,
            result=f'{job.result}\n{message}'
        )

        # 5. Return the Fan-Out Status
        response = {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'message': 'Orchestration complete. Jobs persisted and fanned out to SQS queues.'
            })
        }
        return response

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request body: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Invalid JSON', 'message': str(e)})
        }
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Internal server error', 'message': str(e)})
        }
