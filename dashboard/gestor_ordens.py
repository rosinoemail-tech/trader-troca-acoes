# ============================================================
# GESTOR DE ORDENS — Execução real no MT5 (B3 / Genial)
# ============================================================

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, time as dtime
import logging
import json
import os

import config_operacoes as cfg
import posicoes as pos

logger = logging.getLogger(__name__)

MAGIC = 234001          # identificador das ordens deste sistema
LOG_FILE = "log_ordens.json"

# Horário de funcionamento da B3
MERCADO_ABRE  = dtime(10, 0)
MERCADO_FECHA = dtime(17, 55)


# ── Mercado aberto? ──────────────────────────────────────────

def mercado_aberto() -> bool:
    agora = datetime.now().time()
    return MERCADO_ABRE <= agora <= MERCADO_FECHA


# ── Saldo da conta ───────────────────────────────────────────

def get_saldo() -> float:
    info = mt5.account_info()
    if info is None:
        return 0.0
    return info.balance

def get_saldo_livre() -> float:
    info = mt5.account_info()
    if info is None:
        return 0.0
    return info.margin_free

def get_info_conta() -> dict:
    info = mt5.account_info()
    if info is None:
        return {}
    return {
        "login":        info.login,
        "nome":         info.name,
        "saldo":        round(info.balance, 2),
        "equity":       round(info.equity, 2),
        "margem_livre": round(info.margin_free, 2),
        "lucro":        round(info.profit, 2),
        "moeda":        info.currency,
    }


# ── Cálculo de quantidade ────────────────────────────────────

def calcular_quantidade(preco_a: float, preco_b: float,
                        capital_por_par: float) -> tuple[int, int]:
    """
    Divide o capital igualmente entre as duas pontas.
    Retorna (qty_a, qty_b) em número inteiro de ações.
    """
    if preco_a <= 0 or preco_b <= 0 or capital_por_par <= 0:
        return 0, 0

    capital_por_ponta = capital_por_par / 2
    qty_a = int(capital_por_ponta / preco_a)
    qty_b = int(capital_por_ponta / preco_b)

    return max(qty_a, 1), max(qty_b, 1)


def calcular_distribuicao(oportunidades: list) -> list:  # noqa: E302
    """
    Dado o saldo e % configurado, distribui capital
    igualmente entre os pares habilitados com oportunidade,
    ordenados do maior Z-score para o menor.

    Retorna lista de dicts com par + qty calculado.
    """
    saldo = get_saldo_livre()
    percentual = cfg.get_percentual()
    capital_total = saldo * (percentual / 100)

    if not oportunidades or capital_total <= 0:
        return []

    capital_por_par = capital_total / len(oportunidades)

    resultado = []
    for op in oportunidades:
        qty_a, qty_b = calcular_quantidade(
            op["preco_a"], op["preco_b"], capital_por_par
        )

        # Aplica limite máximo configurado (0 = sem limite)
        qtd_max = cfg.get_qtd_maxima(op["par_a"], op["par_b"])
        if qtd_max > 0:
            qty_a = min(qty_a, qtd_max)
            qty_b = min(qty_b, qtd_max)

        custo_estimado = (qty_a * op["preco_a"]) + (qty_b * op["preco_b"])
        resultado.append({
            **op,
            "qty_a":           qty_a,
            "qty_b":           qty_b,
            "qtd_max":         qtd_max,
            "capital_alocado": round(custo_estimado, 2),
        })

    return resultado


# ── Envio de ordem ───────────────────────────────────────────

def _enviar_ordem(symbol: str, volume: int,
                  tipo: int, comment: str = "") -> dict:
    """
    Envia ordem a mercado para o símbolo.

    tipo: mt5.ORDER_TYPE_BUY ou mt5.ORDER_TYPE_SELL
    """
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return {"ok": False, "erro": f"Sem tick para {symbol}"}

    price = tick.ask if tipo == mt5.ORDER_TYPE_BUY else tick.bid

    info_sym = mt5.symbol_info(symbol)
    volume_min = info_sym.volume_min if info_sym else 1.0
    volume_real = max(float(volume), volume_min)

    request = {
        "action":      mt5.TRADE_ACTION_DEAL,
        "symbol":      symbol,
        "volume":      volume_real,
        "type":        tipo,
        "price":       price,
        "deviation":   50,
        "magic":       MAGIC,
        "comment":     f"TraderTrocaAcoes {comment}"[:31],
        "type_time":   mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)

    ok = result is not None and result.retcode == mt5.TRADE_RETCODE_DONE
    return {
        "ok":      ok,
        "retcode": result.retcode if result else -1,
        "ticket":  result.order  if (result and ok) else None,
        "volume":  volume_real,
        "price":   price,
        "erro":    "" if ok else mt5.last_error(),
    }


