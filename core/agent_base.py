"""
Base class para todos os agentes do sistema
"""
from abc import ABC, abstractmethod
from enum import Enum
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import logging


class AgentStatus(Enum):
    """Estados possíveis do agente"""
    IDLE = "idle"
    RUNNING = "running"
    PROCESSING = "processing"
    ERROR = "error"
    PAUSED = "paused"


class MessagePriority(Enum):
    """Prioridades das mensagens"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class Message:
    """Estrutura de mensagem entre agentes"""
    
    def __init__(self, 
                 sender: str,
                 receiver: str,
                 message_type: str,
                 payload: Dict[str, Any],
                 priority: MessagePriority = MessagePriority.NORMAL):
        self.id = f"{sender}_{receiver}_{datetime.now().timestamp()}"
        self.sender = sender
        self.receiver = receiver
        self.message_type = message_type
        self.payload = payload
        self.priority = priority
        self.timestamp = datetime.now()
        self.status = "pending"  # pending, delivered, processed
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte mensagem para dicionário"""
        return {
            'id': self.id,
            'sender': self.sender,
            'receiver': self.receiver,
            'message_type': self.message_type,
            'payload': self.payload,
            'priority': self.priority.name,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status
        }
    
    def __repr__(self) -> str:
        return f"Message(from={self.sender}, to={self.receiver}, type={self.message_type})"


class Agent(ABC):
    """Classe base para todos os agentes"""
    
    def __init__(self, name: str, agent_type: str, description: str = ""):
        self.name = name
        self.agent_type = agent_type
        self.description = description
        self.status = AgentStatus.IDLE
        self.logger = logging.getLogger(f"Agent_{name}")
        self.message_queue: List[Message] = []
        self.processed_messages: List[Message] = []
        self.performance_metrics = {
            'messages_processed': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    @abstractmethod
    async def process_message(self, message: Message) -> Dict[str, Any]:
        """
        Processa uma mensagem recebida
        
        Args:
            message: Mensagem a processar
            
        Returns:
            Resultado do processamento
        """
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Retorna status atual do agente"""
        pass
    
    def add_message(self, message: Message) -> None:
        """Adiciona mensagem à fila"""
        self.message_queue.append(message)
        self.logger.debug(f"Mensagem recebida: {message}")
    
    def get_queued_messages(self) -> List[Message]:
        """Retorna mensagens na fila"""
        return self.message_queue.copy()
    
    def clear_queue(self) -> None:
        """Limpa fila de mensagens"""
        self.message_queue.clear()
    
    def log_message(self, message: Message) -> None:
        """Registra mensagem como processada"""
        message.status = "processed"
        self.processed_messages.append(message)
        self.performance_metrics['messages_processed'] += 1
    
    def log_error(self, error: str) -> None:
        """Registra erro"""
        self.logger.error(error)
        self.performance_metrics['errors'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas de desempenho"""
        uptime = datetime.now() - self.performance_metrics['start_time']
        
        return {
            'agent_name': self.name,
            'agent_type': self.agent_type,
            'status': self.status.value,
            'messages_processed': self.performance_metrics['messages_processed'],
            'errors': self.performance_metrics['errors'],
            'uptime_seconds': uptime.total_seconds(),
            'queue_size': len(self.message_queue)
        }
    
    async def start(self) -> None:
        """Inicia o agente"""
        self.status = AgentStatus.RUNNING
        self.logger.info(f"✓ Agente {self.name} iniciado")
    
    async def stop(self) -> None:
        """Para o agente"""
        self.status = AgentStatus.IDLE
        self.logger.info(f"✓ Agente {self.name} parado")
    
    async def pause(self) -> None:
        """Pausa o agente"""
        self.status = AgentStatus.PAUSED
        self.logger.info(f"⏸ Agente {self.name} pausado")
    
    def __repr__(self) -> str:
        return f"Agent(name={self.name}, type={self.agent_type}, status={self.status.value})"
