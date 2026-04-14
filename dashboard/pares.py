# ============================================================
# LISTA DE PARES DE AÇÕES PARA MONITORAMENTO
# Ajuste os nomes dos símbolos conforme aparecem no seu MT5
# ============================================================

PARES = [
    # ── Lista original ──────────────────────────────────────
    {"par_a": "MOVI3F",  "par_b": "RENT3F",   "setor": "Mobilidade"},
    {"par_a": "VALE3F",  "par_b": "CSNA3F",   "setor": "Mineração"},
    {"par_a": "ITUB4F",  "par_b": "ITSA4F",   "setor": "Financeiro"},
    {"par_a": "GOAU4F",  "par_b": "GGBR4F",   "setor": "Siderurgia"},
    {"par_a": "ELET3F",  "par_b": "ELET6F",   "setor": "Energia"},
    {"par_a": "CMIG3F",  "par_b": "CMIG4F",   "setor": "Energia"},
    {"par_a": "CPLE3F",  "par_b": "CPLE6F",   "setor": "Energia"},
    {"par_a": "CPLE6F",  "par_b": "CMIG4F",   "setor": "Energia"},
    {"par_a": "CSMG3F",  "par_b": "SBSP3F",   "setor": "Saneamento"},
    {"par_a": "SAPR4F",  "par_b": "SAPR11F",  "setor": "Saneamento"},
    {"par_a": "SAPR11F", "par_b": "SBSP3F",   "setor": "Saneamento"},
    {"par_a": "TIMS3F",  "par_b": "VIVT3F",   "setor": "Telecom"},

    # ── ON vs PN (mesma empresa) ────────────────────────────
    {"par_a": "PETR3F",  "par_b": "PETR4F",   "setor": "Petróleo"},
    {"par_a": "BBDC3F",  "par_b": "BBDC4F",   "setor": "Financeiro"},
    {"par_a": "ITUB3F",  "par_b": "ITUB4F",   "setor": "Financeiro"},

    # ── Bancos concorrentes ─────────────────────────────────
    {"par_a": "ITUB4F",  "par_b": "BBDC4F",   "setor": "Financeiro"},
    {"par_a": "ITUB4F",  "par_b": "BBAS3F",   "setor": "Financeiro"},
    {"par_a": "BBDC4F",  "par_b": "SANB11F",  "setor": "Financeiro"},

    # ── Frigoríficos ────────────────────────────────────────
    {"par_a": "JBSS3F",  "par_b": "MRFG3F",   "setor": "Frigoríficos"},
    {"par_a": "JBSS3F",  "par_b": "BEEF3F",   "setor": "Frigoríficos"},
    {"par_a": "MRFG3F",  "par_b": "BEEF3F",   "setor": "Frigoríficos"},

    # ── Siderurgia ──────────────────────────────────────────
    {"par_a": "CSNA3F",  "par_b": "USIM5F",   "setor": "Siderurgia"},
    {"par_a": "GGBR4F",  "par_b": "USIM5F",   "setor": "Siderurgia"},

    # ── Papel e Celulose ────────────────────────────────────
    {"par_a": "SUZB3F",  "par_b": "KLBN11F",  "setor": "Papel/Celulose"},

    # ── Aviação ─────────────────────────────────────────────
    {"par_a": "GOLL4F",  "par_b": "AZUL4F",   "setor": "Aviação"},
]

# Todos os símbolos únicos usados
SIMBOLOS = list(set(
    s for par in PARES for s in [par["par_a"], par["par_b"]]
))
