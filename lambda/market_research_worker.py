import json
import logging
import os
import re
from datetime import datetime
from shared.anthropic import Anthropic, ConversationMessage
from shared.job_model import JobHandler

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def extract_json_from_response(response_text: str) -> dict:
    """
    Extract JSON object from Claude's response which may contain markdown, web search tags, and other text.
    Looks for ```json ... ``` blocks or standalone JSON objects.
    """
    if not response_text:
        return {}

    # Remove web search tags first
    cleaned_text = re.sub(r'<web_search>.*?</web_search>', '', response_text, flags=re.DOTALL)
    
    # Try to find JSON in code blocks first
    json_match = re.search(r'```json\s*\n([\s\S]*?)\n```', cleaned_text)
    if json_match:
        try:
            json_str = json_match.group(1).strip()
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from code block: {e}")
            # Try to repair truncated JSON
            try:
                json_str = json_match.group(1).strip()
                # Count braces and brackets
                open_braces = json_str.count('{')
                close_braces = json_str.count('}')
                open_brackets = json_str.count('[')
                close_brackets = json_str.count(']')
                
                # Add missing closures
                repaired = json_str
                for _ in range(open_brackets - close_brackets):
                    repaired += ']'
                for _ in range(open_braces - close_braces):
                    repaired += '}'
                
                return json.loads(repaired)
            except Exception as repair_error:
                logger.warning(f"Failed to repair JSON: {repair_error}")

    # Try to find standalone JSON object (between first { and last })
    first_brace = cleaned_text.find('{')
    if first_brace != -1:
        # Find the matching closing brace
        brace_count = 0
        for i in range(first_brace, len(cleaned_text)):
            if cleaned_text[i] == '{':
                brace_count += 1
            elif cleaned_text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    json_str = cleaned_text[first_brace:i+1]
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse standalone JSON: {e}")
                    break

    # If all else fails, return empty dict with error note
    logger.error(f"Could not extract valid JSON from response. First 500 chars: {response_text[:500]}")
    return {"error": "Could not parse agent response", "raw_preview": response_text[:500]}


# Get environment variables
JOBS_TABLE_NAME = os.environ.get("JOBS_TABLE_NAME", "test-table")
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
ANTHROPIC_API_KEY_2 = os.environ["ANTHROPIC_API_KEY_2"]

# Get table reference
job_handler = JobHandler(JOBS_TABLE_NAME)

# Initialize Anthropic client
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)
anthropic_2 = Anthropic(api_key=ANTHROPIC_API_KEY_2)


def handler(event, context):
    """
    Market Research Orchestrator: Coordinates 5 research agents sequentially.

    Flow: Obstacles → Solutions → Legal → Competitor → Market → Synthesis
    """
    logger.info(f"Market Research Orchestrator received event: {json.dumps(event)}")
    
    # Normal SQS processing with DynamoDB
    for record in event["Records"]:
        try:
            # Parse the SQS message
            message_body = json.loads(record["body"])
            job_id = message_body["job_id"]
            session_id = message_body["session_id"]

            job = job_handler.find_one(session_id=session_id, job_id=job_id)
            if job is None:
                logger.error(f"Job {job_id} not found in session {session_id}. Skipping.")
                continue

            if job.status != 'CREATED':
                logger.warning(f"Job {job_id} in session {session_id} is not in CREATED status. Current status: {job.status}. Skipping.")
                continue

            logger.info(f"Starting market research orchestration for job {job_id} with status {job.status}")

            job_handler.mark_in_progress(session_id=session_id, job_id=job_id)
            
            final_result = _execute_agents(job.instructions, session_id, job_id)

            # Mark as completed
            job_handler.mark_completed(
                session_id=session_id,
                job_id=job_id,
                result=json.dumps(final_result)
            )

            logger.info(
                f"Market research orchestration completed successfully for job {job_id}"
            )

        except Exception as agent_error:
            logger.error(
                f"Agent execution failed for job {job_id}: {str(agent_error)}", exc_info=True
            )

            job_handler.mark_failed(
                session_id=session_id,
                job_id=job_id,
                result=str(agent_error)
            )

            raise

    return {
        "statusCode": 200,
        "body": json.dumps("Successfully processed messages")
    }


