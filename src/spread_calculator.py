"""
Módulo de cálculo do spread e Z-score
"""
import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any
import config


class SpreadCalculator:
    """Calcula spread e Z-score entre pares de ativos"""
    
    def __init__(self, log_price_a: pd.Series, log_price_b: pd.Series, beta: float):
        """
        Inicializa o calculador de spread
        
        Args:
            log_price_a: Logaritmo dos preços do ativo A
            log_price_b: Logaritmo dos preços do ativo B
            beta: Hedge ratio (coeficiente de regressão)
        """
        self.log_price_a = log_price_a
        self.log_price_b = log_price_b
        self.beta = beta
    
    def calculate_spread(self, lookback: int = config.LOOKBACK_WINDOW) -> pd.DataFrame:
        """
        Calcula o spread: S = log(P_A) - β * log(P_B)
        
        Args:
            lookback: Número de períodos para histórico
            
        Returns:
            DataFrame com spread, média móvel e desvio padrão
        """
        # Calcular spread
        spread = self.log_price_a - self.beta * self.log_price_b
        
        # Calcular média e desvio padrão móvel
        spread_mean = spread.rolling(window=lookback).mean()
        spread_std = spread.rolling(window=lookback).std()
        
        result = pd.DataFrame({
            'spread': spread,
            'spread_mean': spread_mean,
            'spread_std': spread_std
        })
        
        return result
    
    def calculate_zscore(self, spread_df: pd.DataFrame) -> pd.Series:
        """
        Calcula Z-score: Z = (spread - média) / desvio_padrão
        
        Args:
            spread_df: DataFrame com spread, média e desvio padrão
            
        Returns:
            Series com Z-scores
        """
        zscore = (spread_df['spread'] - spread_df['spread_mean']) / spread_df['spread_std']
        return zscore
    
    def calculate_all_metrics(self, lookback: int = config.LOOKBACK_WINDOW) -> pd.DataFrame:
        """
        Calcula todos os métricas de uma vez
        
        Args:
            lookback: Período para cálculo de média e desvio
            
        Returns:
            DataFrame com todos os indicadores
        """
        spread_data = self.calculate_spread(lookback)
        zscore = self.calculate_zscore(spread_data)
        
        result = spread_data.copy()
        result['zscore'] = zscore
        
        return result
