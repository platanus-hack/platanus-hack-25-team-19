# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AWS CDK Python project that implements a job orchestration system using Lambda functions, SQS queues, API Gateway, and DynamoDB. The architecture follows a producer-consumer pattern where an orchestrator Lambda creates jobs and distributes them to specialized worker Lambdas via SQS queues.

## Development Environment Setup

### Virtual Environment
```bash
# Create virtual environment
python3 -m venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Code Formatting

The project uses automated formatting tools:
- **Black** - Code formatter (100 char line length)
- **isort** - Import sorter
- **flake8** - Linter
- **pre-commit** - Git hooks for automatic formatting

```bash
# Format code
make format

# Run linter
make lint

# Run pre-commit on all files
make pre-commit

# Or use directly
black .
isort .
flake8 .
```

### Common Commands (Makefile)

```bash
# Show all available commands
make help

# Install dependencies and setup pre-commit
make install

# Format code with black and isort
make format

# Run linters
make lint

# Run tests
make test

# Build Lambda layer
make layer

# Deploy to AWS
make deploy
```

### AWS CDK Commands
```bash
# Synthesize CloudFormation template
cdk synth
# Or: make synth

# List all stacks
cdk ls

# Deploy to AWS (account: 306679357471, region: us-east-1)
cdk deploy
# Or: make deploy

# Compare deployed stack with current state
cdk diff
# Or: make diff

# Destroy stack
cdk destroy
# Or: make destroy
```

## Architecture

### High-Level Flow
1. **API Gateway** receives POST requests at `/jobs` endpoint with a `problem` parameter
2. **Orchestrator Lambda** (orchestrator.py) creates 3 jobs in DynamoDB and sends messages to 3 SQS queues
3. **Worker Lambdas** consume messages from their respective queues, process jobs, and update DynamoDB with results

### Multi-Agent Market Research System

The **market_research_worker** implements a sophisticated multi-agent orchestration system with 5 specialized research agents:

**Sequential Agent Execution:**
1. **Obstacles Agent** (`obstacles_agent.py`) - Identifies technical, market, regulatory, user, and financial obstacles
2. **Solutions Agent** (`solutions_agent.py`) - Researches existing manual/digital solutions and workarounds
3. **Legal Agent** (`legal_agent.py`) - Analyzes legal and regulatory requirements
4. **Competitor Agent** (`competitor_agent.py`) - Analyzes competitive landscape and market structure
5. **Market Agent** (`market_agent.py`) - Quantifies market size, growth trends, and customer segments

**Architecture Pattern:**
- Each agent is a separate Lambda function (15min timeout, 1GB memory)
- The `market_research_worker` orchestrates sequential execution
- Each agent receives accumulated context from all previous agents
- Each agent uses Claude Sonnet 4 with web_search and web_fetch tools for real-time research
- Findings are saved to DynamoDB after each agent completes
- Final synthesis generates an executive summary of all findings

**Context Accumulation:**
```
Obstacles Agent: problem_context
  ↓
Solutions Agent: problem_context + obstacles_findings
  ↓
Legal Agent: problem_context + obstacles + solutions
  ↓
Competitor Agent: problem_context + obstacles + solutions + legal
  ↓
Market Agent: problem_context + all previous findings
  ↓
Synthesis: Generates executive summary from all findings
```

**Agent Output Schemas:**
- All agents return structured JSON with specific fields
- Each includes a "sources" array with URLs for verification
- Orchestrator handles JSON parsing with fallback to raw text
- Final result stored in DynamoDB includes all findings + synthesis

### Infrastructure Components (hackaton_platanus_stack.py)

**DynamoDB Table**: `jobs`
- Partition key: `id` (string)
- Stores job metadata: id, status, instructions, type, result, created_at, updated_at

**SQS Queues** (300s visibility timeout, 14-day retention):
- `slack` - for Slack integration jobs
- `market_research` - for market research jobs
- `external_research` - for external research jobs

**Lambda Functions**:
- `orchestrator` (30s timeout, 256MB) - Creates jobs and distributes to queues
- `slack_worker` (15min timeout, 1GB) - Processes Slack jobs
- `market_research_worker` (15min timeout, 1GB) - Orchestrates multi-agent market research
- `external_research_worker` (15min timeout, 1GB) - Processes external research jobs
- **Market Research Agents** (15min timeout, 1GB each):
  - `obstacles_agent` - Identifies challenges and obstacles
  - `solutions_agent` - Researches existing solutions
  - `legal_agent` - Analyzes regulatory landscape
  - `competitor_agent` - Analyzes competitive dynamics
  - `market_agent` - Quantifies market opportunity

**API Gateway**: REST API with `/jobs` POST endpoint, CORS enabled

### Lambda Function Patterns

All worker Lambdas follow the same pattern:
1. Parse SQS message to extract `job_id` and `instructions`
2. Update job status to "processing" in DynamoDB
3. Execute job-specific logic in a dedicated function
4. Update job status to "completed" with result, or "failed" with error message
5. Use structured logging and proper error handling

### Job Status Flow
- `pending` - Job created, queued for processing
- `processing` - Worker Lambda has picked up the job
- `completed` - Job finished successfully
- `failed` - Job encountered an error

## Testing

```bash
# Run tests (requires pytest from requirements-dev.txt)
pytest

