import json
import logging
import os
from datetime import datetime

import boto3
from anthropic import Anthropic

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")

# Get environment variables
JOBS_TABLE_NAME = os.environ["JOBS_TABLE_NAME"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# Get table reference
jobs_table = dynamodb.Table(JOBS_TABLE_NAME)

# Initialize Anthropic client
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)


def handler(event, context):
    """
    Competitor Agent: Analyzes competitive landscape.

    Input: {job_id, problem_context, obstacles_findings, solutions_findings, legal_findings}
    Output: {direct_competitors, indirect_competitors, market_structure, barriers, white_space, sources}
    """
    logger.info(f"Competitor Agent received event: {json.dumps(event)}")

    try:
        # Parse input
        job_id = event["job_id"]
        problem_context = event["problem_context"]
        obstacles_findings = event.get("obstacles_findings", {})
        solutions_findings = event.get("solutions_findings", {})
        legal_findings = event.get("legal_findings", {})

        logger.info(f"Processing Competitor Agent for job {job_id}")

        # Update job status
        jobs_table.update_item(
            Key={"id": job_id},
            UpdateExpression="SET #status = :status, updated_at = :updated_at",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": "processing_competitors",
                ":updated_at": datetime.utcnow().isoformat(),
            },
        )

        # Run agent with Claude
        result = run_competitor_analysis(
            problem_context, obstacles_findings, solutions_findings, legal_findings
        )

        # Save findings to DynamoDB
        jobs_table.update_item(
            Key={"id": job_id},
            UpdateExpression=("SET competitor_findings = :findings, " "updated_at = :updated_at"),
            ExpressionAttributeValues={
                ":findings": json.dumps(result),
                ":updated_at": datetime.utcnow().isoformat(),
            },
        )

        logger.info(f"Completed Competitor Agent for job {job_id}")

        return {
            "statusCode": 200,
            "body": json.dumps({"job_id": job_id, "agent": "competitor", "findings": result}),
        }

    except Exception as e:
        logger.error(f"Error in Competitor Agent: {str(e)}", exc_info=True)

        if "job_id" in locals():
            try:
                jobs_table.update_item(
                    Key={"id": job_id},
                    UpdateExpression=(
                        "SET #status = :status, "
                        "error_message = :error, "
                        "updated_at = :updated_at"
                    ),
                    ExpressionAttributeNames={"#status": "status"},
                    ExpressionAttributeValues={
                        ":status": "failed_competitors",
                        ":error": str(e),
                        ":updated_at": datetime.utcnow().isoformat(),
                    },
                )
            except Exception as update_error:
                logger.error(f"Failed to update job status: {str(update_error)}")

        raise


def run_competitor_analysis(
    problem_context, obstacles_findings, solutions_findings, legal_findings
):
    """
    Analyze competitive landscape using Claude with web search.
    """
    system_prompt = """You are an expert competitive intelligence analyst specializing in market analysis.

Your role is to research and identify:
1. Direct competitors - companies/products solving the exact same problem
2. Indirect competitors - alternative solutions or substitute products
3. Market structure - is it monopolistic, oligopolistic, fragmented, or emerging?
4. Entry barriers - what makes it hard for new entrants to compete?
5. White space opportunities - underserved segments or gaps in the market

For each competitor category, provide:
- Company/product names with URLs
- Their approach and value proposition
- Strengths and weaknesses
- Market position (leader, challenger, niche)
- Funding/revenue (if available)
- Recent developments or news

Use web_search and web_fetch to find:
- Current players in the market
- Recent funding announcements
- Product launches and features
- Market share data
- Customer reviews and sentiment
- Industry reports and analysis

Output your findings as a JSON object with this structure:
{
  "direct_competitors": [
    {
      "name": "...",
      "url": "...",
      "description": "...",
      "strengths": ["..."],
      "weaknesses": ["..."],
      "market_position": "...",
      "funding": "..."
    }
  ],
  "indirect_competitors": [
    {
      "name": "...",
      "type": "substitute|alternative",
      "description": "...",
      "why_competitive": "..."
    }
  ],
  "market_structure": {
    "type": "monopolistic|oligopolistic|fragmented|emerging",
    "description": "...",
    "key_players": ["..."]
  },
  "barriers": [
    {
      "type": "brand|network|technology|regulatory|capital",
      "description": "...",
      "severity": "high|medium|low"
    }
  ],
  "white_space": ["opportunity 1", "opportunity 2", ...],
  "sources": ["url 1", "url 2", ...]
}"""

    previous_context = f"""
PREVIOUS FINDINGS - OBSTACLES:
{json.dumps(obstacles_findings, indent=2)}

PREVIOUS FINDINGS - SOLUTIONS:
{json.dumps(solutions_findings, indent=2)}

PREVIOUS FINDINGS - LEGAL:
{json.dumps(legal_findings, indent=2)}
"""

    user_prompt = f"""PROBLEM CONTEXT:
{problem_context}

{previous_context}

Given the problem and previous research, please analyze the competitive landscape. Use web search to find:
- Direct and indirect competitors
- Market structure and dynamics
- Entry barriers and moats
- Opportunities and white space
- Recent competitive developments

Provide detailed, current information with sources."""

    logger.info("Calling Claude API for competitor analysis...")

    response = anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        temperature=0.3,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
        tools=[
            {
                "name": "web_search",
                "description": "Search the web for information",
                "input_schema": {
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "The search query"}},
                    "required": ["query"],
                },
            },
            {
                "name": "web_fetch",
                "description": "Fetch and read the full content of a webpage",
                "input_schema": {
                    "type": "object",
                    "properties": {"url": {"type": "string", "description": "The URL to fetch"}},
                    "required": ["url"],
                },
            },
        ],
    )

    # Extract and parse response
    result = extract_json_from_response(response)

    return result


def extract_json_from_response(response):
    """
    Extract JSON from Claude's response, handling various formats.
    """
    import re

    # Get the text content from response
    text_content = ""
    for block in response.content:
        if block.type == "text":
            text_content += block.text

    logger.info(f"Raw response text: {text_content[:500]}...")

    # Try to extract JSON from markdown code blocks
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", text_content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from code block: {e}")

    # Try to find JSON object in text
    json_match = re.search(r"\{.*\}", text_content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON object: {e}")

    # If all else fails, return structured error
    logger.warning("Could not extract JSON from response, returning raw text")
    return {
        "direct_competitors": [],
        "indirect_competitors": [],
        "market_structure": {},
        "barriers": [],
        "white_space": [],
        "sources": [],
        "raw_response": text_content,
        "parse_error": "Could not parse structured JSON from response",
    }
