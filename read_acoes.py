"""
Script para ler e exibir o arquivo de ações
"""
import pandas as pd
import sys

try:
    # Ler arquivo Excel
    file_path = r"ARQUIVOS\LISTA DE AÇOES.xlsx"
    df = pd.read_excel(file_path)
    
    print("\n" + "="*80)
    print(" LISTA DE AÇÕES PARA PAIRS TRADING")
    print("="*80 + "\n")
    
    print(f"Total de linhas: {len(df)}")
    print(f"Total de colunas: {len(df.columns)}\n")
    
    print("Colunas encontradas:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i}. {col}")
    
    print("\n" + "-"*80)
    print("DADOS:\n")
    print(df.to_string())
    
    print("\n" + "-"*80)
    print(f"\nResumo estatístico:")
    print(df.describe())
    
except Exception as e:
    print(f"Erro ao ler arquivo: {e}")
    sys.exit(1)
