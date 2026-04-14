"""
Sistema central de evento e orquestração entre agentes
"""
import asyncio
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime
import logging
from enum import Enum

from .agent_base import Agent, Message, MessagePriority


class EventBus:
    """Bus central de eventos para comunicação entre agentes"""
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.message_handlers: Dict[str, List[Callable]] = {}
        self.message_history: List[Message] = []
        self.logger = logging.getLogger("EventBus")
        self.running = False
        self.process_interval = 0.1  # segundos
    
    def register_agent(self, agent: Agent) -> None:
        """Registra um agente no sistema"""
        self.agents[agent.name] = agent
        self.logger.info(f"✓ Agente registrado: {agent.name} ({agent.agent_type})")
    
    def unregister_agent(self, agent_name: str) -> None:
        """Remove um agente do sistema"""
        if agent_name in self.agents:
            del self.agents[agent_name]
            self.logger.info(f"✓ Agente removido: {agent_name}")
    
    def subscribe(self, message_type: str, handler: Callable) -> None:
        """
        Subscreve um handler a um tipo de mensagem
        
        Args:
            message_type: Tipo de mensagem (ex: 'market_update', 'trading_signal')
            handler: Função/callable para processar mensagem
        """
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        
        self.message_handlers[message_type].append(handler)
        self.logger.debug(f"Handler subscrito para: {message_type}")
    
    def unsubscribe(self, message_type: str, handler: Callable) -> None:
        """Remove subscription"""
        if message_type in self.message_handlers:
            self.message_handlers[message_type].remove(handler)
    
    async def publish(self, message: Message) -> None:
        """
        Publica uma mensagem para todos os interessados
        
        Args:
            message: Mensagem a publicar
        """
        self.logger.debug(f"Publicando: {message}")
        
        # Se tem receiver específico, entrega diretamente
        if message.receiver and message.receiver in self.agents:
            self.agents[message.receiver].add_message(message)
        
        # Notifica handlers suscritos
        if message.message_type in self.message_handlers:
            for handler in self.message_handlers[message.message_type]:
                try:
                    await handler(message)
                except Exception as e:
                    self.logger.error(f"Erro no handler: {e}")
        
        # Registra no histórico
        message.status = "delivered"
        self.message_history.append(message)
    
    async def send_message(self, message: Message) -> None:
        """
        Envia uma mensagem ponto-a-ponto
        
        Args:
            message: Mensagem a enviar
        """
        await self.publish(message)
    
    async def broadcast(self, sender: str, message_type: str, payload: Dict[str, Any]) -> None:
        """
        Envia mensagem para todos os agentes
        
        Args:
            sender: Nome do agente remetente
            message_type: Tipo da mensagem
            payload: Dados da mensagem
        """
        msg = Message(sender, "*", message_type, payload, MessagePriority.NORMAL)
        await self.publish(msg)
    
    async def process_messages(self) -> None:
        """Processa mensagens na fila de todos os agentes"""
        for agent_name, agent in self.agents.items():
            messages = agent.get_queued_messages()
            
            for message in messages:
                try:
                    result = await agent.process_message(message)
                    agent.log_message(message)
                    
                    # Se há resultado, publica como novo evento
                    if result:
                        response = Message(
                            agent.name,
                            message.sender,
                            f"{message.message_type}_response",
                            result,
                            message.priority
                        )
                        await self.publish(response)
                
                except Exception as e:
                    agent.log_error(f"Erro ao processar mensagem: {e}")
                    self.logger.error(f"Erro no agente {agent_name}: {e}")
            
            agent.clear_queue()
    
    async def start(self) -> None:
        """Inicia o bus de eventos"""
        self.running = True
        self.logger.info("✓ EventBus iniciado")
        
        # Inicia todos os agentes
        for agent in self.agents.values():
            await agent.start()
        
        # Loop principal
        try:
            while self.running:
                await self.process_messages()
                await asyncio.sleep(self.process_interval)
        except KeyboardInterrupt:
            await self.stop()
    
    async def stop(self) -> None:
        """Para o bus de eventos"""
        self.running = False
        
        # Para todos os agentes
        for agent in self.agents.values():
            await agent.stop()
        
        self.logger.info("✓ EventBus parado")
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status do sistema"""
        return {
            'running': self.running,
            'agents': len(self.agents),
            'agent_statuses': {
                name: agent.get_metrics() 
                for name, agent in self.agents.items()
            },
            'message_history_size': len(self.message_history),
            'message_handlers': {k: len(v) for k, v in self.message_handlers.items()}
        }
    
    def get_messages_history(self, limit: int = 100) -> List[Message]:
        """Retorna histórico de mensagens"""
        return self.message_history[-limit:]
    
    def __repr__(self) -> str:
        return f"EventBus(agents={len(self.agents)}, running={self.running})"
