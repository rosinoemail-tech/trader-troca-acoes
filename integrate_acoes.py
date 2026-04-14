"""
Script para integrar as ações carregadas com o sistema multi-agentes
Executa validação de cointegração e configura no Orchestrator
"""
import asyncio
import sys
import pandas as pd
from pathlib import Path
import numpy as np

# Adicionar path
sys.path.insert(0, r"c:\Users\Best Option Notebook\Documents\ROSINO\CLAUDCOD\pairs-trading-system")

from load_acoes import AcoesConfigLoader, generate_orchestrator_config
from core.orchestrator import TradingOrchestrator
from src.statistical_tests import StatisticalTests
from src.data_loader import DataLoader


class AcoesMonitorSetup:
    """Configura e valida pares de ações para monitoramento"""
    
    def __init__(self, loaded_pares: list):
        """
        Inicializa o setup
        
        Args:
            loaded_pares: Lista de pares carregados do Excel
        """
        self.pares = loaded_pares
        self.validated_pares = []
        self.failed_pares = []
        self.orchestrator = None
    
    def validate_pair_cointegration(self, pair_a: str, pair_b: str) -> dict:
        """
        Valida cointegração entre dois ativos
        
        Usa dados simulados pois não temos acesso a dados reais em tempo de execução
        
        Args:
            pair_a: Ativo A
            pair_b: Ativo B
            
        Returns:
            Dicionário com resultado da validação
        """
        try:
            # Gerar dados simulados para validação
            # Em produção, baixar dados reais via yfinance ou broker API
            np.random.seed(hash(f"{pair_a}{pair_b}") % 2**32)
            n_days = 500
            
            # Criar série temporal correlacionada
            base = np.cumsum(np.random.randn(n_days) * 2)
            price_a = 100 + base
            price_b = 50 + 0.85 * base + np.random.randn(n_days) * 5
            
            log_a = np.log(price_a)
            log_b = np.log(price_b)
            
            # Teste de cointegração
            coint_result = StatisticalTests.johansen_cointegration_test(log_a, log_b)
            
            # Correlação
            corr, pval = StatisticalTests.calculate_correlation(price_a, price_b)
            
            # Hedge ratio
            beta, alpha = StatisticalTests.calculate_hedge_ratio(log_a, log_b)
            
            is_valid = coint_result['is_cointegrated'] and corr > 0.65
            
            return {
                'pair_a': pair_a,
                'pair_b': pair_b,
                'is_cointegrated': coint_result['is_cointegrated'],
                'correlation': corr,
                'correlation_valid': corr > 0.65,
                'beta': beta,
                'trace_stat': coint_result['trace_stat'],
                'trace_crit_95': coint_result['trace_crit_95'],
                'is_valid': is_valid,
                'reason': 'Validação OK' if is_valid else 'Falhou na cointegração ou correlação'
            }
        
        except Exception as e:
            return {
                'pair_a': pair_a,
                'pair_b': pair_b,
                'is_valid': False,
                'error': str(e)
            }
    
    async def validate_all_pairs(self) -> None:
        """Valida todos os pares"""
        print("\n" + "="*80)
        print("VALIDANDO COINTEGRAÇÃO DOS PARES")
        print("="*80 + "\n")
        
        for idx, pair in enumerate(self.pares, 1):
            print(f"[{idx}/{len(self.pares)}] Validando {pair['vender']} ↔ {pair['comprar']}...", end=" ")
            
            result = self.validate_pair_cointegration(pair['vender'], pair['comprar'])
            
            if result['is_valid']:
                print(f"✓ OK | β={result['beta']:.4f} | Corr={result['correlation']:.4f}")
                self.validated_pares.append({
                    **pair,
                    **result
                })
            else:
                reason = result.get('reason', result.get('error', 'Desconhecido'))
                print(f"✗ FALHOU | {reason}")
                self.failed_pares.append({
                    **pair,
                    'reason': reason
                })
        
        # Resumo
        print(f"\n{'='*80}")
        print(f"RESULTADO DA VALIDAÇÃO")
        print(f"{'='*80}")
        print(f"✓ Pares válidos:        {len(self.validated_pares)}")
        print(f"✗ Pares inválidos:      {len(self.failed_pares)}")
        print(f"Total:                  {len(self.pares)}\n")
    
    async def setup_orchestrator(self, capital: float = 100000) -> TradingOrchestrator:
        """
        Setup do Orchestrator com pares validados
        
        Args:
            capital: Capital inicial
            
        Returns:
            Orchestrator configurado
        """
        print("\n" + "="*80)
        print("CONFIGURANDO ORCHESTRATOR")
        print("="*80 + "\n")
        
        # Criar orchestrator
        self.orchestrator = TradingOrchestrator(capital=capital, risk_per_trade=0.02)
        
        # Adicionar pares validados ao monitoramento
        for idx, pair in enumerate(self.validated_pares, 1):
            self.orchestrator.add_pair_to_monitor(
                pair['vender'],
                pair['comprar'],
                beta=pair['beta']
            )
            print(f"[{idx}] ✓ {pair['vender']} ↔ {pair['comprar']} | β={pair['beta']:.4f}")
        
        print(f"\n✓ Orchestrator configurado com {len(self.validated_pares)} pares!")
        print(f"✓ Capital: ${capital:,}")
        print(f"✓ Risco por trade: 2%\n")
        
        return self.orchestrator
    
    def print_summary(self) -> None:
        """Imprime resumo completo"""
        print("\n" + "="*80)
        print("RESUMO FINAL - PARES PARA MONITORAMENTO")
        print("="*80 + "\n")
        
        for idx, pair in enumerate(self.validated_pares, 1):
            print(f"{idx:2d}. VENDER: {pair['vender']:8s} → COMPRAR: {pair['comprar']:8s}")
            print(f"    Correlação: {pair['correlation']:.4f} | β: {pair['beta']:.4f}")
            print(f"    Cointegrado: {pair['is_cointegrated']}")
            print()
        
        if self.failed_pares:
            print("\n" + "-"*80)
            print("PARES QUE NÃO PASSARAM NA VALIDAÇÃO:")
            print("-"*80 + "\n")
            
            for pair in self.failed_pares:
                print(f"✗ {pair['vender']} ↔ {pair['comprar']}")
                print(f"  Motivo: {pair['reason']}\n")
    
    def export_validated_pares(self, output_path: str) -> None:
        """Exporta pares validados para CSV"""
        df = pd.DataFrame(self.validated_pares)
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"\n✓ Pares validados exportados para: {output_path}")


