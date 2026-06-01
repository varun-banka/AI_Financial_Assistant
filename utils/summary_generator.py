"""
Phase 9: Executive Summary Generator Module
Generates concise executive summaries of financial documents
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, List
from langchain_core.documents import Document
from utils.embeddings import get_api_key

load_dotenv()


class ExecutiveSummaryGenerator:
    """
    Generates executive summaries with key metrics and insights.
    """
    
    def __init__(self):
        """Initialize the generator with Gemini LLM."""
        api_key = get_api_key()
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0.3,
            google_api_key=api_key
        )
    
    def generate_summary(self, text: str, company_name: str = "Company") -> Dict[str, str]:
        """
        Generates executive summary from financial text.
        
        Args:
            text (str): Financial document text
            company_name (str): Company name for personalization
            
        Returns:
            Dict with structured summary sections
        """
        prompt = f"""
Generate an executive summary for {company_name}'s annual report. 

Include these sections:
1. REVENUE SUMMARY: Key revenue metrics and growth
2. PROFIT SUMMARY: Profitability metrics and trends
3. KEY RISKS: Top 3 business risks
4. OPPORTUNITIES: Top 3 growth opportunities
5. INVESTMENT OUTLOOK: Overall assessment

Be concise, analytical, and professional. Focus on financials, not marketing.

Text:
{text[:3000]}

