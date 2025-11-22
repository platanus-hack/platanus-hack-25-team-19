import json
import logging
import os
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
slack_client = SlackHelper(token=os.environ.get('SLACK_BOT_TOKEN'))

# Get environment variables
JOBS_TABLE_NAME = os.environ["JOBS_TABLE_NAME"]

# Get table reference
jobs_table = dynamodb.Table(JOBS_TABLE_NAME)
conversations_table = dynamodb.Table(os.environ['CONVERSATIONS_TABLE_NAME'])

def extract_email_and_question_claude(text):
    """Extracts email and question using Claude via the anthropic helper."""
    prompt = f"""
    Instruction: "{text}"
    Task: Extract target email and question.
    Output JSON only: keys "email", "question".
    """
    try:
        # Create a message using the anthropic helper
        messages = [ConversationMessage(role="user", content=prompt, timestamp="")]
        response = anthropic_client.send_message(messages)
        data = json.loads(response)
        return data.get("email"), data.get("question")
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
                    slack_res = slack_client.send_message(
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

        # ====================================================
        # STATE 3: FINISHED
        # ====================================================
        elif jobStatus == "FINISHED":
            print("Job is already finished.")

    return {"statusCode": 200}
