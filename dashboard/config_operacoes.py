# ============================================================
# CONFIGURAÇÕES DE OPERAÇÕES — Pares habilitados e capital
# ============================================================

import json
import os

CONFIG_FILE = "config_operacoes.json"

DEFAULTS = {
    "auto_executar":      False,   # ligado/desligado pelo painel
    "modo_simulacao":     True,    # True = não executa ordens reais
    "percentual_capital": 30,      # % do saldo para operar
    "pares_habilitados":  {},      # { "PETR3F_PETR4F": True, ... }
    "qtd_maxima":         {},      # { "PETR3F_PETR4F": 100, ... }  0 = sem limite
}


def _chave(par_a: str, par_b: str) -> str:
    return f"{par_a}_{par_b}"


def _carregar() -> dict:
    if not os.path.exists(CONFIG_FILE):
        _salvar(DEFAULTS.copy())
        return DEFAULTS.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        # Garante que todas as chaves existem
        for k, v in DEFAULTS.items():
            cfg.setdefault(k, v)
        return cfg
    except Exception:
        return DEFAULTS.copy()


def _salvar(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ── Leitura ──────────────────────────────────────────────────

def get_config() -> dict:
    return _carregar()

def is_auto_executar() -> bool:
    return _carregar().get("auto_executar", False)

def is_simulacao() -> bool:
    return _carregar().get("modo_simulacao", True)

def get_percentual() -> float:
    return float(_carregar().get("percentual_capital", 30))

def is_par_habilitado(par_a: str, par_b: str) -> bool:
    cfg = _carregar()
    return cfg["pares_habilitados"].get(_chave(par_a, par_b), False)

def get_qtd_maxima(par_a: str, par_b: str) -> int:
    """Retorna qtd máxima configurada. 0 = sem limite (usa cálculo pelo saldo)."""
    cfg = _carregar()
    return int(cfg.get("qtd_maxima", {}).get(_chave(par_a, par_b), 0))


# ── Escrita ──────────────────────────────────────────────────

def set_auto_executar(valor: bool):
    cfg = _carregar()
    cfg["auto_executar"] = valor
    _salvar(cfg)

def set_simulacao(valor: bool):
    cfg = _carregar()
    cfg["modo_simulacao"] = valor
    _salvar(cfg)

def set_percentual(valor: float):
    cfg = _carregar()
    cfg["percentual_capital"] = max(1.0, min(100.0, valor))
    _salvar(cfg)

def set_par_habilitado(par_a: str, par_b: str, habilitado: bool):
    cfg = _carregar()
    cfg["pares_habilitados"][_chave(par_a, par_b)] = habilitado
    _salvar(cfg)

def set_qtd_maxima(par_a: str, par_b: str, qtd: int):
    """Define quantidade máxima de ações por ponta para o par. 0 = sem limite."""
    cfg = _carregar()
    cfg.setdefault("qtd_maxima", {})
    cfg["qtd_maxima"][_chave(par_a, par_b)] = max(0, int(qtd))
    _salvar(cfg)

def habilitar_todos(pares: list):
    cfg = _carregar()
    for par in pares:
        cfg["pares_habilitados"][_chave(par["par_a"], par["par_b"])] = True
    _salvar(cfg)

def desabilitar_todos(pares: list):
    cfg = _carregar()
    for par in pares:
        cfg["pares_habilitados"][_chave(par["par_a"], par["par_b"])] = False
    _salvar(cfg)
