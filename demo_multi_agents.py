"""
DEMO: Sistema Completo de Múltiplos Agentes para Pairs Trading
Demonstra como usar todos os 4 agentes coordenados
"""
import asyncio
import logging
import sys
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)

from core.orchestrator import TradingOrchestrator
from src.statistical_tests import StatisticalTests
import numpy as np
import pandas as pd


def print_banner(text):
    """Imprime banner formatado"""
    print("\n" + "="*80)
    print(f" {text}")
    print("="*80)


def generate_sample_pair_data(n_days=500):
    """Gera dados de exemplo para demonstração"""
    np.random.seed(42)
    
    dates = pd.date_range(start='2023-01-01', periods=n_days, freq='D')
    
    # Ativo A: movimento de random walk
    price_a = 100 + np.cumsum(np.random.randn(n_days) * 2)
    
    # Ativo B: correlacionado com A
    price_b = 50 + 0.8 * (price_a - 100) + np.cumsum(np.random.randn(n_days) * 1)
    
    # Adicionar períodos de desvinculação (oportunidades)
    price_a[100:110] *= 1.05  # A sobe muito
    price_b[250:260] *= 1.08  # B sobe muito
    
    return dates, price_a, price_b


async def main():
    print_banner("SISTEMA DE MÚLTIPLOS AGENTES PARA PAIRS TRADING")
    
    # ==========================================================================
    # INICIALIZAÇÃO
    # ==========================================================================
    print_banner("ETAPA 1: Inicializar Orchestrator")
    
    orchestrator = TradingOrchestrator(capital=100000, risk_per_trade=0.02)
    print(f"✓ {orchestrator}")
    print(f"✓ {len(orchestrator.event_bus.agents)} agentes registrados:")
    for name, agent in orchestrator.event_bus.agents.items():
        print(f"  - {name}: {agent.agent_type}")
    
    # ==========================================================================
    # PREPARAR DADOS
    # ==========================================================================
    print_banner("ETAPA 2: Preparar Pares de Ativos")
    
    dates, price_a, price_b = generate_sample_pair_data(n_days=500)
    
    print(f"✓ Par de exemplo gerado: 500 dias de dados")
    print(f"  Ativo A: ${price_a[0]:.2f} → ${price_a[-1]:.2f}")
    print(f"  Ativo B: ${price_b[0]:.2f} → ${price_b[-1]:.2f}")
    
    # Calcular estatísticas
    log_price_a = np.log(price_a)
    log_price_b = np.log(price_b)
    
    correlation, pval = StatisticalTests.calculate_correlation(price_a, price_b)
    beta, alpha = StatisticalTests.calculate_hedge_ratio(log_price_a, log_price_b)
    
    print(f"\n📊 Estatísticas do Par:")
    print(f"  Correlação: {correlation:.4f}")
    print(f"  P-value: {pval:.6f}")
    print(f"  Hedge Ratio (β): {beta:.4f}")
    
    # Teste de cointegração
    coint_result = StatisticalTests.johansen_cointegration_test(log_price_a, log_price_b)
    is_cointegrated = coint_result['is_cointegrated']
    print(f"  Cointegração: {'✓ SIM' if is_cointegrated else '✗ NÃO'}")
    
    if not is_cointegrated:
        print("\n⚠️  AVISO: Os ativos não são cointegrados.")
        print("   Sistema pode não funcionar bem. Recomenda-se usar ativos verdadeiramente correlacionados.")
        return
    
    # ==========================================================================
    # ADICIONAR PARES AO MONITORAMENTO
    # ==========================================================================
    print_banner("ETAPA 3: Adicionar Pares ao Monitoramento")
    
    orchestrator.add_pair_to_monitor("AAPL", "MSFT", beta=beta)
    orchestrator.add_pair_to_monitor("GOOGL", "AMZN", beta=0.92)  # Exemplo adicional
    
    print(f"✓ Pares configurados para monitoramento")
    print(f"  Status Monitor: {orchestrator.monitor.get_status()['pairs_watching']} pares")
    
    # ==========================================================================
    # SIMULAR OPERAÇÕES DOS AGENTES
    # ==========================================================================
    print_banner("ETAPA 4: Simular Operações dos Agentes")
    
    # Simular detecção de oportunidade
    print("\n[MONITOR AGENT] Buscando oportunidades de arbitragem...")
    await asyncio.sleep(1)
    
    # Simular uma oportunidade
    opportunity = {
        'pair_key': 'AAPL_MSFT',
        'pair_a': 'AAPL',
        'pair_b': 'MSFT',
        'signal': 'BUY_A_SELL_B',
        'current_price_a': price_a[-1],
        'current_price_b': price_b[-1],
        'zscore': 2.5,
        'spread': 0.05,
        'spread_mean': 0.0,
        'spread_std': 0.02,
        'detected_at': datetime.now().isoformat(),
        'confidence': 92.5
    }
    
    print(f"\n🔔 [MONITOR] Oportunidade detectada!")
    print(f"   Par: {opportunity['pair_key']}")
    print(f"   Sinal: {opportunity['signal']}")
    print(f"   Z-score: {opportunity['zscore']:.2f}")
    print(f"   Confiança: {opportunity['confidence']:.1f}%")
    
    # Validação pelo Expert
    print(f"\n[EXPERT AGENT] Validando oportunidade...")
    await asyncio.sleep(0.5)
    
    is_valid, confidence, rejections = orchestrator.expert.validate_opportunity(
        opportunity,
        {
            'correlation': correlation,
            'volatility': 1.0,
            'cointegration': coint_result['trace_stat']
        }
    )
    
    print(f"   Válida: {'✓ SIM' if is_valid else '✗ NÃO'}")
    print(f"   Confiança: {confidence:.1%}")
    if rejections:
        print(f"   Rejeições: {len(rejections)}")
        for r in rejections:
            print(f"    - {r}")
    
    if not is_valid:
        print(f"\n⚠️  Oportunidade rejeitada pelo Expert. Abortando...")
        return
    
    # Cálculo de tamanho de posição
    print(f"\n[EXECUTOR AGENT] Calculando tamanho de posição...")
    position_size = orchestrator.risk_manager.calculate_position_size(
        opportunity['current_price_a'],
        opportunity['current_price_b'],
        opportunity['zscore'],
        beta=beta
    )
    
    print(f"   Ativo A: {position_size['position_a']:.2f} contratos (${position_size['notional_a']:.2f})")
    print(f"   Ativo B: {position_size['position_b']:.2f} contratos (${position_size['notional_b']:.2f})")
    print(f"   Exposição Total: ${position_size['notional_a'] + position_size['notional_b']:.2f}")
    
    # Validar margem
    margin = orchestrator.risk_manager.check_margin_requirements(
        position_size['position_a'],
        position_size['position_b'],
        opportunity['current_price_a'],
        opportunity['current_price_b']
    )
    
    print(f"   Status Margem: {'✓ OK' if margin['is_valid'] else '✗ INSUFICIENTE'}")
    print(f"   Margem Exigida: {margin['margin_ratio']*100:.2f}% da conta")
    
    if not margin['is_valid']:
        print(f"   ⚠️  Margem insuficiente. Abortando trade...")
        return
    
    # Executar ordens
    print(f"\n[EXECUTOR] Executando par de ordens...")
    orders = await orchestrator.executor.place_pair_orders(opportunity, position_size)
    
    if orders:
        print(f"   ✓ Ordens executadas!")
        for order_key, order in orders.items():
            print(f"    {order_key}: {order.side} {order.quantity:.2f} {order.symbol} @ ${order.price:.2f}")
    else:
        print(f"   ✗ Falha na execução de ordens")
        return
    
    # Registrar em Relatórios
    print(f"\n[REPORTS AGENT] Registrando trade...")
    orchestrator.reports.add_trade({
        'pair_key': opportunity['pair_key'],
        'signal': opportunity['signal'],
        'entry_price_a': opportunity['current_price_a'],
        'entry_price_b': opportunity['current_price_b'],
        'entry_zscore': opportunity['zscore'],
        'pnl': 0  # Será atualizado ao fechar
    })
    
    orchestrator.reports.add_equity_checkpoint(100000 - (position_size['notional_a'] + position_size['notional_b']))
    
    print(f"   ✓ Trade registrado no histórico")
    
    # ==========================================================================
    # SIMULAR FECHAMENTO DE POSIÇÃO
    # ==========================================================================
    print_banner("ETAPA 5: Simular Fechamento de Posição")
    
    print("\n[MONITOR] Monitorando convergência do spread...")
    await asyncio.sleep(1)
    
    # Simular pressão para convergência
    new_price_a = opportunity['current_price_a'] * 0.99
    new_price_b = opportunity['current_price_b'] * 1.01
    new_zscore = 0.3
    
    print(f"   Novo Z-score: {new_zscore:.2f} (convergência detectada!)")
    
    print(f"\n[EXECUTOR] Fechando posição...")
    close_orders = await orchestrator.executor.close_position(
        opportunity['pair_key'],
        new_price_a,
        new_price_b
    )
    
    if close_orders:
        print(f"   ✓ Posição fechada!")
        estimated_pnl = 1250  # P&L estimado
        print(f"   P&L Estimado: ${estimated_pnl:.2f}")
    
    # Registrar resultado no Expert
    orchestrator.expert.record_outcome(
        pair_key=opportunity['pair_key'],
        signal=opportunity['signal'],
        entry_zscore=opportunity['zscore'],
        exit_zscore=new_zscore,
        pnl=estimated_pnl,
        duration_minutes=240
    )
    
    print(f"\n[EXPERT] Outcome registrado para aprendizado histórico")
    
    # ==========================================================================
    # GERAR RELATÓRIOS
    # ==========================================================================
    print_banner("ETAPA 6: Gerar Relatórios")
    
    daily_report = orchestrator.reports.generate_daily_report()
    
    print(f"\n📊 Relatório Diário:")
    print(f"   Total de Trades: {daily_report['statistics']['total_trades']}")
    print(f"   Winning Trades: {daily_report['statistics']['winning_trades']}")
    print(f"   Win Rate: {daily_report['statistics']['win_rate']:.1f}%")
    print(f"   Total P&L: ${daily_report['statistics']['total_pnl']:.2f}")
    print(f"   Profit Factor: {daily_report['statistics']['profit_factor']:.2f}")
    
    # ==========================================================================
    # STATUS DO SISTEMA
    # ==========================================================================
    print_banner("ETAPA 7: Status Completo do Sistema")
    
    system_status = orchestrator.get_system_status()
    
    print(f"\n🤖 MONITOR AGENT:")
    print(f"   Status: {orchestrator.monitor.get_status()['status']}")
    print(f"   Pares Monitorando: {orchestrator.monitor.get_status()['pairs_watching']}")
    print(f"   Oportunidades Encontradas: {orchestrator.monitor.get_status()['opportunities_found']}")
    
    print(f"\n⚙️  EXECUTOR AGENT:")
    print(f"   Status: {orchestrator.executor.get_status()['status']}")
    print(f"   Ordens Pendentes: {orchestrator.executor.get_status()['pending_orders']}")
    print(f"   Opers Executadas: {orchestrator.executor.get_status()['executed_orders']}")
    print(f"   Posições Abertas: {orchestrator.executor.get_status()['open_positions']}")
    
    print(f"\n📈 REPORTS AGENT:")
    print(f"   Status: {orchestrator.reports.get_status()['status']}")
    print(f"   Trades Registrados: {orchestrator.reports.get_status()['trades_recorded']}")
    print(f"   Total P&L: ${orchestrator.reports.get_status()['total_pnl']:.2f}")
    
    print(f"\n🧠 EXPERT AGENT:")
    print(f"   Status: {orchestrator.expert.get_status()['status']}")
    print(f"   Padrões Aprendidos: {orchestrator.expert.get_status()['patterns_learned']}")
    print(f"   Decisões Tomadas: {orchestrator.expert.get_status()['decisions_made']}")
    print(f"   Confiança Média: {orchestrator.expert.get_status()['avg_confidence']:.1%}")
    
    # ==========================================================================
    # DEMO DE FUNCIONALIDADES AVANÇADAS
    # ==========================================================================
    print_banner("ETAPA 8: Funcionalidades Avançadas")
    
    # Análise de spread
    spread_history = [0.01, 0.015, 0.025, 0.02, 0.01, 0.005]
    zscore_history = [-0.5, 0.0, 1.5, 1.0, 0.5, -0.2]
    
    analysis = orchestrator.expert.analyze_spread_behavior(spread_history, zscore_history)
    
    print(f"\n📊 Análise de Spread:")
    print(f"   Tendência: {analysis['spread_trend']}")
    print(f"   Volatilidade: {analysis['volatility']:.4f}")
    print(f"   Autocorrelação: {analysis['autocorrelation']:.4f}")
    print(f"   Probabilidade de Mean Reversion: {analysis['mean_reversion_likelihood']:.1%}")
    
    # Parâmetros de execução otimizados
    exec_params = orchestrator.expert.identify_optimal_execution(
        opportunity,
        {'correlation': correlation, 'volatility': analysis['volatility']}
    )
    
    print(f"\n⚡ Parâmetros Recomendados de Execução:")
    print(f"   Tamanho de Posição: {exec_params['recommended_position_size']:.1%} do calculado")
    print(f"   Slippage Esperado: {exec_params['recommended_slippage']*100:.2f}%")
    print(f"   Timeout: {exec_params['recommended_timeout']}s")
    print(f"   Take Profit em Z-score: {exec_params['take_profit_zscore']:.2f}")
    print(f"   Stop Loss em Z-score: {exec_params['stop_loss_zscore']:.2f}")
    
    # ==========================================================================
    # CONCLUSÃO
    # ==========================================================================
    print_banner("Demonstração Completa - Sistema Multi-Agentes Funcional")
    
    print(f"""
✅ Sistema de Pairs Trading com Multi-Agentes foi demonstrado com sucesso!

Componentes:
  1. Monitor Agent      → Detecta oportunidades em tempo real ✅
  2. Executor Agent     → Executa ordens no broker ✅
  3. Reports Agent      → Gera análise de performance ✅
  4. Expert Agent       → Valida e aprende com histórico ✅

Fluxo de Execução:
  1. Monitor detecta oportunidade (Z-score extremo)
  2. Expert valida a oportunidade
  3. Executor calcula tamanho e executa ordens
  4. Reports registra a operação
  5. Ao convergir, posição é fechada
  6. Expert aprende do resultado para futuras decisões

Próximos Passos:
  → Conectar com API de broker real (Interactive Brokers, Alpaca, etc)
  → Implementar monitoramento contínuo em tempo real
  → Adicionar mais regar de validação
  → Otimizar parâmetros com dados históricos
  → Deploy em produção com failsafes robustos
    """)
    
    print_banner("Fim da Demonstração")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrompida pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
