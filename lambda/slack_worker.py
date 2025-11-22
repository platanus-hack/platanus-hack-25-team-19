import json
import logging
import os
from shared.job_model import JobHandler
from shared.slack import SlackHelper
from shared.anthropic import Anthropic, ConversationMessage

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')

# Initialize external service clients
anthropic_client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
slack_client = SlackHelper(token=os.environ['SLACK_BOT_TOKEN'])

# Get environment variables
JOBS_TABLE_NAME = os.environ["JOBS_TABLE_NAME"]

# Get table reference
jobs_table = dynamodb.Table(JOBS_TABLE_NAME)
conversations_table = dynamodb.Table(os.environ['CONVERSATIONS_TABLE_NAME'])
job_handler = JobHandler(JOBS_TABLE_NAME)

def generate_question(text):
    prompt = f"""
        **Rol:** Experto en comunicación interna corporativa.

        **Tarea:**
        Generar un mensaje directo para plataforma de chat (Teams/Slack) basado en los datos del JSON proporcionado.

        **Instrucciones de Contenido:**
        1.  Usa `contact.name` para el saludo (Ej: "Hola [Nombre]").
        2.  Menciona el `context_summary` como el motivo del mensaje.
        3.  Redacta las preguntas del array `questions` integrándolas en un solo párrafo coherente o punteos muy breves, manteniendo un tono de solicitud de ayuda profesional.

        **Reglas de Salida (ESTRICTO):**
        * Tu respuesta debe ser **ÚNICAMENTE** el texto del mensaje final.
        * **NO** incluyas introducciones como "Aquí está tu mensaje", "Propuesta:", ni saludos al usuario.
        * **NO** uses comillas al inicio o final ni bloques de código.

        **Input JSON:**
        ${text}
        """
    try:
        # Create a message using the anthropic helper
        messages = [ConversationMessage(role="user", content=prompt, timestamp="")]
        response = anthropic_client.send_message(messages)
        return response.content
    
    except Exception as e:
        print(f"AI Error: {e}")
        return None, None
    
def get_slack_user(email):
    return slack_client.get_user_by_email(email)

def check_for_reply(channel_id, oldest_ts, user_id):
    return slack_client.check_for_user_reply(channel_id, oldest_ts, user_id)

def lambda_handler(event, context):
    for record in event['Records']:
        payload = json.loads(record['body'])
        job_id = payload['job_id']
        session_id = payload['session_id']

        job = job_handler.find_one(session_id=session_id, job_id=job_id)

        if not job:
            print("No job found in payload")
            continue

        jobId = job['id']
        jobStatus = job['status']
        jobInstruction = job['instruction']

        print(f">> Processing Job {jobId} | Status: {jobStatus}")

        # ====================================================
        # STATE 1: CREATED -> Transition to PROCESSING
        # ====================================================
        if jobStatus == "CREATED":
            # A. AI Extraction

            target_email = json.parse(jobInstruction)['contact']['email']

            question = generate_question(jobInstruction)

            if not target_email or not question:
                print("AI Extraction failed.")
                continue # Logic to handle failure could go here

            # B. Slack Lookup & Send
            user_id = get_slack_user(target_email)
            if user_id:
                try:
                    slack_res = slack_client.send_message(
                        channel=user_id,
                        text=f"🤖 *Action Required:*\n{question}\n_(Reply here)_"
                    )
                    
                    # C. WRITE SEPARATION
                    
                    # 1. Update Status in Jobs Table
                    job_handler.mark_in_progress(session_id=session_id, job_id=jobId)

                    # 2. Create Entry in Conversations Table
                    # This keeps the Jobs table clean of Slack IDs and timestamps
                    conversations_table.put_item(Item={
                        'jobId': jobId,
                        'target_user_id': user_id,
                        'slack_channel': slack_res['channel'],
                        'slack_ts': slack_res['ts'],
                        'extracted_email': target_email,
                        'extracted_question': question,
                        'user_response': None # Empty for now
                    })

                    print(f"Job {jobId} initialized. Conversation stored.")

                except Exception as e:
                    print(f"Slack Error: {e}")
            else:
                print(f"User {target_email} not found.")

        # ====================================================
        # STATE 2: PROCESSING -> Transition to FINISHED
        # ====================================================
        elif jobStatus == "PROCESSING":
            # A. Fetch Technical Details from 'JobConversations'
            # We need the timestamp and channel to poll.
            conv_response = conversations_table.get_item(Key={'jobId': jobId})
            
            if 'Item' not in conv_response:
                print(f"Error: Job is PROCESSING but no conversation record found.")
                continue

            conv_item = conv_response['Item']
            
            # B. Check for Reply
            reply_text = check_for_reply(
                conv_item['slack_channel'], 
                conv_item['slack_ts'], 
                conv_item['target_user_id']
            )

            if reply_text:
                # C. RESPONSE FOUND
                
                # 1. Update Jobs Table (Business Logic)
                job_handler.mark_completed(session_id=session_id, job_id=jobId, result=reply_text)

                # 2. Update Conversations Table (Data Logic)
                conversations_table.update_item(
                    Key={'jobId': jobId},
                    UpdateExpression="SET user_response = :r",
                    ExpressionAttributeValues={':r': reply_text}
                )

                print(f"✅ Job {jobId} Finished. Response saved.")
            
            else:
                # D. No response yet -> Loop
                print(f"Waiting for reply on Job {jobId}...")

        # ====================================================
        # STATE 3: FINISHED
        # ====================================================
        elif jobStatus == "FINISHED":
            print("Job is already finished.")

    return {"statusCode": 200}
