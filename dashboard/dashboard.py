# ============================================================
# PAINEL TRADER TROCA DE AÇÕES — Layout redesenhado
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from pares import PARES
import mt5_connector as mt5c
import analyzer
import posicoes as pos
import config_operacoes as cfg_op
import gestor_ordens as gestor

# ── Configuração ─────────────────────────────────────────────
st.set_page_config(
    page_title="Trader Troca de Ações",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=60_000, key="autorefresh")

# ── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Fundo geral */
    .stApp { background-color: #0f1117; }

    /* Cabeçalho */
    .header-box {
        background: linear-gradient(135deg, #1a1f35 0%, #0f1117 100%);
        border: 1px solid #2d3250;
        border-radius: 12px;
        padding: 20px 30px;
        margin-bottom: 20px;
    }
    .header-title {
        font-size: 28px;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
    }
    .header-sub {
        font-size: 14px;
        color: #8892b0;
        margin-top: 4px;
    }

    /* Cards de métricas */
    .metric-box {
        background-color: #1a1f35;
        border: 1px solid #2d3250;
        border-radius: 10px;
        padding: 18px 20px;
        text-align: center;
    }
    .metric-label {
        font-size: 12px;
        color: #8892b0;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 36px;
        font-weight: 700;
        color: #ffffff;
        line-height: 1;
    }
    .metric-value.green  { color: #00e676; }
    .metric-value.yellow { color: #ffd600; }
    .metric-value.red    { color: #ff5252; }
    .metric-value.gray   { color: #8892b0; }

    /* Cards de oportunidade */
    .card {
        border-radius: 10px;
        padding: 20px 24px;
        margin-bottom: 14px;
        border: 1px solid;
    }
    .card-buy {
        background-color: #0a2218;
        border-color: #00c853;
    }
    .card-sell {
        background-color: #220a0a;
        border-color: #ff5252;
    }
    .card-watch {
        background-color: #1a1800;
        border-color: #ffd600;
    }
    .card-neutral {
        background-color: #13141a;
        border-color: #2d3250;
    }
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .card-title {
        font-size: 20px;
        font-weight: 700;
        color: #ffffff;
    }
    .card-setor {
        font-size: 12px;
        color: #8892b0;
        background: #1e2235;
        padding: 3px 10px;
        border-radius: 20px;
    }
    .badge-buy  { background: #00c853; color: #000; font-weight: 700; padding: 4px 14px; border-radius: 20px; font-size: 13px; }
    .badge-sell { background: #ff5252; color: #fff; font-weight: 700; padding: 4px 14px; border-radius: 20px; font-size: 13px; }
    .badge-watch  { background: #ffd600; color: #000; font-weight: 700; padding: 4px 14px; border-radius: 20px; font-size: 13px; }
    .card-info {
        display: flex;
        gap: 30px;
        flex-wrap: wrap;
        margin-top: 8px;
    }
    .info-item label {
        font-size: 11px;
        color: #8892b0;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        display: block;
    }
    .info-item span {
        font-size: 18px;
        font-weight: 600;
        color: #ffffff;
    }
    .z-buy  { color: #00e676 !important; }
    .z-sell { color: #ff5252 !important; }

    /* Tabela */
    .tabela-linha {
        background: #1a1f35;
        border: 1px solid #2d3250;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 16px;
    }

    /* Remove padding extra do streamlit */
    .block-container { padding-top: 1.5rem !important; }
    div[data-testid="stMetric"] { background: #1a1f35; border-radius: 10px; padding: 14px; border: 1px solid #2d3250; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background: #1a1f35; border-radius: 10px; padding: 4px; gap: 4px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; color: #8892b0; font-weight: 500; }
    .stTabs [aria-selected="true"] { background: #2d3250 !important; color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)


# ── Conexão MT5 ──────────────────────────────────────────────
@st.cache_resource
def iniciar_mt5():
    return mt5c.conectar()

mt5_ok = iniciar_mt5()


# ── Cabeçalho ────────────────────────────────────────────────
agora = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
status_mt5 = "🟢 MT5 Conectado" if mt5_ok else "🔴 MT5 Desconectado"

st.markdown(f"""
<div class="header-box">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <p class="header-title">📊 Trader Troca de Ações</p>
            <p class="header-sub">Monitoramento de pares em tempo real — B3 via MT5 Genial</p>
        </div>
        <div style="text-align:right;">
            <p style="color:#8892b0; font-size:13px; margin:0;">{status_mt5}</p>
            <p style="color:#8892b0; font-size:12px; margin:4px 0 0;">Atualizado: {agora}</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if not mt5_ok:
    st.error("⚠️ MT5 não conectado. Abra o MetaTrader 5 na VPS e recarregue a página.")
    st.stop()


# ── Carrega dados ────────────────────────────────────────────
@st.cache_data(ttl=60)
def carregar_analise():
    return analyzer.analisar_todos_pares(PARES)

with st.spinner("Calculando Z-scores..."):
    resultados = carregar_analise()

if not resultados:
    st.warning("Carregando dados...")
    st.stop()

oportunidades = [r for r in resultados if r.get("sinal") in ("VENDER_A", "COMPRAR_A")]
monitorando   = [r for r in resultados if r.get("sinal") == "MONITORANDO"]
neutros       = [r for r in resultados if r.get("sinal") == "NEUTRO"]
com_erro      = [r for r in resultados if r.get("erro")]


# ── Métricas do topo ─────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">Oportunidades</div>
        <div class="metric-value green">{len(oportunidades)}</div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">Monitorando</div>
        <div class="metric-value yellow">{len(monitorando)}</div>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">Neutros</div>
        <div class="metric-value gray">{len(neutros)}</div>
    </div>""", unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">Total de Pares</div>
        <div class="metric-value">{len(PARES)}</div>
    </div>""", unsafe_allow_html=True)

with c5:
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">Sem Dados</div>
        <div class="metric-value {"red" if com_erro else "gray"}">{len(com_erro)}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col_refresh, _ = st.columns([1, 6])
with col_refresh:
    if st.button("🔄 Atualizar agora"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")


# ── Abas ─────────────────────────────────────────────────────
aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "🔥  Oportunidades",
    "📈  Gráficos Z-Score",
    "📋  Todos os Pares",
    "💰  Simulador P&L",
    "⚙️  Gestão",
    "📊  Histórico",
])


# ══════════════════════════════════════════════════════════════
# ABA 1 — OPORTUNIDADES
# ══════════════════════════════════════════════════════════════
with aba1:
    if not oportunidades:
        st.markdown("""
        <div style="background:#1a1f35; border:1px solid #2d3250; border-radius:10px;
                    padding:40px; text-align:center; margin-top:20px;">
            <p style="font-size:48px; margin:0;">🔍</p>
            <p style="font-size:18px; color:#ffffff; margin:10px 0 4px;">Nenhuma oportunidade no momento</p>
            <p style="font-size:14px; color:#8892b0;">O sistema está monitorando todos os {len(PARES)} pares.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for r in oportunidades:
            z = r["zscore_atual"]
            is_buy = r["sinal"] == "COMPRAR_A"
            card_class  = "card-buy"  if is_buy else "card-sell"
            badge_class = "badge-buy" if is_buy else "badge-sell"
            z_class     = "z-buy"     if is_buy else "z-sell"
            sinal_texto = r["texto_sinal"]
            emoji = "🟢" if is_buy else "🔴"

            col_card, col_gauge = st.columns([3, 1])

            with col_card:
                st.markdown(f"""
                <div class="card {card_class}">
                    <div class="card-header">
                        <span class="card-title">{emoji} {r['par_a']} / {r['par_b']}</span>
                        <div style="display:flex; gap:8px; align-items:center;">
                            <span class="card-setor">{r['setor']}</span>
                            <span class="{badge_class}">{sinal_texto}</span>
                        </div>
                    </div>
                    <div class="card-info">
                        <div class="info-item">
                            <label>Z-Score</label>
                            <span class="{z_class}">{z:+.4f}</span>
                        </div>
                        <div class="info-item">
                            <label>Beta (β)</label>
                            <span>{r['beta']:.4f}</span>
                        </div>
                        <div class="info-item">
                            <label>Correlação</label>
                            <span>{r['correlacao']:.4f}</span>
                        </div>
                        <div class="info-item">
                            <label>Preço {r['par_a']}</label>
                            <span>R$ {r['preco_a']:.2f}</span>
                        </div>
                        <div class="info-item">
                            <label>Preço {r['par_b']}</label>
                            <span>R$ {r['preco_b']:.2f}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col_gauge:
                cor = "#00c853" if is_buy else "#ff5252"
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=abs(z),
                    number={"font": {"color": cor, "size": 28}, "suffix": ""},
                    gauge={
                        "axis": {"range": [0, 4], "tickcolor": "#8892b0",
                                 "tickfont": {"color": "#8892b0", "size": 10}},
                        "bar": {"color": cor, "thickness": 0.25},
                        "bgcolor": "#13141a",
                        "bordercolor": "#2d3250",
                        "steps": [
                            {"range": [0, 0.5], "color": "#1a1f35"},
                            {"range": [0.5, 2.0], "color": "#1e2235"},
                            {"range": [2.0, 3.5], "color": "#1a2a1a" if is_buy else "#2a1a1a"},
                            {"range": [3.5, 4.0], "color": "#3a1a1a"},
                        ],
                        "threshold": {
                            "line": {"color": "white", "width": 2},
                            "thickness": 0.75,
                            "value": 2.0,
                        },
                    },
                ))
                fig.update_layout(
                    height=160,
                    margin=dict(t=10, b=0, l=10, r=10),
                    paper_bgcolor="#0f1117",
                    font={"color": "#ffffff"},
                )
                st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# ABA 2 — GRÁFICOS
# ══════════════════════════════════════════════════════════════
with aba2:
    opcoes = [f"{r['par_a']} / {r['par_b']}" for r in resultados if not r.get("erro")]

    if not opcoes:
        st.warning("Nenhum dado disponível.")
    else:
        par_sel = st.selectbox("Selecione o par:", opcoes, label_visibility="collapsed")
        idx = opcoes.index(par_sel)
        d = resultados[idx]

        st.markdown(f"### {d['par_a']} / {d['par_b']}  <span style='color:#8892b0; font-size:16px;'>({d['setor']})</span>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Z-Score Atual", f"{d['zscore_atual']:+.4f}")
        c2.metric("Beta (β)", f"{d['beta']:.4f}")
        c3.metric("Correlação", f"{d['correlacao']:.4f}")

        st.markdown("<br>", unsafe_allow_html=True)

        zserie = d.get("zscore_serie")
        if zserie is not None and len(zserie) > 0:
            fig_z = go.Figure()
            fig_z.add_trace(go.Scatter(
                x=zserie.index, y=zserie.values, name="Z-Score",
                line=dict(color="#4488ff", width=2),
                fill="tozeroy", fillcolor="rgba(68,136,255,0.05)"
            ))
            # Linhas de referência
            for val, cor, nome in [
                ( analyzer.Z_ENTRADA,  "#ff5252", "Vender"),
                (-analyzer.Z_ENTRADA,  "#00c853", "Comprar"),
                ( analyzer.Z_SAIDA,    "#555",    ""),
                (-analyzer.Z_SAIDA,    "#555",    ""),
            ]:
                fig_z.add_hline(
                    y=val, line_dash="dash", line_color=cor, line_width=1.5,
                    annotation_text=nome, annotation_font_color=cor
                )
            fig_z.add_hline(y=0, line_color="#444", line_width=1)
            fig_z.update_layout(
                template="plotly_dark",
                paper_bgcolor="#1a1f35",
                plot_bgcolor="#1a1f35",
                height=380,
                margin=dict(t=20, b=40, l=50, r=20),
                xaxis=dict(gridcolor="#2d3250"),
                yaxis=dict(gridcolor="#2d3250"),
                showlegend=False,
            )
            st.plotly_chart(fig_z, use_container_width=True)

        # Preços normalizados
        df_mt5 = mt5c.buscar_historico_par(d["par_a"], d["par_b"])
        if df_mt5 is not None:
            norm_a = (df_mt5[d["par_a"]] / df_mt5[d["par_a"]].iloc[0]) * 100
            norm_b = (df_mt5[d["par_b"]] / df_mt5[d["par_b"]].iloc[0]) * 100

            fig_p = go.Figure()
            fig_p.add_trace(go.Scatter(x=norm_a.index, y=norm_a.values,
                                       name=d["par_a"], line=dict(color="#ff8800", width=2)))
            fig_p.add_trace(go.Scatter(x=norm_b.index, y=norm_b.values,
                                       name=d["par_b"], line=dict(color="#00aaff", width=2)))
            fig_p.update_layout(
                title="Preços normalizados (base 100)",
                template="plotly_dark",
                paper_bgcolor="#1a1f35",
                plot_bgcolor="#1a1f35",
                height=320,
                margin=dict(t=40, b=40, l=50, r=20),
                xaxis=dict(gridcolor="#2d3250"),
                yaxis=dict(gridcolor="#2d3250"),
                legend=dict(bgcolor="#1a1f35", bordercolor="#2d3250"),
            )
            st.plotly_chart(fig_p, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# ABA 3 — TODOS OS PARES
# ══════════════════════════════════════════════════════════════
with aba3:
    for r in resultados:
        z = r.get("zscore_atual")
        sinal = r.get("sinal", "ERRO")

        if sinal in ("VENDER_A", "COMPRAR_A"):
            card_c = "card-buy" if sinal == "COMPRAR_A" else "card-sell"
            emoji  = "🟢" if sinal == "COMPRAR_A" else "🔴"
        elif sinal == "MONITORANDO":
            card_c = "card-watch"
            emoji  = "🟡"
        elif r.get("erro"):
            card_c = "card-neutral"
            emoji  = "❌"
        else:
            card_c = "card-neutral"
            emoji  = "⚪"

        z_str = f"{z:+.3f}" if z is not None else "—"
        pa = r.get("preco_a")
        pb = r.get("preco_b")
        pa_str = f"R$ {pa:.2f}" if pa else "—"
        pb_str = f"R$ {pb:.2f}" if pb else "—"

        st.markdown(f"""
        <div class="card {card_c}" style="padding:14px 20px;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                <span style="font-size:17px; font-weight:700; color:#fff;">{emoji} {r['par_a']} / {r['par_b']}</span>
                <span class="card-setor">{r.get('setor','')}</span>
                <span style="font-size:22px; font-weight:700; color:#{'00e676' if (z or 0)<0 else 'ff5252' if (z or 0)>0 else 'aaa'};">{z_str}</span>
                <span style="font-size:13px; color:#ccc;">{r.get('texto_sinal','—')}</span>
                <span style="font-size:13px; color:#8892b0;">{r['par_a']}: {pa_str} &nbsp;|&nbsp; {r['par_b']}: {pb_str}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# ABA 4 — SIMULADOR P&L
# ══════════════════════════════════════════════════════════════
with aba4:

    st.markdown("### 💰 Simulador de P&L — Posições Abertas")

    abertas = pos.listar_abertas()
    fechadas = pos.listar_fechadas()
    resumo = pos.resumo_fechadas()

    # ── Quantidade global ──────────────────────────────────
    quantidade = st.number_input(
        "Quantidade de ações por ponta (A e B):",
        min_value=1, max_value=10000, value=10, step=1
    )

    st.markdown("---")

    # ── Posições abertas ───────────────────────────────────
    if not abertas:
        st.markdown("""
        <div style="background:#1a1f35; border:1px solid #2d3250; border-radius:10px;
                    padding:30px; text-align:center;">
            <p style="font-size:36px; margin:0;">📭</p>
            <p style="font-size:16px; color:#fff; margin:10px 0 4px;">Nenhuma posição aberta</p>
            <p style="font-size:13px; color:#8892b0;">Posições são abertas automaticamente quando Z-score ≥ ±2.0</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        pl_total_aberto = 0.0

        for p in abertas:
            preco_atual_a = mt5c.buscar_preco_atual(p["par_a"])
            preco_atual_b = mt5c.buscar_preco_atual(p["par_b"])

            if preco_atual_a is None or preco_atual_b is None:
                continue

            pl = pos.calcular_pl(p, preco_atual_a, preco_atual_b, quantidade)
            pl_total_aberto += pl

            pl_cor   = "#00e676" if pl >= 0 else "#ff5252"
            pl_sinal = "+" if pl >= 0 else ""
            card_c   = "card-buy" if pl >= 0 else "card-sell"

            var_a = ((preco_atual_a - p["preco_entrada_a"]) / p["preco_entrada_a"]) * 100
            var_b = ((preco_atual_b - p["preco_entrada_b"]) / p["preco_entrada_b"]) * 100

            col_card, col_fechar = st.columns([5, 1])

            with col_card:
                st.markdown(f"""
                <div class="card {card_c}">
                    <div class="card-header">
                        <span class="card-title">{p['par_a']} / {p['par_b']}</span>
                        <span class="card-setor">{p['setor']}</span>
                        <span style="font-size:26px; font-weight:800; color:{pl_cor};">
                            {pl_sinal}R$ {pl:.2f}
                        </span>
                    </div>
                    <div class="card-info">
                        <div class="info-item">
                            <label>Entrada em</label>
                            <span>{p['data_entrada']} {p['hora_entrada']}</span>
                        </div>
                        <div class="info-item">
                            <label>Z Entrada</label>
                            <span>{p['zscore_entrada']:+.3f}</span>
                        </div>
                        <div class="info-item">
                            <label>Entrada {p['par_a']}</label>
                            <span>R$ {p['preco_entrada_a']:.2f}</span>
                        </div>
                        <div class="info-item">
                            <label>Atual {p['par_a']}</label>
                            <span>R$ {preco_atual_a:.2f}
                                <small style="color:{'#00e676' if var_a>=0 else '#ff5252'}">
                                    ({'+' if var_a>=0 else ''}{var_a:.1f}%)
                                </small>
                            </span>
                        </div>
                        <div class="info-item">
                            <label>Entrada {p['par_b']}</label>
                            <span>R$ {p['preco_entrada_b']:.2f}</span>
                        </div>
                        <div class="info-item">
                            <label>Atual {p['par_b']}</label>
                            <span>R$ {preco_atual_b:.2f}
                                <small style="color:{'#00e676' if var_b>=0 else '#ff5252'}">
                                    ({'+' if var_b>=0 else ''}{var_b:.1f}%)
                                </small>
                            </span>
                        </div>
                        <div class="info-item">
                            <label>Qtd por ponta</label>
                            <span>{quantidade}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col_fechar:
                st.markdown("<br><br><br>", unsafe_allow_html=True)
                if st.button("✅ Fechar", key=f"fechar_{p['id']}"):
                    # Busca Z-score atual para registrar na saída
                    dados_par = next(
                        (r for r in resultados
                         if r.get("par_a") == p["par_a"] and r.get("par_b") == p["par_b"]),
                        None
                    )
                    z_saida = dados_par["zscore_atual"] if dados_par else 0.0
                    pos.fechar_posicao(p["id"], preco_atual_a, preco_atual_b, z_saida, quantidade)
                    st.success("Posição fechada!")
                    st.cache_data.clear()
                    st.rerun()

        # ── Resumo das abertas ─────────────────────────────
        st.markdown("---")
        pl_cor_total = "#00e676" if pl_total_aberto >= 0 else "#ff5252"
        st.markdown(f"""
        <div style="background:#1a1f35; border:1px solid #2d3250; border-radius:10px;
                    padding:20px 30px; text-align:center;">
            <p style="color:#8892b0; font-size:13px; margin:0 0 6px;">
                P&L TOTAL ESTIMADO ({len(abertas)} posição(ões) × {quantidade} ações)
            </p>
            <p style="font-size:40px; font-weight:800; color:{pl_cor_total}; margin:0;">
                {'+'if pl_total_aberto>=0 else ''}R$ {pl_total_aberto:.2f}
            </p>
        </div>
        """, unsafe_allow_html=True)

    # ── Resumo das fechadas ────────────────────────────────
    if fechadas:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📋 Operações Fechadas")

        if resumo:
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Total de Operações", resumo["total_operacoes"])
            c2.metric("Vencedoras",         f"{resumo['vencedoras']} ({resumo['taxa_acerto']}%)")
            c3.metric("P&L Total",          f"R$ {resumo['pl_total']:.2f}")
            c4.metric("Maior Ganho",        f"R$ {resumo['maior_ganho']:.2f}")
            c5.metric("Maior Perda",        f"R$ {resumo['maior_perda']:.2f}")

        st.markdown("<br>", unsafe_allow_html=True)

        linhas = []
        for p in reversed(fechadas):
            pl = p.get("pl_final", 0) or 0
            linhas.append({
                "Par":          f"{p['par_a']} / {p['par_b']}",
                "Setor":        p["setor"],
                "Entrada":      f"{p['data_entrada']} {p['hora_entrada']}",
                "Fechamento":   p.get("data_fechamento", "—"),
                "Z Entrada":    p["zscore_entrada"],
                "Z Saída":      p.get("zscore_saida", "—"),
                "P&L (R$)":     round(pl, 2),
            })

        df_fechadas = pd.DataFrame(linhas)

        def cor_pl(val):
            try:
                return "color: #00e676" if float(val) >= 0 else "color: #ff5252"
            except Exception:
                return ""

        st.dataframe(
            df_fechadas.style.applymap(cor_pl, subset=["P&L (R$)"]),
            use_container_width=True,
            height=300,
        )

        csv = df_fechadas.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Exportar operações fechadas", csv,
                           "operacoes_fechadas.csv", "text/csv")


# ══════════════════════════════════════════════════════════════
# ABA 5 — GESTÃO DE OPERAÇÕES
# ══════════════════════════════════════════════════════════════
with aba5:

    config_atual = cfg_op.get_config()
    conta = gestor.get_info_conta()

    # ── Conta MT5 ──────────────────────────────────────────
    st.markdown("### 🏦 Conta MT5 — Genial")
    if conta:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Saldo",        f"R$ {conta['saldo']:,.2f}")
        c2.metric("Equity",       f"R$ {conta['equity']:,.2f}")
        c3.metric("Margem Livre", f"R$ {conta['margem_livre']:,.2f}")
        c4.metric("Lucro Aberto", f"R$ {conta['lucro']:,.2f}",
                  delta=f"{conta['lucro']:+.2f}")
    else:
        st.warning("Não foi possível obter dados da conta. MT5 conectado?")

    st.markdown("---")

    # ── Controles globais ──────────────────────────────────
    st.markdown("### ⚙️ Configurações Globais")

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        simulacao = st.toggle(
            "🔵 Modo Simulação (sem ordens reais)",
            value=config_atual.get("modo_simulacao", True),
            help="Ligado = calcula tudo mas NÃO envia ordens ao MT5"
        )
        if simulacao != config_atual.get("modo_simulacao"):
            cfg_op.set_simulacao(simulacao)

    with col_b:
        auto = st.toggle(
            "🤖 Execução Automática",
            value=config_atual.get("auto_executar", False),
            help="Quando ativado, executa ordens automaticamente a cada atualização"
        )
        if auto != config_atual.get("auto_executar"):
            cfg_op.set_auto_executar(auto)

    with col_c:
        pct = st.slider(
            "💰 % do saldo para operar",
            min_value=1, max_value=100,
            value=int(config_atual.get("percentual_capital", 30)),
            step=1,
            help="Percentual do saldo livre que será distribuído entre os pares habilitados"
        )
        if pct != config_atual.get("percentual_capital"):
            cfg_op.set_percentual(pct)

    # Preview do capital alocado
    if conta:
        capital_alocado = conta["margem_livre"] * (pct / 100)
        st.info(f"💡 Com {pct}% do saldo livre → **R$ {capital_alocado:,.2f}** disponível para operar")

    if auto and not simulacao:
        st.error("⚠️ **ATENÇÃO: Execução Automática REAL ativada.** "
                 "O sistema enviará ordens reais ao MT5 quando detectar oportunidades nos pares habilitados.")
    elif auto and simulacao:
        st.success("✅ Execução Automática em **MODO SIMULAÇÃO** — ordens calculadas mas não enviadas ao MT5.")

    st.markdown("---")

    # ── Habilitar / desabilitar pares ──────────────────────
    st.markdown("### 📋 Pares — Habilitar para operação automática")

    col_btn1, col_btn2, _ = st.columns([1, 1, 5])
    with col_btn1:
        if st.button("✅ Habilitar todos"):
            cfg_op.habilitar_todos(PARES)
            st.rerun()
    with col_btn2:
        if st.button("❌ Desabilitar todos"):
            cfg_op.desabilitar_todos(PARES)
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Agrupa por setor
    setores = {}
    for par in PARES:
        setores.setdefault(par["setor"], []).append(par)

    pares_habilitados_count = 0

    for setor, pares_setor in setores.items():
        st.markdown(f"**{setor}**")
        cols = st.columns(min(len(pares_setor), 3))

        for i, par in enumerate(pares_setor):
            habilitado = config_atual["pares_habilitados"].get(
                f"{par['par_a']}_{par['par_b']}", False
            )
            if habilitado:
                pares_habilitados_count += 1

            # Busca Z-score atual
            dado_par = next(
                (r for r in resultados
                 if r.get("par_a") == par["par_a"] and r.get("par_b") == par["par_b"]),
                None
            )
            z_str = f"Z: {dado_par['zscore_atual']:+.2f}" if dado_par and dado_par.get("zscore_atual") else "Z: —"
            emoji_z = dado_par.get("emoji", "⚪") if dado_par else "⚪"

            with cols[i % 3]:
                novo = st.checkbox(
                    f"{emoji_z} {par['par_a']} / {par['par_b']}  `{z_str}`",
                    value=habilitado,
                    key=f"ck_{par['par_a']}_{par['par_b']}"
                )
                if novo != habilitado:
                    cfg_op.set_par_habilitado(par["par_a"], par["par_b"], novo)
                    st.rerun()

        st.markdown("")

    # Preview da distribuição de capital
    if pares_habilitados_count > 0 and conta:
        capital_total = conta["margem_livre"] * (pct / 100)
        capital_por_par = capital_total / pares_habilitados_count

        st.markdown("---")
        st.markdown(f"### 💡 Distribuição de Capital — {pares_habilitados_count} par(es) habilitado(s)")

        oport_habilitadas = [
            r for r in resultados
            if r.get("sinal") in ("VENDER_A", "COMPRAR_A")
            and cfg_op.is_par_habilitado(r["par_a"], r["par_b"])
        ]

        if oport_habilitadas:
            st.success(f"🔥 {len(oport_habilitadas)} oportunidade(s) ativa(s) nos pares habilitados")
            dist = gestor.calcular_distribuicao(oport_habilitadas)

            linhas_dist = []
            for op in dist:
                linhas_dist.append({
                    "Par":            f"{op['par_a']} / {op['par_b']}",
                    "Z-Score":        f"{op['zscore_atual']:+.3f}",
                    "Sinal":          op["texto_sinal"],
                    f"Qtd {op['par_a']}": op["qty_a"],
                    f"Qtd {op['par_b']}": op["qty_b"],
                    "Capital (R$)":   f"R$ {op['capital_alocado']:,.2f}",
                })
            st.dataframe(pd.DataFrame(linhas_dist), use_container_width=True)
        else:
            st.info("Nenhuma oportunidade ativa nos pares habilitados no momento.")

    st.markdown("---")

    # ── Log de ordens ──────────────────────────────────────
    st.markdown("### 📋 Log de Ordens")
    log = gestor.carregar_log()
    if not log:
        st.info("Nenhuma ordem registrada ainda.")
    else:
        df_log = pd.DataFrame(reversed(log))
        cols_show = ["timestamp", "par_a", "par_b", "sinal",
                     "zscore", "qty_a", "qty_b", "status", "simulacao"]
        cols_show = [c for c in cols_show if c in df_log.columns]
        st.dataframe(df_log[cols_show], use_container_width=True, height=300)

        csv_log = df_log.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Exportar log", csv_log, "log_ordens.csv", "text/csv")


# ══════════════════════════════════════════════════════════════
# ABA 6 — HISTÓRICO
# ══════════════════════════════════════════════════════════════
with aba6:
    df_hist = analyzer.carregar_historico_df()
    stats   = analyzer.estatisticas_historico()

    if df_hist.empty:
        st.markdown("""
        <div style="background:#1a1f35; border:1px solid #2d3250; border-radius:10px;
                    padding:40px; text-align:center;">
            <p style="font-size:40px; margin:0;">📋</p>
            <p style="font-size:16px; color:#fff; margin:10px 0 4px;">Histórico ainda vazio</p>
            <p style="font-size:13px; color:#8892b0;">Oportunidades detectadas serão registradas automaticamente aqui.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total de Oportunidades", stats.get("total_oportunidades", 0))
        c2.metric("Pares com Ocorrências",  stats.get("pares_ativos", 0))
        c3.metric("Z-Score Médio",          stats.get("zscore_medio", 0))
        c4.metric("Setor Mais Ativo",       stats.get("setor_mais_ativo", "—"))

        st.markdown("<br>", unsafe_allow_html=True)

        col_g1, col_g2 = st.columns(2)

        with col_g1:
            contagem = df_hist.groupby("par").size().reset_index(name="n")
            fig_bar = px.bar(contagem.sort_values("n"), x="n", y="par",
                             orientation="h", template="plotly_dark",
                             color="n", color_continuous_scale="Blues",
                             title="Oportunidades por Par")
            fig_bar.update_layout(
                paper_bgcolor="#1a1f35", plot_bgcolor="#1a1f35",
                height=350, showlegend=False, coloraxis_showscale=False,
                margin=dict(t=40, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_g2:
            if "setor" in df_hist.columns:
                cont_s = df_hist.groupby("setor").size().reset_index(name="n")
                fig_pie = px.pie(cont_s, names="setor", values="n",
                                 template="plotly_dark", title="Por Setor",
                                 color_discrete_sequence=px.colors.sequential.Blues_r)
                fig_pie.update_layout(
                    paper_bgcolor="#1a1f35",
                    height=350, margin=dict(t=40, b=20, l=20, r=20)
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        st.dataframe(
            df_hist[["data","hora","par","setor","zscore","texto","preco_a","preco_b"]],
            use_container_width=True, height=350
        )

        csv = df_hist.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Exportar CSV", csv, "historico.csv", "text/csv")
