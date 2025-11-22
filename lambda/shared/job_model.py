from dataclasses import dataclass
from typing import Literal
import boto3
import uuid

dynamodb = boto3.resource('dynamodb')

@dataclass
class JobModel:
    status: Literal['CREATED', 'IN_PROGRESS', 'COMPLETED', 'FAILED']
    job_type: Literal['ADI', 'ECG', 'VEE']
    instructions: str
    context_summary: str
    created_at: str
    updated_at: str

    # Default fields
    id: str = uuid.uuid4()
    result: str = ''

class JobHandler:
    def __init__(self, jobs_table_name: str):
        self.jobs_table = dynamodb.Table(jobs_table_name)

    def create(self, job: JobModel) -> None:
        self.jobs_table.put_item(Item=job.__dict__)
