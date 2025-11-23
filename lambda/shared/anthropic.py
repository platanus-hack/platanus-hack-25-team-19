import json
import logging
import os
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Literal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ANTHROPIC_API_KEY = os.environ['ANTHROPIC_API_KEY']

@dataclass
class ConversationMessage:
    role: Literal["user", "assistant"]
    content: str
    timestamp: str

@dataclass
class ContentBlock:
    type: str
    text: str | None = None
    id: str | None = None
    name: str | None = None
    input: dict | None = None

@dataclass
class MessageResponse:
    id: str
    type: str
    role: str
    content: list[ContentBlock]
    model: str
    stop_reason: str | None
    stop_sequence: str | None
    usage: dict

class Anthropic():
    def __init__(self, api_key, model: str = 'claude-sonnet-4-5-20250929'):
        self.api_key = api_key
        self.model = model

    def create_message(self, messages: list[ConversationMessage], system: str | None = None, tools: list | None = None) -> MessageResponse:
        '''
        Call AI API and get a structured response object.

        Args:
            messages: List of previous messages
            system: Optional system instruction to guide the assistant's behavior
            tools: Optional list of tool schemas for structured output

        Returns:
            MessageResponse object with structured content blocks
        '''
        if tools:
            logger.info('Calling Anthropic API with tools support')
        else:
            logger.info('Calling Anthropic API directly')

        # Prepare the request
        url = 'https://api.anthropic.com/v1/messages'
        headers = {
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }

        payload = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 4096 if tools else 1024,
            "thinking": {
                "type": "disabled"
            },
            'messages': [
                { 'role': msg.role, 'content': msg.content } for msg in messages
            ]
        }

        # Add system instruction if provided
        if system:
            payload['system'] = system

        # Add tools if provided
        if tools:
            payload['tools'] = tools

        # Make the HTTP request
        data = json.dumps(payload).encode('utf-8')
        request = urllib.request.Request(url, data=data, headers=headers, method='POST')

        try:
            with urllib.request.urlopen(request) as response:
                response_text = response.read().decode('utf-8')
                response_data = json.loads(response_text)

                logger.info(f'Anthropic API response: {response_text[:500]}...')

                # Parse content blocks
                content_blocks = []
                for block in response_data['content']:
                    content_blocks.append(ContentBlock(
                        type=block.get('type'),
                        text=block.get('text'),
                        id=block.get('id'),
                        name=block.get('name'),
                        input=block.get('input')
                    ))

                return MessageResponse(
                    id=response_data['id'],
                    type=response_data['type'],
                    role=response_data['role'],
                    content=content_blocks,
                    model=response_data['model'],
                    stop_reason=response_data.get('stop_reason'),
                    stop_sequence=response_data.get('stop_sequence'),
                    usage=response_data.get('usage', {})
                )

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            logger.error(f'Anthropic API error: {e.code} - {error_body}')
            raise
        except Exception as e:
            logger.error(f'Error calling Anthropic API: {str(e)}')
            raise

    def send_message(self, messages: list[ConversationMessage], system: str | None = None, tools: list | None = None):
        '''
        Call AI API to get a response with optional tools support.

        Args:
            messages: List of previous messages
            system: Optional system instruction to guide the assistant's behavior
            tools: Optional list of tool schemas for structured output

        Returns:
            AI generated response string (if no tools) or tool use response dict (if tools provided)
        '''
        if tools:
            logger.info('Calling Anthropic API with tools support')
        else:
            logger.info('Calling Anthropic API directly')

        # Prepare the request
        url = 'https://api.anthropic.com/v1/messages'
        headers = {
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }

        payload = {
            'model': self.model,
            'max_tokens': 4096,
            "thinking": {
                "type": "disabled"
            },
            'messages': [
                { 'role': msg.role, 'content': msg.content } for msg in messages
            ]
        }

        # Add system instruction if provided
        if system:
            payload['system'] = system

        # Add tools if provided
        if tools:
            payload['tools'] = tools

        # Make the HTTP request
        data = json.dumps(payload).encode('utf-8')
        request = urllib.request.Request(url, data=data, headers=headers, method='POST')

        try:
            with urllib.request.urlopen(request) as response:
                response_text = response.read().decode('utf-8')
                response_data = json.loads(response_text)

                logger.info(f'Anthropic API response: {response_text}')

                result = ''
                for content_block in response_data['content']:
                    if content_block['type'] == 'text':
                        result += content_block['text']

                    if content_block['type'] == 'tool_use' and content_block['name'] in [tool['name'] for tool in tools or []]:
                        result = json.dumps(content_block['input'])

                return result

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            logger.error(f'Anthropic API error: {e.code} - {error_body}')
            raise
        except Exception as e:
            logger.error(f'Error calling Anthropic API: {str(e)}')
            raise
