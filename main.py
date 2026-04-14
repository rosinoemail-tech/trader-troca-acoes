"""
Sistema de Pairs Trading - Arquivo Principal
Exemplo de uso completo do sistema
"""
import pandas as pd
import numpy as np
import sys
from datetime import datetime, timedelta

# Importar módulos do sistema
from src.data_loader import DataLoader
from src.statistical_tests import StatisticalTests
from src.spread_calculator import SpreadCalculator
from src.trading_signals import TradingSignals
from src.risk_management import RiskManager
from src.backtester import Backtest
import config


def generate_sample_data(n_days=500):
    """
    Gera dados de exemplo para demonstração
    Dois ativos altamente correlacionados com desvios temporários
    """
    dates = pd.date_range(start='2023-01-01', periods=n_days, freq='D')
    
    # Ativo A: movimento de random walk
    price_a = 100 + np.cumsum(np.random.randn(n_days) * 2)
    
    # Ativo B: correlacionado com A + componente independente
    price_b = 50 + 0.8 * (price_a - 100) + np.cumsum(np.random.randn(n_days) * 1)
    
    # Adicionar alguns períodos de desvinculação (oportunidades de trading)
    price_a[100:110] *= 1.05  # A sobe muito
    price_b[250:260] *= 1.08  # B sobe muito
    
    df_a = pd.DataFrame({
        'date': dates,
        'price': price_a
    }).set_index('date')
    
    df_b = pd.DataFrame({
        'date': dates,
        'price': price_b
    }).set_index('date')
    
    return df_a, df_b


def print_header(text):
    """Imprime cabeçalho formatado"""
    print("\n" + "="*70)
    print(f" {text}")
    print("="*70)


