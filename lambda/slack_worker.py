import json
import logging
import os
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from anthropic import Anthropic

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')

# Initialize external service clients
anthropic_client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
slack_client = WebClient(token=os.environ.get('SLACK_BOT_TOKEN'))

# Get environment variables
JOBS_TABLE_NAME = os.environ["JOBS_TABLE_NAME"]

# Get table reference
jobs_table = dynamodb.Table(JOBS_TABLE_NAME)
conversations_table = dynamodb.Table(os.environ['CONVERSATIONS_TABLE_NAME'])

def extract_email_and_question_claude(text):
    """Extracts email and question using Claude 3 Haiku."""
    prompt = f"""
    Instruction: "{text}"
    Task: Extract target email and question.
    Output JSON only: keys "email", "question".
    """
    try:
        message = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        data = json.loads(message.content[0].text)
        return data.get("email"), data.get("question")
    except Exception as e:
        print(f"AI Error: {e}")
        return None, None
    
def get_slack_user(email):
    try:
        r = slack_client.users_lookupByEmail(email=email)
        return r['user']['id']
    except SlackApiError:
        return None

def check_for_reply(channel_id, oldest_ts, user_id):
    try:
        # Buffer to ensure we don't read our own message
        buffer_ts = str(float(oldest_ts) + 0.000001)
        history = slack_client.conversations_history(
            channel=channel_id, 
            oldest=buffer_ts
        )
        for msg in history.get('messages', []):
            if 'bot_id' not in msg and msg.get('user') == user_id:
                return msg['text']
        return None
    except Exception as e:
        print(f"History check failed: {e}")
        return None

def requeue_job(job_id):
    """Requeue a job for later processing"""
    try:
        queue_url = os.environ['SLACK_QUEUE_URL']
        message_body = json.dumps({
            'job': {
                'id': job_id,
                'status': 'PROCESSING',  # Will be fetched from DB in actual processing
                'instruction': ''  # Will be fetched from DB in actual processing
            }
        })
        
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=message_body,
            DelaySeconds=30  # Wait 30 seconds before reprocessing
        )
        print(f"Job {job_id} requeued successfully")
    except Exception as e:
        print(f"Failed to requeue job {job_id}: {e}")



def lambda_handler(event, context):
    for record in event['Records']:
        payload = json.loads(record['body'])
        job = payload.get('job')

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
            target_email, question = extract_email_and_question_claude(jobInstruction)

            if not target_email or not question:
                print("AI Extraction failed.")
                continue # Logic to handle failure could go here

            # B. Slack Lookup & Send
            user_id = get_slack_user(target_email)
            if user_id:
                try:
                    slack_res = slack_client.chat_postMessage(
                        channel=user_id,
                        text=f"🤖 *Action Required:*\n{question}\n_(Reply here)_"
                    )
                    
                    # C. WRITE SEPARATION
                    
                    # 1. Update Status in Jobs Table
                    jobs_table.update_item(
                        Key={'id': jobId},
                        UpdateExpression="SET #st = :s",
                        ExpressionAttributeNames={'#st': 'status'},
                        ExpressionAttributeValues={':s': "PROCESSING"}
                    )

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
                    requeue_job(jobId)

                except SlackApiError as e:
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
                jobs_table.update_item(
                    Key={'id': jobId},
                    UpdateExpression="SET #st = :s",
                    ExpressionAttributeNames={'#st': 'status'},
                    ExpressionAttributeValues={':s': "FINISHED"}
                )

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
                requeue_job(jobId)

        # ====================================================
        # STATE 3: FINISHED
        # ====================================================
        elif jobStatus == "FINISHED":
            print("Job is already finished.")

    return {"statusCode": 200}


        



    result = {
        "message": "Slack job processed successfully",
        "instructions": instructions,
        "action": "Simulated Slack notification sent",
        "channels_notified": ["#general", "#notifications"],
    }

    return json.dumps(result)
