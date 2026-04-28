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
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log_ordens.json")

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


def calcular_distribuicao(oportunidades: list) -> list:
    """
    Cada oportunidade recebe exatamente valor_por_operacao.
    Só inclui a operação se houver saldo suficiente.
    Slots simultâneos = saldo_livre // valor_por_operacao.
    """
    saldo         = get_saldo_livre()
    valor_por_op  = cfg.get_valor_por_operacao()
    pct_lucro     = cfg.get_percentual_lucro()

    if not oportunidades or saldo < valor_por_op:
        return []

    resultado     = []
    saldo_restante = saldo

    for op in oportunidades:
        if saldo_restante < valor_por_op:
            break

        qty_a, qty_b = calcular_quantidade(op["preco_a"], op["preco_b"], valor_por_op)

        qtd_max = cfg.get_qtd_maxima(op["par_a"], op["par_b"])
        if qtd_max > 0:
            qty_a = min(qty_a, qtd_max)
            qty_b = min(qty_b, qtd_max)

        custo_estimado = round((qty_a * op["preco_a"]) + (qty_b * op["preco_b"]), 2)
        lucro_alvo     = round(custo_estimado * pct_lucro / 100, 2)
        saldo_restante -= custo_estimado

        resultado.append({
            **op,
            "qty_a":           qty_a,
            "qty_b":           qty_b,
            "qtd_max":         qtd_max,
            "capital_alocado": custo_estimado,
            "lucro_alvo":      lucro_alvo,
        })

    return resultado


# ── Envio de ordem ───────────────────────────────────────────

def _filling_mode(symbol: str) -> int:
    """
    Detecta o modo de preenchimento suportado pelo símbolo.
    B3 via Genial usa RETURN (3). Fallback para IOC se não suportado.
    """
    info = mt5.symbol_info(symbol)
    if info is None:
        return mt5.ORDER_FILLING_RETURN
    filling = info.filling_mode
    # bit 0 = FOK, bit 1 = IOC, bit 2 = RETURN
    if filling & 4:   # RETURN suportado
        return mt5.ORDER_FILLING_RETURN
    if filling & 2:   # IOC suportado
        return mt5.ORDER_FILLING_IOC
    return mt5.ORDER_FILLING_FOK


