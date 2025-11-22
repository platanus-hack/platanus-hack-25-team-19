import json
import logging
import os
from shared.anthropic import Anthropic, ConversationMessage

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get environment variables
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# Initialize Anthropic client
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)


def handler(event, context):
    """
    Obstacles Agent: Identifies technical, market, regulatory, user, and financial obstacles.

    Input: {job_id, problem_context}
    Output: {technical, market, regulatory, user, financial, critical_insights, sources}
    """
    logger.info(f"Obstacles Agent received event: {json.dumps(event)}")

    try:
        # Parse input
        job_id = event["job_id"]
        problem_context = event["instructions"]

        logger.info(f"Processing Obstacles Agent for job {job_id}")

        # Run agent with Claude
        result = run_obstacles_analysis(problem_context)

        logger.info(f"Completed Obstacles Agent for job {job_id}")

        return {
            "statusCode": 200,
            "body": json.dumps({"job_id": job_id, "agent": "obstacles", "findings": result}),
        }

    except Exception as e:
        logger.error(f"Error in Obstacles Agent: {str(e)}", exc_info=True)

        raise


def run_obstacles_analysis(problem_context):
    """
    Analyze obstacles using Claude with web search tools.
    """
    system_prompt = """You are an expert analyst identifying obstacles and challenges for new business ideas or products.

Your role is to conduct comprehensive research and identify:
1. Technical obstacles - technology limitations, implementation challenges, scalability issues
2. Market obstacles - market maturity, timing issues, customer adoption barriers
3. Regulatory obstacles - compliance requirements, legal restrictions, licensing needs
4. User obstacles - user behavior challenges, adoption friction, education needs
5. Financial obstacles - cost barriers, funding challenges, pricing difficulties

For each obstacle category, provide:
- Specific, concrete obstacles (not generic)
- Severity assessment (critical, high, medium, low)
- Evidence and sources to support your findings

Use web_search to find recent information about similar products/markets and their challenges.

Output your findings as a JSON object with this structure:
{
  "technical": ["obstacle 1", "obstacle 2", ...],
  "market": ["obstacle 1", "obstacle 2", ...],
  "regulatory": ["obstacle 1", "obstacle 2", ...],
  "user": ["obstacle 1", "obstacle 2", ...],
  "financial": ["obstacle 1", "obstacle 2", ...],
  "critical_insights": ["key insight 1", "key insight 2", ...],
  "sources": ["url 1", "url 2", ...]
}"""

    user_prompt = f"""PROBLEM CONTEXT:
{problem_context}

Please analyze the obstacles and challenges for this problem/solution. Use web search to gather current information about:
- Similar solutions that have faced challenges
- Regulatory landscape
- Market conditions
- Technical feasibility
- User adoption patterns

Provide comprehensive, evidence-based analysis."""

    logger.info("Calling Claude API for obstacles analysis...")

    response = anthropic.send_message(
        messages=[ConversationMessage(
            role="user",
            content=user_prompt
        )],
        system=system_prompt,
        tools=[
            {
                "name": "web_search",
                "description": "Search the web for information",
                "input_schema": {
                    "type": "object",
                    "properties": {"query": {"type": "string", "description": "The search query"}},
                    "required": ["query"],
                },
            }
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
        "technical": [],
        "market": [],
        "regulatory": [],
        "user": [],
        "financial": [],
        "critical_insights": [text_content],
        "sources": [],
        "parse_error": "Could not parse structured JSON from response",
    }
