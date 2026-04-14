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

# Horário padrão B3 (sobreposto pelos horários configurados no painel)
_MERCADO_ABRE_PADRAO  = dtime(10, 0)
_MERCADO_FECHA_PADRAO = dtime(17, 55)


# ── Mercado aberto? ──────────────────────────────────────────

def mercado_aberto() -> bool:
    """Verifica se está dentro do horário de operação configurado no painel."""
    try:
        h_ini = cfg.get_horario_inicio()   # "HH:MM"
        h_fim = cfg.get_horario_fim()
        hi, mi = map(int, h_ini.split(":"))
        hf, mf = map(int, h_fim.split(":"))
        abre  = dtime(hi, mi)
        fecha = dtime(hf, mf)
    except Exception:
        abre  = _MERCADO_ABRE_PADRAO
        fecha = _MERCADO_FECHA_PADRAO

    agora = datetime.now().time()
    return abre <= agora <= fecha


# ── Saldo da conta ───────────────────────────────────────────

def get_saldo() -> float:
    info = mt5.account_info()
    if info is None:
        return 0.0
    return info.balance

def get_saldo_livre() -> float:
    """
    Retorna o capital disponível para operações.
    Prioridade: capital_manual (se > 0) → margin_free do MT5 → 0
    """
    capital_manual = cfg.get_capital_manual()
    if capital_manual > 0:
        return capital_manual

    info = mt5.account_info()
    if info is None:
        return 0.0
    return info.margin_free if info.margin_free > 0 else 0.0

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


# ── Sincronização com MT5 ────────────────────────────────────

def sincronizar_posicoes_mt5(pares: list) -> dict:
    """
    Sincroniza posicoes.json com as posições reais abertas no MT5.

    1. Posição aberta no MT5 mas NÃO no JSON  → importa automaticamente
    2. Posição aberta no JSON mas SEM as duas pernas no MT5 → marca como fechada

    Funciona com posições manuais e do robô (qualquer magic number).
    Retorna dict: { "novos_registros": int, "fechamentos": int }
    """
    # Coleta todos os símbolos dos pares conhecidos
    todos_simbolos = set()
    for par in pares:
        todos_simbolos.add(par["par_a"])
        todos_simbolos.add(par["par_b"])

    # Busca posições abertas no MT5, agrupadas por símbolo
    mt5_por_simbolo: dict = {}
    for symbol in todos_simbolos:
        positions = mt5.positions_get(symbol=symbol)
        if positions:
            mt5_por_simbolo[symbol] = list(positions)

    abertas_json = pos.listar_abertas()
    pares_ja_abertos = {(p["par_a"], p["par_b"]) for p in abertas_json}

    novos    = 0
    fechados = 0

    # ── 1. Importar pares do MT5 ainda não no JSON ────────────
    for par in pares:
        par_a = par["par_a"]
        par_b = par["par_b"]

        if (par_a, par_b) in pares_ja_abertos:
            continue  # já rastreado, ignora

        lista_a = mt5_por_simbolo.get(par_a, [])
        lista_b = mt5_por_simbolo.get(par_b, [])

        if not lista_a or not lista_b:
            continue  # não há pernas complementares abertas

        # Procura combinações que formam um par
        buy_a  = next((p for p in lista_a if p.type == mt5.POSITION_TYPE_BUY),  None)
        sell_a = next((p for p in lista_a if p.type == mt5.POSITION_TYPE_SELL), None)
        buy_b  = next((p for p in lista_b if p.type == mt5.POSITION_TYPE_BUY),  None)
        sell_b = next((p for p in lista_b if p.type == mt5.POSITION_TYPE_SELL), None)

        sinal       = None
        preco_a_ent = None
        preco_b_ent = None
        qty         = None

        # COMPRAR_A: BUY par_a + SELL par_b
        if buy_a and sell_b:
            sinal       = "COMPRAR_A"
            preco_a_ent = buy_a.price_open
            preco_b_ent = sell_b.price_open
            qty         = int(min(buy_a.volume, sell_b.volume))

        # VENDER_A: SELL par_a + BUY par_b
        elif sell_a and buy_b:
            sinal       = "VENDER_A"
            preco_a_ent = sell_a.price_open
            preco_b_ent = buy_b.price_open
            qty         = int(min(sell_a.volume, buy_b.volume))

        if sinal:
            pos.abrir_posicao(
                par_a     = par_a,
                par_b     = par_b,
                setor     = par["setor"],
                sinal     = sinal,
                zscore    = 0.0,       # desconhecido para posições manuais
                preco_a   = preco_a_ent,
                preco_b   = preco_b_ent,
                quantidade = qty,
                origem    = "manual",
            )
            logger.info(f"[SYNC MT5] Importada: {par_a}/{par_b} {sinal} "
                        f"preco_a={preco_a_ent} preco_b={preco_b_ent} qty={qty}")
            novos += 1

    # ── 2. Detectar posições fechadas no MT5 ─────────────────
    for p in abertas_json:
        par_a = p["par_a"]
        par_b = p["par_b"]
        sinal = p["sinal"]

        lista_a = mt5_por_simbolo.get(par_a, [])
        lista_b = mt5_por_simbolo.get(par_b, [])

        # Verifica se as pernas do par ainda existem no MT5
        if sinal == "COMPRAR_A":
            perna_a_existe = any(x.type == mt5.POSITION_TYPE_BUY  for x in lista_a)
            perna_b_existe = any(x.type == mt5.POSITION_TYPE_SELL for x in lista_b)
        else:  # VENDER_A
            perna_a_existe = any(x.type == mt5.POSITION_TYPE_SELL for x in lista_a)
            perna_b_existe = any(x.type == mt5.POSITION_TYPE_BUY  for x in lista_b)

        if perna_a_existe or perna_b_existe:
            continue  # ao menos uma perna ainda aberta, mantém

        # Ambas as pernas foram fechadas → encerra no JSON
        tick_a   = mt5.symbol_info_tick(par_a)
        tick_b   = mt5.symbol_info_tick(par_b)
        preco_a  = (tick_a.last  or tick_a.bid)  if tick_a  else p["preco_entrada_a"]
        preco_b  = (tick_b.last  or tick_b.bid)  if tick_b  else p["preco_entrada_b"]
        qty_real = p.get("quantidade_mt5") or 1

        pos.fechar_posicao(
            pos_id        = p["id"],
            preco_saida_a = preco_a,
            preco_saida_b = preco_b,
            zscore_saida  = 0.0,
            quantidade    = qty_real,
        )
        logger.info(f"[SYNC MT5] Fechamento detectado: {par_a}/{par_b}")
        fechados += 1

    return {"novos_registros": novos, "fechamentos": fechados}


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
