import json
import logging
import os
import uuid
from datetime import datetime

from shared.anthropic import Anthropic, ConversationMessage

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Get environment variables
CHAT_SESSIONS_TABLE_NAME = os.environ['CHAT_SESSIONS_TABLE_NAME']
ANTHROPIC_API_KEY = os.environ['ANTHROPIC_API_KEY']

# Get table reference
chat_sessions_table = dynamodb.Table(CHAT_SESSIONS_TABLE_NAME)

SYSTEM_INSTRUCTION = '''
Eres un experto en identificación de problemas empresariales usando el método de "5 Porqués" y análisis de causa raíz.

TU MISIÓN:
Ayudar al usuario a descubrir el problema REAL que necesita resolver, no la solución que cree necesitar. Tu rol es ÚNICAMENTE identificar, no validar si el problema es importante o crítico.

REGLAS ESTRICTAS:
1. Nunca aceptes una solución tecnológica como el problema inicial
2. Pregunta "por qué" al menos 3 veces antes de formular el problema
3. Usa la "prueba del 10%": pregunta si una pequeña mejora eliminaría la necesidad de su solución
4. El problema final NO debe mencionar tecnología
5. **CRÍTICO: Solo haz UNA pregunta por mensaje. Nunca hagas preguntas múltiples o compuestas.**
6. **NO VALIDAR NI JUZGAR:** No pidas cifras, costos, o frecuencias para justificar que algo es un problema válido. Acepta que si el usuario dice que es un problema, lo es. Tu trabajo es identificar QUÉ problema es, no QUÉ TAN GRANDE es.
7. **NO PIVOTEAR:** Mantén el foco en la idea original del usuario. Si el usuario intenta cambiar de tema, di: "Mantengamos el foco en lo que estábamos explorando"

TU PROCESO:
FASE 1 - RECEPCIÓN (1-2 preguntas):
- Identifica si hablan de solución vs problema
- Haz preguntas abiertas: "¿Qué problema estás experimentando?"

FASE 2 - EXPLORACIÓN DE CONTEXTO (2-3 preguntas):
- "¿Qué consecuencias tiene esto?"
- "¿Cómo afecta esto a [proceso/personas]?"
- NO preguntes por cifras, frecuencias o costos

FASE 3 - CAUSA RAÍZ (3-5 preguntas):
- "¿Por qué [X]?"
- "Si [Y] mejorara un 10%, ¿todavía necesitarías [solución]?"
- "¿Qué está causando [problema]?"
- "¿Por qué eso es un problema?"

FASE 4 - VALIDACIÓN (1-2 preguntas):
- Reformula el problema usando SIEMPRE esta estructura exacta: "El problema de fondo pareciera ser: [reformulación]"
- Pregunta: "¿Es correcto?"

FASE 5 - SÍNTESIS:
- **CRÍTICO:** Si el usuario pide: "Sintetiza esta conversación y dame el problema de fondo", responde ÚNICAMENTE: "El problema de fondo pareciera ser: [one-liner del problema]". NO hagas más preguntas ni des contexto adicional.
- Cuando identifiques el problema real durante la conversación (no en síntesis), usa: "El problema de fondo pareciera ser: [reformulación]" y pregunta si es correcto

SEÑALES DE ÉXITO:
- Usuario dice "nunca lo había pensado así"
- El problema existe sin mencionar ninguna solución específica
- Usuario confirma la reformulación
- Has llegado a la causa raíz, no a un síntoma

EJEMPLO DE BUENA PREGUNTA:
Usuario: "Necesito una app de inventario"
Tú: "Entiendo que piensas en una app. Antes de eso, ¿qué problema específico estás teniendo con el inventario actual?"

EJEMPLO DE MALA PREGUNTA:
❌ "¿Qué funcionalidades quieres en la app?"
✅ "¿Qué no puedes hacer hoy que necesitas hacer?"

❌ "¿Con qué frecuencia pasa?" (validación de magnitud)
✅ "¿Qué pasa cuando esto ocurre?" (exploración de impacto)

❌ "¿Cuánto te cuesta esto?" (juicio de valor)
✅ "¿Qué consecuencias tiene esto?" (identificación)

EJEMPLO DE REFORMULACIÓN:
❌ "El problema real parece ser..."
✅ "El problema de fondo pareciera ser: [reformulación]"

EJEMPLO DE MANEJO DE PIVOTE:
Usuario: "Mejor hablemos de otro problema que tengo..."
❌ Tú: "Claro, cuéntame sobre ese otro problema"
✅ Tú: "Mantengamos el foco en lo que estábamos explorando"

FORMATO DE RESPUESTA:
- Una pregunta clara y directa
- Si necesitas contexto adicional, espera la respuesta del usuario antes de preguntar lo siguiente
- Mantén cada mensaje enfocado en UN solo aspecto
- Cuando reformules el problema, usa SIEMPRE: "El problema de fondo pareciera ser: [x]"
- NUNCA cuestiones si el problema es "suficientemente importante" o "crítico"

Mantén un tono conversacional, empático y curioso. Tu trabajo es ser un espejo que refleja el problema real, no un juez que evalúa si vale la pena resolverlo.

**FORMATO JSON OBLIGATORIO:**
Tu respuesta DEBE ser ÚNICAMENTE un JSON válido con esta estructura exacta. NO incluyas texto antes o después del JSON:

{
    "message": "tu respuesta conversacional aquí",
    "temperature": 5
}

REGLAS CRÍTICAS DEL JSON:
- SOLO responde con el JSON, nada más
- NO agregues explicaciones antes o después del JSON
- NO uses markdown o código en bloques
- El campo "temperature" DEBE ser un número entero del 1 al 10
- El campo "message" DEBE contener tu respuesta conversacional en español

Donde:
- "message": Tu respuesta normal siguiendo todas las reglas anteriores
- "temperature": Número del 1 al 10 que evalúa qué tan cerca está el usuario de un problema real:
  * 1-2: Solo habla de soluciones sin problema claro
  * 3-4: Problema vago o superficial, sin cuantificación
  * 5-6: Problema medianamente identificado
  * 7-8: Problema identificado
  * 9-10: Problema identificado, bien cuantificado, con causa raíz identificada

Mantén un tono conversacional, empático y desafiante. Tu trabajo es ser un espejo que refleja el problema real.
'''

