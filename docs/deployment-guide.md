# Financial AI Agent - Deployment Guide

## Prerequisites

### AWS Account Setup
1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured with credentials
3. **AWS CDK** installed (`npm install -g aws-cdk`)
4. **Python 3.11+** installed
5. **Node.js 18+** for CDK

### API Keys Required
- **Alpha Vantage API Key** (free tier available)
- **Anthropic API Key** (for Claude Sonnet)
- **AWS Bedrock Access** (request access if needed)

## Phase 1: Infrastructure Setup

### Step 1: Clone and Setup Repository

```bash
git clone <repository-url>
cd financial-ai-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure AWS Credentials

```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: us-east-1
# Default output format: json
```

### Step 3: Deploy Infrastructure

```bash
cd infrastructure/cdk

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy the stack
cdk deploy FinancialAgentStack
```

### Step 4: Configure Secrets

```bash
# Update Secrets Manager with your API keys
aws secretsmanager update-secret \
    --secret-id FinancialAgentSecrets \
    --secret-string '{
        "alpha_vantage_key": "YOUR_ALPHA_VANTAGE_KEY",
        "anthropic_key": "YOUR_ANTHROPIC_KEY"
    }'
```

## Phase 2: Bedrock AgentCore Setup

### Step 1: Enable Bedrock Access

1. Go to AWS Bedrock console
2. Request access to Anthropic Claude models
3. Wait for approval (usually 24-48 hours)

### Step 2: Create Bedrock Agent

```bash
# Create agent using AWS CLI
aws bedrock-agent create-agent \
    --agent-name "FinancialAnalysisAgent" \
    --foundation-model "anthropic.claude-3-sonnet-20240229-v1:0" \
    --instruction "You are a sophisticated financial AI agent specializing in financial analysis, investment research, portfolio optimization, and risk management."
```

### Step 3: Configure Agent Knowledge Base

```bash
# Create knowledge base for financial data
aws bedrock-agent create-knowledge-base \
    --name "FinancialKnowledgeBase" \
    --description "Financial markets and investment knowledge base"
```

## Phase 3: Application Deployment

### Step 1: Package Lambda Function

```bash
cd ../../src

# Create deployment package
zip -r ../deployment/financial-agent.zip . -x "*.pyc" "__pycache__/*"
```

### Step 2: Update Lambda Function

```bash
aws lambda update-function-code \
    --function-name FinancialAgentFunction \
    --zip-file fileb://../deployment/financial-agent.zip
```

### Step 3: Test API Endpoints

```bash
# Get API Gateway URL from CDK output
API_URL=$(aws cloudformation describe-stacks \
    --stack-name FinancialAgentStack \
    --query 'Stacks[0].Outputs[?OutputKey==`APIEndpoint`].OutputValue' \
    --output text)

# Test health endpoint
curl $API_URL/health

# Test chat endpoint
curl -X POST $API_URL/chat \
    -H "Content-Type: application/json" \
    -d '{
        "query": "What is the current market sentiment?",
        "agent_type": "general"
    }'
```

## Phase 4: QuickSight Integration

### Step 1: Setup QuickSight

1. Enable QuickSight in your AWS account
2. Create QuickSight user with appropriate permissions
3. Configure S3 access for QuickSight

### Step 2: Create Data Source

```bash
# Upload sample data to S3
aws s3 cp sample-data/market-data.csv s3://financial-ai-agent-data-{ACCOUNT}/quicksight/

# Create QuickSight manifest
cat > quicksight-manifest.json << EOF
{
    "fileLocations": [
        {
            "URIs": [
                "s3://financial-ai-agent-data-{ACCOUNT}/quicksight/market-data.csv"
            ]
        }
    ],
    "globalUploadSettings": {
        "format": "CSV",
        "delimiter": ",",
        "textqualifier": "\"",
        "containsHeader": "true"
    }
}
EOF

aws s3 cp quicksight-manifest.json s3://financial-ai-agent-data-{ACCOUNT}/quicksight/manifest.json
```

## Phase 5: Frontend Integration

### Step 1: Web Application Setup

```bash
# Create React frontend (optional)
npx create-react-app financial-agent-frontend
cd financial-agent-frontend

# Install additional dependencies
npm install axios recharts @mui/material
```

### Step 2: Configure API Integration

```javascript
// src/config/api.js
export const API_BASE_URL = 'YOUR_API_GATEWAY_URL';

export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json'
    }
});
```

## Monitoring and Logging

### CloudWatch Setup

```bash
# Create custom dashboard
aws cloudwatch put-dashboard \
    --dashboard-name "FinancialAgentDashboard" \
    --dashboard-body file://monitoring/dashboard.json
```

### X-Ray Tracing

```bash
# Enable X-Ray tracing for Lambda
aws lambda update-function-configuration \
    --function-name FinancialAgentFunction \
    --tracing-config Mode=Active
```

## Security Configuration

### Step 1: IAM Policies

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeAgent"
            ],
            "Resource": "*"
        }
    ]
}
```

### Step 2: API Gateway Security

```bash
# Create API key
aws apigateway create-api-key \
    --name "FinancialAgentAPIKey" \
    --description "API key for Financial AI Agent"

# Create usage plan
aws apigateway create-usage-plan \
    --name "FinancialAgentUsagePlan" \
    --throttle burstLimit=100,rateLimit=50
```

## Testing and Validation

### Unit Tests

```bash
cd tests
python -m pytest unit/ -v
```

### Integration Tests

```bash
python -m pytest integration/ -v
```

### Load Testing

```bash
# Install artillery for load testing
npm install -g artillery

# Run load tests
artillery run load-tests/api-load-test.yml
```

## Production Checklist

- [ ] All API keys configured in Secrets Manager
- [ ] Bedrock access approved and agent created
- [ ] Lambda function deployed and tested
- [ ] API Gateway endpoints responding
- [ ] QuickSight dashboards created
- [ ] CloudWatch monitoring enabled
- [ ] Security policies applied
- [ ] Load testing completed
- [ ] Documentation updated

## Troubleshooting

### Common Issues

1. **Bedrock Access Denied**
   - Ensure model access is requested and approved
   - Check IAM permissions for Bedrock

2. **Lambda Timeout**
   - Increase timeout in CDK configuration
   - Optimize code for better performance

3. **API Gateway 502 Error**
   - Check Lambda function logs in CloudWatch
   - Verify Lambda function permissions

4. **QuickSight Connection Issues**
   - Verify S3 bucket permissions
   - Check manifest file format

### Logs and Debugging

```bash
# View Lambda logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/FinancialAgent"

# Stream logs in real-time
aws logs tail /aws/lambda/FinancialAgentFunction --follow
```

## Maintenance

### Regular Updates

1. **Weekly**: Update market data and refresh models
2. **Monthly**: Review and optimize Lambda performance
3. **Quarterly**: Update dependencies and security patches

### Backup Strategy

```bash
# Backup configuration
aws s3 sync s3://financial-ai-agent-data-{ACCOUNT} ./backups/$(date +%Y%m%d)
```

## Support and Resources

- **AWS Bedrock Documentation**: https://docs.aws.amazon.com/bedrock/
- **Alpha Vantage API**: https://www.alphavantage.co/documentation/
- **CDK Documentation**: https://docs.aws.amazon.com/cdk/
- **Project Repository**: [GitHub Repository URL]