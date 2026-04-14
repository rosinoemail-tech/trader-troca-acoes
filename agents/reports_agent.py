"""
AGENTE REPORTS - Gera relatórios de performance e análise
Funcionalidade: Analisa trades e gera relatórios de performance
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import json
import numpy as np
import pandas as pd

from core.agent_base import Agent, Message, MessagePriority, AgentStatus


class PerformanceMetrics:
    """Calcula métricas de performance"""
    
    @staticmethod
    def calculate_stats(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcula estatísticas de um conjunto de trades
        
        Args:
            trades: Lista de trades
            
        Returns:
            Dicionário com estatísticas
        """
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'total_pnl': 0,
                'largest_win': 0,
                'largest_loss': 0
            }
        
        trades_df = pd.DataFrame(trades)
        
        winning = trades_df[trades_df['pnl'] > 0]
        losing = trades_df[trades_df['pnl'] < 0]
        
        total_wins = winning['pnl'].sum() if len(winning) > 0 else 0
        total_losses = abs(losing['pnl'].sum()) if len(losing) > 0 else 0
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'win_rate': (len(winning) / len(trades) * 100) if len(trades) > 0 else 0,
            'avg_win': winning['pnl'].mean() if len(winning) > 0 else 0,
            'avg_loss': losing['pnl'].mean() if len(losing) > 0 else 0,
            'profit_factor': total_wins / total_losses if total_losses > 0 else 0,
            'total_pnl': trades_df['pnl'].sum(),
            'largest_win': trades_df['pnl'].max(),
            'largest_loss': trades_df['pnl'].min()
        }
    
    @staticmethod
    def calculate_drawdown(equity_curve: List[float]) -> Dict[str, Any]:
        \"\"\"
        Calcula drawdown da curva de equity
        
        Args:
            equity_curve: Lista de valores de equity
            
        Returns:
            Estatísticas de drawdown
        \"\"\"
        if not equity_curve:
            return {'max_drawdown': 0, 'avg_drawdown': 0, 'duration': 0}
        
        equity = np.array(equity_curve)
        cummax = np.maximum.accumulate(equity)
        drawdown = (equity - cummax) / cummax * 100
        
        return {
            'max_drawdown': drawdown.min(),
            'avg_drawdown': drawdown.mean(),
            'current_drawdown': drawdown[-1],
            'drawdown_duration': np.where(drawdown == drawdown.min())[0][0] if len(equity) > 0 else 0
        }
    
    @staticmethod
    def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
        \"\"\"Calcula Sharpe Ratio\"\"\"
        if not returns or len(returns) < 2:
            return 0
        
        returns_arr = np.array(returns)
        excess_returns = returns_arr - (risk_free_rate / 252)
        
        if np.std(excess_returns) == 0:
            return 0
        
        return (np.mean(excess_returns) / np.std(excess_returns)) * np.sqrt(252)


