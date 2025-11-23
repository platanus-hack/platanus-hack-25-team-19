from dataclasses import dataclass
import boto3
import uuid

dynamodb = boto3.resource('dynamodb')

@dataclass
class ConversationModel:
    slack_channel: str  # PK
    target_user_id: str  # SK
    session_id: str
    job_id: str
    slack_ts: str
    extracted_email: str
    extracted_question: str
    user_response: str | None = None
    id: str = ''

class ConversationHandler:
    def __init__(self, conversations_table_name: str):
        self.conversations_table = dynamodb.Table(conversations_table_name)

    def create(self, conversation: ConversationModel) -> None:
        conversation.id = str(uuid.uuid4())

        self.conversations_table.put_item(Item=conversation.__dict__)

    def find_one(self, slack_channel: str, target_user_id: str) -> ConversationModel | None:
        response = self.conversations_table.get_item(Key={'slack_channel': slack_channel, 'target_user_id': target_user_id})
        item = response.get('Item')

        if item:
            return ConversationModel(**item)
        return None