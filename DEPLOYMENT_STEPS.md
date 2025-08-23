# Complete Deployment Steps

## Phase 1: Dependencies Installation ✅
```bash
python -m pip install boto3 fastapi uvicorn pandas numpy anthropic alpha-vantage openpyxl reportlab python-pptx python-docx
```

## Phase 2: AWS Setup ✅
### CloudShell Commands Executed:
```bash
# Check AWS account
aws sts get-caller-identity

# Create IAM role
aws iam create-role --role-name FinancialAIAgentRole --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "lambda.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
}'

# Attach policies
aws iam attach-role-policy --role-name FinancialAIAgentRole --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
aws iam attach-role-policy --role-name FinancialAIAgentRole --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

## Phase 3: Bedrock Model Access ✅
- Requested Claude 3 Haiku and Claude 3.5 Sonnet access
- Status: Access granted for both models
- Models tested successfully with financial queries

## Phase 4: Lambda Deployment ✅
```bash
# Create Lambda function
cat > lambda_function.py << 'EOF'
import json
import boto3

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        message = body.get('message', 'Hello')
        
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 1000,
                'messages': [{'role': 'user', 'content': f'As a financial AI assistant: {message}'}]
            })
        )
        
        result = json.loads(response['body'].read())
        ai_response = result['content'][0]['text']
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'response': ai_response})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }
EOF

# Deploy Lambda
zip lambda-deployment.zip lambda_function.py
aws lambda create-function --function-name FinancialAIAgent --runtime python3.9 --role arn:aws:iam::931024183968:role/FinancialAIAgentRole --handler lambda_function.lambda_handler --zip-file fileb://lambda-deployment.zip --region us-east-1 --timeout 30
```

## Phase 5: API Gateway Setup ✅
```bash
# Create API Gateway
aws apigateway create-rest-api --name FinancialAIAPI --region us-east-1

# Setup variables
API_ID="51jzujkz8h"
ROOT_ID="c0mdrrp39c"

# Create /chat resource
RESOURCE_ID=$(aws apigateway create-resource --rest-api-id $API_ID --parent-id $ROOT_ID --path-part chat --query 'id' --output text)

# Create POST method
aws apigateway put-method --rest-api-id $API_ID --resource-id $RESOURCE_ID --http-method POST --authorization-type NONE

# Connect to Lambda
aws apigateway put-integration --rest-api-id $API_ID --resource-id $RESOURCE_ID --http-method POST --type AWS_PROXY --integration-http-method POST --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:931024183968:function:FinancialAIAgent/invocations

# Deploy API
aws apigateway create-deployment --rest-api-id $API_ID --stage-name prod

# Add Lambda permission
aws lambda add-permission --function-name FinancialAIAgent --statement-id api-gateway-invoke --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:us-east-1:931024183968:51jzujkz8h/*/*"
```

## Phase 6: CORS Configuration ✅
```bash
# Add OPTIONS method
aws apigateway put-method --rest-api-id $API_ID --resource-id $RESOURCE_ID --http-method OPTIONS --authorization-type NONE

# Add CORS integration
aws apigateway put-integration --rest-api-id $API_ID --resource-id $RESOURCE_ID --http-method OPTIONS --type MOCK --request-templates '{"application/json":"{\"statusCode\":200}"}'

# Add CORS response
aws apigateway put-method-response --rest-api-id $API_ID --resource-id $RESOURCE_ID --http-method OPTIONS --status-code 200 --response-parameters method.response.header.Access-Control-Allow-Headers=false,method.response.header.Access-Control-Allow-Methods=false,method.response.header.Access-Control-Allow-Origin=false

# Configure CORS headers
aws apigateway put-integration-response --rest-api-id $API_ID --resource-id $RESOURCE_ID --http-method OPTIONS --status-code 200 --response-parameters '{"method.response.header.Access-Control-Allow-Headers":"'\''Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'\''","method.response.header.Access-Control-Allow-Methods":"'\''GET,POST,OPTIONS'\''","method.response.header.Access-Control-Allow-Origin":"'\''*'\''"}' --response-templates '{"application/json":""}'

# Final deployment
aws apigateway create-deployment --rest-api-id $API_ID --stage-name prod
```

## Phase 7: Frontend Updates ✅
- Created welcome.html landing page
- Updated index.html with live API integration
- Configured fetch calls to real endpoint
- Tested live Claude responses

## Final Status ✅
- **Live Demo:** https://mohamedfteha.github.io/financial-ai-agent
- **API Endpoint:** https://51jzujkz8h.execute-api.us-east-1.amazonaws.com/prod/chat
- **Repository:** https://github.com/mohamedfteha/financial-ai-agent
- **Status:** Fully functional with real AI responses