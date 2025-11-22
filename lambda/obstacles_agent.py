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
    Obstacles Agent: Identifies technical, market, regulatory,
    user, and financial obstacles.

    Input: {job_id, problem_context}
    Output: {technical, market, regulatory, user, financial,
            critical_insights, sources}
    """
    print("=" * 80)
    print(f"Obstacles Agent received event: {json.dumps(event)}")
    print("=" * 80)

    try:
        # Parse input
        job_id = event["job_id"]
        problem_context = event["instructions"]

        print("=" * 80)
        print(f"Processing Obstacles Agent for job {job_id}")
        print("=" * 80)

        # Run agent with Claude
        result = run_obstacles_analysis(problem_context)

        print("=" * 80)
        print(f"Completed Obstacles Agent for job {job_id}")
        print("=" * 80)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "job_id": job_id,
                "agent": "obstacles",
                "findings": result
            }),
        }

    except Exception as e:
        print("=" * 80)
        print(f"Error in Obstacles Agent: {str(e)}")
        print("=" * 80)

        raise


def run_obstacles_analysis(problem_context):
    """
    Analyze obstacles using Claude with Anthropic's built-in web search.
    The web search is executed server-side by Anthropic.
    """
    system_prompt = """Eres un analista experto identificando obstáculos y \
desafíos para nuevas ideas de negocio o productos.

Tu rol es realizar una investigación exhaustiva e identificar:
1. Obstáculos técnicos - limitaciones tecnológicas, desafíos de \
implementación, problemas de escalabilidad
2. Obstáculos de mercado - madurez del mercado, problemas de timing, \
barreras de adopción por clientes
3. Obstáculos regulatorios - requisitos de cumplimiento, restricciones \
legales, necesidades de licencias
4. Obstáculos de usuario - desafíos de comportamiento de usuario, \
fricción en adopción, necesidades de educación
5. Obstáculos financieros - barreras de costo, desafíos de financiamiento, \
dificultades de pricing

Tienes acceso a la herramienta web_search para encontrar ejemplos reales, \
datos y evidencia.

Para cada categoría de obstáculo, proporciona:
- Obstáculos específicos y concretos (no genéricos)
- Evaluación de severidad (crítica, alta, media, baja)
- Razonamiento basado en ejemplos reales y datos de búsquedas web

Cuando hayas reunido suficiente información, entrega tus hallazgos como un \
objeto JSON con esta estructura:
{
  "technical": ["obstáculo 1", "obstáculo 2", ...],
  "market": ["obstáculo 1", "obstáculo 2", ...],
  "regulatory": ["obstáculo 1", "obstáculo 2", ...],
  "user": ["obstáculo 1", "obstáculo 2", ...],
  "financial": ["obstáculo 1", "obstáculo 2", ...],
  "critical_insights": ["insight clave 1", "insight clave 2", ...],
  "sources": ["url 1", "url 2", ...]
}"""

    user_prompt = f"""CONTEXTO DEL PROBLEMA:
{problem_context}

Por favor analiza los obstáculos y desafíos para este problema/solución. \
Usa web_search para encontrar:
- Soluciones similares que han enfrentado desafíos
- Panorama regulatorio y requisitos de cumplimiento
- Condiciones de mercado y barreras de adopción
- Preocupaciones de viabilidad técnica
- Desafíos financieros y de costos

Proporciona un análisis exhaustivo basado en evidencia con fuentes."""

    # Use Anthropic's built-in server-side web search
    # Docs: https://platform.claude.com/docs/en/agents-and-tools/
    #       tool-use/web-search-tool
    tools = [
        {
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 5  # Limit to 5 searches ($0.05 cost)
        }
    ]

    print("=" * 80)
    print("Calling Claude API with built-in web search...")
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
    print(f"Response stop_reason: {response.stop_reason}")
    print(f"Response has {len(response.content)} content blocks")
    print("=" * 80)

    # Log web search usage if present
    if hasattr(response, 'usage'):
        server_tool_use = response.usage.get('server_tool_use', {})
        if server_tool_use:
            searches = server_tool_use.get('web_search_requests', 0)
            print("=" * 80)
            print(f"Web searches performed: {searches}")
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
    print(f"Raw response text: {text_content[:500]}...")
    print("=" * 80)

    # Try to extract JSON from markdown code blocks
    json_match = re.search(
        r"```json\s*(\{.*?\})\s*```", text_content, re.DOTALL
    )
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError as e:
            print("=" * 80)
            print(f"Failed to parse JSON from code block: {e}")
            print("=" * 80)

    # Try to find JSON object in text
    json_match = re.search(r"\{.*\}", text_content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError as e:
            print("=" * 80)
            print(f"Failed to parse JSON object: {e}")
            print("=" * 80)

    # If all else fails, return structured error
    logger.warning(
        "Could not extract JSON from response, returning raw text"
    )
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
