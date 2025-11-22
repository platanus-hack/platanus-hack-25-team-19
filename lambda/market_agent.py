import json
import logging
import os
from shared.anthropic import Anthropic, ConversationMessage
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get environment variables
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# Initialize Anthropic client
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)


def handler(event, context):
    """
    Market Agent: Analyzes market size, growth, and dynamics.

    Input: {job_id, problem_context, + all previous findings}
    Output: {market_size, growth_trends, customer_segments, pricing_benchmarks, sources}
    """
    logger.info(f"Market Agent received event: {json.dumps(event)}")

    try:
        # Parse input
        job_id = event["job_id"]
        problem_context = event["instructions"]
        obstacles_findings = event.get("obstacles_findings", {})
        solutions_findings = event.get("solutions_findings", {})
        legal_findings = event.get("legal_findings", {})
        competitor_findings = event.get("competitor_findings", {})

        logger.info(f"Processing Market Agent for job {job_id}")

        # Run agent with Claude
        result = run_market_analysis(
            problem_context,
            obstacles_findings,
            solutions_findings,
            legal_findings,
            competitor_findings,
        )

        logger.info(f"Completed Market Agent for job {job_id}")

        return {
            "statusCode": 200,
            "body": json.dumps({"job_id": job_id, "agent": "market", "findings": result}),
        }

    except Exception as e:
        logger.error(f"Error in Market Agent: {str(e)}", exc_info=True)

        raise


def run_market_analysis(
    problem_context, obstacles_findings, solutions_findings, legal_findings, competitor_findings
):
    """
    Analyze market dynamics using Claude with web search.
    """
    system_prompt = """You are an expert market analyst specializing in market sizing, trends, and customer analysis.

Your role is to research and quantify:
1. Market size - TAM (Total Addressable Market), SAM (Serviceable Addressable Market), SOM (Serviceable Obtainable Market)
2. Growth trends - historical growth rates, projections, driving factors
3. Customer segments - who are the buyers, their characteristics, needs, and behaviors
4. Pricing benchmarks - what similar products cost, pricing models, willingness to pay

For each area, provide:
- Specific numbers and data points with sources
- Geographic breakdown (global vs regional)
- Time-based trends (historical and projected)
- Supporting evidence and methodology

Use web_search to find:
- Market research reports and industry analyses
- Company financials and metrics
- Customer surveys and reviews
- Pricing information from competitor websites
- Industry publications and statistics

Output your findings as a JSON object with this structure:
{
  "market_size": {
    "tam": {"value": "...", "unit": "USD|users|...", "year": "...", "source": "..."},
    "sam": {"value": "...", "unit": "...", "year": "...", "methodology": "..."},
    "som": {"value": "...", "unit": "...", "year": "...", "assumptions": "..."}
  },
  "growth_trends": {
    "historical_cagr": "...",
    "projected_cagr": "...",
    "time_period": "...",
    "drivers": ["driver 1", "driver 2", ...],
    "headwinds": ["headwind 1", "headwind 2", ...]
  },
  "customer_segments": [
    {
      "segment": "...",
      "size": "...",
      "characteristics": "...",
      "needs": ["..."],
      "buying_behavior": "..."
    }
  ],
  "pricing_benchmarks": {
    "range": "...",
    "average": "...",
    "models": ["subscription", "one-time", "usage-based", ...],
    "examples": [
      {"product": "...", "price": "...", "model": "..."}
    ]
  },
  "sources": ["url 1", "url 2", ...]
}"""

    previous_context = f"""
PREVIOUS FINDINGS - OBSTACLES:
{json.dumps(obstacles_findings, indent=2)}

PREVIOUS FINDINGS - SOLUTIONS:
{json.dumps(solutions_findings, indent=2)}

PREVIOUS FINDINGS - LEGAL:
{json.dumps(legal_findings, indent=2)}

PREVIOUS FINDINGS - COMPETITORS:
{json.dumps(competitor_findings, indent=2)}
"""

    user_prompt = f"""PROBLEM CONTEXT:
{problem_context}

{previous_context}

Given the problem and all previous research, please analyze the market dynamics. Use web search to find:
- Market size data and projections
- Growth rates and trends
- Customer segments and characteristics
- Pricing benchmarks and models
- Industry reports and statistics

Focus on quantitative data with clear sources. Be specific with numbers, time periods, and geographies."""

    logger.info("Calling Claude API for market analysis...")

    response = anthropic.send_message(
        messages=[ConversationMessage(
            role="user",
            content=user_prompt,
            timestamp=datetime.utcnow().isoformat()
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
        "market_size": {},
        "growth_trends": {},
        "customer_segments": [],
        "pricing_benchmarks": {},
        "sources": [],
        "raw_response": text_content,
        "parse_error": "Could not parse structured JSON from response",
    }
