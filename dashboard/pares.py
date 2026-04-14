# ============================================================
# LISTA DE PARES DE AÇÕES PARA MONITORAMENTO
# Ajuste os nomes dos símbolos conforme aparecem no seu MT5
# ============================================================

PARES = [
    {"par_a": "MOVI3",  "par_b": "RENT3",  "setor": "Mobilidade"},
    {"par_a": "VALE3",  "par_b": "CSNA3",  "setor": "Mineração"},
    {"par_a": "ITUB4",  "par_b": "ITSA4",  "setor": "Financeiro"},
    {"par_a": "GOAU4",  "par_b": "GGBR4",  "setor": "Siderurgia"},
    {"par_a": "ELET3",  "par_b": "ELET6",  "setor": "Energia"},
    {"par_a": "CMIG3",  "par_b": "CMIG4",  "setor": "Energia"},
    {"par_a": "CPLE3",  "par_b": "CPLE6",  "setor": "Energia"},
    {"par_a": "CPLE6",  "par_b": "CMIG4",  "setor": "Energia"},
    {"par_a": "CSMG3",  "par_b": "SBSP3",  "setor": "Saneamento"},
    {"par_a": "SAPR4",  "par_b": "SAPR11", "setor": "Saneamento"},
    {"par_a": "SAPR11", "par_b": "SBSP3",  "setor": "Saneamento"},
    {"par_a": "TIMS3",  "par_b": "VIVT3",  "setor": "Telecom"},
]

# Todos os símbolos únicos usados
SIMBOLOS = list(set(
    s for par in PARES for s in [par["par_a"], par["par_b"]]
))
