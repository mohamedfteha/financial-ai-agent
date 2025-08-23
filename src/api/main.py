"""
FastAPI Main Application
Financial AI Agent REST API
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio
import json
import io
from datetime import datetime

# Internal imports
from ..agents.financial_agent import FinancialAgent, AgentConfig, AgentOrchestrator
from ..services.data_service import RealTimeDataService
from ..services.output_service import OutputService

# Pydantic models
class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    context: Optional[Dict] = None
    agent_type: str = "general"

class ChatResponse(BaseModel):
    success: bool
    response: str
    session_id: str
    timestamp: str
    error: Optional[str] = None

class MarketDataRequest(BaseModel):
    symbols: List[str]
    include_analysis: bool = True

class ReportRequest(BaseModel):
    data: Dict[str, Any]
    format_type: str
    filename: Optional[str] = None

# Initialize FastAPI app
app = FastAPI(
    title="Financial AI Agent API",
    description="Advanced AI-powered financial analytics and investment management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global services
orchestrator = AgentOrchestrator()
data_service = RealTimeDataService()
output_service = OutputService()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    
    # Initialize agent configurations
    config = AgentConfig(
        agent_id="financial-agent-001",
        model_id="anthropic.claude-3-sonnet-20240229-v1:0"
    )
    
    # Create specialized agents
    general_agent = FinancialAgent(config)
    
    # Register agents
    orchestrator.register_agent("general", general_agent)
    orchestrator.register_agent("portfolio", general_agent)  # Can be specialized later
    orchestrator.register_agent("risk", general_agent)      # Can be specialized later
    
    # Initialize data service (API key should come from environment)
    # data_service.initialize("YOUR_ALPHA_VANTAGE_KEY")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Financial AI Agent API",
        "status": "active",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint for financial queries"""
    
    try:
        # Route query to appropriate agent
        result = await orchestrator.route_query(
            query=request.query,
            session_id=request.session_id or f"session_{datetime.utcnow().timestamp()}",
            agent_type=request.agent_type
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/market-data")
async def get_market_data(request: MarketDataRequest):
    """Get real-time market data for specified symbols"""
    
    try:
        market_snapshot = await data_service.get_market_snapshot(request.symbols)
        
        if request.include_analysis:
            # Add AI analysis of market data
            analysis_query = f"Analyze the current market data for {', '.join(request.symbols)}"
            
            analysis_result = await orchestrator.route_query(
                query=analysis_query,
                session_id=f"market_analysis_{datetime.utcnow().timestamp()}",
                agent_type="general"
            )
            
            market_snapshot["ai_analysis"] = analysis_result.get("response", "")
        
        return market_snapshot
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-report")
async def generate_report(request: ReportRequest):
    """Generate financial report in specified format"""
    
    try:
        report_bytes = await output_service.generate_report(
            data=request.data,
            format_type=request.format_type,
            filename=request.filename
        )
        
        # Determine content type and filename
        content_type_map = {
            'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'pdf': 'application/pdf',
            'powerpoint': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        }
        
        extension_map = {
            'excel': 'xlsx',
            'pdf': 'pdf',
            'powerpoint': 'pptx'
        }
        
        content_type = content_type_map.get(request.format_type, 'application/octet-stream')
        extension = extension_map.get(request.format_type, 'bin')
        filename = request.filename or f"financial_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
        
        return StreamingResponse(
            io.BytesIO(report_bytes),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported output formats"""
    return {
        "formats": output_service.get_supported_formats(),
        "descriptions": {
            "excel": "Excel spreadsheet with charts and formulas",
            "pdf": "Professional PDF report",
            "powerpoint": "PowerPoint presentation",
            "word": "Word document",
            "csv": "Comma-separated values",
            "json": "JSON data format"
        }
    }

@app.post("/portfolio-analysis")
async def portfolio_analysis(portfolio_data: Dict[str, Any]):
    """Analyze portfolio performance and provide recommendations"""
    
    try:
        # Create portfolio analysis query
        query = f"""
        Analyze the following portfolio data and provide:
        1. Performance analysis
        2. Risk assessment
        3. Optimization recommendations
        4. Diversification analysis
        
        Portfolio Data: {json.dumps(portfolio_data, indent=2)}
        """
        
        result = await orchestrator.route_query(
            query=query,
            session_id=f"portfolio_{datetime.utcnow().timestamp()}",
            agent_type="portfolio"
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/risk-assessment")
async def risk_assessment(risk_data: Dict[str, Any]):
    """Perform comprehensive risk assessment"""
    
    try:
        query = f"""
        Perform a comprehensive risk assessment based on:
        1. Market risk analysis
        2. Credit risk evaluation
        3. Operational risk factors
        4. Liquidity risk assessment
        
        Risk Data: {json.dumps(risk_data, indent=2)}
        """
        
        result = await orchestrator.route_query(
            query=query,
            session_id=f"risk_{datetime.utcnow().timestamp()}",
            agent_type="risk"
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "agent_orchestrator": "active",
            "data_service": "active",
            "output_service": "active"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)