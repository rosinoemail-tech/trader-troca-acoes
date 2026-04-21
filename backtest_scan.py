import sys
sys.path.insert(0, r'C:\Users\Administrator\trader-troca-acoes\dashboard')

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from scipy.stats import linregress

mt5.initialize()

PARES = [
    ("MOVI3F",  "RENT3F",   "Mobilidade"),
    ("VALE3F",  "CSNA3F",   "Mineracao"),
    ("ITUB4F",  "ITSA4F",   "Financeiro"),
    ("GOAU4F",  "GGBR4F",   "Siderurgia"),
    ("ELET3F",  "ELET6F",   "Energia"),
    ("CMIG3F",  "CMIG4F",   "Energia"),
    ("CPLE3F",  "CPLE6F",   "Energia"),
    ("CPLE6F",  "CMIG4F",   "Energia"),
    ("CSMG3F",  "SBSP3F",   "Saneamento"),
    ("SAPR4F",  "SAPR11F",  "Saneamento"),
    ("SAPR11F", "SBSP3F",   "Saneamento"),
    ("TIMS3F",  "VIVT3F",   "Telecom"),
    ("PETR3F",  "PETR4F",   "Petroleo"),
    ("BBDC3F",  "BBDC4F",   "Financeiro"),
    ("ITUB3F",  "ITUB4F",   "Financeiro"),
    ("ITUB4F",  "BBDC4F",   "Financeiro"),
    ("ITUB4F",  "BBAS3F",   "Financeiro"),
    ("BBDC4F",  "SANB11F",  "Financeiro"),
    ("JBSS3F",  "MRFG3F",   "Frigorificos"),
    ("CSNA3F",  "USIM5F",   "Siderurgia"),
    ("GGBR4F",  "USIM5F",   "Siderurgia"),
    ("SUZB3F",  "KLBN11F",  "Papel/Celulose"),
]

LOOKBACK      = 60
N_BARRAS      = 250   # ~1 ano para ter janela suficiente
LIMIAR_Z      = 3.0
LUCRO_ALVO    = 9.0   # R$
CAPITAL_TOTAL = 1000.0

# ── Busca histórico de cada símbolo ──────────────────────────
print("Buscando dados do MT5...")
historico = {}
for par_a, par_b, _ in PARES:
    for sym in (par_a, par_b):
        if sym not in historico:
            mt5.symbol_select(sym, True)
            rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_D1, 0, N_BARRAS)
            if rates is not None and len(rates) > 0:
                df = pd.DataFrame(rates)[["time","close"]]
                df["time"] = pd.to_datetime(df["time"], unit="s").dt.date
                df = df.set_index("time")["close"]
                historico[sym] = df

mt5.shutdown()

# ── Simulação dia a dia ───────────────────────────────────────
capital     = CAPITAL_TOTAL
posicoes    = {}   # par -> {sinal, preco_a, preco_b, qty_a, qty_b, capital_alocado, data_entrada, z_entrada}
log_eventos = []
log_diario  = []

# Datas comuns dos últimos 3 meses
todas_datas = sorted(set.intersection(*[set(s.index) for s in historico.values()]))
tres_meses  = todas_datas[-65:]  # ~65 dias úteis = 3 meses

