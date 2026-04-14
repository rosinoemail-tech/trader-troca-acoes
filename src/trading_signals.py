"""
Módulo de geração de sinais de trading
"""
import pandas as pd
import numpy as np
from enum import Enum
from typing import Dict, Tuple
import config


class SignalType(Enum):
    """Tipos de sinais de trading"""
    NO_SIGNAL = 0
    BUY_A_SELL_B = 1      # A está baixo (Z negativo), compra A vende B
    SELL_A_BUY_B = -1     # A está alto (Z positivo), vende A compra B
    CLOSE_POSITION = 2    # Fechar posição (convergência)
    STOP_LOSS = 3         # Stop loss ativado


class TradingSignals:
    """Gera sinais de trading baseado em Z-score"""
    
    def __init__(self, entry_threshold: float = config.Z_SCORE_ENTRY_THRESHOLD,
                 exit_threshold: float = config.Z_SCORE_EXIT_THRESHOLD,
                 stop_loss_threshold: float = config.Z_SCORE_STOP_LOSS):
        """
        Inicializa gerador de sinais
        
        Args:
            entry_threshold: Z-score para entrada (|Z| > threshold)
            exit_threshold: Z-score para saída (|Z| < threshold)
            stop_loss_threshold: Z-score para stop loss
        """
        self.entry_threshold = entry_threshold
        self.exit_threshold = exit_threshold
        self.stop_loss_threshold = stop_loss_threshold
        self.current_position = None  # None, 'LONG', 'SHORT'
    
    def generate_signals(self, zscore: pd.Series) -> Tuple[pd.Series, Dict[str, int]]:
        """
        Gera sinais de trading baseado em Z-score
        
        Args:
            zscore: Series com Z-scores
            
        Returns:
            Tupla (signals, trade_count)
        """
        signals = pd.Series(index=zscore.index, dtype=int)
        trade_count = {
            'BUY_A_SELL_B': 0,
            'SELL_A_BUY_B': 0,
            'CLOSE': 0,
            'STOP_LOSS': 0
        }
        
        for i, z in enumerate(zscore):
            if pd.isna(z):
                signals.iloc[i] = SignalType.NO_SIGNAL.value
                continue
            
            # Verificar stop loss primeiro
            if abs(z) > self.stop_loss_threshold:
                signals.iloc[i] = SignalType.STOP_LOSS.value
                trade_count['STOP_LOSS'] += 1
                self.current_position = None
                continue
            
            # Se em posição, fechar se convergência
            if self.current_position is not None and abs(z) < self.exit_threshold:
                signals.iloc[i] = SignalType.CLOSE_POSITION.value
                trade_count['CLOSE'] += 1
                self.current_position = None
                continue
            
            # Sinal de entrada: Z < -2 (A está relativamente barato)
            if z < -self.entry_threshold and self.current_position != 'LONG':
                signals.iloc[i] = SignalType.BUY_A_SELL_B.value
                trade_count['BUY_A_SELL_B'] += 1
                self.current_position = 'LONG'
                continue
            
            # Sinal de entrada: Z > +2 (A está relativamente caro)
            if z > self.entry_threshold and self.current_position != 'SHORT':
                signals.iloc[i] = SignalType.SELL_A_BUY_B.value
                trade_count['SELL_A_BUY_B'] += 1
                self.current_position = 'SHORT'
                continue
            
            signals.iloc[i] = SignalType.NO_SIGNAL.value
        
        return signals, trade_count
    
    def get_signal_description(self, signal_value: int) -> str:
        """Retorna descrição do sinal"""
        try:
            return SignalType(signal_value).name
        except ValueError:
            return "UNKNOWN"
    
    def identify_trades(self, signals: pd.Series) -> pd.DataFrame:
        """
        Identifica trades individuais com entrada e saída
        
        Args:
            signals: Series com sinais
            
        Returns:
            DataFrame com informações de cada trade
        """
        trades = []
        entry_idx = None
        entry_signal = None
        
        for idx, signal in signals.items():
            # Entrada
            if signal in [SignalType.BUY_A_SELL_B.value, SignalType.SELL_A_BUY_B.value]:
                if entry_idx is None:  # Nova entrada
                    entry_idx = idx
                    entry_signal = signal
            
            # Saída
            elif signal in [SignalType.CLOSE_POSITION.value, SignalType.STOP_LOSS.value]:
                if entry_idx is not None:
                    trade_type = "LONG" if entry_signal == SignalType.BUY_A_SELL_B.value else "SHORT"
                    exit_type = "Normal" if signal == SignalType.CLOSE_POSITION.value else "StopLoss"
                    
                    trades.append({
                        'entry_date': entry_idx,
                        'exit_date': idx,
                        'type': trade_type,
                        'exit_type': exit_type
                    })
                    entry_idx = None
                    entry_signal = None
        
        return pd.DataFrame(trades)
