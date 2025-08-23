#!/bin/bash

# Create Lambda function code
cat > lambda_function.py << 'EOF'
import json
import boto3
from typing import Dict, Any

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
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

# Create deployment package
zip lambda-deployment.zip lambda_function.py

# Deploy Lambda function
aws lambda create-function \
    --function-name FinancialAIAgent \
    --runtime python3.9 \
    --role arn:aws:iam::931024183968:role/FinancialAIAgentRole \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://lambda-deployment.zip \
    --region us-east-1 \
    --timeout 30

# Create API Gateway
aws apigateway create-rest-api --name FinancialAIAPI --region us-east-1

echo "✅ Deployment complete!"