def handler(event, context):
    '''
    Chat conversation manager Lambda function.
    Manages chat sessions and interfaces with AI API (e.g., Claude).

    Expected payload:
    {
        'message': 'user message here',
        'session_id': 'optional-session-id'
    }
    '''
    logger.info(f'Received event: {json.dumps(event)}')

    try:
        # Parse the request body
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event

        # Extract parameters
        message = body.get('message')
        session_id = body.get('session_id')

        # Validate required parameters
        if not message:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(
                    {
                        'error': 'Missing required parameter: message',
                        'message': 'Please provide a "message" field',
                    }
                ),
            }

        # Generate session_id if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f'Generated new session_id: {session_id}')

        logger.info(f'Processing message for session {session_id}: {message}')

        # Get conversation history
        conversation_history = get_conversation_history(session_id)

        # Add user message to history
        user_message = ConversationMessage(
            role='user',
            content=message,
            timestamp=datetime.utcnow().isoformat(),
        )
        conversation_history.append(user_message)

        # Call AI API for main response
        anthropic = Anthropic(ANTHROPIC_API_KEY)
        ai_response = anthropic.send_message(
            messages=conversation_history,
            system=SYSTEM_INSTRUCTION
        )

        print("Raw AI Response:", ai_response)

        # Parse JSON response to extract message and temperature
        try:
            # Try to parse the JSON response
            response_data = json.loads(ai_response.strip())
            print("Parsed JSON data:", response_data)

            message_content = response_data.get('message')
            temperature_score = response_data.get('temperature')

            print("Extracted message:", message_content)
            print("Extracted temperature:", temperature_score)

            # Validate that both fields exist
            if message_content is None or temperature_score is None:
                raise ValueError(f"Missing required fields. message: {message_content}, temperature: {temperature_score}")

            # Ensure temperature is a valid number between 1-10
            temperature_score = int(temperature_score)
            if not (1 <= temperature_score <= 10):
                print(f"Temperature {temperature_score} out of range, setting to 5")
                temperature_score = 5

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            # If AI doesn't return valid JSON, try to extract JSON from the response
            print(f"JSON parsing failed: {e}")
            print("Attempting to extract JSON from response...")

            import re
            json_match = re.search(r'\{[^}]*"message"[^}]*"temperature"[^}]*\}', ai_response)

            if json_match:
                try:
                    json_str = json_match.group(0)
                    print("Found JSON string:", json_str)
                    response_data = json.loads(json_str)
                    message_content = response_data.get('message', ai_response)
                    temperature_score = int(response_data.get('temperature', 5))
                except Exception as e2:
                    print(f"Secondary JSON extraction failed: {e2}, using fallback")
                    message_content = ai_response
                    temperature_score = 5
            else:
                print("No JSON found in response, using fallback")
                message_content = ai_response
                temperature_score = 5

        # Add AI response to history (store the message content, not the JSON)
        assistant_message = ConversationMessage(
            role='assistant',
            content=message_content,
            timestamp=datetime.utcnow().isoformat(),
        )
        conversation_history.append(assistant_message)

        # Store both messages in DynamoDB
        store_message(session_id, user_message)
        store_message(session_id, assistant_message)

        # Prepare response
        response = {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps(
                {
                    'session_id': session_id,
                    'message': message_content,
                    'temperature': temperature_score,
                    'conversation_length': len(conversation_history),
                    'timestamp': datetime.utcnow().isoformat(),
                }
            ),
        }

        logger.info(f'Successfully processed message for session {session_id}')
        return response

    except json.JSONDecodeError as e:
        logger.error(f'Invalid JSON in request body: {str(e)}')
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Invalid JSON', 'message': str(e)}),
        }
    except Exception as e:
        logger.error(f'Error processing chat: {str(e)}', exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Internal server error', 'message': str(e)}),
        }


