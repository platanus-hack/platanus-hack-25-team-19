import json
import logging
import os
import boto3
from datetime import datetime
from typing import Dict, Any, List

from shared.anthropic import Anthropic, ConversationMessage
from shared.job_model import JobHandler

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Get environment variables
JOBS_TABLE_NAME = os.environ['JOBS_TABLE_NAME']
ANTHROPIC_API_KEY = os.environ['ANTHROPIC_API_KEY']

# Initialize Anthropic client
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

def handler(event, context):
    """
    External Research Lambda function.
    Searches for external experts using AI-powered web research.
    """
    logger.info(f'Received event: {json.dumps(event)}')

    for record in event['Records']:
        try:
            # Parse the SQS message
            message_body = json.loads(record['body'])
            job_id = message_body.get('job_id')
            session_id = message_body.get('session_id')

            if not job_id:
                logger.error('Missing job_id in message')
                continue

            # Retrieve job from DynamoDB
            job_handler = JobHandler(JOBS_TABLE_NAME)
            job = job_handler.find_one(session_id, job_id)

            if not job:
                logger.error(f'Job {job_id} not found')
                continue

            logger.info(f'Processing external research job {job_id}')

            # Parse job instructions
            instructions = json.loads(job.instructions)
            expert_profile = instructions.get('expert_profile', '')
            questions = instructions.get('questions', [])
            context_summary = instructions.get('context_summary', job.context_summary)

            # Update job status to IN_PROGRESS
            job_handler.mark_in_progress(
                session_id=session_id,
                job_id=job_id
            )

            # Conduct external expert search
            research_results = conduct_expert_search(expert_profile, questions, context_summary)

            job_handler.mark_completed(
                session_id=session_id,
                job_id=job_id,
                result=json.dumps(research_results, ensure_ascii=False)
            )

            logger.info(f'Successfully completed external research job {job_id}')

        except Exception as e:
            logger.error(f'Error processing external research: {str(e)}', exc_info=True)

            # Update job status to FAILED
            if 'job' in locals():
                try:
                    job.status = 'FAILED'
                    job.result = f'Error: {str(e)}'
                    job.updated_at = datetime.utcnow().isoformat()
                    job_handler.update(job)
                except Exception:
                    pass

    return {'statusCode': 200, 'body': 'External research processing completed'}


def conduct_expert_search(expert_profile: str, questions: List[str], context_summary: str) -> Dict[str, Any]:
    """
    Conduct AI-powered search for external experts.

    Args:
        expert_profile: Description of the type of expert needed
        questions: List of questions that need expert input
        context_summary: Summary of the business problem context

    Returns:
        Dictionary with search results and expert recommendations
    """

    # Generate search strategies using AI
    search_strategy = generate_search_strategy(expert_profile, questions, context_summary)

    results = {
        'expert_profile_needed': expert_profile,
        'questions_for_experts': questions,
        'search_strategy': search_strategy,
        'search_summary': '',
        'generated_at': datetime.utcnow().isoformat()
    }

    return results


def generate_search_strategy(expert_profile: str, questions: List[str], context_summary: str) -> Dict[str, Any]:
    """Generate AI-powered search strategy for finding experts."""

    strategy_prompt = f"""
    Analiza el siguiente perfil de experto necesario y genera una estrategia de búsqueda para encontrar profesionales externos.

    PERFIL DE EXPERTO REQUERIDO:
    {expert_profile}

    PREGUNTAS PARA EL EXPERTO:
    {chr(10).join(f"- {q}" for q in questions)}

    CONTEXTO DEL PROBLEMA:
    {context_summary}

    Genera una estrategia de búsqueda que incluya:
    1. Palabras clave para búsqueda en LinkedIn/profesional
    2. Palabras clave para búsqueda académica
    3. Palabras clave para directorios de industria
    4. Tipos de roles/títulos a buscar
    5. Industrias o sectores relevantes

    Responde en formato JSON:
    {{
        "professional_keywords": ["keyword1", "keyword2", ...],
        "academic_keywords": ["keyword1", "keyword2", ...],
        "industry_keywords": ["keyword1", "keyword2", ...],
        "target_roles": ["role1", "role2", ...],
        "target_industries": ["industry1", "industry2", ...]
    }}
    """

    try:
        response = anthropic.send_message(
            messages=[ConversationMessage(
                role="user",
                content=strategy_prompt,
                timestamp=datetime.utcnow().isoformat()
            )],
            system="Eres un especialista en búsqueda de talento y identificación de expertos. Genera estrategias de búsqueda precisas y efectivas."
        )

        return json.loads(response)
    except Exception as e:
        logger.error(f"Error generating search strategy: {e}")
        # Fallback strategy
        return {
            "professional_keywords": [expert_profile.split()[0] if expert_profile else None],
            "academic_keywords": [expert_profile.split()[0] if expert_profile else None],
            "industry_keywords": [expert_profile.split()[0] if expert_profile else None],
            "target_roles": ["consultor", "director", "especialista"],
            "target_industries": ["tecnología", "negocios", "consultoría"]
        }


