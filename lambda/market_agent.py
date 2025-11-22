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
    system_prompt = """Eres un analista de mercado experto especializado en \
dimensionamiento de mercado, tendencias y análisis de clientes.

Tu rol es investigar y cuantificar:
1. Tamaño de mercado - TAM (Total Addressable Market), SAM (Serviceable \
Addressable Market), SOM (Serviceable Obtainable Market)
2. Tendencias de crecimiento - tasas de crecimiento históricas, proyecciones, \
factores impulsores
3. Segmentos de clientes - quiénes son los compradores, sus características, \
necesidades y comportamientos
4. Benchmarks de precio - cuánto cuestan productos similares, modelos de \
precio, disposición a pagar

Para cada área, proporciona:
- Números específicos y puntos de datos con fuentes
- Desglose geográfico (global vs regional)
- Tendencias basadas en tiempo (históricas y proyectadas)
- Evidencia de soporte y metodología

Usa web_search para encontrar:
- Reportes de investigación de mercado y análisis de industria
- Finanzas de empresas y métricas
- Encuestas y reseñas de clientes
- Información de precios de sitios web de competidores
- Publicaciones y estadísticas de la industria

Entrega tus hallazgos como un objeto JSON con esta estructura:
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
    "drivers": ["impulsor 1", "impulsor 2", ...],
    "headwinds": ["viento en contra 1", "viento en contra 2", ...]
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
HALLAZGOS PREVIOS - OBSTÁCULOS:
{json.dumps(obstacles_findings, indent=2)}

HALLAZGOS PREVIOS - SOLUCIONES:
{json.dumps(solutions_findings, indent=2)}

HALLAZGOS PREVIOS - LEGAL:
{json.dumps(legal_findings, indent=2)}

HALLAZGOS PREVIOS - COMPETIDORES:
{json.dumps(competitor_findings, indent=2)}
"""

    user_prompt = f"""CONTEXTO DEL PROBLEMA:
{problem_context}

{previous_context}

Dado el problema y toda la investigación previa, por favor analiza las \
dinámicas del mercado. Usa búsqueda web para encontrar:
- Datos de tamaño de mercado y proyecciones
- Tasas de crecimiento y tendencias
- Segmentos y características de clientes
- Benchmarks y modelos de precio
- Reportes y estadísticas de la industria

Enfócate en datos cuantitativos con fuentes claras. Sé específico con \
números, períodos de tiempo y geografías."""

    # Use Anthropic's built-in server-side web search
    tools = [
        {
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 5
        }
    ]

    print("=" * 80)
    print("MARKET AGENT: Calling Claude API with built-in web search...")
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
    print(f"MARKET AGENT: Response stop_reason: {response.stop_reason}")
    print(f"MARKET AGENT: Response has {len(response.content)} content blocks")
    
    # Log web search usage if present
    if hasattr(response, 'usage'):
        server_tool_use = response.usage.get('server_tool_use', {})
        if server_tool_use:
            searches = server_tool_use.get('web_search_requests', 0)
            print(f"MARKET AGENT: Web searches performed: {searches}")
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
    print(f"MARKET AGENT: Raw response text: {text_content[:500]}...")
    print("=" * 80)

    # Try to extract JSON from markdown code blocks
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", text_content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError as e:
            print(f"MARKET AGENT: Failed to parse JSON from code block: {e}")

    # Try to find JSON object in text
    json_match = re.search(r"\{.*\}", text_content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError as e:
            print(f"MARKET AGENT: Failed to parse JSON object: {e}")

    # If all else fails, return structured error
    print("MARKET AGENT: Could not extract JSON from response, returning raw text")
    return {
        "market_size": {},
        "growth_trends": {},
        "customer_segments": [],
        "pricing_benchmarks": {},
        "sources": [],
        "raw_response": text_content,
        "parse_error": "Could not parse structured JSON from response",
    }
