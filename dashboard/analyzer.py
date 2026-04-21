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
import posicoes as pos
import config_operacoes as cfg_op

LOOKBACK = 60        # dias para janela móvel de Z-score

# Valores lidos dinamicamente do config (editável pelo painel)
def _z_entrada() -> float: return cfg_op.get_z_entrada()
def _z_saida()   -> float: return cfg_op.get_z_saida()
def _z_stop()    -> float: return cfg_op.get_z_stop()

_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORICO_FILE = os.path.join(_DIR, "historico_oportunidades.json")


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
    z_ent = _z_entrada()
    z_sai = _z_saida()

    if zscore_atual > z_ent:
        sinal   = "VENDER_A"
        emoji   = "🔴"
        texto   = f"VENDER {par_a} / COMPRAR {par_b}"
    elif zscore_atual < -z_ent:
        sinal   = "COMPRAR_A"
        emoji   = "🟢"
        texto   = f"COMPRAR {par_a} / VENDER {par_b}"
    elif abs(zscore_atual) > z_sai:
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

        z_atual = dados["zscore_atual"]

        # Oportunidade detectada → salva no histórico
        # (pos.abrir_posicao é chamado pelo gestor.executar_par ao executar)
        if dados["sinal"] in ("VENDER_A", "COMPRAR_A"):
            _salvar_oportunidade(dados)

        # Verifica condições de saída para posições abertas neste par
        abertas = pos.listar_abertas()
        for p in abertas:
            if p["par_a"] != dados["par_a"] or p["par_b"] != dados["par_b"]:
                continue

            quantidade = p.get("quantidade_mt5") or 10
            pl_atual   = pos.calcular_pl(p, dados["preco_a"], dados["preco_b"], quantidade)

            lucro_alvo_pos  = p.get("lucro_alvo") or 0.0
            corr_minima     = cfg_op.get_correlacao_minima()
            correlacao_atual = dados.get("correlacao", 1.0)

            motivo = None

            # 1. Lucro alvo atingido (% do capital alocado na posição)
            if lucro_alvo_pos > 0 and pl_atual >= lucro_alvo_pos:
                motivo = "lucro_alvo"

            # 2. Correlação abaixo do mínimo
            elif corr_minima > 0 and correlacao_atual < corr_minima:
                motivo = "correlacao"

            # 3. Z-score voltou ao neutro (saída normal)
            elif abs(z_atual) <= _z_saida():
                motivo = "zscore"

            if motivo:
                pos.fechar_posicao(
                    pos_id        = p["id"],
                    preco_saida_a = dados["preco_a"],
                    preco_saida_b = dados["preco_b"],
                    zscore_saida  = z_atual,
                    quantidade    = quantidade,
                    motivo        = motivo,
                )

    # Ordena: oportunidades primeiro, depois por |Z| (maior = melhor)
    resultados = sorted(
        resultados,
        key=lambda x: (
            0 if x.get("sinal") in ("VENDER_A", "COMPRAR_A") else 1,
            -abs(x.get("zscore_atual") or 0)
        )
    )

    return resultados


def executar_ciclo(resultados: list):
    """
    Executa ordens com base nos resultados de análise.
    DEVE ser chamada fora de qualquer cache — roda a cada ciclo do painel.
    """
    import logging
    _log = logging.getLogger("analyzer")

    if not cfg_op.is_auto_executar():
        _log.warning("[EXEC] Execução automática DESLIGADA — ative na aba Gestão do painel.")
        return

    import gestor_ordens as gestor

    simulacao = cfg_op.is_simulacao()
    if simulacao:
        _log.warning("[EXEC] Modo SIMULAÇÃO ativo — ordens calculadas mas NÃO enviadas ao MT5. "
                     "Desative 'Modo Simulação' na aba Gestão para operar de verdade.")

    # Filtra oportunidades com par habilitado e sem posição já aberta
    abertas_ids = {(p["par_a"], p["par_b"]) for p in pos.listar_abertas()}

    oportunidades_exec = []
    for r in resultados:
        if r.get("sinal") not in ("VENDER_A", "COMPRAR_A"):
            continue
        par_key = f"{r['par_a']}/{r['par_b']}"
        if not cfg_op.is_par_habilitado(r["par_a"], r["par_b"]):
            _log.info(f"[EXEC] {par_key} — par não habilitado, pulando.")
            continue
        if (r["par_a"], r["par_b"]) in abertas_ids:
            _log.info(f"[EXEC] {par_key} — posição já aberta, pulando.")
            continue
        oportunidades_exec.append(r)

    if oportunidades_exec:
        distribuicao = gestor.calcular_distribuicao(oportunidades_exec)
        for op in distribuicao:
            _log.info(f"[EXEC] Enviando ordem: {op['par_a']}/{op['par_b']} "
                      f"sinal={op['sinal']} qty_a={op['qty_a']} qty_b={op['qty_b']} "
                      f"simulacao={simulacao}")
            gestor.executar_par(
                par_a     = op["par_a"],
                par_b     = op["par_b"],
                sinal     = op["sinal"],
                qty_a     = op["qty_a"],
                qty_b     = op["qty_b"],
                setor     = op.get("setor", ""),
                zscore    = op["zscore_atual"],
                preco_a   = op["preco_a"],
                preco_b   = op["preco_b"],
                simulacao = simulacao,
            )
    else:
        if not simulacao:
            _log.info("[EXEC] Nenhuma oportunidade com par habilitado e sem posição aberta.")

    # Fecha automaticamente posições que atingiram condição de saída
    corr_minima = cfg_op.get_correlacao_minima()

    for r in resultados:
        z    = r.get("zscore_atual") or 0
        corr = r.get("correlacao", 1.0)
        for p in pos.listar_abertas():
            if p["par_a"] != r["par_a"] or p["par_b"] != r["par_b"]:
                continue
            quantidade     = p.get("quantidade_mt5") or 10
            pl_atual       = pos.calcular_pl(p, r["preco_a"], r["preco_b"], quantidade)
            lucro_alvo_pos = p.get("lucro_alvo") or 0.0

            motivo = None
            if lucro_alvo_pos > 0 and pl_atual >= lucro_alvo_pos:
                motivo = "lucro_alvo"
            elif corr_minima > 0 and corr < corr_minima:
                motivo = "correlacao"
            elif abs(z) <= _z_saida():
                motivo = "zscore"

            if motivo:
                _log.info(f"[EXEC] Fechando {r['par_a']}/{r['par_b']} motivo={motivo} pl={pl_atual:.2f} alvo={lucro_alvo_pos:.2f}")
                gestor.fechar_par_mt5(r["par_a"], r["par_b"], simulacao)


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
