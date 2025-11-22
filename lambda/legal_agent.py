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
    system_prompt = """Eres un analista experto legal y regulatorio \
especializado en requisitos de cumplimiento para nuevos negocios y productos.

Tu rol es investigar e identificar:
1. Regulaciones específicas de la industria - leyes específicas del sector \
y requisitos de cumplimiento
2. Protección de datos - GDPR, CCPA, leyes de privacidad de datos
3. Regulaciones financieras - procesamiento de pagos, transmisión de dinero, \
leyes de valores
4. Variaciones regionales - cómo las regulaciones difieren por país/estado
5. Requisitos de licencias y certificación

Para cada categoría regulatoria, proporciona:
- Regulaciones y leyes específicas (con nombres/códigos oficiales)
- Jurisdicciones donde aplican
- Requisitos y pasos de cumplimiento
- Penalidades potenciales por incumplimiento
- Línea de tiempo y complejidad para el cumplimiento

Usa web_search para encontrar:
- Regulaciones actuales y cambios recientes
- Requisitos de cumplimiento específicos de la industria
- Organismos y autoridades regulatorias
- Ejemplos reales de problemas de cumplimiento de productos similares

Entrega tus hallazgos como un objeto JSON con esta estructura:
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
HALLAZGOS PREVIOS - OBSTÁCULOS:
{json.dumps(obstacles_findings, indent=2)}

HALLAZGOS PREVIOS - SOLUCIONES:
{json.dumps(solutions_findings, indent=2)}
"""

    user_prompt = f"""CONTEXTO DEL PROBLEMA:
{problem_context}

{previous_context}

Dado el problema y la investigación previa, por favor analiza el panorama \
legal y regulatorio. Usa búsqueda web para encontrar:
- Regulaciones relevantes de la industria
- Requisitos de protección de datos y privacidad
- Regulaciones financieras/de pago (si aplica)
- Necesidades de licencias o certificación
- Diferencias regionales en regulaciones

Proporciona información específica y accionable con fuentes."""

    # Use Anthropic's built-in server-side web search
    tools = [
        {
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 5
        }
    ]

    print("=" * 80)
    print("LEGAL AGENT: Calling Claude API with built-in web search...")
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
    print(f"LEGAL AGENT: Response stop_reason: {response.stop_reason}")
    print(f"LEGAL AGENT: Response has {len(response.content)} content blocks")
    
    # Log web search usage if present
    if hasattr(response, 'usage'):
        server_tool_use = response.usage.get('server_tool_use', {})
        if server_tool_use:
            searches = server_tool_use.get('web_search_requests', 0)
            print(f"LEGAL AGENT: Web searches performed: {searches}")
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
    print(f"LEGAL AGENT: Raw response text: {text_content[:500]}...")
    print("=" * 80)

    # Try to extract JSON from markdown code blocks
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", text_content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError as e:
            print(f"LEGAL AGENT: Failed to parse JSON from code block: {e}")

    # Try to find JSON object in text
    json_match = re.search(r"\{.*\}", text_content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError as e:
            print(f"LEGAL AGENT: Failed to parse JSON object: {e}")

    # If all else fails, return structured error
    print("LEGAL AGENT: Could not extract JSON from response, returning raw text")
    return {
        "industry_regulations": [],
        "data_protection": [],
        "financial_regs": [],
        "regional_variations": [],
        "sources": [],
        "raw_response": text_content,
        "parse_error": "Could not parse structured JSON from response",
    }
