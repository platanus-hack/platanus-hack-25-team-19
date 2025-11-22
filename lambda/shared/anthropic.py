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

class Anthropic():
    def __init__(self, api_key):
        self.api_key = api_key

    def send_message(self, messages: list[ConversationMessage], system: str | None = None) -> str:
        '''
        Call AI API to get a response.

        Args:
            messages: List of previous messages
            system: Optional system instruction to guide the assistant's behavior

        Returns:
            AI generated response string
        '''
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
            'max_tokens': 1024,
            'messages': [
                { 'role': msg.role, 'content': msg.content } for msg in messages
            ]
        }

        # Add system instruction if provided
        if system:
            payload['system'] = system

        # Make the HTTP request
        data = json.dumps(payload).encode('utf-8')
        request = urllib.request.Request(url, data=data, headers=headers, method='POST')

        try:
            with urllib.request.urlopen(request) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                return response_data['content'][0]['text']
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            logger.error(f'Anthropic API error: {e.code} - {error_body}')
            raise
        except Exception as e:
            logger.error(f'Error calling Anthropic API: {str(e)}')
            raise

    def send_message_with_tools(self, messages: list[ConversationMessage], tools: list, system: str | None = None) -> dict:
        '''
        Call AI API to get a response with tools support.

        Args:
            messages: List of previous messages
            tools: List of tool schemas for structured output
            system: Optional system instruction to guide the assistant's behavior

        Returns:
            Tool use response as dict
        '''
        logger.info('Calling Anthropic API with tools support')

        # Prepare the request
        url = 'https://api.anthropic.com/v1/messages'
        headers = {
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }

        payload = {
            'model': 'claude-sonnet-4-5-20250929',
            'max_tokens': 4096,
            'messages': [
                { 'role': msg.role, 'content': msg.content } for msg in messages
            ],
            'tools': tools
        }

        # Add system instruction if provided
        if system:
            payload['system'] = system

        # Make the HTTP request
        data = json.dumps(payload).encode('utf-8')
        request = urllib.request.Request(url, data=data, headers=headers, method='POST')

        try:
            with urllib.request.urlopen(request) as response:
                response_data = json.loads(response.read().decode('utf-8'))

                # Parse tool use response
                for content_block in response_data['content']:
                    if content_block['type'] == 'tool_use' and content_block['name'] == 'project_quantification_engine_output':
                        return content_block['input']

                raise Exception("Model did not return the required 'project_quantification_engine_output' via tool execution.")

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            logger.error(f'Anthropic API error: {e.code} - {error_body}')
            raise
        except Exception as e:
            logger.error(f'Error calling Anthropic API: {str(e)}')
            raise