# Run specific test
pytest tests/unit/test_hackaton_platanus_stack.py

# Note: Current tests are commented out placeholders
```

## Lambda Function Development

When modifying Lambda functions in `lambda/`:
- All Lambda code must be in the `lambda/` directory (deployed as a single asset)
- Worker functions should implement their business logic in dedicated `process_*` functions
- Use environment variables for AWS resource names (queues, tables)
- Follow the existing error handling pattern with try-catch and DynamoDB status updates
- Workers receive messages in batches (currently batch_size=1)

### Lambda Layer for Dependencies

The project uses a Lambda Layer for shared dependencies (Anthropic SDK):
- Layer directory: `lambda/layer/`
- Requirements: `lambda/layer/requirements.txt`
- To update the layer:
  ```bash
  cd lambda/layer
  pip install -r requirements.txt -t python/
  ```

### Multi-Agent Development

When modifying market research agents:
- Each agent has a dedicated system prompt defining its research scope
- Agents output structured JSON with specific schemas (see PRD)
- Use `extract_json_from_response()` helper for parsing Claude responses
- All agents use Claude Sonnet 4 with temperature=0.3 for consistency
- Agents save intermediate findings to DynamoDB for resume capability
- The orchestrator passes accumulated context to each subsequent agent

## Key AWS Configuration

- **Deployed Account**: 306679357471
- **Region**: us-east-1
- **Python Runtime**: 3.11
- **CDK Version**: 2.215.0

## DynamoDB Schema

Job Item Structure:
```python
{
    'id': 'uuid',
    'status': 'pending|processing|completed|failed',
    'instructions': 'string',  # The problem description
    'type': 'slack|market_research|external_research',
    'result': 'string',  # JSON string with job results
    'created_at': 'ISO8601 timestamp',
    'updated_at': 'ISO8601 timestamp'
}
```

## API Usage

**POST /jobs**
```json
{
  "problem": "Your problem description here"
}
```

Response:
```json
{
  "message": "Jobs created successfully",
  "jobs": [
    {"job_id": "uuid", "type": "slack", "status": "pending"},
    {"job_id": "uuid", "type": "market_research", "status": "pending"},
    {"job_id": "uuid", "type": "external_research", "status": "pending"}
  ],
  "job_ids": ["uuid1", "uuid2", "uuid3"]
}
```

## Environment Variables

**Required for Market Research Agents:**
- `ANTHROPIC_API_KEY` - API key for Claude (currently set to placeholder)
- `JOBS_TABLE_NAME` - DynamoDB table name
- Agent function names (for orchestrator):
  - `OBSTACLES_AGENT_NAME`
  - `SOLUTIONS_AGENT_NAME`
  - `LEGAL_AGENT_NAME`
  - `COMPETITOR_AGENT_NAME`
  - `MARKET_AGENT_NAME`

**Before deploying:** Update the ANTHROPIC_API_KEY in `hackaton_platanus_stack.py` with your actual API key.

## Performance Characteristics

**Market Research System:**
- Estimated execution time: 5-7 minutes for full research run
- Token usage per run: ~15,000-25,000 input, ~6,000-10,000 output
- Cost per research run: ~$0.08-$0.15 (Claude Sonnet 4 pricing)
- Each agent may make 2-5 web searches/fetches
- Sequential execution enables context accumulation but trades off speed

## Important Notes

- Stack uses `RemovalPolicy.DESTROY` for DynamoDB - table will be deleted on stack destruction
- API Gateway has throttling: 100 requests/second rate limit, 200 burst limit
- SQS visibility timeout set to 1000s (16+ minutes) to accommodate long-running agents
- Workers process one message at a time (batch_size=1)
- Lambda functions share code from the `lambda/` directory - changes affect all functions
- Agent Lambda invocations are synchronous (RequestResponse) to maintain execution order
- Partial failure handling: If an agent fails, the job is marked as failed with error details
