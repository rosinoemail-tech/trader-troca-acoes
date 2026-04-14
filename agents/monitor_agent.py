"""
AGENTE MONITOR - Monitora mercado em tempo real e identifica oportunidades
Funcionalidade: Busca pares em tempo real durante horário de pregão
"""
import asyncio
from datetime import datetime, time
from typing import Dict, Any, Optional, List
import logging
import numpy as np
import pandas as pd

from core.agent_base import Agent, Message, MessagePriority, AgentStatus
import config


class MonitorAgent(Agent):
    """Agente responsável por monitorar mercado em tempo real"""
    
    def __init__(self, 
                 name: str = "MonitorAgent",
                 market_data_source=None,
                 check_interval: float = 60.0):
        """
        Inicializa agente monitor
        
        Args:
            name: Nome do agente
            market_data_source: Fonte de dados de mercado (yfinance, API broker, etc)
            check_interval: Intervalo de verificação em segundos
        """
        super().__init__(
            name=name,
            agent_type="MONITOR",
            description="Monitora mercado em tempo real buscando oportunidades"
        )
        
        self.market_data_source = market_data_source
        self.check_interval = check_interval
        
        # Estado do monitor
        self.watching_pairs: Dict[str, Dict[str, Any]] = {}
        self.current_opportunities: List[Dict[str, Any]] = []
        self.market_open = False
        self.last_check = None
        
        # Horário do pregão (ajustar conforme mercado)
        self.market_open_time = time(9, 30)    # 9:30 AM
        self.market_close_time = time(16, 0)   # 4:00 PM
        
        # Histórico para cálculos
        self.price_history: Dict[str, pd.DataFrame] = {}
        
        self.logger = logging.getLogger(f"Agent_{name}")
    
    def add_pair_to_watch(self, pair_a: str, pair_b: str, beta: float) -> None:
        """
        Adiciona um par à lista de monitoramento
        
        Args:
            pair_a: Símbolo do ativo A
            pair_b: Símbolo do ativo B
            beta: Hedge ratio pré-calculado
        """
        pair_key = f"{pair_a}_{pair_b}"
        self.watching_pairs[pair_key] = {
            'pair_a': pair_a,
            'pair_b': pair_b,
            'beta': beta,
            'added_at': datetime.now(),
            'last_spread': 0,
            'last_zscore': 0,
            'signals': []
        }
        self.logger.info(f"✓ Par adicionado ao monitoramento: {pair_key} (β={beta:.4f})")
    
    def remove_pair_from_watch(self, pair_key: str) -> None:
        """Remove par do monitoramento"""
        if pair_key in self.watching_pairs:
            del self.watching_pairs[pair_key]
            self.logger.info(f"✓ Par removido do monitoramento: {pair_key}")
    
    def _is_market_open(self) -> bool:
        """Verifica se o mercado está aberto"""
        now = datetime.now().time()
        is_weekday = datetime.now().weekday() < 5  # Segunda a sexta
        return is_weekday and self.market_open_time <= now <= self.market_close_time
    
    async def _fetch_current_prices(self) -> Dict[str, float]:
        """
        Obtém preços atuais do mercado
        
        Returns:
            Dicionário com {símbolo: preço}
        """
        if not self.market_data_source:
            # Simulação para demo
            return {
                symbol: 100 + np.random.randn() 
                for symbol in self._get_all_symbols()
            }
        
        # Implementar com fonte real
        try:
            prices = await asyncio.to_thread(
                self.market_data_source.get_prices,
                self._get_all_symbols()
            )
            return prices
        except Exception as e:
            self.logger.error(f"Erro ao buscar preços: {e}")
            return {}
    
    def _get_all_symbols(self) -> List[str]:
        """Retorna todos os símbolos sendo monitorados"""
        symbols = set()
        for pair_info in self.watching_pairs.values():
            symbols.add(pair_info['pair_a'])
            symbols.add(pair_info['pair_b'])
        return list(symbols)
    
    def _calculate_spread_metrics(self, 
                                  prices_a: List[float],
                                  prices_b: List[float],
                                  beta: float) -> Dict[str, float]:
        """
        Calcula spread e Z-score
        
        Args:
            prices_a: Histórico de preços A
            prices_b: Histórico de preços B
            beta: Hedge ratio
            
        Returns:
            Dicionário com spread, média, desvio, zscore
        """
        # Log prices
        log_prices_a = np.log(prices_a)
        log_prices_b = np.log(prices_b)
        
        # Spread
        spread = log_prices_a - beta * log_prices_b
        
        # Média e desvio usando janela (últimos 60 períodos)
        window = min(60, len(spread))
        spread_mean = np.mean(spread[-window:])
        spread_std = np.std(spread[-window:])
        
        current_spread = spread[-1]
        
        # Z-score
        if spread_std > 0:
            zscore = (current_spread - spread_mean) / spread_std
        else:
            zscore = 0
        
        return {
            'spread': current_spread,
            'spread_mean': spread_mean,
            'spread_std': spread_std,
            'zscore': zscore,
            'spread_window': spread[-window:].tolist()
        }
    
    def _generate_trading_signals(self, zscore: float) -> Optional[str]:
        """
        Gera sinal de trading baseado em Z-score
        
        Args:
            zscore: Z-score atual
            
        Returns:
            Sinal: 'BUY_A_SELL_B', 'SELL_A_BUY_B', ou None
        """
        if zscore < -config.Z_SCORE_ENTRY_THRESHOLD:
            return 'BUY_A_SELL_B'      # A está desvalorizado
        elif zscore > config.Z_SCORE_ENTRY_THRESHOLD:
            return 'SELL_A_BUY_B'      # A está sobrevalorizado
        return None
    
    async def process_message(self, message: Message) -> Dict[str, Any]:
        """Processa mensagens recebidas"""
        
        if message.message_type == 'add_pair':
            self.add_pair_to_watch(
                message.payload['pair_a'],
                message.payload['pair_b'],
                message.payload['beta']
            )
            return {'status': 'pair_added', 'pair': f"{message.payload['pair_a']}_{message.payload['pair_b']}"}
        
        elif message.message_type == 'remove_pair':
            self.remove_pair_from_watch(message.payload['pair_key'])
            return {'status': 'pair_removed', 'pair': message.payload['pair_key']}
        
        elif message.message_type == 'get_opportunities':
            return {
                'opportunities': self.current_opportunities,
                'count': len(self.current_opportunities)
            }
        
        return {'status': 'message_processed'}
    
    async def scan_for_opportunities(self) -> List[Dict[str, Any]]:
        """
        Faz varredura de pares para identificar oportunidades
        
        Returns:
            Lista com oportunidades encontradas
        """
        opportunities = []
        
        if not self._is_market_open():
            self.logger.debug("Mercado fora do horário")
            return opportunities
        
        # Buscar preços atuais
        prices = await self._fetch_current_prices()
        
        if not prices:
            return opportunities
        
        # Analisar cada par
        for pair_key, pair_info in self.watching_pairs.items():
            pair_a = pair_info['pair_a']
            pair_b = pair_info['pair_b']
            beta = pair_info['beta']
            
            if pair_a not in prices or pair_b not in prices:
                continue
            
            # Simular histórico (em produção, usar dados reais)
            current_price_a = prices[pair_a]
            current_price_b = prices[pair_b]
            
            # Gerar histórico simulado
            prices_a = [current_price_a * (1 + np.random.randn() * 0.01) for _ in range(100)]
            prices_b = [current_price_b * (1 + np.random.randn() * 0.01) for _ in range(100)]
            
            # Calcular métricas
            metrics = self._calculate_spread_metrics(prices_a, prices_b, beta)
            
            # Gerar sinal
            signal = self._generate_trading_signals(metrics['zscore'])
            
            if signal:
                opportunity = {
                    'pair_key': pair_key,
                    'pair_a': pair_a,
                    'pair_b': pair_b,
                    'signal': signal,
                    'current_price_a': current_price_a,
                    'current_price_b': current_price_b,
                    'zscore': metrics['zscore'],
                    'spread': metrics['spread'],
                    'spread_mean': metrics['spread_mean'],
                    'spread_std': metrics['spread_std'],
                    'detected_at': datetime.now().isoformat(),
                    'confidence': min(abs(metrics['zscore']) / config.Z_SCORE_ENTRY_THRESHOLD, 1.0) * 100
                }
                
                opportunities.append(opportunity)
                
                self.logger.info(
                    f"📊 Oportunidade: {pair_key} | {signal} | Z={metrics['zscore']:.2f} | "
                    f"Confiança: {opportunity['confidence']:.1f}%"
                )
        
        self.current_opportunities = opportunities
        return opportunities
    
    async def start_monitoring(self) -> None:
        """Inicia monitoramento contínuo"""
        await self.start()
        
        self.logger.info(f"🚀 Iniciando monitoramento com intervalo de {self.check_interval}s")
        
        try:
            while self.status == AgentStatus.RUNNING:
                # Varrer pares
                opportunities = await self.scan_for_opportunities()
                
                if opportunities:
                    # Publicar oportunidades via evento
                    for opp in opportunities:
                        yield {
                            'type': 'trading_opportunity',
                            'data': opp
                        }
                
                self.last_check = datetime.now()
                await asyncio.sleep(self.check_interval)
        
        except Exception as e:
            self.logger.error(f"✗ Erro no monitoramento: {e}")
            self.status = AgentStatus.ERROR
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status do agente"""
        return {
            **super().get_metrics(),
            'market_open': self._is_market_open(),
            'pairs_watching': len(self.watching_pairs),
            'opportunities_found': len(self.current_opportunities),
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'watching_pairs': list(self.watching_pairs.keys())
        }
