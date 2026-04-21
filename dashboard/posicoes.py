# ============================================================
# GERENCIADOR DE POSIÇÕES — Abertura, P&L e Fechamento
# ============================================================

import json
import os
from datetime import datetime

POSICOES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "posicoes.json")


# ── Leitura / Escrita ────────────────────────────────────────

def _carregar() -> list:
    if not os.path.exists(POSICOES_FILE):
        return []
    try:
        with open(POSICOES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _salvar(posicoes: list):
    with open(POSICOES_FILE, "w", encoding="utf-8") as f:
        json.dump(posicoes, f, ensure_ascii=False, indent=2)


# ── Abertura ─────────────────────────────────────────────────

def abrir_posicao(par_a: str, par_b: str, setor: str, sinal: str,
                  zscore: float, preco_a: float, preco_b: float,
                  quantidade: int = None, origem: str = "robo",
                  lucro_alvo: float = None):
    """
    Registra uma nova posição aberta.
    Ignora se já existe posição aberta para esse par.

    origem: "robo" (execução automática) ou "manual" (importada do MT5)
    quantidade: volume real do MT5, usado no cálculo de P&L ao fechar
    """
    posicoes = _carregar()

    # Evita duplicata
    for p in posicoes:
        if p["par_a"] == par_a and p["par_b"] == par_b and p["status"] == "aberta":
            return

    agora = datetime.now()
    posicoes.append({
        "id":              f"{par_a}_{par_b}_{agora.strftime('%Y%m%d_%H%M')}",
        "par_a":           par_a,
        "par_b":           par_b,
        "setor":           setor,
        "sinal":           sinal,
        "data_entrada":    agora.strftime("%d/%m/%Y"),
        "hora_entrada":    agora.strftime("%H:%M"),
        "zscore_entrada":  round(zscore, 4),
        "preco_entrada_a": round(preco_a, 4),
        "preco_entrada_b": round(preco_b, 4),
        "status":          "aberta",
        "origem":          origem,
        "quantidade_mt5":  quantidade,
        "lucro_alvo":      round(lucro_alvo, 2) if lucro_alvo is not None else None,
        "data_fechamento": None,
        "preco_saida_a":   None,
        "preco_saida_b":   None,
        "zscore_saida":    None,
        "pl_final":        None,
        "motivo_fechamento": None,
    })
    _salvar(posicoes)


def fechar_posicao(pos_id: str, preco_saida_a: float,
                   preco_saida_b: float, zscore_saida: float, quantidade: int,
                   motivo: str = "zscore"):
    """
    Marca uma posição como fechada e calcula o P&L final.

    motivo: "zscore" | "lucro_alvo" | "correlacao" | "stop" | "manual"
    """
    posicoes = _carregar()

    for p in posicoes:
        if p["id"] == pos_id and p["status"] == "aberta":
            pl = calcular_pl(p, preco_saida_a, preco_saida_b, quantidade)
            p["status"]          = "fechada"
            p["data_fechamento"] = datetime.now().strftime("%d/%m/%Y %H:%M")
            p["preco_saida_a"]   = round(preco_saida_a, 4)
            p["preco_saida_b"]   = round(preco_saida_b, 4)
            p["zscore_saida"]    = round(zscore_saida, 4)
            p["pl_final"]        = round(pl, 2)
            p["motivo_fechamento"] = motivo
            break

    _salvar(posicoes)


# ── Consultas ────────────────────────────────────────────────

def listar_abertas() -> list:
    return [p for p in _carregar() if p["status"] == "aberta"]


def listar_fechadas() -> list:
    return [p for p in _carregar() if p["status"] == "fechada"]


def listar_todas() -> list:
    return _carregar()


# ── Cálculo de P&L ───────────────────────────────────────────

def calcular_pl(posicao: dict, preco_atual_a: float,
                preco_atual_b: float, quantidade: int) -> float:
    """
    Calcula P&L estimado da posição com base nos preços atuais.

    COMPRAR_A (Z < -2):  Long A + Short B
      P&L = (atual_A - entrada_A) * qty  +  (entrada_B - atual_B) * qty

    VENDER_A (Z > +2):   Short A + Long B
      P&L = (entrada_A - atual_A) * qty  +  (atual_B - entrada_B) * qty
    """
    ea = posicao["preco_entrada_a"]
    eb = posicao["preco_entrada_b"]

    if posicao["sinal"] == "COMPRAR_A":
        pl = (preco_atual_a - ea) * quantidade + (eb - preco_atual_b) * quantidade
    else:  # VENDER_A
        pl = (ea - preco_atual_a) * quantidade + (preco_atual_b - eb) * quantidade

    return pl


def resumo_fechadas() -> dict:
    """Retorna estatísticas das posições fechadas."""
    fechadas = listar_fechadas()
    if not fechadas:
        return {}

    pls = [p["pl_final"] for p in fechadas if p["pl_final"] is not None]
    ganhos  = [v for v in pls if v > 0]
    perdas  = [v for v in pls if v < 0]

    return {
        "total_operacoes":  len(fechadas),
        "vencedoras":       len(ganhos),
        "perdedoras":       len(perdas),
        "taxa_acerto":      round(len(ganhos) / len(pls) * 100, 1) if pls else 0,
        "pl_total":         round(sum(pls), 2),
        "pl_medio":         round(sum(pls) / len(pls), 2) if pls else 0,
        "maior_ganho":      round(max(pls), 2) if pls else 0,
        "maior_perda":      round(min(pls), 2) if pls else 0,
    }
