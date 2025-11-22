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
    Competitor Agent: Analyzes competitive landscape.

    Input: {job_id, problem_context, obstacles_findings, solutions_findings, legal_findings}
    Output: {direct_competitors, indirect_competitors, market_structure, barriers, white_space, sources}
    """
    logger.info(f"Competitor Agent received event: {json.dumps(event)}")

    try:
        # Parse input
        job_id = event["job_id"]
        problem_context = event["instructions"]
        obstacles_findings = event.get("obstacles_findings", {})
        solutions_findings = event.get("solutions_findings", {})
        legal_findings = event.get("legal_findings", {})

        logger.info(f"Processing Competitor Agent for job {job_id}")

        # Run agent with Claude
        result = run_competitor_analysis(
            problem_context, obstacles_findings, solutions_findings, legal_findings
        )

        logger.info(f"Completed Competitor Agent for job {job_id}")

        return {
            "statusCode": 200,
            "body": json.dumps({"job_id": job_id, "agent": "competitor", "findings": result}),
        }

    except Exception as e:
        logger.error(f"Error in Competitor Agent: {str(e)}", exc_info=True)

        raise


def run_competitor_analysis(
    problem_context, obstacles_findings, solutions_findings, legal_findings
):
    """
    Analyze competitive landscape using Claude with web search.
    """
    system_prompt = """Eres un analista experto en inteligencia competitiva \
especializado en análisis de mercado.

Tu rol es investigar e identificar:
1. Competidores directos - empresas/productos resolviendo exactamente el \
mismo problema
2. Competidores indirectos - soluciones alternativas o productos sustitutos
3. Estructura de mercado - ¿es monopolístico, oligopolístico, fragmentado o \
emergente?
4. Barreras de entrada - ¿qué dificulta que nuevos entrantes compitan?
5. Oportunidades de espacio blanco - segmentos desatendidos o brechas en \
el mercado

Para cada categoría de competidor, proporciona:
- Nombres de empresa/producto con URLs
- Su enfoque y propuesta de valor
- Fortalezas y debilidades
- Posición en el mercado (líder, retador, nicho)
- Financiamiento/ingresos (si está disponible)
- Desarrollos o noticias recientes

Usa web_search y web_fetch para encontrar:
- Jugadores actuales en el mercado
- Anuncios recientes de financiamiento
- Lanzamientos de productos y características
- Datos de participación de mercado
- Reseñas y sentimiento de clientes
- Reportes y análisis de la industria

Entrega tus hallazgos como un objeto JSON con esta estructura:
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
  "white_space": ["oportunidad 1", "oportunidad 2", ...],
  "sources": ["url 1", "url 2", ...]
}"""

    previous_context = f"""
HALLAZGOS PREVIOS - OBSTÁCULOS:
{json.dumps(obstacles_findings, indent=2)}

HALLAZGOS PREVIOS - SOLUCIONES:
{json.dumps(solutions_findings, indent=2)}

HALLAZGOS PREVIOS - LEGAL:
{json.dumps(legal_findings, indent=2)}
"""

    user_prompt = f"""CONTEXTO DEL PROBLEMA:
{problem_context}

{previous_context}

Dado el problema y la investigación previa, por favor analiza el panorama \
competitivo. Usa búsqueda web para encontrar:
- Competidores directos e indirectos
- Estructura y dinámicas del mercado
- Barreras de entrada y ventajas competitivas
- Oportunidades y espacio blanco
- Desarrollos competitivos recientes

Proporciona información detallada y actualizada con fuentes."""

    # Use Anthropic's built-in server-side web search
    tools = [
        {
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 5
        }
    ]

    print("=" * 80)
    print("COMPETITOR AGENT: Calling Claude API with built-in web search...")
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
    print(f"COMPETITOR AGENT: Response stop_reason: {response.stop_reason}")
    print(f"COMPETITOR AGENT: Response has {len(response.content)} content blocks")
    
    # Log web search usage if present
    if hasattr(response, 'usage'):
        server_tool_use = response.usage.get('server_tool_use', {})
        if server_tool_use:
            searches = server_tool_use.get('web_search_requests', 0)
            print(f"COMPETITOR AGENT: Web searches performed: {searches}")
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
    print(f"COMPETITOR AGENT: Raw response text: {text_content[:500]}...")
    print("=" * 80)

    # Try to extract JSON from markdown code blocks
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", text_content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError as e:
            print(f"COMPETITOR AGENT: Failed to parse JSON from code block: {e}")

    # Try to find JSON object in text
    json_match = re.search(r"\{.*\}", text_content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError as e:
            print(f"COMPETITOR AGENT: Failed to parse JSON object: {e}")

    # If all else fails, return structured error
    print("COMPETITOR AGENT: Could not extract JSON from response, returning raw text")
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