for data in tres_meses:
    eventos_dia = []

    # ── Verifica fechamentos antes de abrir ─────────────────
    for chave in list(posicoes.keys()):
        p = posicoes[chave]
        par_a, par_b = chave
        if par_a not in historico or par_b not in historico:
            continue
        if data not in historico[par_a].index or data not in historico[par_b].index:
            continue

        preco_a_atual = historico[par_a][data]
        preco_b_atual = historico[par_b][data]
        qty_a = p["qty_a"]
        qty_b = p["qty_b"]

        if p["sinal"] == "COMPRAR_A":
            pl = (preco_a_atual - p["preco_a"]) * qty_a + (p["preco_b"] - preco_b_atual) * qty_b
        else:
            pl = (p["preco_a"] - preco_a_atual) * qty_a + (preco_b_atual - p["preco_b"]) * qty_b

        if pl >= LUCRO_ALVO:
            capital += p["capital_alocado"] + pl
            eventos_dia.append({
                "data":    str(data),
                "tipo":    "VENDA",
                "par":     f"{par_a}/{par_b}",
                "sinal":   p["sinal"],
                "z_entr":  p["z_entrada"],
                "pl":      round(pl, 2),
                "capital": round(capital, 2),
                "motivo":  f"Lucro R$ {pl:.2f} >= R$ {LUCRO_ALVO:.2f}",
            })
            del posicoes[chave]

    # ── Verifica aberturas ───────────────────────────────────
    for par_a, par_b, setor in PARES:
        chave = (par_a, par_b)
        if chave in posicoes:
            continue
        if par_a not in historico or par_b not in historico:
            continue

        # Precisa de janela suficiente até esta data
        datas_a = [d for d in historico[par_a].index if d <= data]
        datas_b = [d for d in historico[par_b].index if d <= data]
        datas_comuns = sorted(set(datas_a) & set(datas_b))

        if len(datas_comuns) < LOOKBACK + 10:
            continue

        janela = datas_comuns[-(LOOKBACK + 30):]
        sa = historico[par_a][janela]
        sb = historico[par_b][janela]

        la = np.log(sa)
        lb = np.log(sb)
        slope, _, _, _, _ = linregress(lb.values, la.values)
        sp   = la - slope * lb
        mean = sp.rolling(LOOKBACK).mean()
        std  = sp.rolling(LOOKBACK).std()
        zs   = ((sp - mean) / std).dropna()

        if len(zs) == 0:
            continue

        z_atual = float(zs.iloc[-1])

        if abs(z_atual) < LIMIAR_Z:
            continue

        # Há capital disponível?
        if capital < 50:
            eventos_dia.append({
                "data":    str(data),
                "tipo":    "BLOQUEADO",
                "par":     f"{par_a}/{par_b}",
                "sinal":   "COMPRAR_A" if z_atual < 0 else "VENDER_A",
                "z_entr":  round(z_atual, 2),
                "pl":      None,
                "capital": round(capital, 2),
                "motivo":  "Sem capital disponivel",
            })
            continue

        preco_a = historico[par_a][data]
        preco_b = historico[par_b][data]

        cap_por_ponta = capital / 2
        qty_a = max(int(cap_por_ponta / preco_a), 1)
        qty_b = max(int(cap_por_ponta / preco_b), 1)
        capital_alocado = round(qty_a * preco_a + qty_b * preco_b, 2)

        sinal = "COMPRAR_A" if z_atual < 0 else "VENDER_A"
        capital -= capital_alocado

        posicoes[chave] = {
            "sinal":           sinal,
            "preco_a":         preco_a,
            "preco_b":         preco_b,
            "qty_a":           qty_a,
            "qty_b":           qty_b,
            "capital_alocado": capital_alocado,
            "data_entrada":    str(data),
            "z_entrada":       round(z_atual, 2),
        }

        eventos_dia.append({
            "data":    str(data),
            "tipo":    "COMPRA",
            "par":     f"{par_a}/{par_b}",
            "sinal":   sinal,
            "z_entr":  round(z_atual, 2),
            "pl":      None,
            "capital": round(capital, 2),
            "motivo":  f"Z={z_atual:.2f} | {qty_a}x{par_a} + {qty_b}x{par_b} | R${capital_alocado:.2f}",
        })

    # P&L aberto no dia
    pl_aberto = 0.0
    for chave, p in posicoes.items():
        par_a, par_b = chave
        if par_a not in historico or par_b not in historico:
            continue
        if data not in historico[par_a].index or data not in historico[par_b].index:
            continue
        pa = historico[par_a][data]
        pb = historico[par_b][data]
        if p["sinal"] == "COMPRAR_A":
            pl_aberto += (pa - p["preco_a"]) * p["qty_a"] + (p["preco_b"] - pb) * p["qty_b"]
        else:
            pl_aberto += (p["preco_a"] - pa) * p["qty_a"] + (pb - p["preco_b"]) * p["qty_b"]

    log_diario.append({
        "data":         str(data),
        "capital_livre": round(capital, 2),
        "posicoes":     len(posicoes),
        "pl_aberto":    round(pl_aberto, 2),
        "patrimonio":   round(capital + pl_aberto + sum(p["capital_alocado"] for p in posicoes.values()), 2),
    })

    log_eventos.extend(eventos_dia)

# ── Relatório ────────────────────────────────────────────────
print("")
print("=" * 75)
print("  BACKTEST --- CAPITAL R$1.000 | Z >= 3 ENTRA | LUCRO R$9 SAI")
print("=" * 75)

vendas  = [e for e in log_eventos if e["tipo"] == "VENDA"]
compras = [e for e in log_eventos if e["tipo"] == "COMPRA"]
bloq    = [e for e in log_eventos if e["tipo"] == "BLOQUEADO"]

print(f"\n  RESUMO")
print(f"  Capital inicial : R$ {CAPITAL_TOTAL:.2f}")
print(f"  Capital final   : R$ {capital:.2f}")
pl_realizado = sum(e["pl"] for e in vendas)
print(f"  Lucro realizado : R$ {pl_realizado:.2f}")
print(f"  Operacoes abertas (nao fechadas): {len(posicoes)}")
print(f"  Total de entradas : {len(compras)}")
print(f"  Total de saidas   : {len(vendas)}")
print(f"  Vezes bloqueado   : {len(bloq)}")

print(f"\n  EVENTOS DIA A DIA")
print(f"  {'DATA':<12} {'TIPO':<9} {'PAR':<22} {'Z':<7} {'P&L':>7}  {'CAIXA':>8}  DETALHE")
print(f"  " + "-" * 72)

for e in log_eventos:
    pl_str = f"R${e['pl']:.2f}" if e["pl"] is not None else "---"
    print(f"  {e['data']:<12} {e['tipo']:<9} {e['par']:<22} {e['z_entr']:<7} {pl_str:>7}  R${e['capital']:>7.2f}  {e['motivo']}")

print(f"\n  POSICOES AINDA ABERTAS (nao atingiram R$9 no periodo)")
if posicoes:
    print(f"  {'PAR':<22} {'ENTRADA':<12} {'Z':<7} {'ALOCADO':>10}")
    print(f"  " + "-" * 55)
    for (a, b), p in posicoes.items():
        print(f"  {a}/{b:<20} {p['data_entrada']:<12} {p['z_entrada']:<7} R${p['capital_alocado']:>8.2f}")
else:
    print("  Nenhuma")

print("=" * 75)
