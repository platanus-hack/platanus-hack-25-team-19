import json
import logging
import os
from datetime import datetime

import boto3
from shared.anthropic import Anthropic
from shared.job_model import JobHandler

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Check if we're in test mode (local testing without AWS)
TEST_MODE = os.environ.get("TEST_MODE", "false").lower() == "true"

if TEST_MODE:
    logger.info("Running in TEST_MODE - using direct handler calls")
    # Import agent handlers for direct calling
    from obstacles_agent import handler as obstacles_handler
    from solutions_agent import handler as solutions_handler
    from legal_agent import handler as legal_handler
    from competitor_agent import handler as competitor_handler
    from market_agent import handler as market_handler
else:
    # Initialize AWS clients
    dynamodb = boto3.resource("dynamodb")
    lambda_client = boto3.client("lambda")

# Get environment variables
JOBS_TABLE_NAME = os.environ.get("JOBS_TABLE_NAME", "test-table")
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

if not TEST_MODE:
    OBSTACLES_AGENT_NAME = os.environ["OBSTACLES_AGENT_NAME"]
    SOLUTIONS_AGENT_NAME = os.environ["SOLUTIONS_AGENT_NAME"]
    LEGAL_AGENT_NAME = os.environ["LEGAL_AGENT_NAME"]
    COMPETITOR_AGENT_NAME = os.environ["COMPETITOR_AGENT_NAME"]
    MARKET_AGENT_NAME = os.environ["MARKET_AGENT_NAME"]
    
    # Get table reference
    jobs_table = dynamodb.Table(JOBS_TABLE_NAME)
    job_handler = JobHandler(JOBS_TABLE_NAME)

# Initialize Anthropic client
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)


def handler(event, context):
    """
    Market Research Orchestrator: Coordinates 5 research agents sequentially.

    Flow: Obstacles → Solutions → Legal → Competitor → Market → Synthesis
    
    In TEST_MODE: Pass instructions directly without DynamoDB lookup
    """
    logger.info(f"Market Research Orchestrator received event: {json.dumps(event)}")

    # In TEST_MODE, expect direct instructions
    if TEST_MODE:
        logger.info("TEST_MODE: Processing instructions directly")
        try:
            instructions = event.get("instructions", "")
            if not instructions:
                raise Exception("TEST_MODE requires 'instructions' in event")
            
            session_id = "test-session"
            job_id = "test-job"
            
            logger.info(f"TEST_MODE: Processing instructions: {instructions[:100]}...")
            
            # Skip DynamoDB operations in test mode
            logger.info("TEST_MODE: Skipping DynamoDB mark_in_progress")
            
            # Execute agents
            result = _execute_agents(instructions, session_id, job_id)
            
            logger.info("TEST_MODE: Skipping DynamoDB mark_completed")
            
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Market research completed (TEST_MODE)",
                    "result": result
                })
            }
            
        except Exception as e:
            logger.error(f"TEST_MODE error: {str(e)}", exc_info=True)
            raise
    
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

            logger.info(f"Starting market research orchestration for job {job_id}")

            job_handler.mark_in_progress(session_id=session_id, job_id=job_id)
            
            # Execute agents sequentially  
            try:
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

        except Exception as e:
            logger.error(f"Error in orchestrator: {str(e)}", exc_info=True)
            raise

    return {
        "statusCode": 200,
        "body": json.dumps("Successfully processed messages")
    }


