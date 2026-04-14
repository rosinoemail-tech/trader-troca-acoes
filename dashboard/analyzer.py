# ============================================================
# MOTOR DE ANÁLISE — Z-Score, oportunidades e histórico
# ============================================================

import pandas as pd
import numpy as np
from scipy.stats import linregress
from datetime import datetime
from typing import Optional
import json
import os

import mt5_connector as mt5c

LOOKBACK = 60        # dias para janela móvel de Z-score
Z_ENTRADA = 2.0      # sinal de oportunidade
Z_SAIDA = 0.5        # sinal de fechamento
Z_STOP = 3.5         # stop loss extremo

HISTORICO_FILE = "historico_oportunidades.json"


# ── Cálculo principal ────────────────────────────────────────

def calcular_zscore_par(par_a: str, par_b: str, n_barras: int = 500) -> Optional[dict]:
    """
    Calcula Z-score para um par de ativos.

    Returns:
        dict com zscore_atual, serie_zscore, beta, precos, etc.
        None se não houver dados suficientes.
    """
    df = mt5c.buscar_historico_par(par_a, par_b, n_barras)
    if df is None:
        return None

    log_a = np.log(df[par_a])
    log_b = np.log(df[par_b])

    # Hedge ratio via regressão linear
    slope, intercept, r_val, _, _ = linregress(log_b, log_a)

    # Spread = log(A) - beta * log(B)
    spread = log_a - slope * log_b

    # Z-score com janela móvel
    spread_mean = spread.rolling(LOOKBACK).mean()
    spread_std  = spread.rolling(LOOKBACK).std()
    zscore      = (spread - spread_mean) / spread_std

    zscore_atual = zscore.iloc[-1]

    # Sinal e direção
    if zscore_atual > Z_ENTRADA:
        sinal   = "VENDER_A"
        emoji   = "🔴"
        texto   = f"VENDER {par_a} / COMPRAR {par_b}"
    elif zscore_atual < -Z_ENTRADA:
        sinal   = "COMPRAR_A"
        emoji   = "🟢"
        texto   = f"COMPRAR {par_a} / VENDER {par_b}"
    elif abs(zscore_atual) > Z_SAIDA:
        sinal   = "MONITORANDO"
        emoji   = "🟡"
        texto   = "Aguardando sinal"
    else:
        sinal   = "NEUTRO"
        emoji   = "⚪"
        texto   = "Z-score neutro"

    return {
        "par_a":         par_a,
        "par_b":         par_b,
        "zscore_atual":  round(float(zscore_atual), 4),
        "zscore_serie":  zscore.dropna(),
        "spread_serie":  spread,
        "beta":          round(float(slope), 4),
        "correlacao":    round(float(r_val), 4),
        "preco_a":       float(df[par_a].iloc[-1]),
        "preco_b":       float(df[par_b].iloc[-1]),
        "sinal":         sinal,
        "emoji":         emoji,
        "texto_sinal":   texto,
        "timestamp":     datetime.now().isoformat(),
    }


def analisar_todos_pares(pares: list) -> list:
    """
    Analisa todos os pares e retorna lista ordenada por |Z-score|.

    Args:
        pares: lista de dicts com chaves par_a, par_b, setor

    Returns:
        Lista de resultados ordenada (maiores oportunidades primeiro)
    """
    resultados = []

    for par in pares:
        dados = calcular_zscore_par(par["par_a"], par["par_b"])

        if dados is None:
            resultados.append({
                "par_a":        par["par_a"],
                "par_b":        par["par_b"],
                "setor":        par["setor"],
                "zscore_atual": None,
                "sinal":        "ERRO",
                "emoji":        "❌",
                "texto_sinal":  "Sem dados no MT5",
                "erro":         True,
            })
            continue

        dados["setor"] = par["setor"]
        resultados.append(dados)

        # Salva no histórico se for oportunidade
        if dados["sinal"] in ("VENDER_A", "COMPRAR_A"):
            _salvar_oportunidade(dados)

    # Ordena: oportunidades primeiro, depois por |Z|
    return sorted(
        resultados,
        key=lambda x: (
            0 if x.get("sinal") in ("VENDER_A", "COMPRAR_A") else 1,
            -abs(x.get("zscore_atual") or 0)
        )
    )


# ── Histórico de oportunidades ───────────────────────────────

def _salvar_oportunidade(dados: dict):
    """Persiste oportunidade no arquivo JSON local."""
    historico = _carregar_historico()

    entrada = {
        "data":          dados["timestamp"][:10],
        "hora":          dados["timestamp"][11:16],
        "par":           f"{dados['par_a']}/{dados['par_b']}",
        "setor":         dados.get("setor", ""),
        "zscore":        dados["zscore_atual"],
        "sinal":         dados["sinal"],
        "texto":         dados["texto_sinal"],
        "preco_a":       dados["preco_a"],
        "preco_b":       dados["preco_b"],
        "beta":          dados["beta"],
    }

    # Evita duplicata no mesmo dia para o mesmo par
    chave = f"{entrada['data']}_{entrada['par']}"
    if not any(f"{r['data']}_{r['par']}" == chave for r in historico):
        historico.append(entrada)
        _salvar_historico(historico)


def _carregar_historico() -> list:
    if not os.path.exists(HISTORICO_FILE):
        return []
    try:
        with open(HISTORICO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _salvar_historico(historico: list):
    with open(HISTORICO_FILE, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)


def carregar_historico_df() -> pd.DataFrame:
    """Retorna histórico de oportunidades como DataFrame."""
    historico = _carregar_historico()
    if not historico:
        return pd.DataFrame()
    df = pd.DataFrame(historico)
    df["data"] = pd.to_datetime(df["data"])
    return df.sort_values("data", ascending=False)


def estatisticas_historico() -> dict:
    """Calcula estatísticas gerais do histórico."""
    df = carregar_historico_df()
    if df.empty:
        return {}

    return {
        "total_oportunidades":   len(df),
        "pares_ativos":          df["par"].nunique(),
        "setor_mais_ativo":      df["setor"].value_counts().idxmax() if "setor" in df else "—",
        "zscore_medio":          round(df["zscore"].abs().mean(), 2),
        "zscore_maximo":         round(df["zscore"].abs().max(), 2),
        "oportunidades_por_dia": round(len(df) / max(df["data"].nunique(), 1), 1),
    }
