import json
import logging
import os
from shared.anthropic import Anthropic

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get environment variables
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# Initialize Anthropic client
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)


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
    system_prompt = """Eres un analista experto investigando soluciones \
existentes y workarounds para problemas.

Tu rol es realizar una investigación exhaustiva e identificar:
1. Soluciones manuales - cómo las personas resuelven este problema \
manualmente hoy
2. Soluciones digitales - software/apps/plataformas existentes que abordan esto
3. Workarounds - formas creativas en que las personas evitan el problema
4. Brechas - lo que falta en las soluciones actuales que crea oportunidades

Para cada categoría de solución, proporciona:
- Ejemplos específicos con nombres/detalles
- Qué tan bien resuelven el problema (completamente, parcialmente, \
deficientemente)
- Qué les falta o están haciendo mal
- Fuentes y URLs para verificación

Usa web_search y web_fetch para encontrar:
- Productos y servicios existentes
- Foros de usuarios y discusiones sobre soluciones
- Reseñas y comparaciones de productos
- Enfoques alternativos que la gente está usando

Entrega tus hallazgos como un objeto JSON con esta estructura:
{
  "manual_solutions": [
    {"name": "...", "description": "...", "effectiveness": "...", "limitations": "..."}
  ],
  "digital_solutions": [
    {"name": "...", "url": "...", "description": "...", "strengths": "...", "weaknesses": "..."}
  ],
  "workarounds": ["workaround 1", "workaround 2", ...],
  "gaps": ["brecha 1", "brecha 2", ...],
  "sources": ["url 1", "url 2", ...]
}"""

    obstacles_context = f"""
HALLAZGOS PREVIOS - OBSTÁCULOS:
{json.dumps(obstacles_findings, indent=2)}
"""

    user_prompt = f"""CONTEXTO DEL PROBLEMA:
{problem_context}

{obstacles_context}

Dados los obstáculos identificados, por favor investiga las soluciones y \
workarounds existentes. Usa búsqueda web para encontrar:
- Productos/servicios actuales que abordan este problema
- Cómo las personas resuelven esto manualmente hoy
- Discusiones en foros sobre soluciones y workarounds
- Brechas y limitaciones en los enfoques existentes

Enfócate en encontrar ejemplos concretos del mundo real con fuentes."""

    # Use Anthropic's built-in server-side web search
    tools = [
        {
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 5
        }
    ]

    print("=" * 80)
    print("SOLUTIONS AGENT: Calling Claude API with built-in web search...")
    print("=" * 80)

    response = anthropic.send_message(
        messages=[ConversationMessage(
            role="user",
            content=user_prompt,
            timestamp=datetime.utcnow().isoformat()
        )],
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
        tools=tools
    )

    print("=" * 80)
    print(f"SOLUTIONS AGENT: Response stop_reason: {response.stop_reason}")
    print(f"SOLUTIONS AGENT: Response has {len(response.content)} content blocks")
    
    # Log web search usage if present
    if hasattr(response, 'usage'):
        server_tool_use = response.usage.get('server_tool_use', {})
        if server_tool_use:
            searches = server_tool_use.get('web_search_requests', 0)
            print(f"SOLUTIONS AGENT: Web searches performed: {searches}")
    print("=" * 80)

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

    print("=" * 80)
    print(f"SOLUTIONS AGENT: Raw response text: {text_content[:500]}...")
    print("=" * 80)

    # Try to extract JSON from markdown code blocks
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", text_content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError as e:
            print(f"SOLUTIONS AGENT: Failed to parse JSON from code block: {e}")

    # Try to find JSON object in text
    json_match = re.search(r"\{.*\}", text_content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError as e:
            print(f"SOLUTIONS AGENT: Failed to parse JSON object: {e}")

    # If all else fails, return structured error
    print("SOLUTIONS AGENT: Could not extract JSON from response, returning raw text")
    return {
        "manual_solutions": [],
        "digital_solutions": [],
        "workarounds": [],
        "gaps": [],
        "sources": [],
        "raw_response": text_content,
        "parse_error": "Could not parse structured JSON from response",
    }
