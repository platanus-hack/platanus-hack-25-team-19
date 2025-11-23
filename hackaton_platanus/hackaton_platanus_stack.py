from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_sqs as sqs,
    aws_dynamodb as dynamodb,
    aws_lambda_event_sources as lambda_event_sources,
    CfnOutput,
    RemovalPolicy,
)
from constructs import Construct
import os


class HackatonPlatanusStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lambda_code_path = os.path.join(
            os.path.dirname(__file__), "..", "lambda"
        )

        # Create DynamoDB table for jobs
        jobs_table = dynamodb.Table(
            self, "JobsTable",
            table_name="jobs",
            partition_key=dynamodb.Attribute(
                name="session_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True
        )

        # Create DynamoDB table for conversations
        conversations_table = dynamodb.Table(
            self, "ConversationsTable",
            table_name="conversations",
            partition_key=dynamodb.Attribute(
                name="jobId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True
        )

        slack_conversations_table = dynamodb.Table(
            self, "SlackConversationsTable",
            table_name="slack_conversations",
            partition_key=dynamodb.Attribute(
                name="slack_channel",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="target_user_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True
        )

        # Create SQS Queues
        problem_queue = sqs.Queue(
            self, "ProblemQueue",
            queue_name="problem",
            visibility_timeout=Duration.seconds(1000),  # 16+ minutes
            retention_period=Duration.days(14)
        )

        slack_queue = sqs.Queue(
            self, "SlackQueue",
            queue_name="slack",
            visibility_timeout=Duration.seconds(1000),  # 16+ minutes
            retention_period=Duration.days(14)
        )

        market_research_queue = sqs.Queue(
            self, "MarketResearchQueue",
            queue_name="market_research",
            visibility_timeout=Duration.seconds(1000),  # 16+ minutes
            retention_period=Duration.days(14)
        )

        external_research_queue = sqs.Queue(
            self, "ExternalResearchQueue",
            queue_name="external_research",
            visibility_timeout=Duration.seconds(1000),  # 16+ minutes
            retention_period=Duration.days(14)
        )

        problem_lambda = _lambda.Function(
            self, "ProblemFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="problem.handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(800),
            memory_size=256,
            description="Problem Lambda that queues problem job requests",
            function_name="problem",
            environment={
                "PROBLEM_QUEUE_URL": problem_queue.queue_url
            }
        )

        slack_webhook_lambda = _lambda.Function(
            self, "SlackWebhookFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="slack_webhook.handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(800),
            memory_size=256,
            description="Problem Lambda that queues problem job requests",
            function_name="slack_webhook",
            environment={
                "JOBS_TABLE_NAME": jobs_table.table_name,
                "CONVERSATIONS_TABLE_NAME": slack_conversations_table.table_name,
            }
        )

        summarize_lambda = _lambda.Function(
            self, "SummarizeFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="summarize.handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(300),
            memory_size=256,
            description="Summarize Lambda that summarizes job results",
            function_name="summarize",
            environment={
                "ANTHROPIC_API_KEY": os.environ['ANTHROPIC_API_KEY'],
                "JOBS_TABLE_NAME": jobs_table.table_name
            }
        )

        # Define the Orchestrator Lambda function
        orchestrator_lambda = _lambda.Function(
            self, "OrchestratorFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="orchestrator.handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(800),
            memory_size=256,
            description="Orchestrator Lambda that processes job requests",
            function_name="orchestrator",
            environment={
                "JOBS_TABLE_NAME": jobs_table.table_name,
                "SLACK_QUEUE_URL": slack_queue.queue_url,
                "MARKET_RESEARCH_QUEUE_URL": market_research_queue.queue_url,
                "EXTERNAL_RESEARCH_QUEUE_URL": (
                    external_research_queue.queue_url
                ),
                "ANTHROPIC_API_KEY": os.environ['ANTHROPIC_API_KEY']
            }
        )

        # Grant permissions to orchestrator
        problem_queue.grant_send_messages(problem_lambda)
        jobs_table.grant_read_write_data(summarize_lambda)
        jobs_table.grant_write_data(orchestrator_lambda)
        jobs_table.grant_read_write_data(slack_webhook_lambda)
        slack_conversations_table.grant_read_write_data(slack_webhook_lambda)
        slack_queue.grant_send_messages(orchestrator_lambda)
        market_research_queue.grant_send_messages(orchestrator_lambda)
        external_research_queue.grant_send_messages(orchestrator_lambda)

        # Create worker Lambda functions
        slack_worker = _lambda.Function(
            self, "SlackWorker",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="slack_worker.lambda_handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(900),  # 15 minutes
            memory_size=1024,  # 1GB
            description="Processes Slack jobs",
            function_name="slack_worker",
            environment={
                "JOBS_TABLE_NAME": jobs_table.table_name,
                "CONVERSATIONS_TABLE_NAME": slack_conversations_table.table_name,
                "SLACK_QUEUE_URL": slack_queue.queue_url,
                # These should be set via environment variables or AWS Secrets Manager
                "SLACK_BOT_TOKEN": os.environ["SLACK_BOT_TOKEN"],
                "ANTHROPIC_API_KEY": os.environ['ANTHROPIC_API_KEY_2']
            }
        )

        market_research_worker = _lambda.Function(
            self, "MarketResearchWorker",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="market_research_worker.handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(900),  # 15 minutes
            memory_size=1024,  # 1GB
            description="Orchestrates market research agents",
            function_name="market_research_worker",
            environment={
                "JOBS_TABLE_NAME": jobs_table.table_name,
                "ANTHROPIC_API_KEY": os.environ['ANTHROPIC_API_KEY'],
                "ANTHROPIC_API_KEY_2": os.environ['ANTHROPIC_API_KEY_2'],
            }
        )

        external_research_worker = _lambda.Function(
            self, "ExternalResearchWorker",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="external_research_worker.handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(900),  # 15 minutes
            memory_size=1024,  # 1GB
            description="Processes external research jobs",
            function_name="external_research_worker",
            environment={
                "JOBS_TABLE_NAME": jobs_table.table_name,
                "ANTHROPIC_API_KEY": os.environ['ANTHROPIC_API_KEY']
            }
        )

        # Grant DynamoDB permissions to workers
        jobs_table.grant_read_write_data(slack_worker)
        jobs_table.grant_read_write_data(market_research_worker)
        jobs_table.grant_read_write_data(external_research_worker)

        # Grant conversations table permissions to slack worker
        slack_conversations_table.grant_read_write_data(slack_worker)

        # Grant SQS permissions to slack worker for requeuing
        slack_queue.grant_send_messages(slack_worker)

        # Connect queues to worker lambdas
        slack_worker.add_event_source(
            lambda_event_sources.SqsEventSource(
                slack_queue,
                batch_size=1
            )
        )

        orchestrator_lambda.add_event_source(
            lambda_event_sources.SqsEventSource(
                problem_queue,
                batch_size=1
            )
        )

        market_research_worker.add_event_source(
            lambda_event_sources.SqsEventSource(
                market_research_queue,
                batch_size=1
            )
        )

        external_research_worker.add_event_source(
            lambda_event_sources.SqsEventSource(
                external_research_queue,
                batch_size=1
            )
        )

        # Create DynamoDB table for chat sessions
        chat_sessions_table = dynamodb.Table(
            self, "ChatSessionsTable",
            table_name="chat_sessions",
            partition_key=dynamodb.Attribute(
                name="session_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True
        )

        # Create Chat Lambda function
        chat_lambda = _lambda.Function(
            self, "ChatFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="chat.handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(30),
            memory_size=512,
            description="Chat conversation manager Lambda",
            function_name="chat",
            environment={
                "CHAT_SESSIONS_TABLE_NAME": chat_sessions_table.table_name,
                "ANTHROPIC_API_KEY": os.environ['ANTHROPIC_API_KEY']
            }
        )

        # Grant DynamoDB permissions to chat lambda
        chat_sessions_table.grant_read_write_data(chat_lambda)

        # Create Get Jobs Lambda function
        get_jobs_lambda = _lambda.Function(
            self, "GetJobsFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="get_jobs.handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(30),
            memory_size=256,
            description="Get jobs for a session Lambda",
            function_name="get_jobs",
            environment={
                "JOBS_TABLE_NAME": jobs_table.table_name,
                "SLACK_QUEUE_URL": slack_queue.queue_url,
                "MARKET_RESEARCH_QUEUE_URL": market_research_queue.queue_url,
                "EXTERNAL_RESEARCH_QUEUE_URL": (
                    external_research_queue.queue_url
                ),
            }
        )

        # Grant DynamoDB read permissions to get_jobs lambda
        jobs_table.grant_read_data(get_jobs_lambda)
        slack_queue.grant_send_messages(get_jobs_lambda)
        market_research_queue.grant_send_messages(get_jobs_lambda)
        external_research_queue.grant_send_messages(get_jobs_lambda)

        # Create API Gateway REST API
        api = apigateway.RestApi(
            self, "JobsApi",
            rest_api_name="Jobs Service",
            description="API Gateway for job orchestration",
            deploy_options=apigateway.StageOptions(
                stage_name="prod",
                throttling_rate_limit=100,
                throttling_burst_limit=200
            )
        )

        # Create /jobs resource
        jobs_resource = api.root.add_resource("jobs")

        # Add Lambda integration to API Gateway
        problem_integration = apigateway.LambdaIntegration(
            problem_lambda,
            proxy=True
        )

        # Add Lambda integration for get jobs
        get_jobs_integration = apigateway.LambdaIntegration(
            get_jobs_lambda,
            proxy=True
        )

        # Add POST method to /slack-webhook endpoint
        slack_webhook_resource = api.root.add_resource("slack-webhook")
        slack_webhook_integration = apigateway.LambdaIntegration(
            slack_webhook_lambda,
            proxy=True
        )

        # Add POST method to /slack-webhook endpoint
        slack_webhook_resource.add_method("POST", slack_webhook_integration)

        # Add CORS support for /slack-webhook
        slack_webhook_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_methods=["POST", "OPTIONS"],
            allow_headers=["Content-Type", "Authorization"]
        )

        # Add POST method to /jobs endpoint
        jobs_resource.add_method("POST", problem_integration)

        # Add GET method to /jobs endpoint
        jobs_resource.add_method("GET", get_jobs_integration)

        # Add CORS support for /jobs
        jobs_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_methods=["POST", "OPTIONS"],
            allow_headers=["Content-Type", "Authorization"]
        )

        # Create /chat resource
        chat_resource = api.root.add_resource("chat")

        # Add Lambda integration for chat
        chat_integration = apigateway.LambdaIntegration(
            chat_lambda,
            proxy=True
        )

        # Add POST method to /chat endpoint
        chat_resource.add_method("POST", chat_integration)

        # Add CORS support for /chat
        chat_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_methods=["POST", "OPTIONS"],
            allow_headers=["Content-Type", "Authorization"]
        )

        # Add POST method to /summarize endpoint
        summarize_integration = apigateway.LambdaIntegration(
            summarize_lambda,
            proxy=True
        )
        summarize_resource = api.root.add_resource("summarize")
        summarize_resource.add_method("POST", summarize_integration)

        # Add CORS support for /summarize
        summarize_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_methods=["POST", "OPTIONS"],
            allow_headers=["Content-Type", "Authorization"]
        )

        # Output the API endpoint URL
        CfnOutput(
            self, "ApiEndpoint",
            value=api.url,
            description="API Gateway endpoint URL",
            export_name="JobsApiUrl"
        )

        # Output the /jobs endpoint URL
        CfnOutput(
            self, "JobsEndpoint",
            value=f"{api.url}jobs",
            description="Jobs endpoint URL",
            export_name="JobsEndpointUrl"
        )

        # Output the /chat endpoint URL
        CfnOutput(
            self, "ChatEndpoint",
            value=f"{api.url}chat",
            description="Chat endpoint URL",
            export_name="ChatEndpointUrl"
        )

        # Output the Lambda function names
        CfnOutput(
            self, "OrchestratorFunctionName",
            value=orchestrator_lambda.function_name,
            description="Orchestrator Lambda function name",
            export_name="OrchestratorLambdaName"
        )

        # Output queue URLs
        CfnOutput(
            self, "SlackQueueUrl",
            value=slack_queue.queue_url,
            description="Slack queue URL"
        )

        CfnOutput(
            self, "MarketResearchQueueUrl",
            value=market_research_queue.queue_url,
            description="Market research queue URL"
        )

        CfnOutput(
            self, "ExternalResearchQueueUrl",
            value=external_research_queue.queue_url,
            description="External research queue URL"
        )

        # Output DynamoDB table names
        CfnOutput(
            self, "JobsTableName",
            value=jobs_table.table_name,
            description="Jobs DynamoDB table name"
        )

        CfnOutput(
            self, "ChatSessionsTableName",
            value=chat_sessions_table.table_name,
            description="Chat sessions DynamoDB table name"
        )

        # Output Chat Lambda function name
        CfnOutput(
            self, "ChatFunctionName",
            value=chat_lambda.function_name,
            description="Chat Lambda function name"
        )

        CfnOutput(
            self, "ConversationsTableName",
            value=conversations_table.table_name,
            description="Conversations DynamoDB table name"
        )