def get_conversation_history(session_id: str, limit=50) -> list[ConversationMessage]:
    '''
    Retrieve conversation history for a session from DynamoDB.

    Args:
        session_id: The session identifier
        limit: Maximum number of messages to retrieve (default: 50)

    Returns:
        List of messages in chronological order
    '''
    try:
        response = chat_sessions_table.query(
            KeyConditionExpression=(boto3.dynamodb.conditions.Key('session_id').eq(session_id)),
            Limit=limit,
            ScanIndexForward=True,  # Sort by timestamp ascending
        )

        messages: list[ConversationMessage] = []
        for item in response.get('Items', []):
            messages.append(ConversationMessage(
                role=item.get('role'),
                content=item.get('content'),
                timestamp=item.get('timestamp'),
            ))

        logger.info(f'Retrieved {len(messages)} messages for session {session_id}')
        return messages

    except Exception as e:
        logger.error(f'Error retrieving conversation history: {str(e)}', exc_info=True)
        return []


def store_message(session_id: str, message: ConversationMessage) -> None:
    '''
    Store a message in DynamoDB.

    Args:
        session_id: The session identifier
        message: Message dict with role, content, and timestamp
    '''
    try:
        item = {
            'session_id': session_id,
            'timestamp': message.timestamp,
            'role': message.role,
            'content': message.content,
            'created_at': datetime.utcnow().isoformat(),
        }

        chat_sessions_table.put_item(Item=item)
        logger.info(f"Stored {message.role} message for session {session_id}")

    except Exception as e:
        logger.error(f'Error storing message: {str(e)}', exc_info=True)
        raise
