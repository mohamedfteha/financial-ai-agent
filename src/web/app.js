// FinanceGPT - MVP JavaScript Application
// AWS Activate Demo Version

// Configuration
const API_BASE = 'https://your-api-gateway-url.amazonaws.com/prod'; // Replace with actual API Gateway URL
const DEMO_MODE = true; // Set to false when API is ready

// Global variables
let isLoading = false;

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    console.log('FinanceGPT MVP initialized');
    
    // Add welcome message if in demo mode
    if (DEMO_MODE) {
        setTimeout(() => {
            addMessage('ai', '🚀 Demo Mode: This is a simulation of our AI capabilities. In production, this connects to Amazon Bedrock and real market data.');
        }, 1000);
    }
});

// Main chat functionality
async function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();
    
    if (!message || isLoading) return;
    
    // Display user message
    addMessage('user', message);
    input.value = '';
    
    // Show loading
    showLoading(true);
    
    try {
        if (DEMO_MODE) {
            // Demo responses
            const response = await getDemoResponse(message);
            setTimeout(() => {
                addMessage('ai', response);
                showLoading(false);
            }, 1500);
        } else {
            // Real API call
            const response = await fetch(`${API_BASE}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: message,
                    agent_type: 'general'
                })
            });
            
            const result = await response.json();
            addMessage('ai', result.response || 'Sorry, I encountered an error.');
            showLoading(false);
        }
    } catch (error) {
        console.error('Error:', error);
        addMessage('ai', '❌ Connection error. Please try again.');
        showLoading(false);
    }
}

// Demo response generator
async function getDemoResponse(message) {
    const lowerMessage = message.toLowerCase();
    
    if (lowerMessage.includes('apple') || lowerMessage.includes('aapl')) {
        return `📊 **Apple Inc. (AAPL) Analysis**

**Current Price**: $150.25 (+2.5% today)
**Market Cap**: $2.4T
**P/E Ratio**: 28.5

**AI Analysis**: Apple shows strong fundamentals with robust iPhone sales and growing services revenue. The stock is trading near resistance at $152. 

**Recommendation**: BUY with target price $165
**Risk Level**: Medium
**Time Horizon**: 3-6 months

*This analysis uses Claude Sonnet AI through Amazon Bedrock for sophisticated financial modeling.*`;
    }
    
    if (lowerMessage.includes('market') && lowerMessage.includes('sentiment')) {
        return `📈 **Current Market Sentiment Analysis**

**Overall Sentiment**: Cautiously Optimistic (7.2/10)
**Fear & Greed Index**: 65 (Greed)
**VIX Level**: 18.5 (Low volatility)

**Key Factors**:
• Fed policy expectations driving optimism
• Strong earnings season performance
• Geopolitical tensions creating uncertainty

**Sector Rotation**: Tech → Value stocks
**Recommendation**: Diversified approach with defensive positions

*Real-time sentiment analysis powered by AI and multiple data sources.*`;
    }
    
    if (lowerMessage.includes('portfolio')) {
        return `💼 **Portfolio Optimization Insights**

**Risk Assessment**: Your portfolio shows moderate diversification
**Sharpe Ratio**: 1.24 (Good)
**Beta**: 0.95 (Market neutral)

**Recommendations**:
1. Increase international exposure (currently 15%, target 25%)
2. Add defensive sectors (utilities, consumer staples)
3. Consider ESG investments for long-term growth

**Rebalancing**: Quarterly recommended
**Expected Return**: 8-12% annually

*AI-powered portfolio analysis using modern portfolio theory and machine learning.*`;
    }
    
    if (lowerMessage.includes('report') || lowerMessage.includes('generate')) {
        return `📋 **Report Generation Ready**

I can generate professional reports in multiple formats:
• **Excel**: Interactive spreadsheets with formulas and charts
• **PDF**: Professional analysis documents
• **PowerPoint**: Executive presentation slides

**Available Reports**:
- Market Analysis Report
- Portfolio Performance Review
- Risk Assessment Summary
- Investment Recommendations

Click "Generate Report" to create a sample Excel report with live data and AI insights!`;
    }
    
    // Default response
    return `🤖 **AI Financial Analysis**

I'm your AI financial analyst powered by Amazon Bedrock and Claude Sonnet. I can help with:

• **Stock Analysis**: Fundamental and technical analysis
• **Market Research**: Trends, sentiment, and forecasts  
• **Portfolio Management**: Optimization and risk assessment
• **Report Generation**: Professional Excel, PDF, PowerPoint reports

Try asking:
- "Analyze Tesla stock"
- "What's the market outlook?"
- "Optimize my portfolio"
- "Generate a market report"

*This demo showcases our AI capabilities. Full version includes real-time data integration.*`;
}

// Add message to chat
function addMessage(sender, text) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = sender === 'user' ? 'user-message' : 'ai-message';
    
    if (sender === 'ai') {
        // Convert markdown-style formatting to HTML
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
        text = text.replace(/\n/g, '<br>');
        messageDiv.innerHTML = text;
    } else {
        messageDiv.textContent = text;
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Show/hide loading indicator
function showLoading(show) {
    isLoading = show;
    const loading = document.getElementById('loading');
    loading.style.display = show ? 'block' : 'none';
}

// Handle Enter key press
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

// Quick action functions
async function analyzeStock(symbol = 'AAPL') {
    const input = document.getElementById('user-input');
    input.value = `Analyze ${symbol} stock`;
    await sendMessage();
}

async function generateReport() {
    if (DEMO_MODE) {
        addMessage('user', 'Generate financial report');
        showLoading(true);
        
        setTimeout(() => {
            addMessage('ai', `📊 **Sample Report Generated!**

**Report Type**: Market Analysis & Portfolio Summary
**Format**: Excel Spreadsheet
**Data Points**: 50+ metrics and charts

**Contents**:
• Executive Summary Dashboard
• Market Data (Real-time prices, volumes)
• Technical Analysis (RSI, MACD, Moving Averages)
• Portfolio Performance Metrics
• Risk Assessment Matrix
• AI-Generated Recommendations

**File Size**: 2.3 MB
**Charts**: 8 interactive visualizations

*In production, this would download a real Excel file with live data from Alpha Vantage and AI analysis from Claude Sonnet.*

🔗 [Download Sample Report] (Demo - would trigger actual download)`);
            showLoading(false);
        }, 2000);
    } else {
        // Real report generation
        try {
            const reportData = {
                summary: {
                    total_portfolio_value: 100000,
                    daily_change: 1250,
                    top_performer: 'AAPL',
                    risk_score: 6.5
                },
                market_data: {
                    'AAPL': { current_price: 150.25, change: 2.5, volume: 45000000 },
                    'MSFT': { current_price: 380.50, change: -1.2, volume: 28000000 },
                    'GOOGL': { current_price: 140.75, change: 3.1, volume: 32000000 }
                }
            };
            
            const response = await fetch(`${API_BASE}/generate-report`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    data: reportData,
                    format_type: 'excel',
                    filename: 'financial-analysis-report.xlsx'
                })
            });
            
            if (response.ok) {
                const blob = await response.blob();
                downloadFile(blob, 'financial-analysis-report.xlsx');
                addMessage('ai', '✅ Excel report generated and downloaded successfully!');
            } else {
                addMessage('ai', '❌ Error generating report. Please try again.');
            }
        } catch (error) {
            console.error('Report generation error:', error);
            addMessage('ai', '❌ Connection error. Please try again.');
        }
    }
}

async function marketSentiment() {
    const input = document.getElementById('user-input');
    input.value = 'What is the current market sentiment?';
    await sendMessage();
}

// Utility functions
function downloadFile(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

function scrollToDemo() {
    document.getElementById('demo').scrollIntoView({ 
        behavior: 'smooth' 
    });
}

// Demo data for testing
const demoStockData = {
    'AAPL': {
        price: 150.25,
        change: 2.5,
        volume: 45000000,
        marketCap: '2.4T',
        pe: 28.5
    },
    'MSFT': {
        price: 380.50,
        change: -1.2,
        volume: 28000000,
        marketCap: '2.8T',
        pe: 32.1
    },
    'GOOGL': {
        price: 140.75,
        change: 3.1,
        volume: 32000000,
        marketCap: '1.8T',
        pe: 25.4
    }
};

// Initialize demo mode indicator
if (DEMO_MODE) {
    console.log('🚀 FinanceGPT running in DEMO mode');
    console.log('💡 To connect to real API, set DEMO_MODE = false and update API_BASE URL');
}