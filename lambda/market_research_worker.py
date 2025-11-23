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

    response = anthropic.create_message(
        messages=[ConversationMessage(
            role="user",
            content=user_prompt,
            timestamp=datetime.utcnow().isoformat()
        )],
        system=system_prompt,
        # tools=tools
    )

    # Extract only text content from response
    text_response = ""
    for block in response.content:
        if block.type == "text":
            text_response += block.text

    return text_response


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

    response = anthropic_2.create_message(
        messages=[ConversationMessage(
            role="user",
            content=user_prompt,
            timestamp=datetime.utcnow().isoformat()
        )],
        system=system_prompt,
        # tools=tools
    )

    # Extract only text content from response
    text_response = ""
    for block in response.content:
        if block.type == "text":
            text_response += block.text

    return text_response


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

    response = anthropic.create_message(
        messages=[ConversationMessage(
            role="user",
            content=user_prompt,
            timestamp=datetime.utcnow().isoformat()
        )],
        system=system_prompt,
        # tools=tools
    )

    # Extract only text content from response
    text_response = ""
    for block in response.content:
        if block.type == "text":
            text_response += block.text

    return text_response


def run_competitor_analysis(problem_context, obstacles_findings, solutions_findings, legal_findings):
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

    response = anthropic_2.create_message(
        messages=[ConversationMessage(
            role="user",
            content=user_prompt,
            timestamp=datetime.utcnow().isoformat()
        )],
        system=system_prompt,
        # tools=tools
    )

    # Extract only text content from response
    text_response = ""
    for block in response.content:
        if block.type == "text":
            text_response += block.text

    return text_response


def run_market_analysis(problem_context, obstacles_findings, solutions_findings, legal_findings, competitor_findings):
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

    response = anthropic.create_message(
        messages=[ConversationMessage(
            role="user",
            content=user_prompt,
            timestamp=datetime.utcnow().isoformat()
        )],
        system=system_prompt,
        # tools=tools
    )

    # Extract only text content from response
    text_response = ""
    for block in response.content:
        if block.type == "text":
            text_response += block.text

    return text_response


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

    response = anthropic_2.create_message(
        messages=[ConversationMessage(
            role="user",
            content=user_prompt,
            timestamp=datetime.utcnow().isoformat()
        )],
        system=system_prompt
    )

    # Extract only text content from response
    text_response = ""
    for block in response.content:
        if block.type == "text":
            text_response += block.text

    return text_response