def _enviar_ordem(symbol: str, volume: int,
                  tipo: int, comment: str = "") -> dict:
    """
    Envia ordem a mercado para o símbolo.

    tipo: mt5.ORDER_TYPE_BUY ou mt5.ORDER_TYPE_SELL
    """
    # Verifica se Auto Trade está habilitado no terminal MT5
    terminal = mt5.terminal_info()
    if terminal is None or not terminal.trade_allowed:
        return {"ok": False, "erro": "Auto Trade desativado no MT5. Ative o botão 'Auto Trading' na barra do terminal."}

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return {"ok": False, "erro": f"Sem tick para {symbol}"}

    price = tick.ask if tipo == mt5.ORDER_TYPE_BUY else tick.bid

    info_sym = mt5.symbol_info(symbol)
    if info_sym is None:
        return {"ok": False, "erro": f"Símbolo não encontrado: {symbol}"}

    volume_min  = info_sym.volume_min
    volume_step = info_sym.volume_step if info_sym.volume_step > 0 else volume_min
    # Arredonda para múltiplo do step mínimo
    volume_real = max(float(volume), volume_min)
    volume_real = round(round(volume_real / volume_step) * volume_step, 8)

    filling = _filling_mode(symbol)

    request = {
        "action":       mt5.TRADE_ACTION_DEAL,
        "symbol":       symbol,
        "volume":       volume_real,
        "type":         tipo,
        "price":        price,
        "deviation":    50,
        "magic":        MAGIC,
        "comment":      f"TraderTrocaAcoes {comment}"[:31],
        "type_time":    mt5.ORDER_TIME_GTC,
        "type_filling": filling,
    }

    result = mt5.order_send(request)

    ok = result is not None and result.retcode == mt5.TRADE_RETCODE_DONE
    erro_detalhe = ""
    if not ok:
        mt5_err = mt5.last_error()
        retcode = result.retcode if result else -1
        erro_detalhe = f"retcode={retcode} | mt5_error={mt5_err} | filling={filling}"
        logger.error(f"❌ Ordem rejeitada: {symbol} vol={volume_real} | {erro_detalhe}")

    return {
        "ok":      ok,
        "retcode": result.retcode if result else -1,
        "ticket":  result.order  if (result and ok) else None,
        "volume":  volume_real,
        "price":   price,
        "filling": filling,
        "erro":    erro_detalhe if not ok else "",
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
        custo      = (qty_a * preco_a) + (qty_b * preco_b)
        lucro_alvo = round(custo * cfg.get_percentual_lucro() / 100, 2)
        log["status"] = "simulado"
        log["custo_estimado"] = round(custo, 2)
        log["lucro_alvo"]     = lucro_alvo
        logger.info(f"[SIMULAÇÃO] {descricao} | Z={zscore:.3f} | Custo≈R${custo:.2f} | Alvo R${lucro_alvo:.2f}")
        _registrar_log(log)
        pos.abrir_posicao(par_a, par_b, setor, sinal, zscore, preco_a, preco_b, lucro_alvo=lucro_alvo)
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
        custo      = (qty_a * preco_a) + (qty_b * preco_b)
        lucro_alvo = round(custo * cfg.get_percentual_lucro() / 100, 2)
        logger.info(f"✅ Executado: {descricao} | "
                    f"A ticket={res_a['ticket']} B ticket={res_b['ticket']} | Alvo R${lucro_alvo:.2f}")
        pos.abrir_posicao(par_a, par_b, setor, sinal, zscore, preco_a, preco_b,
                          lucro_alvo=lucro_alvo,
                          ticket_a=res_a["ticket"], ticket_b=res_b["ticket"])
    else:
        logger.error(f"❌ Erro ao executar {descricao}: A={res_a} B={res_b}")

    _registrar_log(log)
    return log


# ── Fechar par no MT5 ────────────────────────────────────────

def fechar_par_mt5(par_a: str, par_b: str, simulacao: bool = True,
                   ticket_a: int = None, ticket_b: int = None) -> dict:
    """
    Fecha as duas pernas do par no MT5.

    Se ticket_a/ticket_b informados: fecha posição específica pelo ticket.
    Fallback sem ticket: fecha todas as posições do símbolo (comportamento legado).
    """
    resultados = {}
    for symbol, ticket in [(par_a, ticket_a), (par_b, ticket_b)]:
        if ticket:
            positions = mt5.positions_get(ticket=ticket)
        else:
            positions = mt5.positions_get(symbol=symbol)

        if not positions:
            continue

        for p in positions:
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

        tkt_a = None
        tkt_b = None

        # COMPRAR_A: BUY par_a + SELL par_b
        if buy_a and sell_b:
            sinal       = "COMPRAR_A"
            preco_a_ent = buy_a.price_open
            preco_b_ent = sell_b.price_open
            qty         = int(min(buy_a.volume, sell_b.volume))
            tkt_a       = buy_a.ticket
            tkt_b       = sell_b.ticket

        # VENDER_A: SELL par_a + BUY par_b
        elif sell_a and buy_b:
            sinal       = "VENDER_A"
            preco_a_ent = sell_a.price_open
            preco_b_ent = buy_b.price_open
            qty         = int(min(sell_a.volume, buy_b.volume))
            tkt_a       = sell_a.ticket
            tkt_b       = buy_b.ticket

        if sinal:
            capital_manual = round((preco_a_ent * qty) + (preco_b_ent * qty), 2)
            lucro_alvo_manual = round(capital_manual * cfg.get_percentual_lucro() / 100, 2)
            pos.abrir_posicao(
                par_a      = par_a,
                par_b      = par_b,
                setor      = par["setor"],
                sinal      = sinal,
                zscore     = 0.0,
                preco_a    = preco_a_ent,
                preco_b    = preco_b_ent,
                quantidade = qty,
                origem     = "manual",
                lucro_alvo = lucro_alvo_manual,
                ticket_a   = tkt_a,
                ticket_b   = tkt_b,
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
