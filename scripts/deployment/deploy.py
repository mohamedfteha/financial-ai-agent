#!/usr/bin/env python3
"""
Deployment script for Financial AI Agent
Automates the deployment process across different environments
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List
import boto3
from botocore.exceptions import ClientError

class FinancialAgentDeployer:
    """Handles deployment of Financial AI Agent to AWS"""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.project_root = Path(__file__).parent.parent.parent
        self.config = self._load_config()
        
        # AWS clients
        self.session = boto3.Session(
            profile_name=self.config['aws']['profile'],
            region_name=self.config['aws']['region']
        )
        self.lambda_client = self.session.client('lambda')
        self.s3_client = self.session.client('s3')
        self.secrets_client = self.session.client('secretsmanager')
        
    def _load_config(self) -> Dict:
        """Load environment configuration"""
        config_path = self.project_root / "config" / "environments" / f"{self.environment}.json"
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def deploy_infrastructure(self) -> bool:
        """Deploy AWS infrastructure using CDK"""
        
        print(f"🚀 Deploying infrastructure for {self.environment} environment...")
        
        try:
            # Change to CDK directory
            cdk_dir = self.project_root / "infrastructure" / "cdk"
            os.chdir(cdk_dir)
            
            # Install CDK dependencies
            subprocess.run(["npm", "install"], check=True)
            
            # Bootstrap CDK (if needed)
            result = subprocess.run(
                ["cdk", "bootstrap"], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode != 0 and "already bootstrapped" not in result.stderr:
                print(f"❌ CDK bootstrap failed: {result.stderr}")
                return False
            
            # Deploy stack
            deploy_cmd = [
                "cdk", "deploy", "FinancialAgentStack",
                "--require-approval", "never",
                "--context", f"environment={self.environment}"
            ]
            
            result = subprocess.run(deploy_cmd, check=True)
            print("✅ Infrastructure deployed successfully!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Infrastructure deployment failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error during infrastructure deployment: {e}")
            return False
    
    def package_lambda(self) -> str:
        """Package Lambda function code"""
        
        print("📦 Packaging Lambda function...")
        
        try:
            # Create deployment directory
            deployment_dir = self.project_root / "deployment"
            deployment_dir.mkdir(exist_ok=True)
            
            # Package source code
            src_dir = self.project_root / "src"
            package_path = deployment_dir / f"financial-agent-{self.environment}.zip"
            
            # Create zip package
            import zipfile
            
            with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(src_dir):
                    # Skip __pycache__ directories
                    dirs[:] = [d for d in dirs if d != '__pycache__']
                    
                    for file in files:
                        if not file.endswith('.pyc'):
                            file_path = Path(root) / file
                            arcname = file_path.relative_to(src_dir)
                            zipf.write(file_path, arcname)
            
            print(f"✅ Lambda package created: {package_path}")
            return str(package_path)
            
        except Exception as e:
            print(f"❌ Lambda packaging failed: {e}")
            raise
    
    def deploy_lambda(self, package_path: str) -> bool:
        """Deploy Lambda function"""
        
        print("🔄 Deploying Lambda function...")
        
        try:
            function_name = f"FinancialAgentFunction-{self.environment}"
            
            # Read package
            with open(package_path, 'rb') as f:
                zip_content = f.read()
            
            # Update function code
            response = self.lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_content
            )
            
            print(f"✅ Lambda function deployed: {response['FunctionArn']}")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"❌ Lambda function {function_name} not found. Deploy infrastructure first.")
            else:
                print(f"❌ Lambda deployment failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error during Lambda deployment: {e}")
            return False
    
    def configure_secrets(self, api_keys: Dict[str, str]) -> bool:
        """Configure API keys in Secrets Manager"""
        
        print("🔐 Configuring secrets...")
        
        try:
            secret_name = f"FinancialAgentSecrets-{self.environment}"
            
            # Update secret
            self.secrets_client.update_secret(
                SecretId=secret_name,
                SecretString=json.dumps(api_keys)
            )
            
            print("✅ Secrets configured successfully!")
            return True
            
        except ClientError as e:
            print(f"❌ Secrets configuration failed: {e}")
            return False
    
    def setup_bedrock_agent(self) -> bool:
        """Setup Bedrock Agent (manual step guidance)"""
        
        print("🤖 Setting up Bedrock Agent...")
        print("""
        Manual steps required:
        1. Go to AWS Bedrock console
        2. Request access to Anthropic Claude models (if not done)
        3. Create a new agent with the following configuration:
           - Name: FinancialAnalysisAgent-{environment}
           - Foundation Model: anthropic.claude-3-sonnet-20240229-v1:0
           - Instructions: "You are a sophisticated financial AI agent..."
        4. Note the Agent ID and update configuration
        """.format(environment=self.environment))
        
        return True
    
    def validate_deployment(self) -> bool:
        """Validate deployment by testing endpoints"""
        
        print("🧪 Validating deployment...")
        
        try:
            # Get API Gateway URL from CloudFormation
            cf_client = self.session.client('cloudformation')
            
            stack_name = f"FinancialAgentStack-{self.environment}"
            response = cf_client.describe_stacks(StackName=stack_name)
            
            api_url = None
            for output in response['Stacks'][0]['Outputs']:
                if output['OutputKey'] == 'APIEndpoint':
                    api_url = output['OutputValue']
                    break
            
            if not api_url:
                print("❌ Could not find API Gateway URL")
                return False
            
            # Test health endpoint
            import requests
            
            health_response = requests.get(f"{api_url}/health", timeout=30)
            
            if health_response.status_code == 200:
                print("✅ Health check passed!")
                print(f"🌐 API URL: {api_url}")
                return True
            else:
                print(f"❌ Health check failed: {health_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return False
    
    def deploy_all(self, api_keys: Dict[str, str] = None) -> bool:
        """Deploy complete application"""
        
        print(f"🚀 Starting complete deployment for {self.environment} environment...")
        
        steps = [
            ("Infrastructure", self.deploy_infrastructure),
            ("Lambda Package", lambda: self.package_lambda()),
            ("Lambda Deploy", lambda: self.deploy_lambda(self.package_lambda())),
            ("Bedrock Setup", self.setup_bedrock_agent),
            ("Validation", self.validate_deployment)
        ]
        
        if api_keys:
            steps.insert(-1, ("Secrets", lambda: self.configure_secrets(api_keys)))
        
        for step_name, step_func in steps:
            print(f"\n--- {step_name} ---")
            
            if step_name == "Lambda Package":
                package_path = step_func()
                continue
            elif step_name == "Lambda Deploy":
                if not self.deploy_lambda(package_path):
                    return False
                continue
            
            if not step_func():
                print(f"❌ {step_name} failed!")
                return False
        
        print(f"\n🎉 Deployment completed successfully for {self.environment} environment!")
        return True

def main():
    """Main deployment script"""
    
    parser = argparse.ArgumentParser(description="Deploy Financial AI Agent")
    parser.add_argument(
        "--environment", "-e",
        choices=["development", "staging", "production"],
        default="development",
        help="Deployment environment"
    )
    parser.add_argument(
        "--alpha-vantage-key",
        help="Alpha Vantage API key"
    )
    parser.add_argument(
        "--anthropic-key",
        help="Anthropic API key"
    )
    parser.add_argument(
        "--step",
        choices=["infrastructure", "lambda", "secrets", "bedrock", "validate", "all"],
        default="all",
        help="Specific deployment step to run"
    )
    
    args = parser.parse_args()
    
    # Initialize deployer
    deployer = FinancialAgentDeployer(args.environment)
    
    # Prepare API keys
    api_keys = {}
    if args.alpha_vantage_key:
        api_keys["alpha_vantage_key"] = args.alpha_vantage_key
    if args.anthropic_key:
        api_keys["anthropic_key"] = args.anthropic_key
    
    # Run deployment
    try:
        if args.step == "all":
            success = deployer.deploy_all(api_keys if api_keys else None)
        elif args.step == "infrastructure":
            success = deployer.deploy_infrastructure()
        elif args.step == "lambda":
            package_path = deployer.package_lambda()
            success = deployer.deploy_lambda(package_path)
        elif args.step == "secrets":
            if not api_keys:
                print("❌ API keys required for secrets configuration")
                sys.exit(1)
            success = deployer.configure_secrets(api_keys)
        elif args.step == "bedrock":
            success = deployer.setup_bedrock_agent()
        elif args.step == "validate":
            success = deployer.validate_deployment()
        
        if success:
            print(f"\n✅ {args.step.title()} completed successfully!")
            sys.exit(0)
        else:
            print(f"\n❌ {args.step.title()} failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Deployment failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()