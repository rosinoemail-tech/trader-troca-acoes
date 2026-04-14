"""
AGENTE EXECUTOR - Executa operações de compra e venda em plataforma
Funcionalidade: Integra com broker/plataforma para executar trades
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import logging

from core.agent_base import Agent, Message, MessagePriority, AgentStatus
import config


class OrderStatus(Enum):
    """Status de uma ordem"""
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Order:
    """Representa uma ordem de trading"""
    
    def __init__(self,
                 symbol: str,
                 side: str,  # BUY ou SELL
                 quantity: float,
                 price: float,
                 order_type: str = "LIMIT"):
        self.id = f"{symbol}_{datetime.now().timestamp()}"
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.price = price
        self.order_type = order_type
        self.status = OrderStatus.PENDING
        self.filled_quantity = 0
        self.created_at = datetime.now()
        self.executed_at = None
        self.execution_price = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'price': self.price,
            'order_type': self.order_type,
            'status': self.status.value,
            'filled_quantity': self.filled_quantity,
            'created_at': self.created_at.isoformat(),
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'execution_price': self.execution_price
        }


class ExecutorAgent(Agent):
    """Agente responsável por executar operações no mercado"""
    
    def __init__(self,
                 name: str = "ExecutorAgent",
                 broker_api=None,
                 max_order_size: float = config.MAX_POSITION_SIZE):
        """
        Inicializa agente executor
        
        Args:
            name: Nome do agente
            broker_api: API do broker para execução
            max_order_size: Tamanho máximo de ordem permitido
        """
        super().__init__(
            name=name,
            agent_type="EXECUTOR",
            description="Executa operações de trading em plataforma"
        )
        
        self.broker_api = broker_api
        self.max_order_size = max_order_size
        
        # Controle de ordens
        self.pending_orders: Dict[str, Order] = {}
        self.executed_orders: List[Order] = []
        self.rejected_orders: List[Order] = []
        
        # Posições abertas
        self.open_positions: Dict[str, Dict[str, Any]] = {}
        
        # Riscos
        self.total_notional_exposure = 0
        self.max_total_exposure = 500000  # $500k máximo
        
        self.logger = logging.getLogger(f"Agent_{name}")
    
    async def validate_order(self, order: Order) -> tuple[bool, Optional[str]]:
        """
        Valida uma ordem antes da execução
        
        Args:
            order: Ordem a validar
            
        Returns:
            (válida, mensagem_erro)
        """
        # Validar tamanho
        if order.quantity > self.max_order_size:
            return False, f"Quantidade {order.quantity} excede máximo {self.max_order_size}"
        
        # Validar exposição
        notional = order.quantity * order.price
        if self.total_notional_exposure + notional > self.max_total_exposure:
            return False, f"Exposição total excederia limite de ${self.max_total_exposure}"
        
        # Validar preço
        if order.price <= 0:
            return False, "Preço deve ser positivo"
        
        return True, None
    
    async def execute_order(self, order: Order) -> bool:
        """
        Executa uma ordem
        
        Args:
            order: Ordem a executar
            
        Returns:
            True se sucesso, False caso contrário
        """
        # Validar
        is_valid, error_msg = await self.validate_order(order)
        if not is_valid:
            self.logger.warning(f"✗ Ordem rejeitada: {error_msg}")
            order.status = OrderStatus.REJECTED
            self.rejected_orders.append(order)
            return False
        
        try:
            # Se tem broker real, executar
            if self.broker_api:
                result = await asyncio.to_thread(
                    self.broker_api.place_order,
                    order.symbol,
                    order.side,
                    order.quantity,
                    order.price,
                    order.order_type
                )
                order.id = result.get('order_id', order.id)
                order.status = OrderStatus.OPEN
            else:
                # Simulação
                order.status = OrderStatus.FILLED
                order.filled_quantity = order.quantity
                order.executed_at = datetime.now()
                order.execution_price = order.price
            
            self.pending_orders[order.id] = order
            
            # Atualizar exposição
            notional = order.quantity * order.price
            if order.side == "BUY":
                self.total_notional_exposure += notional
            
            self.logger.info(
                f"✓ Ordem executada: {order.side} {order.quantity} {order.symbol} "
                f"@ ${order.price:.2f}"
            )
            
            return True
        
        except Exception as e:
            self.logger.error(f"✗ Erro ao executar ordem: {e}")
            order.status = OrderStatus.REJECTED
            self.rejected_orders.append(order)
            return False
    
    async def place_pair_orders(self,
                               opportunity: Dict[str, Any],
                               position_size: Dict[str, Any]) -> Dict[str, Order]:
        """
        Executa par de ordens (compra um, vende outro)
        
        Args:
            opportunity: Oportunidade detectada
            position_size: Tamanho da posição
            
        Returns:
            Dicionário com ordens criadas {ordem_a: Order, ordem_b: Order}
        """
        orders = {}
        
        try:
            # Determinar lados
            if opportunity['signal'] == 'BUY_A_SELL_B':
                side_a, side_b = 'BUY', 'SELL'
            else:
                side_a, side_b = 'SELL', 'BUY'
            
            # Criar ordens
            order_a = Order(
                symbol=opportunity['pair_a'],
                side=side_a,
                quantity=position_size['position_a'],
                price=opportunity['current_price_a']
            )
            
            order_b = Order(
                symbol=opportunity['pair_b'],
                side=side_b,
                quantity=position_size['position_b'],
                price=opportunity['current_price_b']
            )
            
            # Executar
            success_a = await self.execute_order(order_a)
            success_b = await self.execute_order(order_b)
            
            if success_a and success_b:
                # Registrar como posição aberta
                position_key = opportunity['pair_key']
                self.open_positions[position_key] = {
                    'pair_a': opportunity['pair_a'],
                    'pair_b': opportunity['pair_b'],
                    'signal': opportunity['signal'],
                    'order_a_id': order_a.id,
                    'order_b_id': order_b.id,
                    'entry_price_a': opportunity['current_price_a'],
                    'entry_price_b': opportunity['current_price_b'],
                    'entry_zscore': opportunity['zscore'],
                    'opened_at': datetime.now(),
                    'status': 'OPENED'
                }
                
                orders['order_a'] = order_a
                orders['order_b'] = order_b
                
                self.logger.info(f"📈 Posição aberta: {position_key}")
            
            return orders
        
        except Exception as e:
            self.logger.error(f"✗ Erro ao colocar ordens de par: {e}")
            return {}
    
    async def close_position(self,
                            position_key: str,
                            current_price_a: float,
                            current_price_b: float) -> Dict[str, Order]:
        """
        Fecha uma posição aberta
        
        Args:
            position_key: Chave da posição
            current_price_a: Preço atual A
            current_price_b: Preço atual B
            
        Returns:
            Dicionário com ordens de fecho
        """
        orders = {}
        
        if position_key not in self.open_positions:
            self.logger.warning(f"Posição não encontrada: {position_key}")
            return orders
        
        position = self.open_positions[position_key]
        
        try:
            # Criar ordens de fecho (reverso)
            if position['signal'] == 'BUY_A_SELL_B':
                # Vender A, Comprar B
                side_a, side_b = 'SELL', 'BUY'
            else:
                # Comprar A, Vender B
                side_a, side_b = 'BUY', 'SELL'
            
            # Recuperar quantidade original
            order_a_orig = self.pending_orders.get(position['order_a_id'])
            order_b_orig = self.pending_orders.get(position['order_b_id'])
            
            qty_a = order_a_orig.quantity if order_a_orig else 100
            qty_b = order_b_orig.quantity if order_b_orig else 80
            
            # Criar ordens de fecho
            order_a = Order(
                symbol=position['pair_a'],
                side=side_a,
                quantity=qty_a,
                price=current_price_a
            )
            
            order_b = Order(
                symbol=position['pair_b'],
                side=side_b,
                quantity=qty_b,
                price=current_price_b
            )
            
            # Executar
            await self.execute_order(order_a)
            await self.execute_order(order_b)
            
            # Calcular P&L
            pnl = self._calculate_position_pnl(position, current_price_a, current_price_b)
            
            # Fechar posição
            position['status'] = 'CLOSED'
            position['closed_at'] = datetime.now()
            position['close_price_a'] = current_price_a
            position['close_price_b'] = current_price_b
            position['pnl'] = pnl
            
            orders['order_a'] = order_a
            orders['order_b'] = order_b
            
            self.logger.info(f"📉 Posição fechada: {position_key} | P&L: ${pnl:.2f}")
            
            return orders
        
        except Exception as e:
            self.logger.error(f"✗ Erro ao fechar posição: {e}")
            return {}
    
    def _calculate_position_pnl(self,
                               position: Dict[str, Any],
                               current_price_a: float,
                               current_price_b: float) -> float:
        """Calcula P&L de uma posição"""
        # Implementação simplificada
        price_change_a = current_price_a - position['entry_price_a']
        price_change_b = current_price_b - position['entry_price_b']
        
        # Assumir quantidade padrão
        qty_a = 100
        qty_b = 80
        
        if position['signal'] == 'BUY_A_SELL_B':
            pnl = (price_change_a * qty_a) - (price_change_b * qty_b)
        else:
            pnl = -(price_change_a * qty_a) + (price_change_b * qty_b)
        
        return pnl
    
    async def process_message(self, message: Message) -> Dict[str, Any]:
        """Processa mensagens recebidas"""
        
        if message.message_type == 'place_orders':
            orders = await self.place_pair_orders(
                message.payload['opportunity'],
                message.payload['position_size']
            )
            return {
                'status': 'orders_placed' if orders else 'orders_failed',
                'orders': {k: v.to_dict() for k, v in orders.items()}
            }
        
        elif message.message_type == 'close_position':
            orders = await self.close_position(
                message.payload['position_key'],
                message.payload['current_price_a'],
                message.payload['current_price_b']
            )
            return {
                'status': 'position_closed' if orders else 'close_failed',
                'orders': {k: v.to_dict() for k, v in orders.items()}
            }
        
        elif message.message_type == 'get_positions':
            return {
                'open_positions': self.open_positions,
                'count': len(self.open_positions)
            }
        
        return {'status': 'message_processed'}
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status do agente"""
        return {
            **super().get_metrics(),
            'pending_orders': len(self.pending_orders),
            'executed_orders': len(self.executed_orders),
            'rejected_orders': len(self.rejected_orders),
            'open_positions': len(self.open_positions),
            'total_exposure': f"${self.total_notional_exposure:.2f}",
            'open_positions_list': list(self.open_positions.keys())
        }
