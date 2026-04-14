"""
Módulo de gestão de risco e tamanho de posição
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple
import config


class RiskManager:
    """Gerencia risco e tamanho de posições"""
    
    def __init__(self, 
                 account_size: float = 100000,
                 max_risk_per_trade: float = 0.02,  # 2% máximo por trade
                 transaction_cost: float = config.TRANSACTION_COST):
        """
        Inicializa gerenciador de risco
        
        Args:
            account_size: Tamanho total da conta
            max_risk_per_trade: Risco máximo por trade (% da conta)
            transaction_cost: Custo de transação por operação
        """
        self.account_size = account_size
        self.max_risk_per_trade = max_risk_per_trade
        self.transaction_cost = transaction_cost
        self.max_position_size = config.MAX_POSITION_SIZE
    
    def calculate_position_size(self, 
                               current_price_a: float,
                               current_price_b: float,
                               zscore: float,
                               beta: float) -> Dict[str, float]:
        """
        Calcula o tamanho da posição baseado em risco
        
        Args:
            current_price_a: Preço atual do ativo A
            current_price_b: Preço atual do ativo B
            zscore: Z-score atual para cálculo de distância do stop
            beta: Hedge ratio
            
        Returns:
            Dicionário com tamanho da posição em dólares para cada ativo
        """
        # Risco máximo por trade
        max_risk_amount = self.account_size * self.max_risk_per_trade
        
        # Distância típica do stop loss é de 0.5 a 1.0 Z-score
        typical_stop_distance = 1.0
        
        # Capital alocado para o trade
        capital_per_trade = max_risk_amount / typical_stop_distance
        capital_per_trade = min(capital_per_trade, self.max_position_size / 2)
        
        # Tamanho da posição em número de contratos
        # Mantendo proporção com hedge ratio
        position_size_a = capital_per_trade / current_price_a
        position_size_b = (beta * capital_per_trade) / current_price_b
        
        return {
            'position_a': position_size_a,
            'position_b': position_size_b,
            'notional_a': position_size_a * current_price_a,
            'notional_b': position_size_b * current_price_b
        }
    
    def calculate_effective_cost(self, position_sizes: Dict[str, float]) -> float:
        """
        Calcula custo efetivo da transação com spread
        
        Args:
            position_sizes: Dicionário com tamanho das posições em valor nominal
            
        Returns:
            Custo total em dólares
        """
        total_notional = position_sizes['notional_a'] + position_sizes['notional_b']
        total_cost = total_notional * self.transaction_cost * 2  # 2 transações (entrada + saída)
        
        return total_cost
    
    def calculate_profit_loss_breakeven(self, 
                                       entry_zscore: float,
                                       current_zscore: float,
                                       spread_std: float,
                                       capital_at_risk: float) -> Tuple[float, float]:
        """
        Calcula P&L baseado em mudança de Z-score
        
        Args:
            entry_zscore: Z-score na entrada
            current_zscore: Z-score atual
            spread_std: Desvio padrão do spread
            capital_at_risk: Capital em risco
            
        Returns:
            Tupla (pnl_points, pnl_percentage)
        """
        zscore_change = entry_zscore - current_zscore  # Movimento em direção ao zero
        
        # 1 Z-score = 1 desvio padrão do spread
        spread_movement = zscore_change * spread_std
        
        # P&L aprox = mudança / posição
        pnl_percentage = (spread_movement / abs(entry_zscore * spread_std)) if entry_zscore != 0 else 0
        pnl_amount = capital_at_risk * pnl_percentage
        
        return pnl_amount, pnl_percentage
    
    def check_margin_requirements(self, 
                                 position_a: float,
                                 position_b: float,
                                 price_a: float,
                                 price_b: float,
                                 maintenance_margin: float = 0.25) -> Dict[str, any]:
        """
        Verifica requisitos de margem
        
        Args:
            position_a: Tamanho posição ativo A
            position_b: Tamanho posição ativo B
            price_a: Preço do ativo A
            price_b: Preço do ativo B
            maintenance_margin: Margem mínima exigida (%)
            
        Returns:
            Dicionário com status de margem
        """
        notional_a = abs(position_a) * price_a
        notional_b = abs(position_b) * price_b
        total_notional = notional_a + notional_b
        
        required_margin = total_notional * maintenance_margin
        
        return {
            'total_notional': total_notional,
            'required_margin': required_margin,
            'available_margin': self.account_size,
            'margin_ratio': required_margin / self.account_size if self.account_size > 0 else 0,
            'is_valid': required_margin <= self.account_size
        }
