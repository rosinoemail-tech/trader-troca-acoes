# ============================================================
# PAINEL TRADER TROCA DE AÇÕES — Layout redesenhado
# ============================================================

import os
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
        color: #aab4c8;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        display: block;
        font-weight: 500;
    }
    .info-item span {
        font-size: 18px;
        font-weight: 600;
        color: #ffffff;
    }
    .z-buy  { color: #00e676 !important; }
    .z-sell { color: #ff5252 !important; }

    /* Forçar texto branco em todos os elementos dentro dos cards */
    .card p, .card div, .card span:not([class*="badge"]):not(.card-setor):not(.card-title) {
        color: #ffffff;
    }
    /* Labels e textos secundários do Streamlit mais brilhantes */
    .stCheckbox label, .stNumberInput label,
    div[data-testid="stWidgetLabel"] p,
    div[data-testid="stCaptionContainer"] p {
        color: #d0d8e8 !important;
        font-weight: 500 !important;
    }
    /* Seção de setor (títulos h4) */
    h4 { color: #e0e8f8 !important; }

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


# ── Sincroniza posições com MT5 ──────────────────────────────
_sync = gestor.sincronizar_posicoes_mt5(PARES)
if _sync["novos_registros"] > 0:
    st.toast(f"🔄 {_sync['novos_registros']} posição(ões) importada(s) do MT5", icon="📥")
if _sync["fechamentos"] > 0:
    st.toast(f"✅ {_sync['fechamentos']} posição(ões) fechada(s) detectada(s) no MT5", icon="📤")


# ── Carrega dados ────────────────────────────────────────────
import json as _json

ROBOT_STATUS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "robot_status.json")

def _salvar_status_robo(n_opor: int, n_exec: int):
    try:
        _json.dump({
            "ultimo_ciclo":   datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "oportunidades":  n_opor,
            "execucoes":      n_exec,
        }, open(ROBOT_STATUS_FILE, "w", encoding="utf-8"))
    except Exception:
        pass

def _ler_status_robo() -> dict:
    try:
        return _json.load(open(ROBOT_STATUS_FILE, "r", encoding="utf-8"))
    except Exception:
        return {}

@st.cache_data(ttl=60)
def carregar_analise():
    """Apenas análise — cacheada por 60s. Sem efeitos colaterais."""
    return analyzer.analisar_todos_pares(PARES)

with st.spinner("Calculando Z-scores..."):
    resultados = carregar_analise()

# Execução de ordens: SEMPRE roda a cada ciclo, nunca cacheada
analyzer.executar_ciclo(resultados)

# Atualiza contadores do status do robô
n_opor = sum(1 for r in resultados if r.get("sinal") in ("VENDER_A", "COMPRAR_A"))
log    = gestor.carregar_log()
hoje   = datetime.now().strftime("%d/%m/%Y")
# Conta apenas ordens realmente executadas no MT5 (não simuladas, não com erro)
n_exec = len([l for l in log
              if l.get("timestamp", "")[:10] == hoje
              and l.get("status") == "executado"])
_salvar_status_robo(n_opor, n_exec)

if not resultados:
    st.warning("Carregando dados...")
    st.stop()

oportunidades = [r for r in resultados if r.get("sinal") in ("VENDER_A", "COMPRAR_A")]
monitorando   = [r for r in resultados if r.get("sinal") == "MONITORANDO"]
neutros       = [r for r in resultados if r.get("sinal") == "NEUTRO"]
com_erro      = [r for r in resultados if r.get("erro")]


# ── Barra de status do robô ───────────────────────────────────
_cfg_robo   = cfg_op.get_config()
_auto_on    = _cfg_robo.get("auto_executar", False)
_sim_on     = _cfg_robo.get("modo_simulacao", True)
_status_arq = _ler_status_robo()
_ult_ciclo  = _status_arq.get("ultimo_ciclo", "—")
_n_opor_arq = _status_arq.get("oportunidades", 0)
_n_exec_arq = _status_arq.get("execucoes", 0)

_h_ini = cfg_op.get_horario_inicio()
_h_fim = cfg_op.get_horario_fim()
_agora_t   = datetime.now().time()
_hi_t = datetime.strptime(_h_ini, "%H:%M").time()
_hf_t = datetime.strptime(_h_fim, "%H:%M").time()
_mercado_ok = _hi_t <= _agora_t <= _hf_t

if _auto_on and not _sim_on and _mercado_ok:
    _robo_cor    = "#00e676"
    _robo_icone  = "🟢"
    _robo_status = "ROBÔ ATIVO — enviando ordens reais ao MT5"
elif _auto_on and _sim_on:
    _robo_cor    = "#ffd600"
    _robo_icone  = "🟡"
    _robo_status = "ROBÔ EM SIMULAÇÃO — calculando ordens mas NÃO enviando ao MT5"
elif _auto_on and not _mercado_ok:
    _robo_cor    = "#ff9100"
    _robo_icone  = "🟠"
    _robo_status = f"ROBÔ AGUARDANDO HORÁRIO — fora da janela {_h_ini}–{_h_fim}"
else:
    _robo_cor    = "#ff5252"
    _robo_icone  = "🔴"
    _robo_status = "ROBÔ DESLIGADO — Execução Automática está OFF na aba Gestão"

st.markdown(f"""
<div style="background:#12191f; border:1px solid {_robo_cor}44;
            border-left: 4px solid {_robo_cor};
            border-radius:10px; padding:14px 24px; margin-bottom:16px;
            display:flex; flex-wrap:wrap; gap:24px; align-items:center;">
    <div>
        <span style="font-size:16px; font-weight:700; color:{_robo_cor};">
            {_robo_icone} {_robo_status}
        </span>
    </div>
    <div style="display:flex; gap:24px; flex-wrap:wrap; margin-left:auto;">
        <div style="text-align:center;">
            <div style="font-size:10px; color:#8892b0; text-transform:uppercase; letter-spacing:1px;">Último ciclo</div>
            <div style="font-size:14px; font-weight:600; color:#fff;">{_ult_ciclo}</div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:10px; color:#8892b0; text-transform:uppercase; letter-spacing:1px;">Oportunidades hoje</div>
            <div style="font-size:14px; font-weight:600; color:#ffd600;">{_n_opor_arq}</div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:10px; color:#8892b0; text-transform:uppercase; letter-spacing:1px;">Ordens hoje</div>
            <div style="font-size:14px; font-weight:600; color:#00e676;">{_n_exec_arq}</div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:10px; color:#8892b0; text-transform:uppercase; letter-spacing:1px;">Ciclo</div>
            <div style="font-size:14px; font-weight:600; color:#8892b0;">60s</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


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
                _z_ent  = cfg_op.get_z_entrada()
                _z_sai  = cfg_op.get_z_saida()
                _z_stp  = cfg_op.get_z_stop()
                _gauge_max = _z_stp + 0.5
                cor = "#00c853" if is_buy else "#ff5252"
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=abs(z),
                    number={"font": {"color": cor, "size": 28}, "suffix": ""},
                    gauge={
                        "axis": {"range": [0, _gauge_max], "tickcolor": "#8892b0",
                                 "tickfont": {"color": "#8892b0", "size": 10}},
                        "bar": {"color": cor, "thickness": 0.25},
                        "bgcolor": "#13141a",
                        "bordercolor": "#2d3250",
                        "steps": [
                            {"range": [0, _z_sai], "color": "#1a1f35"},
                            {"range": [_z_sai, _z_ent], "color": "#1e2235"},
                            {"range": [_z_ent, _z_stp], "color": "#1a2a1a" if is_buy else "#2a1a1a"},
                            {"range": [_z_stp, _gauge_max], "color": "#3a1a1a"},
                        ],
                        "threshold": {
                            "line": {"color": "white", "width": 2},
                            "thickness": 0.75,
                            "value": _z_ent,
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
                ( cfg_op.get_z_entrada(),  "#ff5252", "Vender"),
                (-cfg_op.get_z_entrada(),  "#00c853", "Comprar"),
                ( cfg_op.get_z_saida(),    "#555",    ""),
                (-cfg_op.get_z_saida(),    "#555",    ""),
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

    col_pl_btn, _ = st.columns([2, 5])
    with col_pl_btn:
        if st.button("🗑️ Limpar posições fantasmas",
                     help="Remove posições registradas no painel que não existem no MT5 "
                          "(causadas por bug anterior — use se a posição não aparecer no MT5)"):
            sync_result = gestor.sincronizar_posicoes_mt5(PARES)
            st.success(f"Limpeza concluída. {sync_result['fechamentos']} posição(ões) removida(s).")
            st.cache_data.clear()
            st.rerun()

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
            <p style="font-size:13px; color:#8892b0;">Posições são abertas automaticamente quando Z-score ≥ ±{cfg_op.get_z_entrada():.1f}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        pl_total_aberto = 0.0

        for p in abertas:
            preco_atual_a = mt5c.buscar_preco_atual(p["par_a"])
            preco_atual_b = mt5c.buscar_preco_atual(p["par_b"])

            if preco_atual_a is None or preco_atual_b is None:
                continue

            # Usa qtd real do MT5 para posições importadas, senão usa o campo global
            qty_real = p.get("quantidade_mt5") or quantidade
            pl = pos.calcular_pl(p, preco_atual_a, preco_atual_b, qty_real)
            pl_total_aberto += pl

            pl_cor   = "#00e676" if pl >= 0 else "#ff5252"
            pl_sinal = "+" if pl >= 0 else ""
            card_c   = "card-buy" if pl >= 0 else "card-sell"

            var_a = ((preco_atual_a - p["preco_entrada_a"]) / p["preco_entrada_a"]) * 100
            var_b = ((preco_atual_b - p["preco_entrada_b"]) / p["preco_entrada_b"]) * 100

            origem_badge = (
                '<span style="background:#1e3a5f; color:#64b5f6; font-size:11px; '
                'padding:2px 8px; border-radius:10px; font-weight:600;">📥 Importado MT5</span>'
                if p.get("origem") == "manual"
                else
                '<span style="background:#1a2e1a; color:#81c784; font-size:11px; '
                'padding:2px 8px; border-radius:10px; font-weight:600;">🤖 Robô</span>'
            )

            col_card, col_fechar = st.columns([5, 1])

            with col_card:
                st.markdown(f"""
                <div class="card {card_c}">
                    <div class="card-header">
                        <span class="card-title">{p['par_a']} / {p['par_b']}</span>
                        <span class="card-setor">{p['setor']}</span>
                        {origem_badge}
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
                            <span>{qty_real}</span>
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
            df_fechadas.style.map(cor_pl, subset=["P&L (R$)"]),
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
    capital_manual_cfg = cfg_op.get_capital_manual()

    if conta:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Saldo",        f"R$ {conta['saldo']:,.2f}")
        c2.metric("Equity",       f"R$ {conta['equity']:,.2f}")
        c3.metric("Margem Livre", f"R$ {conta['margem_livre']:,.2f}")
        c4.metric("Lucro Aberto", f"R$ {conta['lucro']:,.2f}",
                  delta=f"{conta['lucro']:+.2f}")
    else:
        st.warning("Não foi possível obter dados da conta. MT5 conectado?")

    # Capital usado para cálculo de ordens (manual sobrepõe MT5)
    saldo_efetivo = capital_manual_cfg if capital_manual_cfg > 0 else (
        conta.get("margem_livre", 0) if conta else 0
    )
    if capital_manual_cfg > 0:
        st.info(f"💼 **Capital Manual Ativo:** R$ {capital_manual_cfg:,.2f} "
                f"— este valor é usado para calcular as ordens (substitui o saldo do MT5)")

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
            "💰 % do capital para operar",
            min_value=1, max_value=100,
            value=int(config_atual.get("percentual_capital", 30)),
            step=1,
            help="Percentual do capital disponível que será distribuído entre os pares habilitados"
        )
        if pct != config_atual.get("percentual_capital"):
            cfg_op.set_percentual(pct)

    # ── Parâmetros de Trading ──────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📐 Parâmetros de Trading")
    st.caption("Defina os limiares de Z-score que controlam entradas, saídas e stop loss.")

    z_ent_cfg  = cfg_op.get_z_entrada()
    z_sai_cfg  = cfg_op.get_z_saida()
    z_stop_cfg = cfg_op.get_z_stop()

    col_ze, col_zs, col_zst = st.columns(3)

    with col_ze:
        z_ent_new = st.slider(
            "🟢 Z Entrada — abrir posição",
            min_value=0.5, max_value=5.0,
            value=z_ent_cfg, step=0.1, format="%.1f",
            help="Abre posição quando |Z-score| ultrapassa este valor"
        )

    with col_zs:
        z_sai_new = st.slider(
            "⚪ Z Saída — fechar posição",
            min_value=0.1, max_value=2.0,
            value=z_sai_cfg, step=0.1, format="%.1f",
            help="Fecha posição quando |Z-score| fica abaixo deste valor (convergência)"
        )

    with col_zst:
        z_stop_new = st.slider(
            "🔴 Stop Loss",
            min_value=2.0, max_value=6.0,
            value=z_stop_cfg, step=0.1, format="%.1f",
            help="Sai imediatamente se |Z-score| exceder este valor (situação extrema)"
        )

    # Validação
    _z_erros = []
    if z_sai_new >= z_ent_new:
        _z_erros.append("⚠️ **Z Saída** deve ser menor que **Z Entrada**.")
    if z_stop_new <= z_ent_new:
        _z_erros.append("⚠️ **Stop Loss** deve ser maior que **Z Entrada**.")

    if _z_erros:
        for msg in _z_erros:
            st.warning(msg)
    else:
        st.markdown(f"""
        <div style="background:#12191f; border:1px solid #2d3250; border-radius:10px;
                    padding:14px 24px; margin:8px 0;">
            <div style="font-size:11px; color:#8892b0; text-transform:uppercase;
                        letter-spacing:1px; margin-bottom:10px;">Prévia dos limiares</div>
            <div style="font-family:monospace; font-size:13px; line-height:2;">
                <span style="color:#ff5252;">────── Stop Loss ──</span>
                <span style="color:#ff5252; font-weight:700; margin-left:8px;">±{z_stop_new:.1f}</span><br>
                <span style="color:#ffd600;">────── Entrada ────</span>
                <span style="color:#ffd600; font-weight:700; margin-left:8px;">±{z_ent_new:.1f}</span><br>
                <span style="color:#8892b0;">── ── Saída ── ──</span>
                <span style="color:#8892b0; font-weight:700; margin-left:8px;">±{z_sai_new:.1f}</span><br>
                <span style="color:#444;">────────── Zero ───</span>
                <span style="color:#444; font-weight:700; margin-left:8px;">0.0</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if z_ent_new != z_ent_cfg:
            cfg_op.set_z_entrada(z_ent_new)
        if z_sai_new != z_sai_cfg:
            cfg_op.set_z_saida(z_sai_new)
        if z_stop_new != z_stop_cfg:
            cfg_op.set_z_stop(z_stop_new)

    st.markdown("---")
    st.markdown("#### 💼 Gestão de Capital por Operação")
    st.caption("O robô abre quantas operações simultâneas couberem no saldo disponível com base no valor por operação.")

    _valor_op_cfg  = cfg_op.get_valor_por_operacao()
    _pct_lucro_cfg = cfg_op.get_percentual_lucro()
    _corr_min_cfg  = cfg_op.get_correlacao_minima()
    _saldo_efetivo = cfg_op.get_capital_manual() or 0.0

    col_vop, col_pct, col_slots = st.columns(3)

    with col_vop:
        valor_op_new = st.number_input(
            "💰 Valor por Operação (R$)",
            min_value=10.0, max_value=1000000.0,
            value=_valor_op_cfg, step=10.0, format="%.2f",
            help="Capital alocado em cada par. O robô abre quantas operações couberem no saldo disponível."
        )

    with col_pct:
        pct_lucro_new = st.number_input(
            "🎯 Lucro Alvo (%)",
            min_value=0.1, max_value=100.0,
            value=_pct_lucro_cfg, step=0.1, format="%.1f",
            help="Fecha a posição quando o lucro atingir este % do capital alocado naquela operação."
        )

    with col_slots:
        slots_possiveis = int(_saldo_efetivo // valor_op_new) if valor_op_new > 0 and _saldo_efetivo > 0 else "—"
        lucro_por_op    = round(valor_op_new * pct_lucro_new / 100, 2)
        st.markdown("<br>", unsafe_allow_html=True)
        st.metric("Slots simultâneos", slots_possiveis)
        st.caption(f"Alvo por op: R$ {lucro_por_op:.2f}")

    if valor_op_new != _valor_op_cfg:
        cfg_op.set_valor_por_operacao(valor_op_new)
    if pct_lucro_new != _pct_lucro_cfg:
        cfg_op.set_percentual_lucro(pct_lucro_new)

    st.markdown("---")
    st.markdown("#### 🛡️ Proteção Adicional")
    st.caption("Fecha a posição se a correlação entre os ativos cair abaixo do mínimo. 0 = desativado.")

    corr_min_new = st.slider(
        "📉 Correlação Mínima",
        min_value=0.0, max_value=1.0,
        value=_corr_min_cfg, step=0.05, format="%.2f",
        help="Fecha a posição se a correlação cair abaixo deste valor. 0 = desativado."
    )
    if corr_min_new > 0:
        st.caption(f"✅ Ativo — fecha se correlação < {corr_min_new:.2f}")
    else:
        st.caption("⬜ Desativado")

    if corr_min_new != _corr_min_cfg:
        cfg_op.set_correlacao_minima(corr_min_new)

    st.markdown("---")

    # ── Capital Manual ─────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 💼 Capital Disponível para Operações")
    st.caption("Se o saldo do MT5 aparecer zerado (problema de integração Genial), "
               "informe o valor manualmente. Zero = usar saldo real do MT5.")

    col_cap1, col_cap2 = st.columns([2, 3])
    with col_cap1:
        cap_input = st.number_input(
            "Capital Manual (R$)  —  0 = usar MT5",
            min_value=0.0,
            max_value=10_000_000.0,
            value=float(config_atual.get("capital_manual", 0.0)),
            step=100.0,
            format="%.2f",
            key="capital_manual_input",
        )
        if cap_input != config_atual.get("capital_manual", 0.0):
            cfg_op.set_capital_manual(cap_input)
            st.rerun()

    with col_cap2:
        capital_alocado = saldo_efetivo * (pct / 100)
        fonte = "Manual" if capital_manual_cfg > 0 else "MT5"
        cor_fonte = "#64b5f6" if capital_manual_cfg > 0 else "#81c784"
        st.markdown(f"""
        <div style="background:#1a1f35; border:1px solid #2d3250; border-radius:10px;
                    padding:16px 20px; margin-top:4px;">
            <div style="font-size:11px; color:#8892b0; text-transform:uppercase;
                        letter-spacing:1px; margin-bottom:6px;">
                Capital base
                <span style="color:{cor_fonte}; margin-left:8px;">({fonte})</span>
            </div>
            <div style="font-size:28px; font-weight:700; color:#fff;">
                R$ {saldo_efetivo:,.2f}
            </div>
            <div style="font-size:13px; color:#8892b0; margin-top:4px;">
                Com {pct}% →
                <span style="color:#ffd600; font-weight:600;">
                    R$ {capital_alocado:,.2f}
                </span>
                disponível para distribuir nos pares
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Horário de operação ────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🕐 Horário de Operação")
    st.caption("Fora desse intervalo o robô NÃO envia ordens reais ao MT5.")

    col_h1, col_h2, col_h3 = st.columns([1, 1, 3])
    with col_h1:
        h_ini_cfg = cfg_op.get_horario_inicio()
        h_ini_val = datetime.strptime(h_ini_cfg, "%H:%M").time()
        h_ini_new = st.time_input("Início", value=h_ini_val, key="h_inicio", step=300)
        h_ini_str = h_ini_new.strftime("%H:%M")
        if h_ini_str != h_ini_cfg:
            cfg_op.set_horario_inicio(h_ini_str)
            st.rerun()

    with col_h2:
        h_fim_cfg = cfg_op.get_horario_fim()
        h_fim_val = datetime.strptime(h_fim_cfg, "%H:%M").time()
        h_fim_new = st.time_input("Fim", value=h_fim_val, key="h_fim", step=300)
        h_fim_str = h_fim_new.strftime("%H:%M")
        if h_fim_str != h_fim_cfg:
            cfg_op.set_horario_fim(h_fim_str)
            st.rerun()

    with col_h3:
        agora_t = datetime.now().time()
        h_ini_t = datetime.strptime(cfg_op.get_horario_inicio(), "%H:%M").time()
        h_fim_t = datetime.strptime(cfg_op.get_horario_fim(), "%H:%M").time()
        mercado_ok = h_ini_t <= agora_t <= h_fim_t
        cor_status = "#00e676" if mercado_ok else "#ff5252"
        status_txt = f"🟢 Dentro do horário ({agora_t.strftime('%H:%M')})" if mercado_ok \
                     else f"🔴 Fora do horário ({agora_t.strftime('%H:%M')})"
        st.markdown(f"""
        <div style="background:#1a1f35; border:1px solid #2d3250; border-radius:10px;
                    padding:14px 20px; margin-top:28px;">
            <div style="font-size:11px; color:#aab4c8; text-transform:uppercase;
                        letter-spacing:1px; margin-bottom:4px;">Status atual</div>
            <div style="font-size:20px; font-weight:700; color:{cor_status};">{status_txt}</div>
            <div style="font-size:12px; color:#aab4c8; margin-top:2px;">
                Janela: {cfg_op.get_horario_inicio()} → {cfg_op.get_horario_fim()}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

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
        st.markdown(
            f'<div style="font-size:18px; font-weight:700; color:#e0e8f8; '
            f'border-left:3px solid #4a6fa5; padding-left:10px; margin:16px 0 8px;">'
            f'{setor}</div>',
            unsafe_allow_html=True
        )

        for par in pares_setor:
            habilitado = config_atual["pares_habilitados"].get(
                f"{par['par_a']}_{par['par_b']}", False
            )
            if habilitado:
                pares_habilitados_count += 1

            # Dados do par nos resultados atuais
            d = next(
                (r for r in resultados
                 if r.get("par_a") == par["par_a"] and r.get("par_b") == par["par_b"]),
                None
            )

            z         = d["zscore_atual"] if d and d.get("zscore_atual") is not None else None
            sinal     = d.get("sinal", "NEUTRO") if d else "NEUTRO"
            emoji_z   = d.get("emoji", "⚪") if d else "⚪"
            preco_a   = d.get("preco_a") if d else None
            preco_b   = d.get("preco_b") if d else None
            beta      = d.get("beta") if d else None
            corr      = d.get("correlacao") if d else None
            texto_sin = d.get("texto_sinal", "—") if d else "—"

            # Cor do card baseada no estado
            if sinal == "COMPRAR_A":
                card_c = "card-buy"
            elif sinal == "VENDER_A":
                card_c = "card-sell"
            elif habilitado:
                card_c = "card-watch"
            else:
                card_c = "card-neutral"

            # Cor do Z-score
            z_cor = "#00e676" if (z or 0) < 0 else "#ff5252" if (z or 0) > 0 else "#8892b0"
            z_str = f"{z:+.4f}" if z is not None else "—"

            col_card, col_controls = st.columns([5, 2])

            with col_card:
                st.markdown(f"""
                <div class="card {card_c}">
                    <div class="card-header">
                        <span class="card-title">{emoji_z} {par['par_a']} / {par['par_b']}</span>
                        <span class="card-setor">{par['setor']}</span>
                        <span style="font-size:22px; font-weight:800; color:{z_cor};">Z {z_str}</span>
                    </div>
                    <div class="card-info">
                        <div class="info-item">
                            <label>Sinal</label>
                            <span style="font-size:14px;">{texto_sin}</span>
                        </div>
                        <div class="info-item">
                            <label>Preço {par['par_a']}</label>
                            <span>{"R$ " + f"{preco_a:.2f}" if preco_a else "—"}</span>
                        </div>
                        <div class="info-item">
                            <label>Preço {par['par_b']}</label>
                            <span>{"R$ " + f"{preco_b:.2f}" if preco_b else "—"}</span>
                        </div>
                        <div class="info-item">
                            <label>Beta (β)</label>
                            <span>{f"{beta:.4f}" if beta else "—"}</span>
                        </div>
                        <div class="info-item">
                            <label>Correlação</label>
                            <span>{f"{corr:.4f}" if corr else "—"}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col_controls:
                st.markdown("<br>", unsafe_allow_html=True)
                novo = st.checkbox(
                    "✅ Habilitado" if habilitado else "❌ Desabilitado",
                    value=habilitado,
                    key=f"ck_{par['par_a']}_{par['par_b']}"
                )
                if novo != habilitado:
                    cfg_op.set_par_habilitado(par["par_a"], par["par_b"], novo)
                    st.rerun()

                qtd_atual = cfg_op.get_qtd_maxima(par["par_a"], par["par_b"])
                nova_qtd = st.number_input(
                    "Qtd máx por ponta",
                    min_value=0,
                    max_value=100000,
                    value=qtd_atual,
                    step=10,
                    key=f"qtd_{par['par_a']}_{par['par_b']}",
                    help="0 = sem limite (calcula pelo % do saldo)",
                )
                if nova_qtd != qtd_atual:
                    cfg_op.set_qtd_maxima(par["par_a"], par["par_b"], nova_qtd)
                    st.rerun()

                if qtd_atual > 0 and preco_a and preco_b:
                    custo = (qtd_atual * preco_a) + (qtd_atual * preco_b)
                    st.markdown(
                        f'<div style="font-size:12px; color:#aab4c8; margin-top:4px;">'
                        f'💰 Custo est.: <b style="color:#ffd600;">R$ {custo:,.2f}</b></div>',
                        unsafe_allow_html=True
                    )

        st.markdown("")

    # Preview da distribuição de capital
    if pares_habilitados_count > 0 and saldo_efetivo > 0:
        capital_total = saldo_efetivo * (pct / 100)
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
# ABA 6 — HISTÓRICO DE OPERAÇÕES REAIS
# ══════════════════════════════════════════════════════════════
with aba6:
    st.markdown("### 📊 Histórico de Operações Reais")

    todas_posicoes = pos.listar_todas()
    fechadas_hist  = [p for p in todas_posicoes if p["status"] == "fechada"]
    abertas_hist   = [p for p in todas_posicoes if p["status"] == "aberta"]
    resumo_hist    = pos.resumo_fechadas()

    if not todas_posicoes:
        st.markdown("""
        <div style="background:#1a1f35; border:1px solid #2d3250; border-radius:10px;
                    padding:40px; text-align:center;">
            <p style="font-size:40px; margin:0;">📋</p>
            <p style="font-size:16px; color:#fff; margin:10px 0 4px;">Nenhuma operação executada ainda</p>
            <p style="font-size:13px; color:#8892b0;">
                Operações executadas pelo robô ou importadas do MT5 aparecerão aqui.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # ── Métricas ───────────────────────────────────────────
        total_ops   = len(todas_posicoes)
        total_aber  = len(abertas_hist)
        total_fech  = len(fechadas_hist)
        pl_total    = resumo_hist.get("pl_total", 0)
        taxa_acerto = resumo_hist.get("taxa_acerto", 0)
        pl_cor      = "green" if pl_total >= 0 else "red"

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Executadas",  total_ops)
        c2.metric("Abertas",           total_aber)
        c3.metric("Fechadas",          total_fech)
        c4.metric("Taxa de Acerto",    f"{taxa_acerto}%" if fechadas_hist else "—")
        c5.metric("P&L Total",         f"R$ {pl_total:+,.2f}" if fechadas_hist else "—",
                  delta=f"{pl_total:+.2f}" if fechadas_hist else None)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Gráficos (só se tiver fechadas) ───────────────────
        if fechadas_hist:
            col_g1, col_g2 = st.columns(2)

            with col_g1:
                # P&L acumulado ao longo do tempo
                pls = [p["pl_final"] for p in fechadas_hist if p.get("pl_final") is not None]
                datas = [p.get("data_fechamento", "")[:10] for p in fechadas_hist
                         if p.get("pl_final") is not None]
                pl_acum = []
                acc = 0
                for v in pls:
                    acc += v
                    pl_acum.append(round(acc, 2))

                fig_acum = go.Figure()
                fig_acum.add_trace(go.Scatter(
                    x=list(range(1, len(pl_acum)+1)),
                    y=pl_acum,
                    mode="lines+markers",
                    line=dict(color="#00e676" if pl_acum[-1] >= 0 else "#ff5252", width=2),
                    marker=dict(size=6),
                    name="P&L Acumulado",
                    fill="tozeroy",
                    fillcolor="rgba(0,230,118,0.1)" if pl_acum[-1] >= 0 else "rgba(255,82,82,0.1)",
                ))
                fig_acum.add_hline(y=0, line_dash="dash", line_color="#8892b0", line_width=1)
                fig_acum.update_layout(
                    title="P&L Acumulado (R$)",
                    paper_bgcolor="#1a1f35", plot_bgcolor="#1a1f35",
                    font=dict(color="#ffffff"), height=300,
                    margin=dict(t=40, b=20, l=20, r=20),
                    xaxis=dict(title="Operação nº", gridcolor="#2d3250"),
                    yaxis=dict(gridcolor="#2d3250"),
                    showlegend=False,
                )
                st.plotly_chart(fig_acum, use_container_width=True)

            with col_g2:
                # P&L por par
                pl_por_par = {}
                for p in fechadas_hist:
                    chave = f"{p['par_a']}/{p['par_b']}"
                    pl_por_par[chave] = pl_por_par.get(chave, 0) + (p.get("pl_final") or 0)

                pares_nomes = list(pl_por_par.keys())
                pares_vals  = list(pl_por_par.values())
                cores = ["#00e676" if v >= 0 else "#ff5252" for v in pares_vals]

                fig_par = go.Figure(go.Bar(
                    x=pares_vals, y=pares_nomes,
                    orientation="h",
                    marker_color=cores,
                ))
                fig_par.update_layout(
                    title="P&L por Par (R$)",
                    paper_bgcolor="#1a1f35", plot_bgcolor="#1a1f35",
                    font=dict(color="#ffffff"), height=300,
                    margin=dict(t=40, b=20, l=20, r=20),
                    xaxis=dict(gridcolor="#2d3250"),
                    yaxis=dict(gridcolor="#2d3250"),
                )
                st.plotly_chart(fig_par, use_container_width=True)

        # ── Tabela completa ────────────────────────────────────
        st.markdown("---")
        st.markdown("### 📋 Todas as Operações")

        linhas = []
        for p in reversed(todas_posicoes):
            origem_label = "📥 Manual" if p.get("origem") == "manual" else "🤖 Robô"
            pl_val = p.get("pl_final")
            linhas.append({
                "Origem":       origem_label,
                "Par":          f"{p['par_a']} / {p['par_b']}",
                "Setor":        p.get("setor", "—"),
                "Sinal":        p.get("sinal", "—"),
                "Entrada":      f"{p['data_entrada']} {p['hora_entrada']}",
                "Z Entrada":    p.get("zscore_entrada", "—"),
                "Preço A":      f"R$ {p['preco_entrada_a']:.2f}",
                "Preço B":      f"R$ {p['preco_entrada_b']:.2f}",
                "Fechamento":   p.get("data_fechamento") or "—",
                "Z Saída":      p.get("zscore_saida") or "—",
                "P&L (R$)":     round(pl_val, 2) if pl_val is not None else "—",
                "Status":       "✅ Fechada" if p["status"] == "fechada" else "🔵 Aberta",
            })

        df_todas = pd.DataFrame(linhas)

        def cor_pl_hist(val):
            try:
                return "color: #00e676" if float(val) >= 0 else "color: #ff5252"
            except Exception:
                return "color: #8892b0"

        st.dataframe(
            df_todas.style.map(cor_pl_hist, subset=["P&L (R$)"]),
            use_container_width=True,
            height=400,
        )

        csv_hist = df_todas.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Exportar operações", csv_hist,
                           "historico_operacoes.csv", "text/csv")
