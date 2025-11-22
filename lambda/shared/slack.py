import json
import os
import urllib3
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger()


class SlackHTTPClient:
    """
    Slack HTTP API client that replaces the Slack SDK for basic operations.
    Uses urllib3 for HTTP requests to avoid external dependencies.
    """
    
    BASE_URL = "https://slack.com/api"
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the Slack HTTP client.
        
        Args:
            token: Slack bot token. If None, will use SLACK_BOT_TOKEN environment variable.
        """
        self.token = token or os.environ.get('SLACK_BOT_TOKEN')
        if not self.token:
            raise ValueError("Slack bot token is required")
        
        self.http = urllib3.PoolManager()
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make an HTTP request to the Slack API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            data: Request payload for POST requests
        
        Returns:
            Dict containing the API response
        
        Raises:
            Exception: If the API request fails or returns an error
        """
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            if method.upper() == 'GET':
                # For GET requests, add parameters to URL
                if data:
                    query_params = '&'.join([f"{k}={v}" for k, v in data.items()])
                    url = f"{url}?{query_params}"
                
                response = self.http.request(
                    method,
                    url,
                    headers=self.headers
                )
            else:
                # For POST requests, send data as JSON body
                response = self.http.request(
                    method,
                    url,
                    headers=self.headers,
                    body=json.dumps(data) if data else None
                )
            
            # Parse response
            response_data = json.loads(response.data.decode('utf-8'))
            
            # Check if Slack API returned an error
            if not response_data.get('ok', False):
                error_msg = response_data.get('error', 'Unknown error')
                logger.error(f"Slack API error: {error_msg}")
                raise SlackApiError(f"Slack API error: {error_msg}", response_data)
            
            return response_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Slack API response: {e}")
            raise Exception(f"Failed to parse Slack API response: {e}")
        except Exception as e:
            logger.error(f"Slack API request failed: {e}")
            raise Exception(f"Slack API request failed: {e}")
    
    def users_lookup_by_email(self, email: str) -> Dict[str, Any]:
        """
        Look up a user by their email address.
        
        Args:
            email: User's email address
        
        Returns:
            Dict containing user information
        
        Raises:
            SlackApiError: If user is not found or API error occurs
        """
        data = {'email': email}
        return self._make_request('GET', 'users.lookupByEmail', data)
    
    def chat_post_message(self, channel: str, text: str, **kwargs) -> Dict[str, Any]:
        """
        Post a message to a Slack channel or user.
        
        Args:
            channel: Channel ID or user ID to send message to
            text: Message text
            **kwargs: Additional message parameters (blocks, attachments, etc.)
        
        Returns:
            Dict containing message information including timestamp
        """
        data = {
            'channel': channel,
            'text': text,
            **kwargs
        }
        return self._make_request('POST', 'chat.postMessage', data)
    
    def conversations_history(self, channel: str, oldest: Optional[str] = None, 
                            latest: Optional[str] = None, limit: int = 100, 
                            **kwargs) -> Dict[str, Any]:
        """
        Retrieve conversation history from a channel.
        
        Args:
            channel: Channel ID to get history from
            oldest: Only messages after this timestamp (inclusive)
            latest: Only messages before this timestamp (exclusive)
            limit: Number of messages to retrieve (max 1000)
            **kwargs: Additional parameters
        
        Returns:
            Dict containing message history
        """
        data = {
            'channel': channel,
            'limit': limit,
            **kwargs
        }
        
        if oldest:
            data['oldest'] = oldest
        if latest:
            data['latest'] = latest
            
        return self._make_request('GET', 'conversations.history', data)
    
    def users_info(self, user: str) -> Dict[str, Any]:
        """
        Get information about a user.
        
        Args:
            user: User ID
        
        Returns:
            Dict containing user information
        """
        data = {'user': user}
        return self._make_request('GET', 'users.info', data)
    
    def conversations_open(self, users: str) -> Dict[str, Any]:
        """
        Open a direct message channel with a user.
        
        Args:
            users: User ID to open DM with
        
        Returns:
            Dict containing channel information
        """
        data = {'users': users}
        return self._make_request('POST', 'conversations.open', data)
    
    def auth_test(self) -> Dict[str, Any]:
        """
        Test the authentication token.
        
        Returns:
            Dict containing authentication information
        """
        return self._make_request('GET', 'auth.test')


class SlackApiError(Exception):
    """Custom exception for Slack API errors."""
    
    def __init__(self, message: str, response: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.response = response


class SlackHelper:
    """
    High-level helper class that provides convenient methods for common Slack operations.
    This class provides the same interface as the original SDK methods used in slack_worker.py.
    """
    
    def __init__(self, token: Optional[str] = None):
        self.client = SlackHTTPClient(token)
    
    def get_user_by_email(self, email: str) -> Optional[str]:
        """
        Get user ID by email address.
        
        Args:
            email: User's email address
        
        Returns:
            User ID if found, None otherwise
        """
        try:
            response = self.client.users_lookup_by_email(email)
            return response['user']['id']
        except SlackApiError:
            logger.warning(f"User not found for email: {email}")
            return None
        except Exception as e:
            logger.error(f"Error looking up user by email {email}: {e}")
            return None
    
    def send_message(self, channel: str, text: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Send a message to a channel or user.
        
        Args:
            channel: Channel ID or user ID
            text: Message text
            **kwargs: Additional message parameters
        
        Returns:
            Message response dict if successful, None otherwise
        """
        try:
            return self.client.chat_post_message(channel, text, **kwargs)
        except Exception as e:
            logger.error(f"Error sending message to {channel}: {e}")
            return None
    
    def get_conversation_history(self, channel: str, oldest: Optional[str] = None, 
                               limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get conversation history messages.
        
        Args:
            channel: Channel ID
            oldest: Only messages after this timestamp
            limit: Number of messages to retrieve
        
        Returns:
            List of message dictionaries
        """
        try:
            response = self.client.conversations_history(
                channel=channel, 
                oldest=oldest, 
                limit=limit
            )
            return response.get('messages', [])
        except Exception as e:
            logger.error(f"Error getting conversation history for {channel}: {e}")
            return []
    
    def check_for_user_reply(self, channel_id: str, oldest_ts: str, user_id: str) -> Optional[str]:
        """
        Check for a reply from a specific user after a given timestamp.
        This method replicates the logic from the original slack_worker.py
        
        Args:
            channel_id: Channel to check
            oldest_ts: Timestamp to check after
            user_id: User ID to look for replies from
        
        Returns:
            Reply text if found, None otherwise
        """
        try:
            # Add small buffer to ensure we don't read our own message
            buffer_ts = str(float(oldest_ts) + 0.000001)
            messages = self.get_conversation_history(channel_id, oldest=buffer_ts)
            
            for msg in messages:
                # Check if message is from the target user and not a bot
                if 'bot_id' not in msg and msg.get('user') == user_id:
                    return msg.get('text')
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking for reply in {channel_id}: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test the Slack connection and authentication.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            response = self.client.auth_test()
            logger.info(f"Slack connection successful. Bot: {response.get('user')}")
            return True
        except Exception as e:
            logger.error(f"Slack connection test failed: {e}")
            return False


# Convenience function to create a SlackHelper instance
def get_slack_client(token: Optional[str] = None) -> SlackHelper:
    """
    Create and return a SlackHelper instance.
    
    Args:
        token: Slack bot token. If None, uses SLACK_BOT_TOKEN environment variable.
    
    Returns:
        SlackHelper instance
    """
    return SlackHelper(token)