def _execute_agents(instructions, session_id, job_id):
    """
    Execute all 5 agents sequentially and return the final result.
    """
    # Agent 1: Obstacles
    logger.info(f"Invoking Obstacles Agent for job {job_id}")
    obstacles_response = run_obstacles_analysis(instructions)
    obstacles_findings = extract_json_from_response(obstacles_response)
    logger.info(f"Obstacles Agent completed for job {job_id}")

    # Agent 2: Solutions
    logger.info(f"Invoking Solutions Agent for job {job_id}")
    solutions_response = run_solutions_analysis(instructions, obstacles_findings)
    solutions_findings = extract_json_from_response(solutions_response)
    logger.info(f"Solutions Agent completed for job {job_id}")

    # Agent 3: Legal
    logger.info(f"Invoking Legal Agent for job {job_id}")
    legal_response = run_legal_analysis(
        instructions,
        obstacles_findings,
        solutions_findings,
    )
    legal_findings = extract_json_from_response(legal_response)
    logger.info(f"Legal Agent completed for job {job_id}")

    # Agent 4: Competitor
    logger.info(f"Invoking Competitor Agent for job {job_id}")
    competitor_response = run_competitor_analysis(
        instructions,
        obstacles_findings,
        solutions_findings,
        legal_findings,
    )
    competitor_findings = extract_json_from_response(competitor_response)
    logger.info(f"Competitor Agent completed for job {job_id}")

    # Agent 5: Market
    logger.info(f"Invoking Market Agent for job {job_id}")
    market_response = run_market_analysis(
        instructions,
        obstacles_findings,
        solutions_findings,
        legal_findings,
        competitor_findings,
    )
    market_findings = extract_json_from_response(market_response)
    logger.info(f"Market Agent completed for job {job_id}")

    # Synthesis: Generate executive summary (keep as text, not JSON)
    logger.info(f"Generating synthesis for job {job_id}")
    synthesis = generate_synthesis(
        instructions,
        obstacles_findings,
        solutions_findings,
        legal_findings,
        competitor_findings,
        market_findings,
    )

    # Build final result - all findings are now proper JSON objects
    final_result = {
        "instructions": instructions,
        "findings": {
            "obstacles": obstacles_findings,
            "solutions": solutions_findings,
            "legal": legal_findings,
            "competitors": competitor_findings,
            "market": market_findings,
        },
        "synthesis": synthesis,
        "completed_at": datetime.utcnow().isoformat(),
    }
    
    return final_result


def run_obstacles_analysis(problem_context):
    """
    Analyze obstacles using Claude with Anthropic's built-in web search.
    The web search is executed server-side by Anthropic.
    """
    system_prompt = """Eres un analista experto identificando los 3-4 obstáculos \
MÁS CRÍTICOS para nuevas ideas de negocio.

IMPORTANTE: Sé CONCISO. Máximo 3-4 obstáculos por categoría, máximo 2 frases por obstáculo.

Identifica SOLO lo más crítico en:
1. Técnico - limitaciones que pueden frenar implementación
2. Mercado - barreras que impiden adopción/ventas
3. Regulatorio - requisitos legales bloqueantes
4. Usuario - fricción principal en adopción
5. Financiero - barreras de costo/financiamiento críticas

Usa web_search para validar con datos reales.

Para cada obstáculo: severidad + dato clave + impacto específico.
Critical insights: Solo los 3 hallazgos MÁS IMPORTANTES y accionables.

Responde en JSON:
{
"technical": ["máximo 3-4 obstáculos críticos, <100 caracteres cada uno"],
"market": ["máximo 3-4 obstáculos críticos, <100 caracteres cada uno"],
"regulatory": ["máximo 3-4 obstáculos críticos, <100 caracteres cada uno"],
"user": ["máximo 3-4 obstáculos críticos, <100 caracteres cada uno"],
"financial": ["máximo 3-4 obstáculos críticos, <100 caracteres cada uno"],
"critical_insights": ["solo 3 insights clave accionables, <150 caracteres cada uno"],
"sources": ["top 3-5 fuentes más relevantes"]
}"""

    user_prompt = f"""CONTEXTO DEL PROBLEMA:
    {problem_context}

    Analiza los 3-4 obstáculos MÁS CRÍTICOS para este problema.

    SÉ CONCISO: Máximo 3-4 obstáculos por categoría, máximo 100 caracteres por obstáculo.
    ENFÓCATE EN: Lo que más puede frenar el éxito.
    USA web_search para: Validar con datos reales y específicos.

    Devuelve JSON con obstáculos cortos, claros y accionables."""

    # Use Anthropic's built-in server-side web search
    # Docs: https://platform.claude.com/docs/en/agents-and-tools/
    #       tool-use/web-search-tool
    # tools = [
    #     {
    #         "type": "web_search_20250305",
    #         "name": "web_search",
    #         "max_uses": 1  # Limit to 5 searches ($0.05 cost)
    #     }
    # ]

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
        # tools=tools
    )

    return response


