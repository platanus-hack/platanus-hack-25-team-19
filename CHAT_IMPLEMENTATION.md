# Chat Implementation Guide

## Overview
The chat endpoint provides a conversation management system that interfaces between users and AI APIs (like Claude, GPT-4, or AWS Bedrock).

## Architecture

### ✅ Current Implementation: Lambda + API Gateway (REST)

**Pros:**
- ✅ Simple, proven architecture
- ✅ Auto-scaling for concurrent users
- ✅ Cost-effective (pay per request)
- ✅ Easy to implement and maintain
- ✅ Works great for synchronous chat

**Cons:**
- ⚠️ 30-second timeout limit (API Gateway)
- ⚠️ No streaming responses (for long AI outputs)
- ⚠️ Each message = 1 Lambda invocation

**Best For:**
- Quick AI responses (< 30s)
- Simple request/response chat
- MVP and initial implementation

### Alternative Architectures (Future Considerations)

#### 1. **WebSocket API + Lambda**
```
User <-> API Gateway WebSocket <-> Lambda <-> AI API
```
- ✅ Real-time streaming responses
- ✅ Bidirectional communication
- ✅ Better user experience for long responses
- ⚠️ More complex to implement
- ⚠️ Higher connection costs

#### 2. **Lambda Function URLs with Streaming**
```
User <-> Lambda Function URL (streaming) <-> AI API
```
- ✅ Native response streaming
- ✅ Simpler than WebSocket
- ✅ Up to 15-minute timeout
- ⚠️ No API Gateway features (throttling, API keys)

#### 3. **Step Functions for Complex Conversations**
```
User <-> API Gateway <-> Step Functions <-> Multiple Lambdas <-> AI APIs
```
- ✅ Complex multi-step conversations
- ✅ Parallel processing
- ✅ Built-in retry and error handling
- ⚠️ More expensive
- ⚠️ Higher latency

## Current Implementation Details

### DynamoDB Schema: `chat_sessions`

**Partition Key:** `session_id` (String)
**Sort Key:** `timestamp` (String)

**Attributes:**
- `session_id` - Unique session identifier
- `timestamp` - ISO 8601 timestamp (for message ordering)
- `role` - Message role: `user` or `assistant`
- `content` - Message content
- `created_at` - Creation timestamp

**Queries:**
- Get conversation history: Query by `session_id`
- Messages automatically sorted by `timestamp`

### Lambda: `chat`

**Timeout:** 30 seconds
**Memory:** 512 MB
**Runtime:** Python 3.11

**Environment Variables:**
- `CHAT_SESSIONS_TABLE_NAME` - DynamoDB table name

**Features:**
1. **Session Management**
   - Auto-generates session_id if not provided
   - Retrieves conversation history
   - Stores all messages in DynamoDB

2. **Conversation Context**
   - Maintains conversation history
   - Passes context to AI API
   - Supports token limit management

3. **Error Handling**
   - Validates input parameters
   - Graceful error responses
   - Detailed logging

### API Endpoint: `POST /chat`

**Request:**
```json
{
  "message": "What is machine learning?",
  "session_id": "optional-uuid-here"
}
```

**Response:**
```json
{
  "session_id": "uuid-generated-or-provided",
  "message": "AI response here...",
  "conversation_length": 2,
  "timestamp": "2024-11-22T10:30:00.000Z"
}
```

**Error Response (400):**
```json
{
  "error": "Missing required parameter: message",
  "message": "Please provide a 'message' field"
}
```

## AI API Integration

### Option 1: Anthropic Claude (Direct API)

1. **Install SDK:**
```bash
pip install anthropic
```

2. **Add API Key to Lambda environment:**
```python
environment={
    "ANTHROPIC_API_KEY": "your-api-key",
    "CHAT_SESSIONS_TABLE_NAME": chat_sessions_table.table_name
}
```

3. **Update `call_ai_api()` function:**
```python
import anthropic

def call_ai_api(conversation_history, current_message):
    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": msg["role"], "content": msg["content"]}
            for msg in conversation_history
        ]
    )
    
    return response.content[0].text
```

### Option 2: AWS Bedrock (Claude via AWS)

**Pros:**
- No API keys needed (uses IAM)
- AWS native
- Pay-as-you-go pricing

**Setup:**

1. **Grant Bedrock permissions to Lambda:**
```python
from aws_cdk import aws_iam as iam

chat_lambda.add_to_role_policy(
    iam.PolicyStatement(
        actions=[
            "bedrock:InvokeModel",
            "bedrock:InvokeModelWithResponseStream"
        ],
        resources=["*"]
    )
)
```

2. **Update `call_ai_api()` function:**
```python
import boto3
import json

def call_ai_api(conversation_history, current_message):
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [
                {"role": msg["role"], "content": msg["content"]}
                for msg in conversation_history
            ]
        })
    )
    
    result = json.loads(response['body'].read())
    return result['content'][0]['text']
```

### Option 3: OpenAI GPT

1. **Install SDK:**
```bash
pip install openai
```

2. **Update `call_ai_api()` function:**
```python
import openai

def call_ai_api(conversation_history, current_message):
    client = openai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": msg["role"], "content": msg["content"]}
            for msg in conversation_history
        ]
    )
    
    return response.choices[0].message.content
```

## Testing

### Basic Chat Request
```bash
curl -X POST <API_URL>/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?"
  }'
```

### Continue Conversation
```bash
curl -X POST <API_URL>/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me more about that",
    "session_id": "session-id-from-previous-response"
  }'
```

## Cost Estimation

**Per 1000 chat messages:**
- Lambda invocations: ~$0.20
- DynamoDB writes (2 per message): ~$0.25
- DynamoDB reads: ~$0.05
- API Gateway: ~$3.50
- **Total infrastructure: ~$4.00**

**Plus AI API costs:**
- Claude (Anthropic): $3-15 per million tokens
- GPT-4 (OpenAI): $30-60 per million tokens
- Bedrock (AWS): $3-15 per million tokens

## Deployment

```bash
cd /Users/cristianrodriguez/workspace/hackaton-platanus
cdk deploy
```

## Future Enhancements

1. **Add Streaming Support**
   - Migrate to Lambda Function URLs
   - Implement Server-Sent Events (SSE)
   - Real-time response streaming

2. **Add Session Management**
   - Session expiry (TTL)
   - Session listing/deletion
   - User authentication

3. **Add Advanced Features**
   - Conversation summarization
   - Multi-turn context management
   - Function calling / tool use
   - File/image support

4. **Add Monitoring**
   - CloudWatch metrics for latency
   - Error rate tracking
   - Cost monitoring
   - Usage analytics

5. **Add Caching**
   - ElastiCache for frequent queries
   - Response caching
   - Reduce AI API calls

## Recommendation

**Your current architecture is perfect for getting started!** 

Start with the synchronous REST API approach, integrate your AI provider, and test with users. If you need streaming responses later, you can migrate to WebSocket or Lambda Function URLs without changing the frontend too much.

The DynamoDB session storage gives you flexibility to add features like:
- Conversation history retrieval
- User conversation browsing
- Analytics and insights
- Multi-device sync

Keep it simple now, optimize later based on actual usage patterns! 🚀

