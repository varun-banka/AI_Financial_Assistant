"""
Phase 2: Financial Ratio Calculator Module
Calculates key financial ratios from extracted metrics
"""

from typing import Dict, Optional, Tuple
import math


class FinancialRatioCalculator:
    """
    Calculates standard financial ratios used in financial analysis.
    
    Key Ratios:
        - Profitability: Profit Margin, ROE, ROA, EBITDA Margin
        - Liquidity: Current Ratio, Quick Ratio
        - Leverage: Debt-to-Equity, Debt-to-Assets
        - Efficiency: Asset Turnover, Inventory Turnover
    """
    
    def __init__(self, metrics: Dict[str, Optional[float]]):
        """
        Initialize calculator with financial metrics.
        
        Args:
            metrics (Dict): Dictionary of financial metrics
        """
        self.metrics = metrics
        self.ratios = {}
    
    def calculate_all_ratios(self) -> Dict[str, Optional[float]]:
        """
        Calculates all available financial ratios.
        
        Returns:
            Dict[str, Optional[float]]: Dictionary of calculated ratios
        """
        self.ratios = {
            # Profitability Ratios
            "Profit_Margin_Percent": self.profit_margin(),
            "ROE_Percent": self.return_on_equity(),
            "ROA_Percent": self.return_on_assets(),
            "EBITDA_Margin_Percent": self.ebitda_margin(),
            
            # Liquidity Ratios
            "Current_Ratio": self.current_ratio(),
            "Quick_Ratio": self.quick_ratio(),
            
            # Leverage Ratios
            "Debt_to_Equity": self.debt_to_equity(),
            "Debt_to_Assets": self.debt_to_assets(),
            "Equity_Ratio": self.equity_ratio(),
            
            # Efficiency Ratios
            "Asset_Turnover": self.asset_turnover(),
        }
        
        return self.ratios
    
    def profit_margin(self) -> Optional[float]:
        """
        Profit Margin = (Net Profit / Revenue) × 100
        
        Indicates what percentage of revenue is profit.
        Higher is better.
        """
        if self.metrics["Revenue"] and self.metrics["Net_Profit"]:
            if self.metrics["Revenue"] > 0:
                return (self.metrics["Net_Profit"] / self.metrics["Revenue"]) * 100
        return None
    
    def return_on_equity(self) -> Optional[float]:
        """
        ROE = (Net Profit / Shareholders' Equity) × 100
        
        Measures how efficiently the company uses shareholder capital.
        Higher is better.
        """
        if self.metrics["Net_Profit"] and self.metrics["Shareholders_Equity"]:
            if self.metrics["Shareholders_Equity"] > 0:
                return (self.metrics["Net_Profit"] / self.metrics["Shareholders_Equity"]) * 100
        return None
    
    def return_on_assets(self) -> Optional[float]:
        """
        ROA = (Net Profit / Total Assets) × 100
        
        Measures how efficiently assets generate profit.
        Higher is better.
        """
        if self.metrics["Net_Profit"] and self.metrics["Total_Assets"]:
            if self.metrics["Total_Assets"] > 0:
                return (self.metrics["Net_Profit"] / self.metrics["Total_Assets"]) * 100
        return None
    
    def ebitda_margin(self) -> Optional[float]:
        """
        EBITDA Margin = (EBITDA / Revenue) × 100
        
        Measures operational efficiency excluding finance and taxes.
        """
        if self.metrics["EBITDA"] and self.metrics["Revenue"]:
            if self.metrics["Revenue"] > 0:
                return (self.metrics["EBITDA"] / self.metrics["Revenue"]) * 100
        return None
    
    def current_ratio(self) -> Optional[float]:
        """
        Current Ratio = Current Assets / Current Liabilities
        
        Measures short-term liquidity (ability to pay short-term debts).
        Ideal range: 1.5 - 3.0
        """
        if self.metrics["Current_Assets"] and self.metrics["Current_Liabilities"]:
            if self.metrics["Current_Liabilities"] > 0:
                return self.metrics["Current_Assets"] / self.metrics["Current_Liabilities"]
        return None
    
    def quick_ratio(self) -> Optional[float]:
        """
        Quick Ratio = (Current Assets - Inventory) / Current Liabilities
        
        Stricter measure of liquidity than current ratio.
        Note: We assume inventory isn't extracted, so this equals current ratio
        """
        return self.current_ratio()
    
    def debt_to_equity(self) -> Optional[float]:
        """
        Debt-to-Equity = Total Liabilities / Shareholders' Equity
        
        Measures financial leverage.
        Lower is generally better (less debt relative to equity).
        """
        if self.metrics["Total_Liabilities"] and self.metrics["Shareholders_Equity"]:
            if self.metrics["Shareholders_Equity"] > 0:
                return self.metrics["Total_Liabilities"] / self.metrics["Shareholders_Equity"]
        return None
    
    def debt_to_assets(self) -> Optional[float]:
        """
        Debt-to-Assets = Total Liabilities / Total Assets
        
        Percentage of assets financed by debt.
        Lower is better.
        """
        if self.metrics["Total_Liabilities"] and self.metrics["Total_Assets"]:
            if self.metrics["Total_Assets"] > 0:
                return (self.metrics["Total_Liabilities"] / self.metrics["Total_Assets"]) * 100
        return None
    
    def equity_ratio(self) -> Optional[float]:
        """
        Equity Ratio = Shareholders' Equity / Total Assets
        
        Percentage of assets financed by equity.
        Higher is better.
        """
        if self.metrics["Shareholders_Equity"] and self.metrics["Total_Assets"]:
            if self.metrics["Total_Assets"] > 0:
                return (self.metrics["Shareholders_Equity"] / self.metrics["Total_Assets"]) * 100
        return None
    
    def asset_turnover(self) -> Optional[float]:
        """
        Asset Turnover = Revenue / Total Assets
        
        Measures how efficiently assets generate revenue.
        Higher is better.
        """
        if self.metrics["Revenue"] and self.metrics["Total_Assets"]:
            if self.metrics["Total_Assets"] > 0:
                return self.metrics["Revenue"] / self.metrics["Total_Assets"]
        return None
    
    def get_ratio_interpretation(self, ratio_name: str, ratio_value: Optional[float]) -> str:
        """
        Provides interpretation of a ratio.
        
        Args:
            ratio_name (str): Name of the ratio
            ratio_value (float): Calculated ratio value
            
        Returns:
            str: Interpretation message
        """
        if ratio_value is None:
            return "❌ Insufficient data to calculate this ratio"
        
        interpretations = {
            "Profit_Margin_Percent": lambda v: (
                "🟢 Excellent" if v > 20 else "🟡 Good" if v > 10 else "🔴 Needs Improvement"
            ),
            "ROE_Percent": lambda v: (
                "🟢 Excellent" if v > 15 else "🟡 Good" if v > 10 else "🔴 Concerning"
            ),
            "Current_Ratio": lambda v: (
                "🟢 Healthy" if 1.5 <= v <= 3 else "🟡 Caution" if v > 1 else "🔴 At Risk"
            ),
            "Debt_to_Equity": lambda v: (
                "🟢 Conservative" if v < 0.5 else "🟡 Moderate" if v < 1.5 else "🔴 High Leverage"
            ),
        }
        
        if ratio_name in interpretations:
            return interpretations[ratio_name](ratio_value)
        
        return f"Value: {ratio_value:.2f}"


def calculate_ratios(metrics: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
    """
    Convenience function to calculate all ratios.
    
    Args:
        metrics (Dict): Financial metrics dictionary
        
    Returns:
        Dict[str, Optional[float]]: Calculated ratios
    """
    calculator = FinancialRatioCalculator(metrics)
    return calculator.calculate_all_ratios()