def run_solutions_analysis(problem_context, obstacles_findings):
    """
    Analyze existing solutions using Claude with web search tools.
    """
    system_prompt = """Eres un analista experto identificando las 2-3 soluciones \
PRINCIPALES que existen hoy.

IMPORTANTE: Sé CONCISO. Máximo 2-3 soluciones por categoría.

Identifica:
1. Manual - cómo se resuelve hoy sin tecnología
2. Digital - top 2-3 productos/plataformas principales
3. Workarounds - top 2-3 formas creativas de evitar el problema
4. Gaps - las 3 MAYORES oportunidades no cubiertas

Para cada solución: nombre + efectividad + limitación clave (máximo 80 caracteres).

Usa web_search para encontrar soluciones reales con nombres específicos.

Responde en JSON:
{
"manual_solutions": [
    {"name": "...", "effectiveness": "alta/media/baja", "limitation": "<60 caracteres"}
],
"digital_solutions": [
    {"name": "...", "url": "...", "strengths": "<60 caracteres", "weaknesses": "<60 caracteres"}
],
"workarounds": ["máximo 3, <80 caracteres cada uno"],
"gaps": ["máximo 3 brechas críticas, <100 caracteres cada una"],
"sources": ["top 3-5 URLs"]
}"""

    obstacles_context = f"""
    HALLAZGOS PREVIOS - OBSTÁCULOS:
    {json.dumps(obstacles_findings, indent=2)}
    """

    user_prompt = f"""CONTEXTO DEL PROBLEMA:
    {problem_context}

    {obstacles_context}

    Identifica las 2-3 MEJORES soluciones que existen HOY para este problema.

    SÉ CONCISO: Máximo 2-3 soluciones por categoría, máximo 80 caracteres por descripción.
    USA web_search para: Nombres específicos de productos/servicios reales.
    ENFÓCATE EN: Qué funciona, qué falta, oportunidades claras.

    Devuelve JSON con soluciones específicas, efectividad y gaps accionables."""

    # Use Anthropic's built-in server-side web search
    # tools = [
    #     {
    #         "type": "web_search_20250305",
    #         "name": "web_search",
    #         "max_uses": 1
    #     }
    # ]

    print("=" * 80)
    print("SOLUTIONS AGENT: Calling Claude API with built-in web search...")
    print("=" * 80)

    response = anthropic_2.send_message(
        messages=[ConversationMessage(
            role="user",
            content=user_prompt,
            timestamp=datetime.utcnow().isoformat()
        )],
        system=system_prompt,
        # tools=tools
    )

    return response


