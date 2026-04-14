"""
AGENTE EXPERT - Expert em arbitragem com conhecimento histórico
Funcionalidade: Valida operações com análise de histórico e padrões
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import logging
import numpy as np
import pandas as pd

from core.agent_base import Agent, Message, MessagePriority, AgentStatus


class ArbitrationKnowledge:
    """Base de conhecimento histórico de arbitração"""
    
    def __init__(self):
        self.historical_patterns: List[Dict[str, Any]] = []
        self.successful_pairs: Dict[str, Dict[str, Any]] = {}
        self.failed_pairs: Dict[str, List[str]] = {}
        self.market_regimes: List[Dict[str, Any]] = []
    
    def add_pattern(self, pattern: Dict[str, Any]) -> None:
        """Registra um padrão histórico bem-sucedido"""
        self.historical_patterns.append(pattern)
    
    def get_similar_patterns(self, zscore: float, market_context: Dict[str, Any], 
                            limit: int = 5) -> List[Dict[str, Any]]:
        """
        Encontra padrões históricos similares
        
        Args:
            zscore: Z-score da oportunidade
            market_context: Contexto de mercado
            limit: Número máximo de padrões a retornar
            
        Returns:
            Lista de padrões similares
        """
        similar = []
        
        for pattern in self.historical_patterns:
            # Calcular similaridade baseado em Z-score
            z_diff = abs(pattern['zscore'] - zscore)
            
            # Se Z-scores similares
            if z_diff < 0.5:
                similarity = 1.0 - (z_diff / 2.0)
                similar.append({
                    **pattern,
                    'similarity_score': similarity
                })
        
        # Ordenar por similaridade e retornar top N
        similar.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similar[:limit]


class ExpertAgent(Agent):
    """Agente expert em arbitragem de pares"""
    
    def __init__(self, name: str = "ExpertAgent"):
        """
        Inicializa agente expert
        
        Args:
            name: Nome do agente
        """
        super().__init__(
            name=name,
            agent_type="EXPERT",
            description="Expert em arbitragem com conhecimento histórico"
        )
        
        self.knowledge_base = ArbitrationKnowledge()
        self.validation_rules: Dict[str, float] = {
            'min_correlation': 0.7,
            'min_cointegration_score': 0.05,
            'max_zscore_for_entry': 3.5,
            'min_zscore_for_entry': 1.5,
            'max_recent_failures': 3,  # Máximo de falhas recentes
            'success_threshold': 0.6  # Taxa mínima de sucesso
        }
        
        # Histórico de decisões
        self.decisions_history: List[Dict[str, Any]] = []
        self.validation_confidence_scores: Dict[str, float] = {}
        
        self.logger = logging.getLogger(f"Agent_{name}")
    
    def validate_opportunity(self, 
                           opportunity: Dict[str, Any],
                           pair_stats: Dict[str, Any]) -> Tuple[bool, float, List[str]]:
        """
        Valida uma oportunidade com regras de arbitragem
        
        Args:
            opportunity: Oportunidade a validar
            pair_stats: Estatísticas do par
            
        Returns:
            (válida, confiança, motivos_rejeição)
        """
        is_valid = True
        confidence = 1.0
        rejections = []
        
        # Validação 1: Correlação
        correlation = pair_stats.get('correlation', 0)
        if correlation < self.validation_rules['min_correlation']:
            is_valid = False
            rejections.append(
                f"Correlação insuficiente: {correlation:.2f} < {self.validation_rules['min_correlation']}"
            )
            confidence *= 0.5
        
        # Validação 2: Z-Score na range apropriada
        zscore = abs(opportunity['zscore'])
        if zscore < self.validation_rules['min_zscore_for_entry']:
            is_valid = False
            rejections.append(
                f"Z-score insuficiente: {zscore:.2f} < {self.validation_rules['min_zscore_for_entry']}"
            )
            confidence *= 0.3
        
        if zscore > self.validation_rules['max_zscore_for_entry']:
            is_valid = False
            rejections.append(
                f"Z-score extremo: {zscore:.2f} > {self.validation_rules['max_zscore_for_entry']}"
            )
            confidence *= 0.2
        
        # Validação 3: Histórico de sucesso do par
        pair_key = opportunity['pair_key']
        if pair_key in self.knowledge_base.failed_pairs:
            recent_failures = len(self.knowledge_base.failed_pairs[pair_key])
            if recent_failures > self.validation_rules['max_recent_failures']:
                is_valid = False
                rejections.append(
                    f"Muitas falhas recentes no par: {recent_failures}"
                )
                confidence *= 0.1
        
        # Validação 4: Padrões históricos similares
        similar_patterns = self.knowledge_base.get_similar_patterns(
            opportunity['zscore'],
            {'market_vol': pair_stats.get('volatility', 0)}
        )
        
        if similar_patterns:
            # Usar taxa de sucesso dos padrões similares
            successes = sum(1 for p in similar_patterns if p.get('result') == 'success')
            success_rate = successes / len(similar_patterns) if similar_patterns else 0
            
            if success_rate < self.validation_rules['success_threshold']:
                rejections.append(
                    f"Taxa de sucesso baixa em padrões similares: {success_rate:.2%}"
                )
                confidence *= success_rate
            else:
                # Boost de confiança
                confidence *= (1.0 + success_rate * 0.2)
        
        # Normalizar confiança
        confidence = min(confidence, 1.0)
        
        # Logar decisão
        decision = {
            'pair_key': pair_key,
            'zscore': opportunity['zscore'],
            'is_valid': is_valid,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat(),
            'rejections': rejections,
            'similar_patterns': len(similar_patterns)
        }
        self.decisions_history.append(decision)
        
        self.logger.info(
            f"🔍 Validação: {pair_key} | Válida: {is_valid} | "
            f"Confiança: {confidence:.1%} | Rejeitada: {len(rejections) > 0}"
        )
        
        if rejections:
            for rejection in rejections:
                self.logger.warning(f"  ⚠️  {rejection}")
        
        return is_valid, confidence, rejections
    
    def analyze_spread_behavior(self,
                               spread_history: List[float],
                               zscore_history: List[float]) -> Dict[str, Any]:
        """
        Analisa comportamento do spread usando dados históricos
        
        Args:
            spread_history: Histórico de spreads
            zscore_history: Histórico de Z-scores
            
        Returns:
            Análise de comportamento
        """
        spread_arr = np.array(spread_history)
        zscore_arr = np.array(zscore_history)
        
        analysis = {
            'spread_trend': 'unknown',
            'mean_reversion_likelihood': 0,
            'volatility': np.std(spread_arr),
            'skewness': float(pd.Series(spread_arr).skew()),
            'autocorrelation': float(pd.Series(spread_arr).autocorr(lag=1))
        }
        
        # Analisar tendência
        if len(spread_arr) > 10:
            recent = spread_arr[-10:]
            older = spread_arr[-20:-10]
            
            if recent.mean() > older.mean():
                analysis['spread_trend'] = 'increasing'
            elif recent.mean() < older.mean():
                analysis['spread_trend'] = 'decreasing'
            else:
                analysis['spread_trend'] = 'stable'
        
        # Probabilidade de mean reversion
        # Se high skewness e autocorr negativa, maior probabilidade
        if analysis['autocorrelation'] < -0.3:
            analysis['mean_reversion_likelihood'] = 0.8
        elif analysis['skewness'] > 1.0:
            analysis['mean_reversion_likelihood'] = 0.6
        else:
            analysis['mean_reversion_likelihood'] = 0.4
        
        return analysis
    
    def identify_optimal_execution(self,
                                  opportunity: Dict[str, Any],
                                  pair_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identifica parâmetros ótimos de execução
        
        Args:
            opportunity: Oportunidade
            pair_stats: Estatísticas
            
        Returns:
            Recomendações de execução
        """
        # Verificar padrões similares históricos
        similar = self.knowledge_base.get_similar_patterns(opportunity['zscore'], pair_stats)
        
        optimal_execution = {
            'recommended_position_size': 1.0,  # 100% do calculado
            'recommended_slippage': 0.001,     # 0.1%
            'recommended_timeout': 300,        # 5 minutos
            'take_profit_zscore': 0.2,
            'stop_loss_zscore': 3.5,
            'execution_notes': []
        }
        
        # Se há muitos padrões similares bem-sucedidos
        if similar:
            successful = sum(1 for p in similar if p.get('result') == 'success')
            if successful / len(similar) > 0.7:
                optimal_execution['recommended_position_size'] = 1.2  # Aumentar posição
                optimal_execution['execution_notes'].append("Histórico positivo - aumentar posição")
        
        # Ajustar baseado em volatilidade
        vol = pair_stats.get('volatility', 1.0)
        if vol > 2.0:
            optimal_execution['recommended_position_size'] *= 0.7
            optimal_execution['execution_notes'].append("Alta volatilidade - reduzir posição")
        elif vol < 0.5:
            optimal_execution['recommended_position_size'] *= 1.2
            optimal_execution['execution_notes'].append("Baixa volatilidade - aumentar posição")
        
        return optimal_execution
    
    def record_outcome(self,
                      pair_key: str,
                      signal: str,
                      entry_zscore: float,
                      exit_zscore: float,
                      pnl: float,
                      duration_minutes: int) -> None:
        """
        Registra resultado de um trade para aprendizado
        
        Args:
            pair_key: Identificador do par
            signal: Sinal que gerou o trade
            entry_zscore: Z-score na entrada
            exit_zscore: Z-score na saída
            pnl: P&L do trade
            duration_minutes: Duração do trade em minutos
        """
        result = 'success' if pnl > 0 else 'failure'
        
        pattern = {
            'pair_key': pair_key,
            'signal': signal,
            'zscore': entry_zscore,
            'exit_zscore': exit_zscore,
            'pnl': pnl,
            'result': result,
            'duration_minutes': duration_minutes,
            'recorded_at': datetime.now().isoformat()
        }
        
        self.knowledge_base.add_pattern(pattern)
        
        # Atualizar estatísticas de sucesso/falha
        if result == 'success':
            if pair_key not in self.knowledge_base.successful_pairs:
                self.knowledge_base.successful_pairs[pair_key] = {
                    'count': 0,
                    'total_pnl': 0,
                    'avg_zscore': 0
                }
            stats = self.knowledge_base.successful_pairs[pair_key]
            stats['count'] += 1
            stats['total_pnl'] += pnl
            stats['avg_zscore'] = (stats['avg_zscore'] * (stats['count']-1) + entry_zscore) / stats['count']
        else:
            if pair_key not in self.knowledge_base.failed_pairs:
                self.knowledge_base.failed_pairs[pair_key] = []
            self.knowledge_base.failed_pairs[pair_key].append(datetime.now().isoformat())
        
        self.logger.info(
            f"📚 Outcome registrado: {pair_key} | {result} | P&L: ${pnl:.2f} | "
            f"Duração: {duration_minutes}m"
        )
    
    async def process_message(self, message: Message) -> Dict[str, Any]:
        """Processa mensagens recebidas"""
        
        if message.message_type == 'validate_opportunity':
            is_valid, conf, rejections = self.validate_opportunity(
                message.payload['opportunity'],
                message.payload['pair_stats']
            )
            return {
                'is_valid': is_valid,
                'confidence': conf,
                'rejections': rejections
            }
        
        elif message.message_type == 'analyze_spread':
            analysis = self.analyze_spread_behavior(
                message.payload['spread_history'],
                message.payload['zscore_history']
            )
            return analysis
        
        elif message.message_type == 'get_execution_params':
            params = self.identify_optimal_execution(
                message.payload['opportunity'],
                message.payload['pair_stats']
            )
            return params
        
        elif message.message_type == 'record_trade_outcome':
            self.record_outcome(
                message.payload['pair_key'],
                message.payload['signal'],
                message.payload['entry_zscore'],
                message.payload['exit_zscore'],
                message.payload['pnl'],
                message.payload['duration_minutes']
            )
            return {'status': 'outcome_recorded'}
        
        return {'status': 'message_processed'}
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status do agente"""
        return {
            **super().get_metrics(),
            'patterns_learned': len(self.knowledge_base.historical_patterns),
            'successful_pairs': len(self.knowledge_base.successful_pairs),
            'failed_pairs': {k: len(v) for k, v in self.knowledge_base.failed_pairs.items()},
            'decisions_made': len(self.decisions_history),
            'avg_confidence': np.mean([d['confidence'] for d in self.decisions_history]) 
                            if self.decisions_history else 0
        }
