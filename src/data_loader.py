"""
Módulo de carregamento e preparação de dados
"""
import pandas as pd
import numpy as np
from typing import Tuple


class DataLoader:
    """Carrega e prepara dados históricos de preços"""
    
    @staticmethod
    def load_from_csv(filepath_a: str, filepath_b: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Carrega dados de dois ativos a partir de arquivos CSV
        
        Args:
            filepath_a: Caminho para arquivo do ativo A
            filepath_b: Caminho para arquivo do ativo B
            
        Returns:
            Tupla com DataFrames dos ativos A e B
        """
        df_a = pd.read_csv(filepath_a, parse_dates=['date'], index_col='date')
        df_b = pd.read_csv(filepath_b, parse_dates=['date'], index_col='date')
        
        # Sincronizar índices (manter apenas datas comuns)
        common_dates = df_a.index.intersection(df_b.index)
        df_a = df_a.loc[common_dates].sort_index()
        df_b = df_b.loc[common_dates].sort_index()
        
        return df_a, df_b
    
    @staticmethod
    def load_from_dict(dates: list, prices_a: list, prices_b: list) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Carrega dados a partir de listas de preços
        
        Args:
            dates: Lista de datas
            prices_a: Lista de preços do ativo A
            prices_b: Lista de preços do ativo B
            
        Returns:
            Tupla com DataFrames dos ativos A e B
        """
        df_a = pd.DataFrame({
            'date': dates,
            'price': prices_a
        }).set_index('date')
        
        df_b = pd.DataFrame({
            'date': dates,
            'price': prices_b
        }).set_index('date')
        
        return df_a, df_b
    
    @staticmethod
    def get_log_prices(df: pd.DataFrame) -> pd.Series:
        """
        Retorna logaritmo natural dos preços
        
        Args:
            df: DataFrame com coluna 'price'
            
        Returns:
            Series com log dos preços
        """
        return np.log(df['price'])
