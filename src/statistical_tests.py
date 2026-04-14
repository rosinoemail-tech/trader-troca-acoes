"""
Módulo de testes estatísticos para cointegração e correlação
"""
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import linregress
from typing import Tuple, Dict, Any


class StatisticalTests:
    """Realiza testes estatísticos entre pares de ativos"""
    
    @staticmethod
    def johansen_cointegration_test(log_prices_a: pd.Series, log_prices_b: pd.Series, 
                                   det_order: int = 0, k_ar_diff: int = 1) -> Dict[str, Any]:
        """
        Teste de cointegração de Johansen
        
        Args:
            log_prices_a: logaritmo natural dos preços do ativo A
            log_prices_b: logaritmo natural dos preços do ativo B
            det_order: Ordem determinística (-1=nenhum, 0=constante)
            k_ar_diff: Defasagens para testes
            
        Returns:
            Dicionário com resultados do teste
        """
        from statsmodels.tsa.vector_ar.vecm import coint_johansen
        
        data = np.column_stack([log_prices_a, log_prices_b])
        result = coint_johansen(data, det_order=det_order, k_ar_diff=k_ar_diff)
        
        return {
            'trace_stat': result.lr1[0],  # Estatística de traço (cointegração)
            'trace_crit_90': result.cvt[0, 0],  # Valor crítico 90%
            'trace_crit_95': result.cvt[0, 1],  # Valor crítico 95%
            'trace_crit_99': result.cvt[0, 2],  # Valor crítico 99%
            'is_cointegrated': result.lr1[0] > result.cvt[0, 1],  # 95% confidence
            'eigenvect': result.evec[:, 0]  # Vetor de cointegração
        }
    
    @staticmethod
    def calculate_hedge_ratio(log_prices_a: pd.Series, log_prices_b: pd.Series) -> Tuple[float, float]:
        """
        Calcula o hedge ratio (beta) usando regressão linear
        Y = α + β*X
        
        Args:
            log_prices_a: logaritmo dos preços do ativo A
            log_prices_b: logaritmo dos preços do ativo B
            
        Returns:
            Tupla (beta, alpha)
        """
        slope, intercept, r_value, p_value, std_err = linregress(log_prices_b, log_prices_a)
        
        return slope, intercept
    
    @staticmethod
    def calculate_correlation(price_a: pd.Series, price_b: pd.Series) -> Tuple[float, float]:
        """
        Calcula correlação de Pearson
        
        Args:
            price_a: Preços do ativo A
            price_b: Preços do ativo B
            
        Returns:
            Tupla (correlação, p_value)
        """
        corr, p_value = stats.pearsonr(price_a, price_b)
        return corr, p_value
    
    @staticmethod
    def adf_test(series: pd.Series) -> Dict[str, Any]:
        """
        Teste de Raiz Unitária Aumentado de Dickey-Fuller
        
        Args:
            series: Série temporal para teste
            
        Returns:
            Dicionário com resultados
        """
        from statsmodels.tsa.stattools import adfuller
        
        result = adfuller(series.dropna(), autolag='AIC')
        
        return {
            'adf_stat': result[0],
            'p_value': result[1],
            'n_lags': result[2],
            'n_obs': result[3],
            'critical_values': result[4],
            'is_stationary': result[1] < 0.05
        }
