from dataclasses import dataclass
from typing import Literal
import boto3
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')

@dataclass
class JobModel:
    session_id: str
    status: Literal['CREATED', 'IN_PROGRESS', 'COMPLETED', 'FAILED']
    job_type: Literal['slack', 'research', 'external_research']
    instructions: str
    context_summary: str
    created_at: str
    updated_at: str

    # Default fields
    id: str = ''
    result: str = ''

class JobHandler:
    def __init__(self, jobs_table_name: str):
        self.jobs_table = dynamodb.Table(jobs_table_name)

    def create(self, job: JobModel) -> None:
        job.id = str(uuid.uuid4())

        self.jobs_table.put_item(Item=job.__dict__)

    def find(self, session_id: str) -> list[JobModel]:
        response = self.jobs_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('session_id').eq(session_id)
        )
        items = response.get('Items', [])
        return [JobModel(**item) for item in items]

    def find_one(self, session_id: str, job_id: str) -> JobModel | None:
        response = self.jobs_table.get_item(Key={'session_id': session_id, 'id': job_id})
        item = response.get('Item')
        if item:
            return JobModel(**item)
        return None
        
    def _update(
        self,
        session_id: str,
        job_id: str,
        status: Literal['IN_PROGRESS', 'COMPLETED', 'FAILED'],
        result: str | None = None,
    ) -> None:
        update_expression = 'SET #status = :status, updated_at = :updated_at'
        expression_attribute_values = {
            ':status': status,
            ':updated_at': datetime.utcnow().isoformat(),
        }
        expression_attribute_names = {
            '#status': 'status',
        }

        if result is not None:
            update_expression += ', #result = :result'
            expression_attribute_values[':result'] = result
            expression_attribute_names['#result'] = 'result'


        self.jobs_table.update_item(
            Key={
                'session_id': session_id,
                'id': job_id,
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values
        )
    
    def mark_in_progress(self, session_id: str, job_id: str, result: str | None = None) -> None:
        self._update(session_id, job_id, 'IN_PROGRESS', result)

    def mark_completed(self, session_id: str, job_id: str, result: str) -> None:
        self._update(session_id, job_id, 'COMPLETED', result)

    def mark_failed(self, session_id: str, job_id: str, result: str) -> None:
        self._update(session_id, job_id, 'FAILED', result)
