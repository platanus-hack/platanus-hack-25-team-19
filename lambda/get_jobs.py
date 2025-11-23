import json
import logging
import os

import boto3
from botocore.exceptions import ClientError
from shared.job_model import JobHandler

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
sqs = boto3.client("sqs")

# Get environment variables
JOBS_TABLE_NAME = os.environ['JOBS_TABLE_NAME']
SLACK_QUEUE_URL = os.environ["SLACK_QUEUE_URL"]
MARKET_RESEARCH_QUEUE_URL = os.environ["MARKET_RESEARCH_QUEUE_URL"]
EXTERNAL_RESEARCH_QUEUE_URL = os.environ["EXTERNAL_RESEARCH_QUEUE_URL"]

# Get environment variables
JOBS_TABLE_NAME = os.environ["JOBS_TABLE_NAME"]

def handler(event, context):
    '''
    Get Jobs Lambda: Returns all jobs for a session id

    Path: GET /jobs
    Returns: Jobs associated with the session id
    '''
    logger.info(f'Get Job Status received event: {json.dumps(event)}')

    try:
        # Extract session_id from query parameters
        session_id = event.get('queryStringParameters', {}).get('session_id')

        if not session_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps(
                    {'error': 'Missing session_id', 'message': 'session_id is required in query parameters'}
                ),
            }

        logger.info(f'Fetching status for session {session_id}')

        # Get job from DynamoDB
        jobs = JobHandler(JOBS_TABLE_NAME).find(session_id)

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps(jobs, default=lambda o: o.__dict__),
        }

    except ClientError as e:
        logger.error(f'DynamoDB error: {str(e)}', exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps(
                {'error': 'Database error', 'message': 'Failed to retrieve job status'}
            ),
        }

    except Exception as e:
        logger.error(f'Error getting job status: {str(e)}', exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps(
                {'error': 'Internal server error', 'message': str(e)}
            ),
        }