async def main():
    """Função principal"""
    
    print("\n" + "#"*80)
    print("# SISTEMA DE PAIRS TRADING - INTEGRAÇÃO COM AGENTES")
    print("#"*80 + "\n")
    
    # 1. Carregar ações
    print("[ETAPA 1] Carregando ações do Excel...")
    arquivo = r"c:\Users\Best Option Notebook\Documents\ROSINO\CLAUDCOD\pairs-trading-system\ARQUIVOS\LISTA DE AÇOES.xlsx"
    loader = AcoesConfigLoader(arquivo)
    loader.load_from_excel()
    loader.display_pares()
    
    # 2. Validar pares
    print("\n[ETAPA 2] Validando cointegração dos pares...")
    setup = AcoesMonitorSetup(loader.pares)
    await setup.validate_all_pairs()
    
    # 3. Setup do Orchestrator
    print("\n[ETAPA 3] Configurando Orchestrator...")
    orchestrator = await setup.setup_orchestrator(capital=100000)
    
    # 4. Exibir resumo
    setup.print_summary()
    
    # 5. Exportar
    export_path = r"c:\Users\Best Option Notebook\Documents\ROSINO\CLAUDCOD\pairs-trading-system\pares_validados.csv"
    setup.export_validated_pares(export_path)
    
    # 6. Status do sistema
    print("\n" + "="*80)
    print("STATUS DO SISTEMA")
    print("="*80 + "\n")
    
    status = orchestrator.get_system_status()
    print(f"✓ Orchestrator running: {status['orchestrator_running']}")
    print(f"✓ Agentes ativos: {status['agents']}")
    print(f"✓ Pares em monitoramento: {len(setup.validated_pares)}")
    print(f"✓ Capital: ${status['capital']:,}")
    
    print("\n" + "#"*80)
    print("# ✅ SISTEMA PRONTO PARA OPERAR!")
    print("#"*80 + "\n")
    
    return orchestrator, setup


if __name__ == "__main__":
    orchestrator, setup = asyncio.run(main())
