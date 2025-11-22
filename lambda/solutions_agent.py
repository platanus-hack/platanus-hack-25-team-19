import json
import logging
import os
from shared.anthropic import Anthropic, ConversationMessage

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get environment variables
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# Initialize Anthropic client
client = Anthropic(api_key=ANTHROPIC_API_KEY)


def handler(event, context):
    """
    Solutions Agent: Researches existing manual/digital solutions and workarounds.

    Input: {job_id, problem_context, obstacles_findings}
    Output: {manual_solutions, digital_solutions, workarounds, gaps, sources}
    """
    logger.info(f"Solutions Agent received event: {json.dumps(event)}")

    try:
        # Parse input
        job_id = event["job_id"]
        problem_context = event["instructions"]
        obstacles_findings = event.get("obstacles_findings", {})

        logger.info(f"Processing Solutions Agent for job {job_id}")

        # Run agent with Claude
        result = run_solutions_analysis(problem_context, obstacles_findings)

        logger.info(f"Completed Solutions Agent for job {job_id}")

        return {
            "statusCode": 200,
            "body": json.dumps({"job_id": job_id, "agent": "solutions", "findings": result}),
        }

    except Exception as e:
        logger.error(f"Error in Solutions Agent: {str(e)}", exc_info=True)

        raise


def run_solutions_analysis(problem_context, obstacles_findings):
    """
    Analyze existing solutions using Claude with web search tools.
    """
    system_prompt = """You are an expert analyst researching existing solutions and workarounds for problems.

Your role is to conduct comprehensive research and identify:
1. Manual solutions - how people solve this problem manually today
2. Digital solutions - existing software/apps/platforms addressing this
3. Workarounds - creative ways people bypass the problem
4. Gaps - what's missing in current solutions that creates opportunities

For each solution category, provide:
- Specific examples with names/details
- How well they solve the problem (fully, partially, poorly)
- What they're missing or doing wrong
- Sources and URLs for verification

Use web_search and web_fetch to find:
- Existing products and services
- User forums and discussions about solutions
- Product reviews and comparisons
- Alternative approaches people are using

Output your findings as a JSON object with this structure:
{
  "manual_solutions": [
    {"name": "...", "description": "...", "effectiveness": "...", "limitations": "..."}
  ],
  "digital_solutions": [
    {"name": "...", "url": "...", "description": "...", "strengths": "...", "weaknesses": "..."}
  ],
  "workarounds": ["workaround 1", "workaround 2", ...],
  "gaps": ["gap 1", "gap 2", ...],
  "sources": ["url 1", "url 2", ...]
}"""

    obstacles_context = f"""
PREVIOUS FINDINGS - OBSTACLES:
{json.dumps(obstacles_findings, indent=2)}
"""

    user_prompt = f"""PROBLEM CONTEXT:
{problem_context}

{obstacles_context}

Given the identified obstacles, please research existing solutions and workarounds. Use web search to find:
- Current products/services addressing this problem
- How people solve this manually today
- Forum discussions about solutions and workarounds
- Gaps and limitations in existing approaches

Focus on finding concrete, real-world examples with sources."""

    logger.info("Calling Claude API for solutions analysis...")

    response = client.create_message(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        temperature=0.3,
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
        "manual_solutions": [],
        "digital_solutions": [],
        "workarounds": [],
        "gaps": [],
        "sources": [],
        "raw_response": text_content,
        "parse_error": "Could not parse structured JSON from response",
    }