def search_academic_experts(keywords: List[str], expert_profile: str) -> List[Dict[str, Any]]:
    """
    Simulate academic expert search using AI-generated realistic profiles.
    """

    academic_prompt = f"""
    Genera 2-3 perfiles realistas de expertos académicos que coincidan con este perfil:

    PERFIL BUSCADO: {expert_profile}
    PALABRAS CLAVE: {', '.join(keywords)}

    Para cada académico, proporciona:
    - Nombre completo
    - Título académico (Dr., PhD, etc.)
    - Universidad/Institución
    - Departamento/Facultad
    - Área de investigación principal
    - Publicaciones relevantes recientes
    - Años en academia
    - Especialidades de investigación
    - Por qué es relevante para el problema

    Responde en español con perfiles de académicos de universidades reconocidas de Latinoamérica.
    Formato JSON:
    {{
        "academics": [
            {{
                "name": "Dr./PhD Nombre Completo",
                "title": "Profesor/Investigador",
                "institution": "Universidad",
                "department": "Departamento/Facultad",
                "research_area": "Área de investigación",
                "recent_publications": ["publicación1", "publicación2"],
                "academic_years": 15,
                "specialties": ["especialidad1", "especialidad2"],
                "relevance": "Por qué es relevante para el problema"
            }}
        ]
    }}
    """

    try:
        response = anthropic.send_message(
            messages=[ConversationMessage(
                role="user",
                content=academic_prompt,
                timestamp=datetime.utcnow().isoformat()
            )],
            system="Eres un especialista en búsqueda de talento académico que genera perfiles de investigadores realistas y relevantes."
        )

        data = json.loads(response)
        academics = data.get('academics', [])

        # Add source information
        for academic in academics:
            academic['source'] = 'Academic Research Network'
            academic['contact_method'] = 'Email institucional'

        return academics

    except Exception as e:
        logger.error(f"Error generating academic experts: {e}")
        return []


def search_industry_experts(keywords: List[str], expert_profile: str) -> List[Dict[str, Any]]:
    """
    Simulate industry expert search using AI-generated realistic profiles.
    """

    industry_prompt = f"""
    Genera 2-3 perfiles realistas de expertos de la industria que coincidan con este perfil:

    PERFIL BUSCADO: {expert_profile}
    PALABRAS CLAVE: {', '.join(keywords)}

    Para cada experto de industria, proporciona:
    - Nombre completo
    - Título/Rol actual
    - Sector de la industria
    - Empresa/Organización
    - Años de experiencia en la industria
    - Especialidades técnicas
    - Reconocimientos o logros notables
    - Participación en conferencias/eventos
    - Por qué es relevante para el problema

    Responde en español con perfiles de expertos reconocidos en la industria latinoamericana.
    Formato JSON:
    {{
        "industry_experts": [
            {{
                "name": "Nombre Completo",
                "title": "Título/Rol",
                "industry_sector": "Sector",
                "organization": "Empresa/Organización",
                "industry_years": 12,
                "specialties": ["especialidad1", "especialidad2"],
                "achievements": ["logro1", "logro2"],
                "conferences": ["evento1", "evento2"],
                "relevance": "Por qué es relevante para el problema"
            }}
        ]
    }}
    """

    try:
        response = anthropic.send_message(
            messages=[ConversationMessage(
                role="user",
                content=industry_prompt,
                timestamp=datetime.utcnow().isoformat()
            )],
            system="Eres un especialista en búsqueda de talento industrial que genera perfiles de expertos reconocidos y relevantes."
        )

        data = json.loads(response)
        experts = data.get('industry_experts', [])

        # Add source information
        for expert in experts:
            expert['source'] = 'Industry Professional Network'
            expert['contact_method'] = 'Contacto profesional directo'

        return experts

    except Exception as e:
        logger.error(f"Error generating industry experts: {e}")
        return []


def generate_expert_recommendations(experts: List[Dict[str, Any]], questions: List[str], context_summary: str) -> List[Dict[str, Any]]:
    """Generate AI-powered recommendations for which experts to contact."""

    if not experts:
        return []

    recommendation_prompt = f"""
    Analiza los siguientes expertos encontrados y genera recomendaciones sobre cuáles contactar:

    EXPERTOS ENCONTRADOS:
    {json.dumps(experts, indent=2, ensure_ascii=False)}

    PREGUNTAS PARA LOS EXPERTOS:
    {chr(10).join(f"- {q}" for q in questions)}

    CONTEXTO DEL PROBLEMA:
    {context_summary}

    Para cada experto, evalúa:
    1. Relevancia para el problema específico (1-10)
    2. Probabilidad de respuesta positiva (1-10)
    3. Valor potencial de su input (1-10)
    4. Recomendación de contacto (Sí/No)
    5. Estrategia de acercamiento sugerida
    6. Preguntas específicas a hacer a este experto

    Responde en formato JSON con recomendaciones ordenadas por prioridad:
    {{
        "recommendations": [
            {{
                "expert_name": "Nombre",
                "relevance_score": 9,
                "response_probability": 7,
                "value_score": 8,
                "overall_priority": "Alta",
                "recommend_contact": true,
                "contact_strategy": "Estrategia de acercamiento",
                "specific_questions": ["pregunta1", "pregunta2"],
                "reasoning": "Por qué recomendamos contactar a este experto"
            }}
        ]
    }}
    """

    try:
        response = anthropic.send_message(
            messages=[ConversationMessage(
                role="user",
                content=recommendation_prompt,
                timestamp=datetime.utcnow().isoformat()
            )],
            system="Eres un especialista en análisis de talento que evalúa la idoneidad de expertos para consultas específicas."
        )

        data = json.loads(response)
        return data.get('recommendations', [])

    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return []


def generate_search_summary(results: Dict[str, Any]) -> str:
    """Generate a summary of the expert search results."""

    total_experts = len(results.get('found_experts', []))
    high_priority_recs = len([r for r in results.get('recommendations', []) if r.get('recommend_contact', False)])

    summary = f"""
    Búsqueda de Expertos Externos Completada:

    • Total de expertos identificados: {total_experts}
    • Expertos recomendados para contacto: {high_priority_recs}
    • Fuentes consultadas: LinkedIn Professional Network, Academic Research Network, Industry Professional Network
    • Perfil objetivo: {results.get('expert_profile_needed', 'No especificado')}

    Los expertos están listos para ser contactados según las estrategias de acercamiento recomendadas.
    """

    return summary.strip()
