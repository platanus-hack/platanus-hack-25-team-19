import json
import logging
import os
from datetime import datetime

import boto3
from shared.anthropic import Anthropic
from shared.job_model import JobHandler

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
lambda_client = boto3.client("lambda")

# Get environment variables
JOBS_TABLE_NAME = os.environ["JOBS_TABLE_NAME"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
OBSTACLES_AGENT_NAME = os.environ["OBSTACLES_AGENT_NAME"]
SOLUTIONS_AGENT_NAME = os.environ["SOLUTIONS_AGENT_NAME"]
LEGAL_AGENT_NAME = os.environ["LEGAL_AGENT_NAME"]
COMPETITOR_AGENT_NAME = os.environ["COMPETITOR_AGENT_NAME"]
MARKET_AGENT_NAME = os.environ["MARKET_AGENT_NAME"]

# Get table reference
jobs_table = dynamodb.Table(JOBS_TABLE_NAME)

# Initialize Anthropic client
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)
job_handler = JobHandler(JOBS_TABLE_NAME)

def handler(event, context):
    """
    Market Research Orchestrator: Coordinates 5 research agents sequentially.

    Flow: Obstacles → Solutions → Legal → Competitor → Market → Synthesis
    """
    logger.info(f"Market Research Orchestrator received event: {json.dumps(event)}")

    for record in event["Records"]:
        try:
            # Parse the SQS message
            message_body = json.loads(record["body"])
            job_id = message_body["job_id"]
            session_id = message_body["session_id"]
            
            instructions = message_body["instructions"]

            job = job_handler.find_one(session_id=session_id, job_id=job_id)
            if job is None:
                logger.error(f"Job {job_id} not found in session {session_id}. Skipping.")
                continue

            if job.status != 'CREATED':
                logger.warning(f"Job {job_id} in session {session_id} is not in CREATED status. Current status: {job.status}. Skipping.")
                continue

            logger.info(f"Starting market research orchestration for job {job_id}")

            job_handler.mark_in_progress(session_id=session_id, job_id=job_id)

            # Execute agents sequentially
            try:
                # Agent 1: Obstacles
                logger.info(f"Invoking Obstacles Agent for job {job_id}")
                obstacles_response = invoke_agent(
                    OBSTACLES_AGENT_NAME,
                    {
                        'session_id': session_id,
                        'job_id': job_id,
                        'instructions': instructions,
                    }
                )
                obstacles_findings = extract_findings(obstacles_response)
                logger.info(f"Obstacles Agent completed for job {job_id}")

                # Agent 2: Solutions
                logger.info(f"Invoking Solutions Agent for job {job_id}")
                solutions_response = invoke_agent(
                    SOLUTIONS_AGENT_NAME,
                    {
                        'session_id': session_id,
                        'job_id': job_id,
                        'instructions': instructions,
                        "obstacles_findings": obstacles_findings,
                    },
                )
                solutions_findings = extract_findings(solutions_response)
                logger.info(f"Solutions Agent completed for job {job_id}")

                # Agent 3: Legal
                logger.info(f"Invoking Legal Agent for job {job_id}")
                legal_response = invoke_agent(
                    LEGAL_AGENT_NAME,
                    {
                        'session_id': session_id,
                        'job_id': job_id,
                        'instructions': instructions,
                        "obstacles_findings": obstacles_findings,
                        "solutions_findings": solutions_findings,
                    },
                )
                legal_findings = extract_findings(legal_response)
                logger.info(f"Legal Agent completed for job {job_id}")

                # Agent 4: Competitor
                logger.info(f"Invoking Competitor Agent for job {job_id}")
                competitor_response = invoke_agent(
                    COMPETITOR_AGENT_NAME,
                    {
                        'session_id': session_id,
                        'job_id': job_id,
                        'instructions': instructions,
                        "obstacles_findings": obstacles_findings,
                        "solutions_findings": solutions_findings,
                        "legal_findings": legal_findings,
                    },
                )
                competitor_findings = extract_findings(competitor_response)
                logger.info(f"Competitor Agent completed for job {job_id}")

                # Agent 5: Market
                logger.info(f"Invoking Market Agent for job {job_id}")
                market_response = invoke_agent(
                    MARKET_AGENT_NAME,
                    {
                        'session_id': session_id,
                        'job_id': job_id,
                        'instructions': instructions,
                        "obstacles_findings": obstacles_findings,
                        "solutions_findings": solutions_findings,
                        "legal_findings": legal_findings,
                        "competitor_findings": competitor_findings,
                    },
                )
                market_findings = extract_findings(market_response)
                logger.info(f"Market Agent completed for job {job_id}")

                # Synthesis: Generate executive summary
                logger.info(f"Generating synthesis for job {job_id}")
                synthesis = generate_synthesis(
                    instructions,
                    obstacles_findings,
                    solutions_findings,
                    legal_findings,
                    competitor_findings,
                    market_findings,
                )

                # Update job with final result
                final_result = {
                    "instructions": instructions,
                    "findings": {
                        "obstacles": obstacles_findings,
                        "solutions": solutions_findings,
                        "legal": legal_findings,
                        "competitors": competitor_findings,
                        "market": market_findings,
                    },
                    "synthesis": synthesis,
                    "completed_at": datetime.utcnow().isoformat(),
                }

                job_handler.mark_completed(
                    session_id=session_id,
                    job_id=job_id,
                    result=json.dumps(final_result)
                )

                logger.info(
                    f"Market research orchestration completed successfully for job {job_id}"
                )

            except Exception as agent_error:
                logger.error(
                    f"Agent execution failed for job {job_id}: {str(agent_error)}", exc_info=True
                )

                job_handler.mark_failed(
                    session_id=session_id,
                    job_id=job_id,
                    result=str(agent_error)
                )

                raise

            return {"statusCode": 200, "body": json.dumps("Successfully processed messages")}

        except Exception as e:
            logger.error(f"Error in orchestrator: {str(e)}", exc_info=True)
            raise