def run_legal_analysis(problem_context, obstacles_findings, solutions_findings):
    """
    Analyze legal and regulatory requirements using Claude with web search.
    """
    system_prompt = """Eres un analista legal identificando SOLO las 2-3 \
regulaciones MÁS CRÍTICAS que impactan este negocio.

IMPORTANTE: Sé CONCISO. Máximo 2-3 regulaciones por categoría, solo las críticas.

Identifica:
1. Industria - regulaciones específicas del sector que son OBLIGATORIAS
2. Datos - requisitos de privacidad/protección aplicables
3. Financiero - si aplica procesamiento de pagos/dinero
4. Regional - diferencias clave por país/región (si son críticas)

Para cada regulación: nombre + jurisdicción + complejidad + timeline estimado.

Usa web_search para validar regulaciones actuales.

Responde en JSON CONCISO:
{
"industry_regulations": [
    {"regulation": "<50 caracteres", "jurisdiction": "...", "complexity": "high|medium|low", "timeline": "..."}
],
"data_protection": [
    {"law": "GDPR/CCPA/etc", "jurisdiction": "...", "key_requirements": "<80 caracteres"}
],
"financial_regs": [
    {"regulation": "...", "applies_if": "<60 caracteres"}
],
"regional_variations": [
    {"region": "...", "key_difference": "<80 caracteres"}
],
"sources": ["top 3-5 URLs oficiales"]
}

Si una categoría NO aplica, devuelve array vacío []."""

    previous_context = f"""
    HALLAZGOS PREVIOS - OBSTÁCULOS:
    {json.dumps(obstacles_findings, indent=2)}

    HALLAZGOS PREVIOS - SOLUCIONES:
    {json.dumps(solutions_findings, indent=2)}
    """

    user_prompt = f"""CONTEXTO DEL PROBLEMA:
    {problem_context}

    {previous_context}

    Identifica SOLO las 2-3 regulaciones MÁS CRÍTICAS que impactan este negocio.

    SÉ CONCISO: Máximo 2-3 regulaciones por categoría, solo las obligatorias.
    USA web_search para: Validar nombres oficiales y requisitos actuales.
    ENFÓCATE EN: Qué es obligatorio, complejidad, timeline.

    Si una categoría NO aplica, devuelve array vacío []."""

    # Use Anthropic's built-in server-side web search
    # tools = [
    #     {
    #         "type": "web_search_20250305",
    #         "name": "web_search",
    #         "max_uses": 1
    #     }
    # ]

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
        # tools=tools
    )

    return response


def run_competitor_analysis(problem_context, obstacles_findings, solutions_findings, legal_findings):
    """
    Analyze competitive landscape using Claude with web search.
    """
    system_prompt = """Eres un analista competitivo identificando los TOP 3-4 \
competidores MÁS RELEVANTES.

IMPORTANTE: Sé CONCISO. Máximo 3 competidores directos, 2 indirectos.

Identifica:
1. Directos - top 3 empresas/productos resolviendo el mismo problema
2. Indirectos - top 2 alternativas/sustitutos principales
3. Estructura - tipo de mercado en 1 frase
4. Barreras - las 2-3 barreras MÁS SIGNIFICATIVAS de entrada
5. Oportunidades - top 2-3 brechas/espacios blancos

Para cada competidor: nombre + URL + 1 fortaleza clave + 1 debilidad clave.

Usa web_search para nombres específicos y datos de mercado.

Responde en JSON CONCISO:
{
"direct_competitors": [
    {
    "name": "...",
    "url": "...",
    "strength": "<60 caracteres",
    "weakness": "<60 caracteres",
    "position": "líder|retador|nicho"
    }
],
"indirect_competitors": [
    {
    "name": "...",
    "type": "substitute|alternative",
    "why_competitive": "<80 caracteres"
    }
],
"market_structure": {
    "type": "monopolistic|oligopolistic|fragmented|emerging",
    "key_insight": "<100 caracteres>"
},
"barriers": [
    {"type": "brand|network|tech|regulatory|capital", "severity": "high|med|low", "description": "<60 caracteres"}
],
"white_space": ["máximo 3 oportunidades, <100 caracteres cada una"],
"sources": ["top 3-5 URLs"]
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

    Identifica los TOP 3-4 competidores MÁS RELEVANTES y oportunidades clave.

    SÉ CONCISO: Máximo 3 directos, 2 indirectos, nombres específicos.
    USA web_search para: Empresas reales, URLs, datos de mercado.
    ENFÓCATE EN: Quién domina, barreras principales, espacios blancos.

    Devuelve JSON con competidores específicos, estructura de mercado en 1 frase."""

    # Use Anthropic's built-in server-side web search
    # tools = [
    #     {
    #         "type": "web_search_20250305",
    #         "name": "web_search",
    #         "max_uses": 1
    #     }
    # ]

    print("=" * 80)
    print("COMPETITOR AGENT: Calling Claude API with built-in web search...")
    print("=" * 80)

    response = anthropic_2.send_message(
        messages=[ConversationMessage(
            role="user",
            content=user_prompt,
            timestamp=datetime.utcnow().isoformat()
        )],
        system=system_prompt,
        # tools=tools
    )

    return response