def _execute_agents(instructions, session_id, job_id):
    """
    Execute all 5 agents sequentially and return the final result.
    """
    # Determine function names based on TEST_MODE
    if TEST_MODE:
        obstacles_name = "obstacles"
        solutions_name = "solutions"
        legal_name = "legal"
        competitor_name = "competitor"
        market_name = "market"
    else:
        obstacles_name = OBSTACLES_AGENT_NAME
        solutions_name = SOLUTIONS_AGENT_NAME
        legal_name = LEGAL_AGENT_NAME
        competitor_name = COMPETITOR_AGENT_NAME
        market_name = MARKET_AGENT_NAME
    
    # Agent 1: Obstacles
    logger.info(f"Invoking Obstacles Agent for job {job_id}")
    obstacles_response = invoke_agent(
        obstacles_name,
        {
            'session_id': session_id,
            'job_id': job_id,
            'instructions': instructions,
        }
    )
    obstacles_findings = extract_findings(obstacles_response)
    logger.info(f"Obstacles Agent completed for job {job_id}")

    # Agent 2: Solutions
    logger.info(f"Invoking Solutions Agent for job {job_id}")
    solutions_response = invoke_agent(
        solutions_name,
        {
            'session_id': session_id,
            'job_id': job_id,
            'instructions': instructions,
            "obstacles_findings": obstacles_findings,
        },
    )
    solutions_findings = extract_findings(solutions_response)
    logger.info(f"Solutions Agent completed for job {job_id}")

    # Agent 3: Legal
    logger.info(f"Invoking Legal Agent for job {job_id}")
    legal_response = invoke_agent(
        legal_name,
        {
            'session_id': session_id,
            'job_id': job_id,
            'instructions': instructions,
            "obstacles_findings": obstacles_findings,
            "solutions_findings": solutions_findings,
        },
    )
    legal_findings = extract_findings(legal_response)
    logger.info(f"Legal Agent completed for job {job_id}")

    # Agent 4: Competitor
    logger.info(f"Invoking Competitor Agent for job {job_id}")
    competitor_response = invoke_agent(
        competitor_name,
        {
            'session_id': session_id,
            'job_id': job_id,
            'instructions': instructions,
            "obstacles_findings": obstacles_findings,
            "solutions_findings": solutions_findings,
            "legal_findings": legal_findings,
        },
    )
    competitor_findings = extract_findings(competitor_response)
    logger.info(f"Competitor Agent completed for job {job_id}")

    # Agent 5: Market
    logger.info(f"Invoking Market Agent for job {job_id}")
    market_response = invoke_agent(
        market_name,
        {
            'session_id': session_id,
            'job_id': job_id,
            'instructions': instructions,
            "obstacles_findings": obstacles_findings,
            "solutions_findings": solutions_findings,
            "legal_findings": legal_findings,
            "competitor_findings": competitor_findings,
        },
    )
    market_findings = extract_findings(market_response)
    logger.info(f"Market Agent completed for job {job_id}")

    # Synthesis: Generate executive summary
    logger.info(f"Generating synthesis for job {job_id}")
    synthesis = generate_synthesis(
        instructions,
        obstacles_findings,
        solutions_findings,
        legal_findings,
        competitor_findings,
        market_findings,
    )

    # Build final result
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


def invoke_agent(function_name, payload):
    """
    Invoke an agent Lambda function synchronously.
    In TEST_MODE, calls the handler directly instead of via Lambda.
    """
    if TEST_MODE:
        # Direct handler call for testing
        logger.info(f"TEST_MODE: Calling handler directly for {function_name}")
        
        # Map function names to handlers
        handler_map = {
            "obstacles": obstacles_handler,
            "solutions": solutions_handler,
            "legal": legal_handler,
            "competitor": competitor_handler,
            "market": market_handler,
        }
        
        # Determine which handler to use based on function_name
        agent_name = None
        for key in handler_map.keys():
            if key in function_name.lower():
                agent_name = key
                break
        
        if agent_name is None:
            raise Exception(f"Unknown agent in TEST_MODE: {function_name}")
        
        handler = handler_map[agent_name]
        
        # Call handler directly (no context needed for testing)
        response_payload = handler(payload, None)
        
        logger.info(f"Handler {agent_name} completed successfully")
        return response_payload
    else:
        # Normal Lambda invocation
        logger.info(f"Invoking Lambda function: {function_name}")

        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",  # Synchronous
            Payload=json.dumps(payload),
        )

        # Parse response
        response_payload = json.loads(response["Payload"].read())

        if response["StatusCode"] != 200:
            raise Exception(f"Agent {function_name} returned status {response['StatusCode']}")

        if "FunctionError" in response:
            error_msg = response_payload.get("errorMessage", "Unknown error")
            raise Exception(f"Agent {function_name} failed: {error_msg}")

        logger.info(f"Lambda function {function_name} completed successfully")
        return response_payload


def extract_findings(agent_response):
    """
    Extract findings from agent Lambda response.
    """
    try:
        body = agent_response.get("body")
        if isinstance(body, str):
            body = json.loads(body)

        return body.get("findings", {})
    except Exception as e:
        logger.warning(f"Could not extract findings from response: {e}")
        return {}


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
cuando sea relevante."""

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

    response = anthropic.send_message(
        messages=[ConversationMessage(
            role="user",
            content=user_prompt
        )],
        system=system_prompt
    )

    # Extract text from response
    synthesis_text = ""
    for block in response.content:
        if block.type == "text":
            synthesis_text += block.text

    return synthesis_text
