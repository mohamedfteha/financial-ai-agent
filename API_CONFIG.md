# API Configuration

## AWS Resources Created

### Lambda Function
- **Name:** FinancialAIAgent
- **ARN:** arn:aws:lambda:us-east-1:931024183968:function:FinancialAIAgent
- **Runtime:** python3.9
- **Role:** arn:aws:iam::931024183968:role/FinancialAIAgentRole
- **Handler:** lambda_function.lambda_handler
- **Timeout:** 30 seconds

### API Gateway
- **API ID:** 51jzujkz8h
- **Name:** FinancialAIAPI
- **Endpoint:** https://51jzujkz8h.execute-api.us-east-1.amazonaws.com/prod/chat
- **Stage:** prod
- **Methods:** POST, OPTIONS (CORS enabled)

### IAM Role
- **Role Name:** FinancialAIAgentRole
- **Policies:**
  - AmazonBedrockFullAccess
  - AWSLambdaBasicExecutionRole

### Bedrock Models
- **Claude 3 Haiku:** anthropic.claude-3-haiku-20240307-v1:0
- **Claude 3.5 Sonnet:** anthropic.claude-3-5-sonnet-20240620-v1:0
- **Status:** Access granted

## Environment Variables
- **AWS_REGION:** us-east-1
- **AWS_ACCOUNT_ID:** 931024183968

## CORS Configuration
- **Access-Control-Allow-Origin:** *
- **Access-Control-Allow-Methods:** GET,POST,OPTIONS
- **Access-Control-Allow-Headers:** Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token

## Usage
```javascript
fetch('https://51jzujkz8h.execute-api.us-east-1.amazonaws.com/prod/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({ message: 'Your question here' })
})
```