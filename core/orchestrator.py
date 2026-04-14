"""
ORQUESTRADOR DO SISTEMA - Coordena todos os agentes
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from core.event_bus import EventBus
from core.agent_base import Message, MessagePriority
from agents.monitor_agent import MonitorAgent
from agents.executor_agent import ExecutorAgent
from agents.reports_agent import ReportsAgent
from agents.expert_agent import ExpertAgent
from src.risk_management import RiskManager


class TradingOrchestrator:
    """Orquestra todo o sistema de trading com múltiplos agentes"""
    
    def __init__(self, capital: float = 100000, risk_per_trade: float = 0.02):
        """
        Inicializa o orquestrador
        
        Args:
            capital: Capital disponível
            risk_per_trade: Risco máximo por trade (%)
        """
        # EventBus central
        self.event_bus = EventBus()
        
        # Instanciar agentes
        self.monitor = MonitorAgent(check_interval=60)
        self.executor = ExecutorAgent(max_order_size=50000)
        self.reports = ReportsAgent()
        self.expert = ExpertAgent()
        
        # Registrar agentes
        self.event_bus.register_agent(self.monitor)
        self.event_bus.register_agent(self.executor)
        self.event_bus.register_agent(self.reports)
        self.event_bus.register_agent(self.expert)
        
        # Gerenciador de risco
        self.risk_manager = RiskManager(
            account_size=capital,
            max_risk_per_trade=risk_per_trade
        )
        
        # Estado
        self.capital = capital
        self.running = False
        self.trades_executed = 0
        
        # Logger
        self.logger = logging.getLogger("Orchestrator")
        
        # Configurar subscribers
        self._setup_subscribers()
    
    def _setup_subscribers(self) -> None:
        """Configura handlers de eventos"""
        
        # Quando há uma oportunidade, validar e executar
        self.event_bus.subscribe(
            'trading_opportunity',
            self._handle_opportunity
        )
        
        # Quando uma posição é fechada, registrar
        self.event_bus.subscribe(
            'position_closed',
            self._handle_position_closed
        )
    
    async def _handle_opportunity(self, message: Message) -> None:
        """Handler para novas oportunidades"""
        opportunity = message.payload
        
        self.logger.info(f"🔔 Nova oportunidade detectada: {opportunity['pair_key']}")
        
        # Step 1: Validar com Expert
        validation_msg = Message(
            sender="Orchestrator",
            receiver="ExpertAgent",
            message_type="validate_opportunity",
            payload={
                'opportunity': opportunity,
                'pair_stats': {
                    'correlation': 0.85,  # Em produção, obter estatísticas reais
                    'volatility': 1.0
                }
            },
            priority=MessagePriority.HIGH
        )
        
        await self.event_bus.publish(validation_msg)
        await asyncio.sleep(0.5)  # Dar tempo para processar
        
        # Obter resultado de validação
        expert_messages = [
            m for m in self.expert.processed_messages
            if m.message_type == "validate_opportunity"
        ]
        
        if expert_messages:
            # Assumindo que o agente expert processou
            is_valid = True  # Em produção, obter do resultado real
            confidence = 0.75
            
            if not is_valid:
                self.logger.warning(
                    f"❌ Oportunidade rejeitada pelo Expert: {opportunity['pair_key']}"
                )
                return
            
            # Step 2: Calcular tamanho de posição
            position_size = self.risk_manager.calculate_position_size(
                opportunity['current_price_a'],
                opportunity['current_price_b'],
                opportunity['zscore'],
                beta=1.0  # Em produção, usar beta real
            )
            
            self.logger.info(
                f"📊 Tamanho de posição calculado: "
                f"A=${position_size['notional_a']:.2f}, B=${position_size['notional_b']:.2f}"
            )
            
            # Step 3: Executar ordens via Executor
            execution_msg = Message(
                sender="Orchestrator",
                receiver="ExecutorAgent",
                message_type="place_orders",
                payload={
                    'opportunity': opportunity,
                    'position_size': position_size
                },
                priority=MessagePriority.HIGH
            )
            
            await self.event_bus.publish(execution_msg)
            await asyncio.sleep(0.5)
            
            self.trades_executed += 1
            self.logger.info(f"✅ Trade #{self.trades_executed} executado")
            
            # Step 4: Registrar em Relatórios
            report_msg = Message(
                sender="Orchestrator",
                receiver="ReportsAgent",
                message_type="add_trade",
                payload={
                    'pair_key': opportunity['pair_key'],
                    'symbol': opportunity['pair_a'],
                    'signal': opportunity['signal'],
                    'entry_zscore': opportunity['zscore'],
                    'entry_price_a': opportunity['current_price_a'],
                    'entry_price_b': opportunity['current_price_b'],
                    'position_size_a': position_size['position_a'],
                    'position_size_b': position_size['position_b']
                }
            )
            
            await self.event_bus.publish(report_msg)
    
    async def _handle_position_closed(self, message: Message) -> None:
        """Handler para posições fechadas"""
        position = message.payload
        
        self.logger.info(
            f"📈 Posição fechada: {position['pair_key']} | "
            f"P&L: ${position.get('pnl', 0):.2f}"
        )
        
        # Registrar no Expert para aprendizado
        expert_msg = Message(
            sender="Orchestrator",
            receiver="ExpertAgent",
            message_type="record_trade_outcome",
            payload={
                'pair_key': position['pair_key'],
                'signal': position.get('signal', 'unknown'),
                'entry_zscore': position.get('entry_zscore', 0),
                'exit_zscore': position.get('exit_zscore', 0),
                'pnl': position.get('pnl', 0),
                'duration_minutes': 30  # Exemplo
            }
        )
        
        await self.event_bus.publish(expert_msg)
        
        # Registrar em Relatórios
        report_msg = Message(
            sender="Orchestrator",
            receiver="ReportsAgent",
            message_type="add_trade",
            payload=position
        )
        
        await self.event_bus.publish(report_msg)
    
    def add_pair_to_monitor(self, pair_a: str, pair_b: str, beta: float) -> None:
        """Adiciona um par ao monitoramento"""
        self.monitor.add_pair_to_watch(pair_a, pair_b, beta)
        self.logger.info(f"✓ Par adicionado ao monitoramento: {pair_a}/{pair_b}")
    
    def remove_pair_from_monitor(self, pair_key: str) -> None:
        """Remove um par do monitoramento"""
        self.monitor.remove_pair_from_watch(pair_key)
        self.logger.info(f"✓ Par removido do monitoramento: {pair_key}")
    
    def set_trading_parameters(self,
                              entry_threshold: float,
                              exit_threshold: float,
                              stop_loss: float) -> None:
        """Ajusta parâmetros de trading"""
        import config
        config.Z_SCORE_ENTRY_THRESHOLD = entry_threshold
        config.Z_SCORE_EXIT_THRESHOLD = exit_threshold
        config.Z_SCORE_STOP_LOSS = stop_loss
        self.logger.info(
            f"✓ Parâmetros atualizados: Entry={entry_threshold}, "
            f"Exit={exit_threshold}, SL={stop_loss}"
        )
    
    def pause_all_agents(self) -> None:
        """Pausa todos os agentes"""
        for agent in self.event_bus.agents.values():
            asyncio.create_task(agent.pause())
        self.logger.info("⏸ Todos os agentes pausados")
    
    def resume_all_agents(self) -> None:
        """Resume todos os agentes"""
        for agent in self.event_bus.agents.values():
            if agent.status.value == 'paused':
                asyncio.create_task(agent.start())
        self.logger.info("▶️  Todos os agentes resumidos")
    
    async def start(self) -> None:
        """Inicia o sistema completo"""
        self.running = True
        self.logger.info("🚀 Iniciando Orchestrator...")
        
        await self.event_bus.start()
    
    async def stop(self) -> None:
        """Para o sistema completamente"""
        self.running = False
        await self.event_bus.stop()
        self.logger.info("✓ Orchestrator parado")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Retorna status completo do sistema"""
        status = self.event_bus.get_status()
        status.update({
            'orchestrator_running': self.running,
            'trades_executed': self.trades_executed,
            'capital': self.capital,
            'system_health': 'GOOD' if self.running else 'STOPPED'
        })
        return status
    
    def generate_system_report(self) -> Dict[str, Any]:
        """Gera relatório completo do sistema"""
        return {
            'timestamp': datetime.now().isoformat(),
            'status': self.get_system_status(),
            'monitor_status': self.monitor.get_status(),
            'executor_status': self.executor.get_status(),
            'reports_status': self.reports.get_status(),
            'expert_status': self.expert.get_status()
        }
    
    def __repr__(self) -> str:
        return (
            f"TradingOrchestrator("
            f"agents={len(self.event_bus.agents)}, "
            f"running={self.running}, "
            f"trades={self.trades_executed}"
            f")"
        )
