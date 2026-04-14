# ============================================================
# CONECTOR MT5 — Busca dados reais da Genial via MetaTrader5
# ============================================================

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def conectar() -> bool:
    """Inicializa conexão com o MT5 aberto na máquina."""
    if not mt5.initialize():
        erro = mt5.last_error()
        logger.error(f"Falha ao conectar no MT5: {erro}")
        return False
    info = mt5.terminal_info()
    logger.info(f"MT5 conectado: {info.name} | Build {info.build}")
    return True


def desconectar():
    """Encerra conexão com MT5."""
    mt5.shutdown()


def listar_simbolos_disponiveis(filtro: str = "") -> list:
    """Lista todos os símbolos disponíveis no broker (útil para verificar nomes)."""
    simbolos = mt5.symbols_get()
    if simbolos is None:
        return []
    nomes = [s.name for s in simbolos]
    if filtro:
        nomes = [n for n in nomes if filtro.upper() in n.upper()]
    return sorted(nomes)


def verificar_simbolo(symbol: str) -> bool:
    """Verifica se o símbolo existe no MT5."""
    info = mt5.symbol_info(symbol)
    return info is not None


def buscar_historico(symbol: str, n_barras: int = 500) -> pd.DataFrame | None:
    """
    Busca histórico de fechamento diário do símbolo.

    Args:
        symbol: Nome do ativo (ex: VALE3)
        n_barras: Quantidade de dias históricos

    Returns:
        DataFrame com coluna 'close' e índice de datas, ou None se falhar.
    """
    # Habilita o símbolo se não estiver visível
    mt5.symbol_select(symbol, True)

    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, n_barras)

    if rates is None or len(rates) == 0:
        logger.warning(f"Sem dados para {symbol}")
        return None

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    df.index.name = 'data'

    return df[['close']].rename(columns={'close': symbol})


def buscar_preco_atual(symbol: str) -> float | None:
    """
    Retorna o preço mais recente do ativo.

    Returns:
        Preço (last > bid > ask) ou None se falhar.
    """
    mt5.symbol_select(symbol, True)
    tick = mt5.symbol_info_tick(symbol)

    if tick is None:
        logger.warning(f"Sem tick para {symbol}")
        return None

    preco = tick.last if tick.last > 0 else tick.bid
    return preco if preco > 0 else None


def buscar_historico_par(par_a: str, par_b: str, n_barras: int = 500) -> pd.DataFrame | None:
    """
    Busca histórico alinhado de dois ativos.

    Returns:
        DataFrame com colunas [par_a, par_b] nas datas comuns, ou None.
    """
    df_a = buscar_historico(par_a, n_barras)
    df_b = buscar_historico(par_b, n_barras)

    if df_a is None or df_b is None:
        return None

    df = df_a.join(df_b, how='inner').dropna()

    if len(df) < 60:
        logger.warning(f"Dados insuficientes para {par_a}/{par_b}: {len(df)} barras")
        return None

    return df