# ── Executar par ─────────────────────────────────────────────

def executar_par(par_a: str, par_b: str, sinal: str,
                 qty_a: int, qty_b: int,
                 setor: str, zscore: float,
                 preco_a: float, preco_b: float,
                 simulacao: bool = True) -> dict:
    """
    Executa as duas pontas de um par (compra + venda).

    COMPRAR_A (Z < -2): BUY par_a  + SELL par_b
    VENDER_A  (Z > +2): SELL par_a + BUY par_b
    """
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    if sinal == "COMPRAR_A":
        tipo_a, tipo_b = mt5.ORDER_TYPE_BUY,  mt5.ORDER_TYPE_SELL
        descricao = f"BUY {par_a} / SELL {par_b}"
    else:
        tipo_a, tipo_b = mt5.ORDER_TYPE_SELL, mt5.ORDER_TYPE_BUY
        descricao = f"SELL {par_a} / BUY {par_b}"

    log = {
        "timestamp":  agora,
        "par_a":      par_a,
        "par_b":      par_b,
        "setor":      setor,
        "sinal":      sinal,
        "descricao":  descricao,
        "zscore":     zscore,
        "qty_a":      qty_a,
        "qty_b":      qty_b,
        "simulacao":  simulacao,
        "resultado_a": None,
        "resultado_b": None,
        "status":     "pendente",
    }

    if simulacao:
        custo = (qty_a * preco_a) + (qty_b * preco_b)
        log["status"] = "simulado"
        log["custo_estimado"] = round(custo, 2)
        logger.info(f"[SIMULAÇÃO] {descricao} | Z={zscore:.3f} | Custo≈R${custo:.2f}")
        _registrar_log(log)
        # Registra posição simulada
        pos.abrir_posicao(par_a, par_b, setor, sinal, zscore, preco_a, preco_b)
        return log

    # ── Execução real ──────────────────────────────────────
    if not mercado_aberto():
        log["status"] = "fora_horario"
        logger.warning(f"Mercado fechado. Ordem não enviada: {descricao}")
        _registrar_log(log)
        return log

    res_a = _enviar_ordem(par_a, qty_a, tipo_a, f"Z={zscore:.2f}")
    res_b = _enviar_ordem(par_b, qty_b, tipo_b, f"Z={zscore:.2f}")

    log["resultado_a"] = res_a
    log["resultado_b"] = res_b
    log["status"] = "executado" if (res_a["ok"] and res_b["ok"]) else "erro"

    if res_a["ok"] and res_b["ok"]:
        logger.info(f"✅ Executado: {descricao} | "
                    f"A ticket={res_a['ticket']} B ticket={res_b['ticket']}")
        pos.abrir_posicao(par_a, par_b, setor, sinal, zscore, preco_a, preco_b)
    else:
        logger.error(f"❌ Erro ao executar {descricao}: A={res_a} B={res_b}")

    _registrar_log(log)
    return log


# ── Fechar par no MT5 ────────────────────────────────────────

def fechar_par_mt5(par_a: str, par_b: str, simulacao: bool = True) -> dict:
    """Fecha posições abertas dos dois símbolos do par."""
    resultados = {}
    for symbol in [par_a, par_b]:
        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            continue
        for p in positions:
            if p.magic != MAGIC:
                continue
            tipo_fechamento = (mt5.ORDER_TYPE_SELL
                               if p.type == mt5.POSITION_TYPE_BUY
                               else mt5.ORDER_TYPE_BUY)
            if not simulacao:
                res = _enviar_ordem(symbol, int(p.volume), tipo_fechamento, "close")
                resultados[symbol] = res
            else:
                resultados[symbol] = {"ok": True, "simulacao": True}
    return resultados


# ── Log de ordens ────────────────────────────────────────────

def _registrar_log(entrada: dict):
    historico = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                historico = json.load(f)
        except Exception:
            pass
    historico.append(entrada)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(historico[-500:], f, ensure_ascii=False, indent=2)


def carregar_log() -> list:
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []
