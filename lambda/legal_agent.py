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
    Legal Agent: Analyzes legal and regulatory requirements.

    Input: {job_id, problem_context, obstacles_findings, solutions_findings}
    Output: {industry_regulations, data_protection, financial_regs, regional_variations, sources}
    """
    logger.info(f"Legal Agent received event: {json.dumps(event)}")

    try:
        # Parse input
        job_id = event["job_id"]
        problem_context = event["instructions"]
        obstacles_findings = event.get("obstacles_findings", {})
        solutions_findings = event.get("solutions_findings", {})

        logger.info(f"Processing Legal Agent for job {job_id}")

        # Run agent with Claude
        result = run_legal_analysis(problem_context, obstacles_findings, solutions_findings)

        logger.info(f"Completed Legal Agent for job {job_id}")

        return {
            "statusCode": 200,
            "body": json.dumps({"job_id": job_id, "agent": "legal", "findings": result}),
        }

    except Exception as e:
        logger.error(f"Error in Legal Agent: {str(e)}", exc_info=True)

        raise


def run_legal_analysis(problem_context, obstacles_findings, solutions_findings):
    """
    Analyze legal and regulatory requirements using Claude with web search.
    """
    system_prompt = """You are an expert legal and regulatory analyst specializing in compliance requirements for new businesses and products.

Your role is to research and identify:
1. Industry-specific regulations - sector-specific laws and compliance requirements
2. Data protection - GDPR, CCPA, data privacy laws
3. Financial regulations - payment processing, money transmission, securities laws
4. Regional variations - how regulations differ by country/state
5. Licensing and certification requirements

For each regulatory category, provide:
- Specific regulations and laws (with official names/codes)
- Jurisdictions where they apply
- Compliance requirements and steps
- Potential penalties for non-compliance
- Timeline and complexity for compliance

Use web_search to find:
- Current regulations and recent changes
- Industry-specific compliance requirements
- Regulatory bodies and authorities
- Real examples of compliance issues from similar products

Output your findings as a JSON object with this structure:
{
  "industry_regulations": [
    {"regulation": "...", "jurisdiction": "...", "requirements": "...", "complexity": "high|medium|low"}
  ],
  "data_protection": [
    {"law": "...", "jurisdiction": "...", "key_requirements": "...", "penalties": "..."}
  ],
  "financial_regs": [
    {"regulation": "...", "applies_if": "...", "requirements": "..."}
  ],
  "regional_variations": [
    {"region": "...", "specific_requirements": "...", "difficulty": "..."}
  ],
  "sources": ["url 1", "url 2", ...]
}"""

    previous_context = f"""
PREVIOUS FINDINGS - OBSTACLES:
{json.dumps(obstacles_findings, indent=2)}

PREVIOUS FINDINGS - SOLUTIONS:
{json.dumps(solutions_findings, indent=2)}
"""

    user_prompt = f"""PROBLEM CONTEXT:
{problem_context}

{previous_context}

Given the problem and previous research, please analyze the legal and regulatory landscape. Use web search to find:
- Relevant industry regulations
- Data protection and privacy requirements
- Financial/payment regulations (if applicable)
- Licensing or certification needs
- Regional differences in regulations

Provide specific, actionable information with sources."""

    logger.info("Calling Claude API for legal analysis...")

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
        "industry_regulations": [],
        "data_protection": [],
        "financial_regs": [],
        "regional_variations": [],
        "sources": [],
        "raw_response": text_content,
        "parse_error": "Could not parse structured JSON from response",
    }
