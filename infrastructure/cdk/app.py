#!/usr/bin/env python3
"""
AWS CDK Infrastructure for Financial AI Agent
"""

import aws_cdk as cdk
from constructs import Construct
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_s3 as s3,
    aws_iam as iam,
    aws_bedrock as bedrock,
    aws_quicksight as quicksight,
    aws_secretsmanager as secretsmanager,
    Duration,
    RemovalPolicy
)

class FinancialAgentStack(Stack):
    """Main stack for Financial AI Agent infrastructure"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 Bucket for data storage
        self.data_bucket = s3.Bucket(
            self, "FinancialDataBucket",
            bucket_name=f"financial-ai-agent-data-{self.account}",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # Secrets Manager for API keys
        self.secrets = secretsmanager.Secret(
            self, "FinancialAgentSecrets",
            description="API keys and secrets for Financial AI Agent",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"alpha_vantage_key": ""}',
                generate_string_key="placeholder",
                exclude_characters=' %+~`#$&*()|[]{}:;<>?!\'/@"\\',
            )
        )

        # IAM Role for Lambda functions
        self.lambda_role = iam.Role(
            self, "FinancialAgentLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess")
            ]
        )

        # Add permissions for S3 and Secrets Manager
        self.data_bucket.grant_read_write(self.lambda_role)
        self.secrets.grant_read(self.lambda_role)

        # Lambda Layer for dependencies
        self.dependencies_layer = _lambda.LayerVersion(
            self, "FinancialAgentDependencies",
            code=_lambda.Code.from_asset("../src"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
            description="Dependencies for Financial AI Agent"
        )

        # Main Lambda function
        self.main_lambda = _lambda.Function(
            self, "FinancialAgentFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="api.main.handler",
            code=_lambda.Code.from_asset("../src"),
            role=self.lambda_role,
            layers=[self.dependencies_layer],
            timeout=Duration.minutes(5),
            memory_size=1024,
            environment={
                "DATA_BUCKET": self.data_bucket.bucket_name,
                "SECRETS_ARN": self.secrets.secret_arn,
                "BEDROCK_REGION": self.region
            }
        )

        # API Gateway
        self.api = apigateway.RestApi(
            self, "FinancialAgentAPI",
            rest_api_name="Financial AI Agent API",
            description="API for Financial AI Agent services",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"]
            )
        )

        # Lambda integration
        lambda_integration = apigateway.LambdaIntegration(
            self.main_lambda,
            request_templates={"application/json": '{"statusCode": "200"}'}
        )

        # API Resources
        # Chat endpoint
        chat_resource = self.api.root.add_resource("chat")
        chat_resource.add_method("POST", lambda_integration)

        # Market data endpoint
        market_resource = self.api.root.add_resource("market-data")
        market_resource.add_method("POST", lambda_integration)

        # Report generation endpoint
        report_resource = self.api.root.add_resource("generate-report")
        report_resource.add_method("POST", lambda_integration)

        # Portfolio analysis endpoint
        portfolio_resource = self.api.root.add_resource("portfolio-analysis")
        portfolio_resource.add_method("POST", lambda_integration)

        # Risk assessment endpoint
        risk_resource = self.api.root.add_resource("risk-assessment")
        risk_resource.add_method("POST", lambda_integration)

        # Health check endpoint
        health_resource = self.api.root.add_resource("health")
        health_resource.add_method("GET", lambda_integration)

        # Bedrock Agent (when available in CDK)
        # Note: Bedrock AgentCore might need custom resources or manual setup
        
        # QuickSight Data Source
        self.quicksight_data_source = quicksight.CfnDataSource(
            self, "FinancialDataSource",
            aws_account_id=self.account,
            data_source_id="financial-ai-agent-datasource",
            name="Financial AI Agent Data Source",
            type="S3",
            data_source_parameters=quicksight.CfnDataSource.DataSourceParametersProperty(
                s3_parameters=quicksight.CfnDataSource.S3ParametersProperty(
                    manifest_file_location=quicksight.CfnDataSource.ManifestFileLocationProperty(
                        bucket=self.data_bucket.bucket_name,
                        key="quicksight/manifest.json"
                    )
                )
            )
        )

        # Output important values
        cdk.CfnOutput(
            self, "APIEndpoint",
            value=self.api.url,
            description="API Gateway endpoint URL"
        )

        cdk.CfnOutput(
            self, "DataBucketName",
            value=self.data_bucket.bucket_name,
            description="S3 bucket for financial data"
        )

        cdk.CfnOutput(
            self, "SecretsArn",
            value=self.secrets.secret_arn,
            description="Secrets Manager ARN for API keys"
        )

class FinancialAgentApp(cdk.App):
    """CDK App for Financial AI Agent"""

    def __init__(self):
        super().__init__()

        # Main stack
        FinancialAgentStack(
            self, "FinancialAgentStack",
            env=cdk.Environment(
                account=self.node.try_get_context("account"),
                region=self.node.try_get_context("region") or "us-east-1"
            )
        )

if __name__ == "__main__":
    app = FinancialAgentApp()
    app.synth()