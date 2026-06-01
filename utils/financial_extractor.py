"""
Phase 2: Financial Metrics Extraction Module
Extracts key financial metrics from annual reports using regex and NLP
"""

import re
from typing import Dict, Optional, List
from langchain_core.documents import Document


def extract_financial_metrics(text: str) -> Dict[str, Optional[float]]:
    """
    Extracts key financial metrics from text using regex patterns.
    
    Metrics Extracted:
        - Revenue/Sales
        - Net Profit/Income
        - Total Assets
        - Total Liabilities
        - Shareholders' Equity
        - Operating Cash Flow
        - Free Cash Flow
        - EBITDA
        
    Args:
        text (str): Financial report text
        
    Returns:
        Dict[str, Optional[float]]: Extracted financial metrics
        
    Example:
        >>> metrics = extract_financial_metrics(annual_report_text)
        >>> print(f"Revenue: ₹{metrics['Revenue']}")
        >>> print(f"Net Profit: ₹{metrics['Net_Profit']}")
    """
    
    metrics = {
        "Revenue": None,
        "Net_Profit": None,
        "Total_Assets": None,
        "Total_Liabilities": None,
        "Shareholders_Equity": None,
        "Operating_Cash_Flow": None,
        "Free_Cash_Flow": None,
        "EBITDA": None,
        "Current_Assets": None,
        "Current_Liabilities": None
    }
    
    # Regex patterns for different financial metrics
    patterns = {
        "Revenue": [
            r"(?:Revenue|Sales).*?(?:is|of)?[:\s]+(?:₹|Rs\.?|Rs|INR)?[\s]*([0-9,]+\.?[0-9]*)\s*(?:crore|cr|million|lakh|thousand)",
            r"(?:Revenue|Sales).*?[:\s]+([0-9,]+\.?[0-9]*)"
        ],
        "Net_Profit": [
            r"(?:Net Profit|Net Income|PAT).*?(?:is|of)?[:\s]+(?:₹|Rs\.?|Rs|INR)?[\s]*([0-9,]+\.?[0-9]*)\s*(?:crore|cr|million|lakh)",
            r"(?:Net Profit|Net Income).*?[:\s]+([0-9,]+\.?[0-9]*)"
        ],
        "Total_Assets": [
            r"(?:Total Assets).*?[:\s]+(?:₹|Rs\.?|Rs|INR)?[\s]*([0-9,]+\.?[0-9]*)\s*(?:crore|cr|million)",
            r"(?:Total Assets).*?[:\s]+([0-9,]+\.?[0-9]*)"
        ],
        "Total_Liabilities": [
            r"(?:Total Liabilities).*?[:\s]+(?:₹|Rs\.?|Rs|INR)?[\s]*([0-9,]+\.?[0-9]*)\s*(?:crore|cr|million)",
            r"(?:Total Liabilities).*?[:\s]+([0-9,]+\.?[0-9]*)"
        ],
        "Shareholders_Equity": [
            r"(?:Shareholders.? Equity|Stockholders.? Equity|Total Equity).*?[:\s]+(?:₹|Rs\.?|Rs|INR)?[\s]*([0-9,]+\.?[0-9]*)\s*(?:crore|cr|million)",
            r"(?:Shareholders.? Equity|Stockholders.? Equity).*?[:\s]+([0-9,]+\.?[0-9]*)"
        ],
        "Operating_Cash_Flow": [
            r"(?:Operating Cash Flow|Cash from Operations).*?[:\s]+(?:₹|Rs\.?|Rs|INR)?[\s]*([0-9,]+\.?[0-9]*)\s*(?:crore|cr|million)",
        ],
        "Free_Cash_Flow": [
            r"(?:Free Cash Flow|FCF).*?[:\s]+(?:₹|Rs\.?|Rs|INR)?[\s]*([0-9,]+\.?[0-9]*)\s*(?:crore|cr|million)",
        ],
        "EBITDA": [
            r"(?:EBITDA).*?[:\s]+(?:₹|Rs\.?|Rs|INR)?[\s]*([0-9,]+\.?[0-9]*)\s*(?:crore|cr|million)",
        ],
        "Current_Assets": [
            r"(?:Current Assets).*?[:\s]+(?:₹|Rs\.?|Rs|INR)?[\s]*([0-9,]+\.?[0-9]*)\s*(?:crore|cr|million)",
        ],
        "Current_Liabilities": [
            r"(?:Current Liabilities).*?[:\s]+(?:₹|Rs\.?|Rs|INR)?[\s]*([0-9,]+\.?[0-9]*)\s*(?:crore|cr|million)",
        ]
    }
    
    # Extract metrics using patterns
    for metric, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    # Clean the extracted value
                    value_str = match.group(1).replace(",", "").strip()
                    value = float(value_str)
                    metrics[metric] = value
                    break
                except (ValueError, AttributeError):
                    continue
    
    return metrics


def extract_metrics_from_documents(documents: List[Document]) -> Dict[str, Optional[float]]:
    """
    Extracts financial metrics from a list of documents (chunks).
    
    Combines metrics from all documents.
    
    Args:
        documents (List[Document]): List of document chunks
        
    Returns:
        Dict[str, Optional[float]]: Combined financial metrics
    """
    combined_text = "\n\n".join([doc.page_content for doc in documents])
    return extract_financial_metrics(combined_text)


def get_metric_source(metric_name: str, text: str) -> Optional[str]:
    """
    Finds the exact sentence containing a specific metric.
    
    Args:
        metric_name (str): Name of the metric to find
        text (str): Full text to search
        
    Returns:
        Optional[str]: Sentence containing the metric
    """
    sentences = text.split(". ")
    
    for sentence in sentences:
        if metric_name.lower().replace("_", " ") in sentence.lower():
            return sentence.strip()
    
    return None
