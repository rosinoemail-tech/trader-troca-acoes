"""
Módulo de backtesting da estratégia de pairs trading
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Tuple, List
import config
from .spread_calculator import SpreadCalculator
from .trading_signals import TradingSignals, SignalType
from .risk_management import RiskManager


class Backtest:
    """Executa backtest da estratégia de pairs trading"""
    
    def __init__(self, 
                 price_a: pd.Series,
                 price_b: pd.Series,
                 beta: float,
                 capital: float = 100000,
                 risk_per_trade: float = 0.02):
        """
        Inicializa backtest
        
        Args:
            price_a: Série de preços do ativo A
            price_b: Série de preços do ativo B
            beta: Hedge ratio
            capital: Capital inicial
            risk_per_trade: Risco máximo por trade
        """
        self.price_a = price_a
        self.price_b = price_b
        self.beta = beta
        self.capital = capital
        self.initial_capital = capital
        self.risk_manager = RiskManager(account_size=capital, max_risk_per_trade=risk_per_trade)
        
        # Calculadores
        self.log_price_a = np.log(price_a)
        self.log_price_b = np.log(price_b)
        self.spread_calc = SpreadCalculator(self.log_price_a, self.log_price_b, beta)
        self.signal_gen = TradingSignals()
        
        # Resultados
        self.trades = []
        self.equity_curve = []
        self.daily_metrics = None
    
    def run(self, lookback: int = config.LOOKBACK_WINDOW) -> Dict[str, any]:
        """
        Executa o backtest completo
        
        Args:
            lookback: Período para cálculo de média/desvio
            
        Returns:
            Dicionário com resultados do backtest
        """
        # Calcular métricas
        metrics = self.spread_calc.calculate_all_metrics(lookback)
        
        # Gerar sinais
        signals, signal_count = self.signal_gen.generate_signals(metrics['zscore'])
        
        # Simular trading
        metrics['signal'] = signals
        self.daily_metrics = metrics
        
        # Executar trades
        entry_idx = None
        entry_price_a = None
        entry_price_b = None
        entry_zscore = None
        entry_signal = None
        
        for i in range(len(metrics)):
            date = metrics.index[i]
            signal = signals.iloc[i]
            zscore = metrics['zscore'].iloc[i]
            price_a = self.price_a.iloc[i]
            price_b = self.price_b.iloc[i]
            spread_std = metrics['spread_std'].iloc[i]
            
            # Ignored No signal ou incomplete data
            if pd.isna(zscore) or pd.isna(spread_std) or signal == SignalType.NO_SIGNAL.value:
                self.equity_curve.append({
                    'date': date,
                    'equity': self.capital,
                    'status': 'NO_SIGNAL'
                })
                continue
            
            # ENTRADA
            if signal in [SignalType.BUY_A_SELL_B.value, SignalType.SELL_A_BUY_B.value]:
                if entry_idx is None:
                    entry_idx = i
                    entry_price_a = price_a
                    entry_price_b = price_b
                    entry_zscore = zscore
                    entry_signal = signal
                    
                    # Calcular tamanho posição
                    pos_size = self.risk_manager.calculate_position_size(
                        price_a, price_b, zscore, self.beta
                    )
                    
                    # Calcular custo
                    cost = self.risk_manager.calculate_effective_cost(pos_size)
                    self.capital -= cost
                    
                    signal_type = "LONG" if signal == SignalType.BUY_A_SELL_B.value else "SHORT"
                    print(f"[{date}] ENTRADA {signal_type} | Z={zscore:.2f} | Custo: ${cost:.2f}")
            
            # SAÍDA (fecho ou stop loss)
            elif entry_idx is not None and signal in [SignalType.CLOSE_POSITION.value, SignalType.STOP_LOSS.value]:
                # Calcular P&L
                spread_change = (self.log_price_a.iloc[i] - self.beta * self.log_price_b.iloc[i]) - \
                               (self.log_price_a.iloc[entry_idx] - self.beta * self.log_price_b.iloc[entry_idx])
                
                # P&L aproximado (positivo se Z se move para zero)
                pnl_direction = -1 if entry_signal == SignalType.BUY_A_SELL_B.value else 1
                pnl_approx = pnl_direction * spread_change * self.initial_capital / 100
                
                self.capital += pnl_approx
                
                signal_type = "LONG" if entry_signal == SignalType.BUY_A_SELL_B.value else "SHORT"
                exit_type = "NORMAL" if signal == SignalType.CLOSE_POSITION.value else "STOP_LOSS"
                print(f"[{date}] SAÍDA {exit_type} | {signal_type} | Z={entry_zscore:.2f}→{zscore:.2f} | P&L: ${pnl_approx:.2f}")
                
                self.trades.append({
                    'entry_date': metrics.index[entry_idx],
                    'exit_date': date,
                    'entry_zscore': entry_zscore,
                    'exit_zscore': zscore,
                    'type': signal_type,
                    'exit_type': exit_type,
                    'pnl': pnl_approx,
                    'pnl_pct': pnl_approx / self.initial_capital * 100
                })
                
                entry_idx = None
            
            self.equity_curve.append({
                'date': date,
                'equity': self.capital,
                'zscore': zscore,
                'signal': signal
            })
        
        return self._generate_report()
    
    def _generate_report(self) -> Dict[str, any]:
        """Gera relatório de performance"""
        
        trades_df = pd.DataFrame(self.trades)
        equity_df = pd.DataFrame(self.equity_curve)
        
        if len(trades_df) == 0:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'total_pnl_pct': 0,
                'avg_trade_pnl': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0
            }
        
        # Calcs estatísticas
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] < 0])
        total_trades = len(trades_df)
        
        total_pnl = trades_df['pnl'].sum()
        total_pnl_pct = (self.capital - self.initial_capital) / self.initial_capital * 100
        
        avg_trade_pnl = trades_df['pnl'].mean()
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Drawdown máximo
        if len(equity_df) > 0:
            cummax = equity_df['equity'].cummax()
            drawdown = (equity_df['equity'] - cummax) / cummax
            max_drawdown = drawdown.min() * 100
        else:
            max_drawdown = 0
        
        # Sharpe Ratio
        if len(equity_df) > 1:
            returns = equity_df['equity'].pct_change().dropna()
            sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        else:
            sharpe_ratio = 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'avg_trade_pnl': avg_trade_pnl,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'final_equity': self.capital
        }
