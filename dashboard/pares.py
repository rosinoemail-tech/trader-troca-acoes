# ============================================================
# LISTA DE PARES DE AÇÕES PARA MONITORAMENTO
# Ajuste os nomes dos símbolos conforme aparecem no seu MT5
# ============================================================

PARES = [
    {"par_a": "MOVI3F",  "par_b": "RENT3F",  "setor": "Mobilidade"},
    {"par_a": "VALE3F",  "par_b": "CSNA3F",  "setor": "Mineração"},
    {"par_a": "ITUB4F",  "par_b": "ITSA4F",  "setor": "Financeiro"},
    {"par_a": "GOAU4F",  "par_b": "GGBR4F",  "setor": "Siderurgia"},
    {"par_a": "ELET3F",  "par_b": "ELET6F",  "setor": "Energia"},
    {"par_a": "CMIG3F",  "par_b": "CMIG4F",  "setor": "Energia"},
    {"par_a": "CPLE3F",  "par_b": "CPLE6F",  "setor": "Energia"},
    {"par_a": "CPLE6F",  "par_b": "CMIG4F",  "setor": "Energia"},
    {"par_a": "CSMG3F",  "par_b": "SBSP3F",  "setor": "Saneamento"},
    {"par_a": "SAPR4F",  "par_b": "SAPR11F", "setor": "Saneamento"},
    {"par_a": "SAPR11F", "par_b": "SBSP3F",  "setor": "Saneamento"},
    {"par_a": "TIMS3F",  "par_b": "VIVT3F",  "setor": "Telecom"},
]

# Todos os símbolos únicos usados
SIMBOLOS = list(set(
    s for par in PARES for s in [par["par_a"], par["par_b"]]
))