def invoke_agent(function_name, payload):
    """
    Invoke an agent Lambda function synchronously.
    """
    logger.info(f"Invoking Lambda function: {function_name}")

    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",  # Synchronous
        Payload=json.dumps(payload),
    )

    # Parse response
    response_payload = json.loads(response["Payload"].read())

    if response["StatusCode"] != 200:
        raise Exception(f"Agent {function_name} returned status {response['StatusCode']}")

    if "FunctionError" in response:
        error_msg = response_payload.get("errorMessage", "Unknown error")
        raise Exception(f"Agent {function_name} failed: {error_msg}")

    logger.info(f"Lambda function {function_name} completed successfully")
    return response_payload


def extract_findings(agent_response):
    """
    Extract findings from agent Lambda response.
    """
    try:
        body = agent_response.get("body")
        if isinstance(body, str):
            body = json.loads(body)

        return body.get("findings", {})
    except Exception as e:
        logger.warning(f"Could not extract findings from response: {e}")
        return {}


def generate_synthesis(problem_context, obstacles, solutions, legal, competitors, market):
    """
    Generate executive summary synthesizing all research findings.
    """
    system_prompt = """You are an executive business analyst creating a comprehensive market research report.

Your role is to synthesize findings from 5 research agents into a clear, actionable executive summary.

The summary should:
1. Start with a brief problem statement
2. Summarize key obstacles and challenges
3. Analyze existing solutions and their gaps
4. Highlight critical legal/regulatory considerations
5. Assess the competitive landscape
6. Quantify market opportunity
7. Provide strategic recommendations

Write in clear, professional prose. Use bullet points for key insights. Focus on actionable intelligence.

Aim for 800-1200 words. Include specific data points and sources where relevant."""

    all_findings = f"""
PROBLEM CONTEXT:
{problem_context}

OBSTACLES FINDINGS:
{json.dumps(obstacles, indent=2)}

SOLUTIONS FINDINGS:
{json.dumps(solutions, indent=2)}

LEGAL/REGULATORY FINDINGS:
{json.dumps(legal, indent=2)}

COMPETITIVE LANDSCAPE:
{json.dumps(competitors, indent=2)}

MARKET ANALYSIS:
{json.dumps(market, indent=2)}
"""

    user_prompt = f"""Please synthesize the following market research findings into a comprehensive executive summary.

{all_findings}

Create a well-structured report that tells the complete story and provides actionable insights."""

    logger.info("Generating synthesis with Claude API...")

    response = anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        temperature=0.4,  # Slightly higher for better prose
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    # Extract text from response
    synthesis_text = ""
    for block in response.content:
        if block.type == "text":
            synthesis_text += block.text

    return synthesis_text
