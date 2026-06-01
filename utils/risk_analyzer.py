"""
Phase 8: Sentiment & Risk Analysis Module
Analyzes financial documents for sentiment, risks, and opportunities
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, List, Optional
from langchain_core.documents import Document
from utils.embeddings import get_api_key

load_dotenv()


class SentimentRiskAnalyzer:
    """
    Analyzes financial documents for sentiment, risks, and opportunities.
    """
    
    def __init__(self):
        """Initialize the analyzer with Gemini LLM."""
        api_key = get_api_key()
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0.3,
            google_api_key=api_key
        )
    
    def analyze_sentiment(self, text: str) -> Dict[str, any]:
        """
        Analyzes sentiment of financial text.
        
        Returns:
            Dict with sentiment classification and score
        """
        prompt = f"""
Analyze the sentiment of this financial text. Classify as:
1. POSITIVE (bullish outlook)
2. NEUTRAL (balanced view)
3. NEGATIVE (bearish outlook)

Also provide:
- Confidence score (0-100)
- Key positive indicators (if any)
- Key negative indicators (if any)

Text:
{text[:2000]}

Respond in JSON format:
{{
    "sentiment": "POSITIVE/NEUTRAL/NEGATIVE",
    "confidence": 85,
    "positive_indicators": ["..."],
    "negative_indicators": ["..."],
    "summary": "..."
}}
"""
        
        response = self.llm.invoke(prompt)
        
        try:
            import json
            result = json.loads(response.content)
            return result
        except:
            return {
                "sentiment": "NEUTRAL",
                "confidence": 50,
                "positive_indicators": [],
                "negative_indicators": [],
                "summary": response.content
            }
    
    def identify_risks(self, text: str) -> Dict[str, any]:
        """
        Identifies potential risks from financial document.
        
        Returns:
            Dict with identified risks categorized by severity
        """
        prompt = f"""
Identify business risks mentioned in this financial document. Categorize by severity:

- HIGH RISK: Could materially impact business
- MEDIUM RISK: Should be monitored
- LOW RISK: Minor concerns

Text:
{text[:2000]}

Respond in JSON format:
{{
    "high_risks": ["risk1", "risk2"],
    "medium_risks": ["risk1", "risk2"],
    "low_risks": ["risk1"],
    "risk_mitigation_mentioned": true/false,
    "overall_risk_level": "HIGH/MEDIUM/LOW"
}}
"""
        
        response = self.llm.invoke(prompt)
        
        try:
            import json
            result = json.loads(response.content)
            return result
        except:
            return {
                "high_risks": [],
                "medium_risks": [],
                "low_risks": [],
                "risk_mitigation_mentioned": False,
                "overall_risk_level": "UNKNOWN"
            }
    
    def identify_opportunities(self, text: str) -> Dict[str, any]:
        """
        Identifies growth opportunities and competitive advantages.
        
        Returns:
            Dict with opportunities and strategic initiatives
        """
        prompt = f"""
Identify business opportunities and growth drivers mentioned in this financial document.

Categories:
- MARKET_EXPANSION: New markets or segments
- INNOVATION: New products or technologies
- STRATEGIC_INITIATIVES: Major company programs
- COST_OPTIMIZATION: Efficiency improvements
- PARTNERSHIPS: Collaborations or alliances

Text:
{text[:2000]}

Respond in JSON format:
{{
    "market_expansion": ["opp1", "opp2"],
    "innovation": ["opp1"],
    "strategic_initiatives": ["init1", "init2"],
    "cost_optimization": ["opp1"],
    "partnerships": ["partner1"],
    "overall_outlook": "POSITIVE/NEUTRAL/NEGATIVE"
}}
"""
        
        response = self.llm.invoke(prompt)
        
        try:
            import json
            result = json.loads(response.content)
            return result
        except:
            return {
                "market_expansion": [],
                "innovation": [],
                "strategic_initiatives": [],
                "cost_optimization": [],
                "partnerships": [],
                "overall_outlook": "UNKNOWN"
            }
    
    def generate_business_assessment(self, text: str) -> Dict[str, any]:
        """
        Generates comprehensive business assessment.
        
        Args:
            text (str): Financial document text
            
        Returns:
            Dict with complete assessment
        """
        assessment = {
            "sentiment": self.analyze_sentiment(text),
            "risks": self.identify_risks(text),
            "opportunities": self.identify_opportunities(text)
        }
        
        return assessment
    
    def analyze_documents(self, documents: List[Document]) -> Dict[str, any]:
        """
        Analyzes multiple document chunks.
        
        Args:
            documents (List[Document]): Document chunks to analyze
            
        Returns:
            Dict with combined analysis
        """
        combined_text = "\n\n".join([doc.page_content for doc in documents[:10]])  # Top 10 chunks
        
        return self.generate_business_assessment(combined_text)


def generate_risk_report(documents: List[Document], analyzer: Optional[SentimentRiskAnalyzer] = None) -> str:
    """
    Generates a risk assessment report.
    
    Args:
        documents (List[Document]): Document chunks
        analyzer (SentimentRiskAnalyzer): Optional analyzer instance
        
    Returns:
        str: Formatted risk report
    """
    if analyzer is None:
        analyzer = SentimentRiskAnalyzer()
    
    assessment = analyzer.analyze_documents(documents)
    
    report = "\n📊 FINANCIAL RISK ASSESSMENT REPORT\n"
    report += "=" * 60 + "\n\n"
    
    # Sentiment
    report += "🎯 SENTIMENT ANALYSIS\n"
    report += f"   Outlook: {assessment['sentiment'].get('sentiment', 'N/A')}\n"
    report += f"   Confidence: {assessment['sentiment'].get('confidence', 'N/A')}%\n"
    
    # Risks
    report += "\n⚠️ IDENTIFIED RISKS\n"
    risks = assessment['risks']
    if risks.get('high_risks'):
        report += f"   🔴 HIGH: {', '.join(risks['high_risks'][:3])}\n"
    if risks.get('medium_risks'):
        report += f"   🟡 MEDIUM: {', '.join(risks['medium_risks'][:3])}\n"
    report += f"   Overall Risk Level: {risks.get('overall_risk_level', 'N/A')}\n"
    
    # Opportunities
    report += "\n💡 OPPORTUNITIES\n"
    opps = assessment['opportunities']
    if opps.get('market_expansion'):
        report += f"   📈 Market Expansion: {', '.join(opps['market_expansion'][:2])}\n"
    if opps.get('innovation'):
        report += f"   🚀 Innovation: {', '.join(opps['innovation'][:2])}\n"
    report += f"   Outlook: {opps.get('overall_outlook', 'N/A')}\n"
    
    report += "\n" + "=" * 60
    
    return report
