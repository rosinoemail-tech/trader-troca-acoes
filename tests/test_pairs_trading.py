"""
Testes Unitários para o Sistema de Pairs Trading
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.data_loader import DataLoader
from src.statistical_tests import StatisticalTests
from src.spread_calculator import SpreadCalculator
from src.trading_signals import TradingSignals, SignalType
from src.risk_management import RiskManager


@pytest.fixture
def sample_prices():
    """Fixture com preços de exemplo"""
    np.random.seed(42)
    n = 100
    dates = pd.date_range('2023-01-01', periods=n)
    
    # Criar preços correlacionados
    base = np.cumsum(np.random.randn(n) * 2)
    price_a = 100 + base
    price_b = 50 + 0.8 * base + np.random.randn(n)
    
    df_a = pd.DataFrame({'date': dates, 'price': price_a}).set_index('date')
    df_b = pd.DataFrame({'date': dates, 'price': price_b}).set_index('date')
    
    return df_a, df_b


class TestDataLoader:
    """Testes para módulo de carregamento de dados"""
    
    def test_load_from_dict(self):
        """Testa carregamento de dicionário"""
        dates = pd.date_range('2023-01-01', periods=10)
        prices_a = np.random.rand(10) * 100
        prices_b = np.random.rand(10) * 50
        
        df_a, df_b = DataLoader.load_from_dict(list(dates), list(prices_a), list(prices_b))
        
        assert len(df_a) == 10
        assert len(df_b) == 10
        assert df_a['price'].iloc[0] == prices_a[0]
    
    def test_get_log_prices(self):
        """Testa cálculo de log dos preços"""
        dates = pd.date_range('2023-01-01', periods=10)
        prices = [100, 110, 105, 115, 120]
        df = pd.DataFrame({'date': dates[:5], 'price': prices}).set_index('date')
        
        log_prices = DataLoader.get_log_prices(df)
        
        assert len(log_prices) == 5
        assert log_prices.iloc[0] == np.log(100)


class TestStatisticalTests:
    """Testes para módulo de testes estatísticos"""
    
    def test_calculate_correlation(self, sample_prices):
        """Testa cálculo de correlação"""
        df_a, df_b = sample_prices
        
        corr, pvalue = StatisticalTests.calculate_correlation(df_a['price'], df_b['price'])
        
        assert -1 <= corr <= 1
        assert 0 <= pvalue <= 1
        assert corr > 0.7  # Deve estar correlacionado
    
    def test_calculate_hedge_ratio(self, sample_prices):
        """Testa cálculo do hedge ratio"""
        df_a, df_b = sample_prices
        log_a = np.log(df_a['price'])
        log_b = np.log(df_b['price'])
        
        beta, alpha = StatisticalTests.calculate_hedge_ratio(log_a, log_b)
        
        assert isinstance(beta, (int, float))
        assert isinstance(alpha, (int, float))
        assert 0 <= beta <= 2  # Beta razoável


class TestSpreadCalculator:
    """Testes para cálculo do spread"""
    
    def test_calculate_spread(self, sample_prices):
        """Testa cálculo do spread"""
        df_a, df_b = sample_prices
        log_a = np.log(df_a['price'])
        log_b = np.log(df_b['price'])
        beta = 0.8
        
        calc = SpreadCalculator(log_a, log_b, beta)
        spread_data = calc.calculate_spread(lookback=20)
        
        assert 'spread' in spread_data.columns
        assert 'spread_mean' in spread_data.columns
        assert 'spread_std' in spread_data.columns
        assert len(spread_data) == len(log_a)
    
    def test_calculate_zscore(self, sample_prices):
        """Testa cálculo do Z-score"""
        df_a, df_b = sample_prices
        log_a = np.log(df_a['price'])
        log_b = np.log(df_b['price'])
        beta = 0.8
        
        calc = SpreadCalculator(log_a, log_b, beta)
        spread_data = calc.calculate_spread(lookback=20)
        zscore = calc.calculate_zscore(spread_data)
        
        assert len(zscore) == len(log_a)
        # Depois do lookback window, Z-score deve estar entre -4 e +4
        zscore_valid = zscore.dropna()
        assert zscore_valid.min() >= -5
        assert zscore_valid.max() <= 5


class TestTradingSignals:
    """Testes para geração de sinais"""
    
    def test_generate_signals_basic(self):
        """Testa geração básica de sinais"""
        # Serie artificial com Z-scores conhecidos
        zscore = pd.Series([0, 0, -2.5, -2.5, 0.3, 0.1, 2.5, 2.5, 0.2, 0])
        
        signal_gen = TradingSignals(entry_threshold=2.0, exit_threshold=0.5)
        signals, counts = signal_gen.generate_signals(zscore)
        
        assert len(signals) == len(zscore)
        assert counts['BUY_A_SELL_B'] > 0  # Deve haver entrada LONG
        assert counts['SELL_A_BUY_B'] > 0  # Deve haver entrada SHORT
    
    def test_get_signal_description(self):
        """Testa descrição de sinais"""
        signal_gen = TradingSignals()
        
        desc = signal_gen.get_signal_description(SignalType.BUY_A_SELL_B.value)
        assert desc == "BUY_A_SELL_B"
        
        desc = signal_gen.get_signal_description(SignalType.SELL_A_BUY_B.value)
        assert desc == "SELL_A_BUY_B"


class TestRiskManager:
    """Testes para gerenciamento de risco"""
    
    def test_calculate_position_size(self):
        """Testa cálculo de tamanho de posição"""
        rm = RiskManager(account_size=100000, max_risk_per_trade=0.02)
        
        pos_size = rm.calculate_position_size(
            current_price_a=100,
            current_price_b=50,
            zscore=-2.5,
            beta=0.8
        )
        
        assert 'position_a' in pos_size
        assert 'position_b' in pos_size
        assert 'notional_a' in pos_size
        assert 'notional_b' in pos_size
        assert pos_size['position_a'] > 0
        assert pos_size['position_b'] > 0
    
    def test_calculate_effective_cost(self):
        """Testa cálculo do custo efetivo"""
        rm = RiskManager(account_size=100000, transaction_cost=0.001)
        
        pos_sizes = {
            'notional_a': 50000,
            'notional_b': 40000,
            'position_a': 500,
            'position_b': 800
        }
        
        cost = rm.calculate_effective_cost(pos_sizes)
        
        assert cost > 0
        # 2 transações (entrada + saída) a 0.1% cada
        expected_cost = (50000 + 40000) * 0.001 * 2
        assert abs(cost - expected_cost) < 1
    
    def test_check_margin_requirements(self):
        """Testa verificação de margem"""
        rm = RiskManager(account_size=100000)
        
        margin = rm.check_margin_requirements(
            position_a=500,
            position_b=800,
            price_a=100,
            price_b=50
        )
        
        assert 'total_notional' in margin
        assert 'required_margin' in margin
        assert 'is_valid' in margin
        assert margin['total_notional'] == (500*100 + 800*50)
        assert margin['is_valid']  # Deve ser válido com 25% de margem


class TestIntegration:
    """Testes de integração do sistema completo"""
    
    def test_full_pipeline(self, sample_prices):
        """Testa pipeline completo do sistema"""
        df_a, df_b = sample_prices
        
        # 1. Obter log prices
        log_a = np.log(df_a['price'])
        log_b = np.log(df_b['price'])
        
        # 2. Calcular correlação e cointegração
        corr, pval = StatisticalTests.calculate_correlation(df_a['price'], df_b['price'])
        assert corr > 0.5
        
        # 3. Calcular hedge ratio
        beta, alpha = StatisticalTests.calculate_hedge_ratio(log_a, log_b)
        assert beta > 0
        
        # 4. Calcular spread
        calc = SpreadCalculator(log_a, log_b, beta)
        metrics = calc.calculate_all_metrics(lookback=20)
        assert 'zscore' in metrics.columns
        
        # 5. Gerar sinais
        sig_gen = TradingSignals()
        signals, counts = sig_gen.generate_signals(metrics['zscore'])
        assert len(signals) == len(metrics)
        
        # 6. Gerenciar risco
        rm = RiskManager(account_size=100000)
        pos_size = rm.calculate_position_size(
            df_a['price'].iloc[-1],
            df_b['price'].iloc[-1],
            metrics['zscore'].iloc[-1],
            beta
        )
        assert pos_size['position_a'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