Format as clear bullet points under each section.
"""
        
        response = self.llm.invoke(prompt)
        
        summary = {
            "revenue_summary": "",
            "profit_summary": "",
            "key_risks": "",
            "opportunities": "",
            "investment_outlook": "",
            "full_text": response.content
        }
        
        # Parse response into sections
        sections = response.content.split("\n")
        current_section = None
        
        for line in sections:
            line_lower = line.lower()
            
            if "revenue" in line_lower and "summary" in line_lower:
                current_section = "revenue_summary"
            elif "profit" in line_lower and "summary" in line_lower:
                current_section = "profit_summary"
            elif "risk" in line_lower:
                current_section = "key_risks"
            elif "opportunit" in line_lower:
                current_section = "opportunities"
            elif "outlook" in line_lower or "investment" in line_lower:
                current_section = "investment_outlook"
            elif current_section and line.strip():
                summary[current_section] += line + "\n"
        
        return summary
    
    def generate_metrics_summary(self, metrics: Dict[str, float], ratios: Dict[str, float], company_name: str = "Company") -> str:
        """
        Generates summary of key metrics and ratios.
        
        Args:
            metrics (Dict): Extracted financial metrics
            ratios (Dict): Calculated financial ratios
            company_name (str): Company name
            
        Returns:
            str: Formatted metrics summary
        """
        summary = f"\n📈 KEY METRICS & RATIOS - {company_name}\n"
        summary += "=" * 50 + "\n\n"
        
        # Financial Metrics Section
        summary += "💰 FINANCIAL METRICS\n"
        if metrics.get("Revenue"):
            summary += f"   Revenue: ₹{metrics['Revenue']:,.0f} Cr\n"
        if metrics.get("Net_Profit"):
            summary += f"   Net Profit: ₹{metrics['Net_Profit']:,.0f} Cr\n"
        if metrics.get("Total_Assets"):
            summary += f"   Total Assets: ₹{metrics['Total_Assets']:,.0f} Cr\n"
        if metrics.get("Shareholders_Equity"):
            summary += f"   Shareholders' Equity: ₹{metrics['Shareholders_Equity']:,.0f} Cr\n"
        
        # Profitability Ratios
        summary += "\n📊 PROFITABILITY RATIOS\n"

        if ratios.get("Profit_Margin_Percent"):
            margin = ratios["Profit_Margin_Percent"]
            emoji = "🟢" if margin > 10 else "🟡" if margin > 5 else "🔴"
            summary += f"   {emoji} Profit Margin: {margin:.2f}%\n"

        if ratios.get("ROE_Percent"):
            roe = ratios["ROE_Percent"]
            emoji = "🟢" if roe > 15 else "🟡" if roe > 10 else "🔴"
            summary += f"   {emoji} ROE: {roe:.2f}%\n"

        if ratios.get("ROA_Percent"):
            roa = ratios["ROA_Percent"]
            emoji = "🟢" if roa > 5 else "🟡" if roa > 2 else "🔴"
            summary += f"   {emoji} ROA: {roa:.2f}%\n"

        # Liquidity Ratios
        summary += "\n💧 LIQUIDITY RATIOS\n"

        if ratios.get("Current_Ratio"):
            cr = ratios["Current_Ratio"]
            emoji = "🟢" if 1.5 <= cr <= 3 else "🔴" if cr < 1 else "🟡"
            summary += f"{emoji} Current Ratio: {cr:.2f}\n"

        # Leverage Ratios
        summary += "\n⚙️ LEVERAGE RATIOS\n"

        if ratios.get("Debt_to_Equity"):
            dte = ratios["Debt_to_Equity"]
            emoji = "🟢" if dte < 0.5 else "🟡" if dte < 1.5 else "🔴"
            summary += f"   {emoji} Debt-to-Equity: {dte:.2f}\n"

        if ratios.get("Debt_to_Assets"):
            dta = ratios["Debt_to_Assets"]
            emoji = "🟢" if dta < 30 else "🟡" if dta < 60 else "🔴"
            summary += f"   {emoji} Debt-to-Assets: {dta:.2f}%\n"
        summary += "\n" + "=" * 50
        return summary
    
    def generate_comparative_summary(self, company1_metrics: Dict, company2_metrics: Dict, company1_name: str, company2_name: str) -> str:
        """
        Generates comparison between two companies.
        
        Args:
            company1_metrics (Dict): Company 1 metrics
            company2_metrics (Dict): Company 2 metrics
            company1_name (str): Company 1 name
            company2_name (str): Company 2 name
            
        Returns:
            str: Comparison summary
        """
        summary = f"\n🔍 COMPARATIVE ANALYSIS: {company1_name} vs {company2_name}\n"
        summary += "=" * 60 + "\n\n"
        
        metrics_to_compare = ["Revenue", "Net_Profit", "Total_Assets", "Shareholders_Equity"]
        
        summary += f"{'Metric':<25} {company1_name:<15} {company2_name:<15}\n"
        summary += "-" * 60 + "\n"
        
        for metric in metrics_to_compare:
            if metric in company1_metrics and metric in company2_metrics:
                val1 = company1_metrics[metric]
                val2 = company2_metrics[metric]
                
                if val1 is not None and val2 is not None:
                    metric_display = metric.replace("_", " ")
                    summary += f"{metric_display:<25} ₹{val1:>12,.0f} Cr  ₹{val2:>12,.0f} Cr\n"
        
        summary += "\n" + "=" * 60
        
        return summary
    
    def generate_full_report(self, documents: List[Document], metrics: Dict, ratios: Dict, company_name: str = "Company") -> str:
        """
        Generates comprehensive executive report.
        
        Args:
            documents (List[Document]): Document chunks
            metrics (Dict): Financial metrics
            ratios (Dict): Financial ratios
            company_name (str): Company name
            
        Returns:
            str: Complete executive report
        """
        combined_text = "\n\n".join([doc.page_content for doc in documents[:15]])
        
        report = f"\n{'=' * 70}\n"
        report += f"  EXECUTIVE FINANCIAL REPORT - {company_name.upper()}\n"
        report += f"{'=' * 70}\n"
        
        # Generate summary
        summary = self.generate_summary(combined_text, company_name)
        report += "\n📋 EXECUTIVE SUMMARY\n"
        report += summary["full_text"][:1500] + "...\n"
        
        # Add metrics
        report += self.generate_metrics_summary(metrics, ratios, company_name)
        
        # Investment recommendation
        report += "\n\n💼 INVESTMENT RECOMMENDATION\n"
        
        avg_profitability = ratios.get("Profit_Margin_Percent", 0) or 0
        roe = ratios.get("ROE_Percent", 0) or 0
        debt_to_equity = ratios.get("Debt_to_Equity", 0) or 0
        
        if avg_profitability > 15 and roe > 15 and debt_to_equity < 1:
            recommendation = "🟢 STRONG BUY - Excellent profitability and financial health"
        elif avg_profitability > 10 and roe > 10 and debt_to_equity < 1.5:
            recommendation = "🟡 BUY - Good fundamentals, monitor debt levels"
        elif debt_to_equity > 2:
            recommendation = "🔴 HOLD/SELL - High leverage, elevated risk"
        else:
            recommendation = "🟡 HOLD - Neutral outlook, requires deeper analysis"
        
        report += recommendation + "\n"
        
        report += "\n" + "=" * 70
        
        return report