def main():
    """Função principal que orquestra o sistema de pairs trading"""
    
    print_header("SISTEMA DE PAIRS TRADING - ARBITRAGEM ESTATÍSTICA")
    
    # ============================================================================
    # ETAPA 1: CARREGAR DADOS
    # ============================================================================
    print_header("ETAPA 1: Carregamento de Dados")
    
    print("\n[INFO] Usando dados de exemplo gerados artificialmente...")
    df_a, df_b = generate_sample_data(n_days=500)
    
    print(f"✓ Ativo A: {len(df_a)} períodos | Preço: {df_a['price'].iloc[0]:.2f} → {df_a['price'].iloc[-1]:.2f}")
    print(f"✓ Ativo B: {len(df_b)} períodos | Preço: {df_b['price'].iloc[0]:.2f} → {df_b['price'].iloc[-1]:.2f}")
    
    # ============================================================================
    # ETAPA 2: ANÁLISE ESTATÍSTICA
    # ============================================================================
    print_header("ETAPA 2: Análise Estatística")
    
    log_price_a = DataLoader.get_log_prices(df_a)
    log_price_b = DataLoader.get_log_prices(df_b)
    
    # Correlação
    corr, p_value = StatisticalTests.calculate_correlation(df_a['price'], df_b['price'])
    print(f"\n📊 Correlação de Pearson: {corr:.4f}")
    print(f"   P-value: {p_value:.6f}")
    print(f"   Status: {'✓ ALTAMENTE CORRELACIONADO' if corr > 0.7 else '✗ Correlação insuficiente'}")
    
    # Hedge Ratio
    beta, alpha = StatisticalTests.calculate_hedge_ratio(log_price_a, log_price_b)
    print(f"\n🎯 Hedge Ratio (β): {beta:.4f}")
    print(f"   Interpretação: Para cada $1 de B, vende ${ beta:.4f} de A")
    
    # Teste de Cointegração
    print(f"\n🔍 Teste de Cointegração (Johansen)...")
    coint_result = StatisticalTests.johansen_cointegration_test(log_price_a, log_price_b)
    print(f"   Estatística de Traço: {coint_result['trace_stat']:.4f}")
    print(f"   Valor Crítico (95%): {coint_result['trace_crit_95']:.4f}")
    print(f"   Status: {'✓ COINTEGRADOS (válido para pairs trading)' if coint_result['is_cointegrated'] else '✗ NÃO cointegrados'}")
    
    # ============================================================================
    # ETAPA 3: CÁLCULO DO SPREAD
    # ============================================================================
    print_header("ETAPA 3: Cálculo do Spread")
    
    spread_calc = SpreadCalculator(log_price_a, log_price_b, beta)
    spread_data = spread_calc.calculate_all_metrics(lookback=config.LOOKBACK_WINDOW)
    
    print(f"\n📈 Spread Statistics (últimos 60 dias):")
    print(f"   Média: {spread_data['spread_mean'].iloc[-1]:.6f}")
    print(f"   Desvio Padrão: {spread_data['spread_std'].iloc[-1]:.6f}")
    print(f"   Z-score Atual: {spread_data['zscore'].iloc[-1]:.4f}")
    print(f"   Spread Atual: {spread_data['spread'].iloc[-1]:.6f}")
    
    # ============================================================================
    # ETAPA 4: GERENCIAMENTO DE RISCO
    # ============================================================================
    print_header("ETAPA 4: Cálculo de Tamanhos de Posição")
    
    risk_mgr = RiskManager(account_size=100000, max_risk_per_trade=0.02)
    
    current_price_a = df_a['price'].iloc[-1]
    current_price_b = df_b['price'].iloc[-1]
    current_zscore = spread_data['zscore'].iloc[-1]
    
    pos_sizes = risk_mgr.calculate_position_size(
        current_price_a, current_price_b, current_zscore, beta
    )
    
    print(f"\n💰 Tamanho de Posição (Capital init: $100,000):")
    print(f"   Ativo A: ${pos_sizes['notional_a']:.2f} ({pos_sizes['position_a']:.4f} contratos)")
    print(f"   Ativo B: ${pos_sizes['notional_b']:.2f} ({pos_sizes['position_b']:.4f} contratos)")
    print(f"   Total Notional: ${pos_sizes['notional_a'] + pos_sizes['notional_b']:.2f}")
    
    # Requisitos de margem
    margin = risk_mgr.check_margin_requirements(
        pos_sizes['position_a'], pos_sizes['position_b'],
        current_price_a, current_price_b
    )
    print(f"\n📋 Verificação de Margem:")
    print(f"   Margem Exigida: ${margin['required_margin']:.2f}")
    print(f"   % da Conta: {margin['margin_ratio']*100:.2f}%")
    print(f"   Status: {'✓ Válido' if margin['is_valid'] else '✗ Insuficiente'}")
    
    # ============================================================================
    # ETAPA 5: GERAÇÃO DE SINAIS
    # ============================================================================
    print_header("ETAPA 5: Sinais de Trading")
    
    signal_gen = TradingSignals(
        entry_threshold=config.Z_SCORE_ENTRY_THRESHOLD,
        exit_threshold=config.Z_SCORE_EXIT_THRESHOLD,
        stop_loss_threshold=config.Z_SCORE_STOP_LOSS
    )
    
    signals, signal_count = signal_gen.generate_signals(spread_data['zscore'])
    
    print(f"\n📊 Contagem de Sinais:")
    print(f"   Compra A / Venda B: {signal_count['BUY_A_SELL_B']}")
    print(f"   Venda A / Compra B: {signal_count['SELL_A_BUY_B']}")
    print(f"   Fechos de Posição: {signal_count['CLOSE']}")
    print(f"   Stop Loss Ativados: {signal_count['STOP_LOSS']}")
    
    # ============================================================================
    # ETAPA 6: BACKTESTING
    # ============================================================================
    print_header("ETAPA 6: Backtesting da Estratégia")
    
    backtest = Backtest(
        price_a=df_a['price'],
        price_b=df_b['price'],
        beta=beta,
        capital=100000,
        risk_per_trade=0.02
    )
    
    print("\n[INFO] Executando backtest (msgs de trade abaixo)...\n")
    results = backtest.run(lookback=config.LOOKBACK_WINDOW)
    
    # ============================================================================
    # ETAPA 7: RELATÓRIO DE RESULTADOS
    # ============================================================================
    print_header("ETAPA 7: Resultados do Backtest")
    
    print(f"\n📊 PERFORMANCE GERAL:")
    print(f"   Capital Inicial: $100,000.00")
    print(f"   Capital Final: ${results['final_equity']:.2f}")
    print(f"   P&L Total: ${results['total_pnl']:.2f}")
    print(f"   P&L %: {results['total_pnl_pct']:.2f}%")
    
    print(f"\n📈 ESTATÍSTICAS DE TRADES:")
    print(f"   Total de Trades: {results['total_trades']}")
    print(f"   Trades Vencedores: {results['winning_trades']}")
    print(f"   Trades Perdedores: {results['losing_trades']}")
    print(f"   Taxa de Acerto: {results['win_rate']:.2f}%")
    print(f"   P&L Médio por Trade: ${results['avg_trade_pnl']:.2f}")
    
    print(f"\n⚠️  MÉTRICAS DE RISCO:")
    print(f"   Drawdown Máximo: {results['max_drawdown']:.2f}%")
    print(f"   Sharpe Ratio: {results['sharpe_ratio']:.4f}")
    
    # ============================================================================
    # DETALHES DE TRADES
    # ============================================================================
    print_header("ETAPA 8: Detalhe de Trades Realizados")
    
    if backtest.trades:
        trades_df = pd.DataFrame(backtest.trades)
        print(f"\n Total de {len(trades_df)} trades executados:\n")
        
        for idx, trade in trades_df.iterrows():
            print(f"Trade #{idx+1}:")
            print(f"  Entrada: {trade['entry_date'].strftime('%Y-%m-%d')} (Z={trade['entry_zscore']:.2f})")
            print(f"  Saída:   {trade['exit_date'].strftime('%Y-%m-%d')} (Z={trade['exit_zscore']:.2f})")
            print(f"  Tipo:    {trade['type']} - {trade['exit_type']}")
            print(f"  P&L:     ${trade['pnl']:.2f} ({trade['pnl_pct']:.2f}%)")
            print()
    else:
        print("\n⚠️  Nenhum trade foi executado neste período.")
    
    print_header("Fim da Execução")
    print("\n✓ Sistema de Pairs Trading executado com sucesso!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        import traceback
        traceback.print_exc()