class ReportsAgent(Agent):
    """Agente responsável por gerar relatórios de performance"""
    
    def __init__(self, name: str = "ReportsAgent"):
        """
        Inicializa agente de relatórios
        
        Args:
            name: Nome do agente
        """
        super().__init__(
            name=name,
            agent_type="REPORTS",
            description="Gera relatórios de performance e análise"
        )
        
        # Histórico de dados
        self.trades_history: List[Dict[str, Any]] = []
        self.equity_curve: List[Dict[str, Any]] = []
        self.daily_stats: List[Dict[str, Any]] = []
        
        # Reportes gerados
        self.generated_reports: Dict[str, Dict[str, Any]] = {}
        
        self.logger = logging.getLogger(f"Agent_{name}")
    
    def add_trade(self, trade: Dict[str, Any]) -> None:
        """Adiciona um trade ao histórico"""
        self.trades_history.append({
            **trade,
            'timestamp': datetime.now().isoformat()
        })
        self.logger.debug(f"Trade registrado: P&L = ${trade.get('pnl', 0):.2f}")
    
    def add_equity_checkpoint(self, equity: float, timestamp: Optional[datetime] = None) -> None:
        """Registra checkpoint de equity"""
        self.equity_curve.append({
            'equity': equity,
            'timestamp': (timestamp or datetime.now()).isoformat()
        })
    
    def generate_daily_report(self) -> Dict[str, Any]:
        """Gera relatório do dia"""
        today = datetime.now().date()
        today_trades = [
            t for t in self.trades_history
            if datetime.fromisoformat(t['timestamp']).date() == today
        ]
        
        stats = PerformanceMetrics.calculate_stats(today_trades)
        
        report = {
            'report_type': 'daily',
            'date': today.isoformat(),
            'generated_at': datetime.now().isoformat(),
            'statistics': stats,
            'trades': today_trades
        }
        
        self.generated_reports[f"daily_{today}"] = report
        
        self.logger.info(
            f"📊 Relatório Diário: {stats['total_trades']} trades | "
            f"P&L: ${stats['total_pnl']:.2f} | Win Rate: {stats['win_rate']:.1f}%"
        )
        
        return report
    
    def generate_weekly_report(self) -> Dict[str, Any]:
        \"\"\"Gera relatório semanal\"\"\"
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        
        weekly_trades = [
            t for t in self.trades_history
            if datetime.fromisoformat(t['timestamp']).date() >= week_start
        ]
        
        stats = PerformanceMetrics.calculate_stats(weekly_trades)
        
        # Equity curve da semana
        equity_values = [e['equity'] for e in self.equity_curve]
        drawdown_stats = PerformanceMetrics.calculate_drawdown(equity_values)
        
        report = {
            'report_type': 'weekly',
            'week_start': week_start.isoformat(),
            'generated_at': datetime.now().isoformat(),
            'statistics': stats,
            'risk_metrics': drawdown_stats,
            'trades': weekly_trades
        }
        
        self.generated_reports[f"weekly_{week_start}"] = report
        
        self.logger.info(
            f"📈 Relatório Semanal: {stats['total_trades']} trades | "
            f"P&L: ${stats['total_pnl']:.2f} | Drawdown Máx: {drawdown_stats['max_drawdown']:.2f}%"
        )
        
        return report
    
    def generate_performance_summary(self) -> Dict[str, Any]:
        \"\"\"Gera resumo geral de performance\"\"\"
        stats = PerformanceMetrics.calculate_stats(self.trades_history)
        
        # Equity curve
        equity_values = [e['equity'] for e in self.equity_curve]
        drawdown_stats = PerformanceMetrics.calculate_drawdown(equity_values)
        
        # Retornos diários
        equity_df = pd.DataFrame(self.equity_curve)
        if len(equity_df) > 1:
            equity_df['timestamp'] = pd.to_datetime(equity_df['timestamp'])
            daily_returns = equity_df.groupby(equity_df['timestamp'].dt.date)['equity'].last().pct_change().dropna()
            sharpe = PerformanceMetrics.calculate_sharpe_ratio(daily_returns.tolist())
        else:
            sharpe = 0
        
        # Por símbolo
        symbols_stats = {}
        symbol_trades = pd.DataFrame(self.trades_history)
        if len(symbol_trades) > 0 and 'symbol' in symbol_trades.columns:
            for symbol in symbol_trades['symbol'].unique():
                sym_trades = symbol_trades[symbol_trades['symbol'] == symbol]
                symbols_stats[symbol] = {
                    'trades': len(sym_trades),
                    'pnl': sym_trades['pnl'].sum(),
                    'win_rate': (sym_trades['pnl'] > 0).sum() / len(sym_trades) * 100
                }
        
        summary = {
            'report_type': 'performance_summary',
            'period_start': self.trades_history[0]['timestamp'] if self.trades_history else None,
            'period_end': datetime.now().isoformat(),
            'generated_at': datetime.now().isoformat(),
            'overall_statistics': stats,
            'risk_metrics': {
                **drawdown_stats,
                'sharpe_ratio': sharpe
            },
            'symbols_performance': symbols_stats,
            'total_equity': equity_values[-1] if equity_values else 0
        }
        
        self.generated_reports['performance_summary'] = summary
        
        return summary
    
    def generate_html_report(self, report_data: Dict[str, Any]) -> str:
        \"\"\"Gera HTML formatado do relatório\"\"\"
        html = f\"\"\"
        <html>
        <head>
            <title>Pairs Trading Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .positive {{ color: green; }}
                .negative {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>Pairs Trading Performance Report</h1>
            <p>Generated: {report_data['generated_at']}</p>
            
            <h2>Overall Statistics</h2>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Total Trades</td><td>{report_data['overall_statistics']['total_trades']}</td></tr>
                <tr><td>Winning Trades</td><td>{report_data['overall_statistics']['winning_trades']}</td></tr>
                <tr><td>Losing Trades</td><td>{report_data['overall_statistics']['losing_trades']}</td></tr>
                <tr><td>Win Rate</td><td>{report_data['overall_statistics']['win_rate']:.2f}%</td></tr>
                <tr><td>Total P&L</td>
                    <td class=\"{'positive' if report_data['overall_statistics']['total_pnl'] > 0 else 'negative'}\">
                        ${report_data['overall_statistics']['total_pnl']:.2f}
                    </td>
                </tr>
            </table>
            
            <h2>Risk Metrics</h2>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Max Drawdown</td><td>{report_data['risk_metrics']['max_drawdown']:.2f}%</td></tr>
                <tr><td>Sharpe Ratio</td><td>{report_data['risk_metrics'].get('sharpe_ratio', 0):.4f}</td></tr>
            </table>
        </body>
        </html>
        \"\"\"
        return html
    
    async def process_message(self, message: Message) -> Dict[str, Any]:
        \"\"\"Processa mensagens recebidas\"\"\"
        
        if message.message_type == 'add_trade':
            self.add_trade(message.payload)
            return {'status': 'trade_recorded'}
        
        elif message.message_type == 'add_equity':
            self.add_equity_checkpoint(message.payload['equity'])
            return {'status': 'equity_recorded'}
        
        elif message.message_type == 'generate_daily_report':
            report = self.generate_daily_report()
            return report
        
        elif message.message_type == 'generate_weekly_report':
            report = self.generate_weekly_report()
            return report
        
        elif message.message_type == 'generate_summary':
            report = self.generate_performance_summary()
            return report
        
        return {'status': 'message_processed'}
    
    def get_status(self) -> Dict[str, Any]:
        \"\"\"Retorna status do agente\"\"\"
        return {
            **super().get_metrics(),
            'trades_recorded': len(self.trades_history),
            'equity_checkpoints': len(self.equity_curve),
            'reports_generated': len(self.generated_reports),
            'total_pnl': sum(t.get('pnl', 0) for t in self.trades_history) if self.trades_history else 0
        }
