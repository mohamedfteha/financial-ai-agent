"""
Financial AI Agent - Core Implementation
Amazon Bedrock AgentCore with Claude Sonnet
"""

import boto3
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio

@dataclass
class AgentConfig:
    """Configuration for the Financial AI Agent"""
    agent_id: str
    model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    region: str = "us-east-1"
    max_tokens: int = 4000
    temperature: float = 0.1

class FinancialAgent:
    """Main Financial AI Agent using Bedrock AgentCore"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.bedrock_agent = boto3.client(
            'bedrock-agent-runtime',
            region_name=config.region
        )
        self.bedrock = boto3.client(
            'bedrock-runtime',
            region_name=config.region
        )
        
    async def invoke_agent(self, 
                          query: str, 
                          session_id: str,
                          context: Optional[Dict] = None) -> Dict[str, Any]:
        """Invoke the financial agent with a query"""
        
        try:
            # Prepare the request
            request_body = {
                "inputText": query,
                "sessionId": session_id,
                "agentId": self.config.agent_id,
                "agentAliasId": "TSTALIASID"
            }
            
            if context:
                request_body["sessionState"] = {
                    "sessionAttributes": context
                }
            
            # Invoke the agent
            response = self.bedrock_agent.invoke_agent(**request_body)
            
            # Process streaming response
            result = await self._process_streaming_response(response)
            
            return {
                "success": True,
                "response": result,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _process_streaming_response(self, response) -> str:
        """Process the streaming response from Bedrock Agent"""
        
        result_text = ""
        
        try:
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        result_text += chunk['bytes'].decode('utf-8')
                        
        except Exception as e:
            raise Exception(f"Error processing streaming response: {str(e)}")
            
        return result_text
    
    def create_financial_prompt(self, 
                               query: str, 
                               data_context: Dict = None) -> str:
        """Create a specialized financial analysis prompt"""
        
        base_prompt = f"""
        You are a sophisticated financial AI agent specializing in:
        - Financial analysis and modeling
        - Investment research and recommendations
        - Portfolio optimization and risk management
        - Market analysis and forecasting
        - Quantitative and fundamental analysis
        
        Current Query: {query}
        
        Please provide a comprehensive analysis with:
        1. Key insights and findings
        2. Data-driven recommendations
        3. Risk assessment
        4. Actionable next steps
        
        Format your response for professional financial reporting.
        """
        
        if data_context:
            base_prompt += f"\n\nAdditional Context:\n{json.dumps(data_context, indent=2)}"
            
        return base_prompt

class AgentOrchestrator:
    """Orchestrates multiple specialized financial agents"""
    
    def __init__(self):
        self.agents = {}
        self.session_manager = SessionManager()
    
    def register_agent(self, name: str, agent: FinancialAgent):
        """Register a specialized agent"""
        self.agents[name] = agent
    
    async def route_query(self, 
                         query: str, 
                         session_id: str,
                         agent_type: str = "general") -> Dict[str, Any]:
        """Route query to appropriate specialized agent"""
        
        if agent_type not in self.agents:
            agent_type = "general"
            
        agent = self.agents[agent_type]
        return await agent.invoke_agent(query, session_id)

class SessionManager:
    """Manages user sessions and context"""
    
    def __init__(self):
        self.sessions = {}
    
    def create_session(self, user_id: str) -> str:
        """Create a new session"""
        session_id = f"{user_id}_{datetime.utcnow().timestamp()}"
        self.sessions[session_id] = {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "context": {},
            "history": []
        }
        return session_id
    
    def update_context(self, session_id: str, context: Dict):
        """Update session context"""
        if session_id in self.sessions:
            self.sessions[session_id]["context"].update(context)
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        return self.sessions.get(session_id)