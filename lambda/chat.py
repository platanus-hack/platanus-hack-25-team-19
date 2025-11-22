import json
import logging
import os
import uuid
from datetime import datetime
from decimal import Decimal

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")

# Get environment variables
CHAT_SESSIONS_TABLE_NAME = os.environ["CHAT_SESSIONS_TABLE_NAME"]

# Get table reference
chat_sessions_table = dynamodb.Table(CHAT_SESSIONS_TABLE_NAME)


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert DynamoDB Decimal types to JSON"""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def handler(event, context):
    """
    Chat conversation manager Lambda function.
    Manages chat sessions and interfaces with AI API (e.g., Claude).

    Expected payload:
    {
        "message": "user message here",
        "session_id": "optional-session-id"
    }
    """
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # Parse the request body
        if "body" in event:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
        else:
            body = event

        # Extract parameters
        message = body.get("message")
        session_id = body.get("session_id")

        # Validate required parameters
        if not message:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
                "body": json.dumps(
                    {
                        "error": "Missing required parameter: message",
                        "message": 'Please provide a "message" field',
                    }
                ),
            }

        # Generate session_id if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"Generated new session_id: {session_id}")

        logger.info(f"Processing message for session {session_id}: {message}")

        # Get conversation history
        conversation_history = get_conversation_history(session_id)

        # Add user message to history
        user_message = {
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        conversation_history.append(user_message)

        # Call AI API (placeholder - implement your actual AI integration)
        ai_response = call_ai_api(conversation_history, message)

        # Add AI response to history
        assistant_message = {
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.utcnow().isoformat(),
        }
        conversation_history.append(assistant_message)

        # Store both messages in DynamoDB
        store_message(session_id, user_message)
        store_message(session_id, assistant_message)

        # Prepare response
        response = {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps(
                {
                    "session_id": session_id,
                    "message": ai_response,
                    "conversation_length": len(conversation_history),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
        }

        logger.info(f"Successfully processed message for session {session_id}")
        return response

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request body: {str(e)}")
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": "Invalid JSON", "message": str(e)}),
        }
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": "Internal server error", "message": str(e)}),
        }


def get_conversation_history(session_id, limit=50):
    """
    Retrieve conversation history for a session from DynamoDB.

    Args:
        session_id: The session identifier
        limit: Maximum number of messages to retrieve (default: 50)

    Returns:
        List of messages in chronological order
    """
    try:
        response = chat_sessions_table.query(
            KeyConditionExpression=(boto3.dynamodb.conditions.Key("session_id").eq(session_id)),
            Limit=limit,
            ScanIndexForward=True,  # Sort by timestamp ascending
        )

        messages = []
        for item in response.get("Items", []):
            messages.append(
                {
                    "role": item.get("role"),
                    "content": item.get("content"),
                    "timestamp": item.get("timestamp"),
                }
            )

        logger.info(f"Retrieved {len(messages)} messages for session {session_id}")
        return messages

    except Exception as e:
        logger.error(f"Error retrieving conversation history: {str(e)}", exc_info=True)
        return []


def store_message(session_id, message):
    """
    Store a message in DynamoDB.

    Args:
        session_id: The session identifier
        message: Message dict with role, content, and timestamp
    """
    try:
        item = {
            "session_id": session_id,
            "timestamp": message["timestamp"],
            "role": message["role"],
            "content": message["content"],
            "created_at": datetime.utcnow().isoformat(),
        }

        chat_sessions_table.put_item(Item=item)
        logger.info(f"Stored {message['role']} message for session {session_id}")

    except Exception as e:
        logger.error(f"Error storing message: {str(e)}", exc_info=True)
        raise


def call_ai_api(conversation_history, current_message):
    """
    Call AI API (e.g., Claude, OpenAI) to get a response.
    This is a placeholder - implement your actual AI integration here.

    Args:
        conversation_history: List of previous messages
        current_message: Current user message

    Returns:
        AI generated response string
    """
    logger.info("Calling AI API (placeholder)")

    # TODO: Implement actual AI API integration
    # Example integrations:

    # 1. Anthropic Claude:
    # import anthropic
    # client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
    # response = client.messages.create(
    #     model="claude-3-5-sonnet-20241022",
    #     max_tokens=1024,
    #     messages=[
    #         {"role": msg["role"], "content": msg["content"]}
    #         for msg in conversation_history
    #     ]
    # )
    # return response.content[0].text

    # 2. OpenAI:
    # import openai
    # client = openai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    # response = client.chat.completions.create(
    #     model="gpt-4",
    #     messages=[
    #         {"role": msg["role"], "content": msg["content"]}
    #         for msg in conversation_history
    #     ]
    # )
    # return response.choices[0].message.content

    # 3. AWS Bedrock (Claude via AWS):
    # import json
    # bedrock = boto3.client('bedrock-runtime')
    # response = bedrock.invoke_model(
    #     modelId='anthropic.claude-3-sonnet-20240229-v1:0',
    #     body=json.dumps({
    #         "anthropic_version": "bedrock-2023-05-31",
    #         "max_tokens": 1024,
    #         "messages": [
    #             {"role": msg["role"], "content": msg["content"]}
    #             for msg in conversation_history
    #         ]
    #     })
    # )
    # result = json.loads(response['body'].read())
    # return result['content'][0]['text']

    # Placeholder response
    response = (
        f"This is a placeholder response to: '{current_message}'. "
        f"Conversation has {len(conversation_history)} messages. "
        f"Please implement actual AI API integration in the "
        f"call_ai_api() function."
    )

    return response


def get_token_count_estimate(messages):
    """
    Estimate token count for conversation history.
    This is a rough estimate - use actual tokenizer for production.

    Args:
        messages: List of messages

    Returns:
        Estimated token count
    """
    total_chars = sum(len(msg.get("content", "")) for msg in messages)
    # Rough estimate: ~4 characters per token
    return total_chars // 4


def trim_conversation_history(messages, max_tokens=4000):
    """
    Trim conversation history to fit within token limits.
    Keeps most recent messages.

    Args:
        messages: List of messages
        max_tokens: Maximum token count

    Returns:
        Trimmed list of messages
    """
    if get_token_count_estimate(messages) <= max_tokens:
        return messages

    # Keep trimming from the beginning until we fit
    trimmed = messages[:]
    while get_token_count_estimate(trimmed) > max_tokens and len(trimmed) > 1:
        trimmed.pop(0)

    logger.info(f"Trimmed conversation from {len(messages)} to {len(trimmed)} messages")
    return trimmed