def run_market_analysis(problem_context, obstacles_findings, solutions_findings, legal_findings, competitor_findings):
    """
    Analyze market dynamics using Claude with web search.
    """
    system_prompt = """Eres un analista de mercado enfocado en datos CLAVE y \
accionables.

IMPORTANTE: Sé CONCISO. Números clave + contexto breve.

Cuantifica:
1. Tamaño - TAM/SAM con cifra + año + fuente
2. Crecimiento - CAGR proyectado + top 2 drivers
3. Segmentos - top 2-3 segmentos de clientes más importantes
4. Pricing - rango de precios + modelo dominante

Usa web_search para cifras de reportes de mercado reales.

Responde en JSON CONCISO con DATOS ESPECÍFICOS:
{
"market_size": {
    "tam": {"value": "$XXB", "year": "2024", "source": "nombre reporte"},
    "sam": {"value": "$XXB", "methodology": "<60 caracteres>"},
    "som": {"value": "$XXM", "assumptions": "<60 caracteres>"}
},
"growth_trends": {
    "projected_cagr": "XX%",
    "time_period": "2024-2030",
    "top_drivers": ["driver 1 <60 chars>", "driver 2 <60 chars>"]
},
"customer_segments": [
    {
    "segment": "...",
    "size_pct": "XX%",
    "key_need": "<60 caracteres>"
    }
],
"pricing_benchmarks": {
    "range": "$X - $Y",
    "dominant_model": "subscription|one-time|usage",
    "examples": [
    {"product": "...", "price": "...", "model": "..."}
    ]
},
"sources": ["top 3-5 reportes de mercado con URLs"]
}

Si no encuentras datos: estima con disclaimer "Estimado basado en..."."""

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

    Cuantifica el mercado con DATOS ESPECÍFICOS y fuentes reales.

    SÉ CONCISO: Números clave (TAM, CAGR) + contexto breve.
    USA web_search para: Reportes de mercado con cifras reales.
    ENFÓCATE EN: Tamaño, crecimiento, segmentos principales, pricing.

    IMPORTANTE: Si no encuentras datos exactos, estima con disclaimer "Estimado basado en..."
    Devuelve JSON con números específicos ($XXB, XX%), no vagos."""

    # Use Anthropic's built-in server-side web search
    # tools = [
    #     {
    #         "type": "web_search_20250305",
    #         "name": "web_search",
    #         "max_uses": 1
    #     }
    # ]

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
        # tools=tools
    )

    return response


def generate_synthesis(problem_context, obstacles, solutions, legal, competitors, market):
    """
    Generate executive summary synthesizing all research findings.
    """
    system_prompt = """Eres un analista de negocios ejecutivo creando un informe \
    completo de investigación de mercado.

    Tu rol es sintetizar los hallazgos de 5 agentes de investigación en un resumen \
    ejecutivo claro y accionable.

    El resumen debe:
    1. Comenzar con una breve declaración del problema
    2. Resumir los obstáculos y desafíos clave
    3. Analizar las soluciones existentes y sus brechas
    4. Destacar consideraciones legales/regulatorias críticas
    5. Evaluar el panorama competitivo
    6. Cuantificar la oportunidad de mercado
    7. Proporcionar recomendaciones estratégicas

    Escribe en prosa clara y profesional. Usa viñetas para insights clave. \
    Enfócate en inteligencia accionable.

    Apunta a 800-1200 palabras. Incluye puntos de datos específicos y fuentes \
    cuando sea relevante. Debe ser en texto plano, no incluyas JSON, Markdown u otro formato."""

    all_findings = f"""
    CONTEXTO DEL PROBLEMA:
    {problem_context}

    HALLAZGOS DE OBSTÁCULOS:
    {json.dumps(obstacles, indent=2)}

    HALLAZGOS DE SOLUCIONES:
    {json.dumps(solutions, indent=2)}

    HALLAZGOS LEGALES/REGULATORIOS:
    {json.dumps(legal, indent=2)}

    PANORAMA COMPETITIVO:
    {json.dumps(competitors, indent=2)}

    ANÁLISIS DE MERCADO:
    {json.dumps(market, indent=2)}
    """

    user_prompt = f"""Por favor sintetiza los siguientes hallazgos de \
    investigación de mercado en un resumen ejecutivo completo.

    {all_findings}

    Crea un informe bien estructurado que cuente la historia completa y \
    proporcione insights accionables."""

    logger.info("Generating synthesis with Claude API...")

    response = anthropic_2.send_message(
        messages=[ConversationMessage(
            role="user",
            content=user_prompt,
            timestamp=datetime.utcnow().isoformat()
        )],
        system=system_prompt
    )

    return response
