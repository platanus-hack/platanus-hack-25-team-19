import os
import json
import logging
from typing import Dict, Any

from shared.anthropic import Anthropic, ConversationMessage
from shared.job_model import JobHandler

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ANTHROPIC_API_KEY = os.environ['ANTHROPIC_API_KEY']
JOBS_TABLE_NAME = os.environ['JOBS_TABLE_NAME']

SYSTEM_INSTRUCTION = '''
You are a helpful assistant that summarizes text inputs into concise and clear summaries 

while retaining all essential information. Your summaries should be easy to understand and free of jargon.

Key Requirements:
1. Clarity: Ensure the summary is straightforward and easy to read.
2. Conciseness: Keep the summary brief while covering all important points.
3. Completeness: Do not omit any critical information from the original text.

Use the following format for your summaries:
1. Problem to be solved: Briefly describe the main problem addressed in the text.
2. SMART Goals: List specific, measurable, achievable, relevant, and time-bound goals derived from the text.
3. Target market: Describe the intended audience or market for the content.
4. Impacted stakeholders: Identify the key individuals or groups affected by the content.
5. Key metrics: Highlight important metrics or indicators mentioned in the text.
6. Risks and challenges: Summarize any potential risks or challenges discussed.
7. External dependencies: Note any external factors or dependencies that could influence the content.
8. Functional requirements: Outline the main functional requirements specified.
9. Non-functional requirements: Summarize any non-functional requirements mentioned, such as performance or security needs.

Ensure that each section is clearly labeled and formatted for easy reading.
Separate each section with a newline for better readability.
Use styled markdown for headings and lists.

Always respond in spanish.
Resonse should be as a document, no thinking messages or notes outside the main response.
'''

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to handle the summarization of text inputs.
    """
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # 1. Input Parsing and Validation
        body = event.get('body', event)
        if isinstance(body, str):
            body = json.loads(body)

        session_id = body.get('session_id')

        jobs = JobHandler(JOBS_TABLE_NAME).find(session_id=session_id)
        conversation_history = []

        for job in jobs:
            if job.status != 'COMPLETED':
                continue

            conversation_history.append(
                ConversationMessage(
                    role='user',
                    content=f"Here is the context summary: {job.context_summary}\n"
                            f"Instructions: {job.instructions}\n"
                            f"Result: {job.result}",
                    timestamp=job.created_at
                )
            )

        if len(conversation_history) == 0:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'No completed jobs found for the given session_id'})
            }

        # Call AI API for main response
        anthropic = Anthropic(ANTHROPIC_API_KEY, model='claude-3-5-haiku-20241022')
        ai_response = anthropic.send_message(
            messages=conversation_history,
            system=SYSTEM_INSTRUCTION
        )

        # 5. Return the Fan-Out Status
        response = {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'message': ai_response
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
