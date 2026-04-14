"""
Script para carregar e configurar pares de ações do arquivo LISTA DE AÇOES.xlsx
e integrar com o sistema multi-agentes de pairs trading
"""
import pandas as pd
from pathlib import Path
import json


class AcoesConfigLoader:
    """Carrega configuração de ações do arquivo Excel"""
    
    def __init__(self, filepath: str):
        """
        Inicializa o carregador
        
        Args:
            filepath: Caminho do arquivo LISTA DE AÇOES.xlsx
        """
        self.filepath = filepath
        self.pares = []
        self.df = None
    
    def load_from_excel(self) -> list:
        """
        Carrega pares de ações do arquivo Excel
        
        Returns:
            Lista de pares configurados
        """
        try:
            # Ler o arquivo Excel
            df = pd.read_excel(self.filepath)
            self.df = df
            
            # Renomear colunas para facilitar
            df.columns = ['vender', 'comprar']
            
            print(f"\n✓ Arquivo carregado: {Path(self.filepath).name}")
            print(f"✓ Total de linhas: {len(df)}")
            
            # Processar pares
            for idx, row in df.iterrows():
                ativo_a = str(row['vender']).strip()
                ativo_b = str(row['comprar']).strip()
                
                if ativo_a and ativo_b and ativo_a != 'nan' and ativo_b != 'nan':
                    pair = {
                        'id': idx,
                        'vender': ativo_a,
                        'comprar': ativo_b,
                        'pair_key': f"{ativo_a}_{ativo_b}"
                    }
                    self.pares.append(pair)
            
            print(f"✓ Pares processados: {len(self.pares)}\n")
            
            return self.pares
        
        except FileNotFoundError:
            print(f"✗ Arquivo não encontrado: {filepath}")
            return []
        except Exception as e:
            print(f"✗ Erro ao ler arquivo: {e}")
            return []
    
    def display_pares(self) -> None:
        """Exibe os pares carregados"""
        print("=" * 70)
        print("PARES DE AÇÕES PARA PAIRS TRADING")
        print("=" * 70)
        
        for i, pair in enumerate(self.pares, 1):
            print(f"{i:2d}. VENDER: {pair['vender']:8s} | COMPRAR: {pair['comprar']:8s}")
        
        print(f"\n✓ Total de pares configurados: {len(self.pares)}\n")
    
    def get_unique_ativos(self) -> list:
        """Retorna lista uniqua de ativos"""
        ativos = set()
        for pair in self.pares:
            ativos.add(pair['vender'])
            ativos.add(pair['comprar'])
        return sorted(list(ativos))
    
    def export_to_json(self, output_path: str) -> None:
        """Exporta configuração para JSON"""
        config = {
            'total_pares': len(self.pares),
            'ativos_unicos': len(self.get_unique_ativos()),
            'pares': self.pares
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Configuração exportada para: {output_path}")
    
    def export_to_csv(self, output_path: str) -> None:
        """Exporta configuração para CSV"""
        df = pd.DataFrame(self.pares)
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"✓ Configuração exportada para: {output_path}")


def generate_orchestrator_config(loader: AcoesConfigLoader) -> dict:
    """
    Gera configuração para o Orchestrator
    
    Args:
        loader: Instância do carregador
        
    Returns:
        Dicionário de configuração
    """
    config = {
        'capital': 100000,
        'risk_per_trade': 0.02,
        'monitoring': {
            'check_interval': 60,  # segundos
            'pares_to_monitor': []
        },
        'parameters': {
            'entry_threshold': 2.0,
            'exit_threshold': 0.5,
            'stop_loss': 3.5
        }
    }
    
    # Adicionar pares
    for pair in loader.pares:
        config['monitoring']['pares_to_monitor'].append({
            'pair_a': pair['vender'],
            'pair_b': pair['comprar'],
            'beta': 0.95,  # Valor padrão - será recalculado
            'status': 'pending_cointegration_test'
        })
    
    return config


def main():
    """Função principal"""
    
    print("\n" + "="*70)
    print("SISTEMA DE PAIRS TRADING - CARREGADOR DE AÇÕES")
    print("="*70)
    
    # Caminho do arquivo
    arquivo = r"c:\Users\Best Option Notebook\Documents\ROSINO\CLAUDCOD\pairs-trading-system\ARQUIVOS\LISTA DE AÇOES.xlsx"
    
    # Carregar pares
    loader = AcoesConfigLoader(arquivo)
    loader.load_from_excel()
    
    # Exibir pares
    loader.display_pares()
    
    # Ativos únicos
    ativos = loader.get_unique_ativos()
    print(f"Ativos únicos encontrados: {len(ativos)}")
    print(f"Ativos: {', '.join(ativos)}\n")
    
    # Gerar configuração para Orchestrator
    config = generate_orchestrator_config(loader)
    
    print("Configuração gerada para Orchestrator:")
    print(f"  - Capital: ${config['capital']:,}")
    print(f"  - Risco por trade: {config['risk_per_trade']*100:.1f}%")
    print(f"  - Pares a monitorar: {len(config['monitoring']['pares_to_monitor'])}")
    print(f"  - Intervalo de check: {config['monitoring']['check_interval']}s\n")
    
    # Exportar configurações
    config_path = r"c:\Users\Best Option Notebook\Documents\ROSINO\CLAUDCOD\pairs-trading-system\config_pares.json"
    loader.export_to_json(config_path)
    
    csv_path = r"c:\Users\Best Option Notebook\Documents\ROSINO\CLAUDCOD\pairs-trading-system\pares_configurados.csv"
    loader.export_to_csv(csv_path)
    
    print("\n✓ Sistema pronto para integração com os agentes!")
    print("✓ Próximo passo: Validar cointegração dos pares")
    print("✓ Depois: Configurar no Monitor Agent\n")
    
    return loader, config


if __name__ == "__main__":
    loader, config = main()
