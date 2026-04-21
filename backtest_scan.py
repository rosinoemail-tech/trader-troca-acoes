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

LOOKBACK        = 60
N_BARRAS        = 250    # ~1 ano para ter janela suficiente
LIMIAR_Z        = 3.0
CAPITAL_TOTAL   = 1000.0
MAX_OPERACOES   = 3      # slots simultâneos
PERCENTUAL_LUCRO = 3.0   # % do capital alocado na operação
DIAS_BACKTEST   = 22     # ~1 mês útil

CAPITAL_POR_SLOT = CAPITAL_TOTAL / MAX_OPERACOES  # R$ 333,33

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
posicoes    = {}   # chave -> posicao aberta
log_eventos = []

# Datas do último mês
todas_datas = sorted(set.union(*[set(s.index) for s in historico.values()]))
tres_meses  = todas_datas[-DIAS_BACKTEST:]

for data in tres_meses:
    eventos_dia = []

    slots_livres = MAX_OPERACOES - len(posicoes)

    # ── Verifica fechamentos ─────────────────────────────────
    for chave in list(posicoes.keys()):
        p    = posicoes[chave]
        par_a, par_b = chave
        if par_a not in historico or par_b not in historico:
            continue
        if data not in historico[par_a].index or data not in historico[par_b].index:
            continue

        pa = historico[par_a][data]
        pb = historico[par_b][data]

        if p["sinal"] == "COMPRAR_A":
            pl = (pa - p["preco_a"]) * p["qty_a"] + (p["preco_b"] - pb) * p["qty_b"]
        else:
            pl = (p["preco_a"] - pa) * p["qty_a"] + (pb - p["preco_b"]) * p["qty_b"]

        lucro_alvo_pos = p["lucro_alvo"]

        if pl >= lucro_alvo_pos:
            slots_livres += 1
            eventos_dia.append({
                "data":   str(data),
                "tipo":   "VENDA",
                "par":    f"{par_a}/{par_b}",
                "z_entr": p["z_entrada"],
                "pl":     round(pl, 2),
                "alvo":   round(lucro_alvo_pos, 2),
                "slots":  f"{MAX_OPERACOES - len(posicoes) + 1}/{MAX_OPERACOES}",
                "motivo": f"Lucro R${pl:.2f} >= alvo R${lucro_alvo_pos:.2f} ({PERCENTUAL_LUCRO}% de R${p['capital_alocado']:.2f})",
            })
            del posicoes[chave]

    # ── Verifica aberturas ───────────────────────────────────
    for par_a, par_b, setor in PARES:
        if slots_livres <= 0:
            break
        chave = (par_a, par_b)
        if chave in posicoes:
            continue
        if par_a not in historico or par_b not in historico:
            continue

        datas_comuns = sorted(set(d for d in historico[par_a].index if d <= data) &
                              set(d for d in historico[par_b].index if d <= data))
        if len(datas_comuns) < LOOKBACK + 10:
            continue

        janela = datas_comuns[-(LOOKBACK + 30):]
        sa = historico[par_a][janela]
        sb = historico[par_b][janela]
        la = np.log(sa); lb = np.log(sb)
        slope, _, _, _, _ = linregress(lb.values, la.values)
        sp   = la - slope * lb
        zs   = ((sp - sp.rolling(LOOKBACK).mean()) / sp.rolling(LOOKBACK).std()).dropna()

        if len(zs) == 0 or abs(float(zs.iloc[-1])) < LIMIAR_Z:
            continue

        z_atual = float(zs.iloc[-1])
        preco_a = historico[par_a][data]
        preco_b = historico[par_b][data]

        cap_por_ponta = CAPITAL_POR_SLOT / 2
        qty_a = max(int(cap_por_ponta / preco_a), 1)
        qty_b = max(int(cap_por_ponta / preco_b), 1)
        capital_alocado = round(qty_a * preco_a + qty_b * preco_b, 2)
        lucro_alvo_pos  = round(capital_alocado * PERCENTUAL_LUCRO / 100, 2)
        sinal = "COMPRAR_A" if z_atual < 0 else "VENDER_A"
        slots_livres -= 1

        posicoes[chave] = {
            "sinal":           sinal,
            "preco_a":         preco_a,
            "preco_b":         preco_b,
            "qty_a":           qty_a,
            "qty_b":           qty_b,
            "capital_alocado": capital_alocado,
            "lucro_alvo":      lucro_alvo_pos,
            "data_entrada":    str(data),
            "z_entrada":       round(z_atual, 2),
        }

        eventos_dia.append({
            "data":   str(data),
            "tipo":   "COMPRA",
            "par":    f"{par_a}/{par_b}",
            "z_entr": round(z_atual, 2),
            "pl":     None,
            "alvo":   lucro_alvo_pos,
            "slots":  f"{MAX_OPERACOES - slots_livres}/{MAX_OPERACOES}",
            "motivo": f"Z={z_atual:.2f} | {qty_a}x{par_a}+{qty_b}x{par_b} | R${capital_alocado:.2f} | alvo R${lucro_alvo_pos:.2f}",
        })

    log_eventos.extend(eventos_dia)

# ── Relatório ────────────────────────────────────────────────
vendas  = [e for e in log_eventos if e["tipo"] == "VENDA"]
compras = [e for e in log_eventos if e["tipo"] == "COMPRA"]
pl_realizado = sum(e["pl"] for e in vendas)

print("")
print("=" * 80)
print(f"  BACKTEST 1 MES | CAPITAL R${CAPITAL_TOTAL:.0f} | {MAX_OPERACOES} SLOTS | Z>={LIMIAR_Z} ENTRA | LUCRO {PERCENTUAL_LUCRO}% SAI")
print("=" * 80)
print(f"  Capital total     : R$ {CAPITAL_TOTAL:.2f}")
print(f"  Capital por slot  : R$ {CAPITAL_POR_SLOT:.2f}")
print(f"  Lucro alvo/op     : {PERCENTUAL_LUCRO}% do capital alocado")
print(f"  Entradas          : {len(compras)}")
print(f"  Saidas (realizadas): {len(vendas)}")
print(f"  Lucro realizado   : R$ {pl_realizado:.2f}")
print(f"  Posicoes em aberto: {len(posicoes)}")
print("")
print(f"  {'DATA':<12} {'TIPO':<7} {'SLOT':<7} {'PAR':<22} {'Z':>5}  {'ALVO':>7}  {'P&L':>7}  DETALHE")
print(f"  " + "-" * 78)

for e in log_eventos:
    pl_str   = f"R${e['pl']:>7.2f}" if e["pl"] is not None else "       ---"
    alvo_str = f"R${e['alvo']:>6.2f}"
    print(f"  {e['data']:<12} {e['tipo']:<7} {e['slots']:<7} {e['par']:<22} {e['z_entr']:>5}  {alvo_str}  {pl_str}  {e['motivo']}")

if posicoes:
    print(f"\n  POSICOES ABERTAS (nao atingiram {PERCENTUAL_LUCRO}% no periodo):")
    print(f"  {'PAR':<22} {'ENTRADA':<12} {'Z':>5}  {'ALOCADO':>9}  {'ALVO':>7}")
    print(f"  " + "-" * 60)
    for (a, b), p in posicoes.items():
        print(f"  {a}/{b:<20} {p['data_entrada']:<12} {p['z_entrada']:>5}  R${p['capital_alocado']:>7.2f}  R${p['lucro_alvo']:>5.2f}")

print("=" * 80)
