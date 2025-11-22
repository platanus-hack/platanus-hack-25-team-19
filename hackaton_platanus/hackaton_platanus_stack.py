import os

from aws_cdk import CfnOutput, Duration, RemovalPolicy, Stack
from aws_cdk import aws_apigateway as apigateway
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_lambda_event_sources as lambda_event_sources
from aws_cdk import aws_sqs as sqs
from constructs import Construct


class HackatonPlatanusStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lambda_code_path = os.path.join(os.path.dirname(__file__), "..", "lambda")

        # Create DynamoDB table for jobs
        jobs_table = dynamodb.Table(
            self,
            "JobsTable",
            table_name="jobs",
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True,
        )

        # Create SQS Queues (increased visibility timeout for 15min Lambda execution)
        slack_queue = sqs.Queue(
            self,
            "SlackQueue",
            queue_name="slack",
            visibility_timeout=Duration.seconds(1000),  # 16+ minutes
            retention_period=Duration.days(14),
        )

        market_research_queue = sqs.Queue(
            self,
            "MarketResearchQueue",
            queue_name="market_research",
            visibility_timeout=Duration.seconds(1000),  # 16+ minutes
            retention_period=Duration.days(14),
        )

        external_research_queue = sqs.Queue(
            self,
            "ExternalResearchQueue",
            queue_name="external_research",
            visibility_timeout=Duration.seconds(1000),  # 16+ minutes
            retention_period=Duration.days(14),
        )

        # Define the Orchestrator Lambda function
        orchestrator_lambda = _lambda.Function(
            self,
            "OrchestratorFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="orchestrator.handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(30),
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
                "ANTHROPIC_API_KEY": "Llenar con la key"  # Replace with actual key or use Secrets Manager
            }
        )

        # Grant permissions to orchestrator
        jobs_table.grant_write_data(orchestrator_lambda)
        slack_queue.grant_send_messages(orchestrator_lambda)
        market_research_queue.grant_send_messages(orchestrator_lambda)
        external_research_queue.grant_send_messages(orchestrator_lambda)

        # Create Lambda layer for dependencies
        dependencies_layer = _lambda.LayerVersion(
            self,
            "DependenciesLayer",
            code=_lambda.Code.from_asset("lambda/layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
            description="Anthropic SDK and other dependencies",
        )

        # Create 5 agent Lambda functions for market research orchestration
        obstacles_agent = _lambda.Function(
            self,
            "ObstaclesAgent",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="obstacles_agent.handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(900),  # 15 minutes
            memory_size=1024,  # 1GB
            description="Analyzes obstacles and challenges",
            function_name="obstacles_agent",
            layers=[dependencies_layer],
            environment={
                "JOBS_TABLE_NAME": jobs_table.table_name,
                "ANTHROPIC_API_KEY": "PLACEHOLDER_ANTHROPIC_API_KEY",
            },
        )

        solutions_agent = _lambda.Function(
            self,
            "SolutionsAgent",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="solutions_agent.handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(900),
            memory_size=1024,
            description="Researches existing solutions",
            function_name="solutions_agent",
            layers=[dependencies_layer],
            environment={
                "JOBS_TABLE_NAME": jobs_table.table_name,
                "ANTHROPIC_API_KEY": "PLACEHOLDER_ANTHROPIC_API_KEY",
            },
        )

        legal_agent = _lambda.Function(
            self,
            "LegalAgent",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="legal_agent.handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(900),
            memory_size=1024,
            description="Analyzes legal and regulatory requirements",
            function_name="legal_agent",
            layers=[dependencies_layer],
            environment={
                "JOBS_TABLE_NAME": jobs_table.table_name,
                "ANTHROPIC_API_KEY": "PLACEHOLDER_ANTHROPIC_API_KEY",
            },
        )

        competitor_agent = _lambda.Function(
            self,
            "CompetitorAgent",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="competitor_agent.handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(900),
            memory_size=1024,
            description="Analyzes competitors and market structure",
            function_name="competitor_agent",
            layers=[dependencies_layer],
            environment={
                "JOBS_TABLE_NAME": jobs_table.table_name,
                "ANTHROPIC_API_KEY": "PLACEHOLDER_ANTHROPIC_API_KEY",
            },
        )

        market_agent = _lambda.Function(
            self,
            "MarketAgent",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="market_agent.handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(900),
            memory_size=1024,
            description="Analyzes market size and trends",
            function_name="market_agent",
            layers=[dependencies_layer],
            environment={
                "JOBS_TABLE_NAME": jobs_table.table_name,
                "ANTHROPIC_API_KEY": "PLACEHOLDER_ANTHROPIC_API_KEY",
            },
        )

        # Grant DynamoDB permissions to agent lambdas
        jobs_table.grant_read_write_data(obstacles_agent)
        jobs_table.grant_read_write_data(solutions_agent)
        jobs_table.grant_read_write_data(legal_agent)
        jobs_table.grant_read_write_data(competitor_agent)
        jobs_table.grant_read_write_data(market_agent)

        # Create worker Lambda functions
        slack_worker = _lambda.Function(
            self,
            "SlackWorker",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="slack_worker.handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(900),  # 15 minutes
            memory_size=1024,  # 1GB
            description="Processes Slack jobs",
            function_name="slack_worker",
            environment={"JOBS_TABLE_NAME": jobs_table.table_name},
        )

        market_research_worker = _lambda.Function(
            self,
            "MarketResearchWorker",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="market_research_worker.handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(900),  # 15 minutes
            memory_size=1024,  # 1GB
            description="Orchestrates market research agents",
            function_name="market_research_worker",
            layers=[dependencies_layer],
            environment={
                "JOBS_TABLE_NAME": jobs_table.table_name,
                "ANTHROPIC_API_KEY": "PLACEHOLDER_ANTHROPIC_API_KEY",
                "OBSTACLES_AGENT_NAME": obstacles_agent.function_name,
                "SOLUTIONS_AGENT_NAME": solutions_agent.function_name,
                "LEGAL_AGENT_NAME": legal_agent.function_name,
                "COMPETITOR_AGENT_NAME": competitor_agent.function_name,
                "MARKET_AGENT_NAME": market_agent.function_name,
            },
        )

        external_research_worker = _lambda.Function(
            self,
            "ExternalResearchWorker",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="external_research_worker.handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(900),  # 15 minutes
            memory_size=1024,  # 1GB
            description="Processes external research jobs",
            function_name="external_research_worker",
            environment={"JOBS_TABLE_NAME": jobs_table.table_name},
        )

        # Grant DynamoDB permissions to workers
        jobs_table.grant_read_write_data(slack_worker)
        jobs_table.grant_read_write_data(market_research_worker)
        jobs_table.grant_read_write_data(external_research_worker)

        # Grant market_research_worker permission to invoke agent lambdas
        obstacles_agent.grant_invoke(market_research_worker)
        solutions_agent.grant_invoke(market_research_worker)
        legal_agent.grant_invoke(market_research_worker)
        competitor_agent.grant_invoke(market_research_worker)
        market_agent.grant_invoke(market_research_worker)

        # Connect queues to worker lambdas
        slack_worker.add_event_source(
            lambda_event_sources.SqsEventSource(slack_queue, batch_size=1)
        )

        market_research_worker.add_event_source(
            lambda_event_sources.SqsEventSource(market_research_queue, batch_size=1)
        )

        external_research_worker.add_event_source(
            lambda_event_sources.SqsEventSource(external_research_queue, batch_size=1)
        )

        # Create DynamoDB table for chat sessions
        chat_sessions_table = dynamodb.Table(
            self,
            "ChatSessionsTable",
            table_name="chat_sessions",
            partition_key=dynamodb.Attribute(name="session_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True,
        )

        # Create Chat Lambda function
        chat_lambda = _lambda.Function(
            self,
            "ChatFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="chat.handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(30),
            memory_size=512,
            description="Chat conversation manager Lambda",
            function_name="chat",
            environment={"CHAT_SESSIONS_TABLE_NAME": chat_sessions_table.table_name},
        )

        # Grant DynamoDB permissions to chat lambda
        chat_sessions_table.grant_read_write_data(chat_lambda)

        # Create API Gateway REST API
        api = apigateway.RestApi(
            self,
            "JobsApi",
            rest_api_name="Jobs Service",
            description="API Gateway for job orchestration",
            deploy_options=apigateway.StageOptions(
                stage_name="prod", throttling_rate_limit=100, throttling_burst_limit=200
            ),
        )

        # Create /jobs resource
        jobs_resource = api.root.add_resource("jobs")

        # Add Lambda integration to API Gateway
        orchestrator_integration = apigateway.LambdaIntegration(orchestrator_lambda, proxy=True)

        # Add POST method to /jobs endpoint
        jobs_resource.add_method("POST", orchestrator_integration)

        # Add CORS support for /jobs
        jobs_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_methods=["POST", "OPTIONS"],
            allow_headers=["Content-Type", "Authorization"],
        )

        # Create /chat resource
        chat_resource = api.root.add_resource("chat")

        # Add Lambda integration for chat
        chat_integration = apigateway.LambdaIntegration(chat_lambda, proxy=True)

        # Add POST method to /chat endpoint
        chat_resource.add_method("POST", chat_integration)

        # Add CORS support for /chat
        chat_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_methods=["POST", "OPTIONS"],
            allow_headers=["Content-Type", "Authorization"],
        )

        # Output the API endpoint URL
        CfnOutput(
            self,
            "ApiEndpoint",
            value=api.url,
            description="API Gateway endpoint URL",
            export_name="JobsApiUrl",
        )

        # Output the /jobs endpoint URL
        CfnOutput(
            self,
            "JobsEndpoint",
            value=f"{api.url}jobs",
            description="Jobs endpoint URL",
            export_name="JobsEndpointUrl",
        )

        # Output the /chat endpoint URL
        CfnOutput(
            self,
            "ChatEndpoint",
            value=f"{api.url}chat",
            description="Chat endpoint URL",
            export_name="ChatEndpointUrl",
        )

        # Output the Lambda function names
        CfnOutput(
            self,
            "OrchestratorFunctionName",
            value=orchestrator_lambda.function_name,
            description="Orchestrator Lambda function name",
            export_name="OrchestratorLambdaName",
        )

        # Output queue URLs
        CfnOutput(self, "SlackQueueUrl", value=slack_queue.queue_url, description="Slack queue URL")

        CfnOutput(
            self,
            "MarketResearchQueueUrl",
            value=market_research_queue.queue_url,
            description="Market research queue URL",
        )

        CfnOutput(
            self,
            "ExternalResearchQueueUrl",
            value=external_research_queue.queue_url,
            description="External research queue URL",
        )

        # Output DynamoDB table names
        CfnOutput(
            self,
            "JobsTableName",
            value=jobs_table.table_name,
            description="Jobs DynamoDB table name",
        )

        CfnOutput(
            self,
            "ChatSessionsTableName",
            value=chat_sessions_table.table_name,
            description="Chat sessions DynamoDB table name",
        )

        # Output Chat Lambda function name
        CfnOutput(
            self,
            "ChatFunctionName",
            value=chat_lambda.function_name,
            description="Chat Lambda function name",
        )
