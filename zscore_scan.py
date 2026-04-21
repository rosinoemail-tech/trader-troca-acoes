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
    ("JBSS3F",  "BEEF3F",   "Frigorificos"),
    ("MRFG3F",  "BEEF3F",   "Frigorificos"),
    ("CSNA3F",  "USIM5F",   "Siderurgia"),
    ("GGBR4F",  "USIM5F",   "Siderurgia"),
    ("SUZB3F",  "KLBN11F",  "Papel/Celulose"),
    ("GOLL4F",  "AZUL4F",   "Aviacao"),
]

LOOKBACK = 60
N_BARRAS = 180
LIMIAR_Z = 3.0

resultados = []

for par_a, par_b, setor in PARES:
    try:
        mt5.symbol_select(par_a, True)
        mt5.symbol_select(par_b, True)
        ra = mt5.copy_rates_from_pos(par_a, mt5.TIMEFRAME_D1, 0, N_BARRAS)
        rb = mt5.copy_rates_from_pos(par_b, mt5.TIMEFRAME_D1, 0, N_BARRAS)
        if ra is None or rb is None or len(ra) < LOOKBACK or len(rb) < LOOKBACK:
            resultados.append((setor, par_a, par_b, None, None, None, "sem dados"))
            continue
        da = pd.DataFrame(ra)[["time","close"]].set_index("time").rename(columns={"close": par_a})
        db = pd.DataFrame(rb)[["time","close"]].set_index("time").rename(columns={"close": par_b})
        df = da.join(db, how="inner").dropna()
        if len(df) < LOOKBACK + 10:
            resultados.append((setor, par_a, par_b, None, None, None, "insuf"))
            continue
        la = np.log(df[par_a])
        lb = np.log(df[par_b])
        slope, _, r_val, _, _ = linregress(lb, la)
        sp   = la - slope * lb
        zs   = ((sp - sp.rolling(LOOKBACK).mean()) / sp.rolling(LOOKBACK).std()).dropna()
        z_max = round(float(zs.abs().max()), 2)
        z_at  = round(float(zs.iloc[-1]), 2)
        corr  = round(float(r_val), 2)
        tag   = "OK" if z_max >= LIMIAR_Z else "abaixo"
        resultados.append((setor, par_a, par_b, z_max, z_at, corr, tag))
    except Exception as e:
        resultados.append((setor, par_a, par_b, None, None, None, str(e)[:40]))

mt5.shutdown()

resultados.sort(key=lambda x: -(x[3] or 0))
ok = [r for r in resultados if r[6] == "OK"]
nd = [r for r in resultados if r[6] in ("sem dados", "insuf")]

print("")
print("=" * 65)
print("  PARES COM Z-SCORE >= 3 --- ULTIMOS 3 MESES")
print("=" * 65)
print("  {:<15} {:<23} {:>6} {:>8} {:>6}".format("SETOR", "PAR", "Z MAX", "Z ATUAL", "CORR"))
print("  " + "-" * 58)
for s2, a, b, zm, za, c, _ in ok:
    sg = "+" if za >= 0 else ""
    print("  {:<15} {}/{:<20} {:>6.2f}  {}{:<7.2f} {:>5.2f}".format(s2, a, b, zm, sg, abs(za), c))
if not ok:
    print("  Nenhum par atingiu Z >= 3 no periodo.")
if nd:
    print("\n  SEM DADOS: " + ", ".join(f"{r[1]}/{r[2]}" for r in nd))
print("=" * 65)
