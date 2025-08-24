# Financial AI Agent Lambda Function - Backend Integration
# Updated: August 24, 2025
# Handler: real_data_lambda.lambda_handler
# Purpose: Connect AI agent to FinvestecLab financial backend

import json
import boto3

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def get_google_data():
    """Retrieve Google financial data from DynamoDB"""
    try:
        table = dynamodb.Table('GoogleFinancialData')
        response = table.scan(Limit=5)
        return response.get('Items', [])
    except Exception as e:
        print(f"Error accessing Google data: {e}")
        return []

def lambda_handler(event, context):
    """Main Lambda handler with backend integration"""
    try:
        body = json.loads(event.get('body', '{}'))
        message = body.get('message', 'Hello')
        
        # Check for Google-related queries and fetch real data
        data_context = ""
        if 'google' in message.lower() or 'googl' in message.lower():
            google_data = get_google_data()
            if google_data:
                data_context = f"\nReal Google Data from FinvestecLab: {json.dumps(google_data, default=str)}"
        
        # Enhanced prompt with real backend data
        prompt = f"""Financial AI Assistant with FinvestecLab Real Data:

Query: {message}
{data_context}

Use the actual data above to provide specific analysis.
"""
        
        # Call Claude 3.5 Sonnet via Bedrock
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 1000,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'response': result['content'][0]['text']})
        }
        
    except Exception as e:
        print(f"Lambda execution error: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }