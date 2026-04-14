# ============================================================
# PAINEL TRADER TROCA DE AÇÕES — Streamlit + MT5
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

# ── Configuração da página ───────────────────────────────────

st.set_page_config(
    page_title="Trader Troca de Ações",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Auto-refresh a cada 60 segundos
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=60_000, key="autorefresh")

# ── CSS customizado ──────────────────────────────────────────

st.markdown("""
<style>
    .oportunidade { background-color: #1a3a1a; border-left: 4px solid #00cc44; padding: 10px; border-radius: 4px; }
    .monitorando  { background-color: #2a2a1a; border-left: 4px solid #ffcc00; padding: 10px; border-radius: 4px; }
    .neutro       { background-color: #1a1a2a; border-left: 4px solid #4444aa; padding: 10px; border-radius: 4px; }
    .erro         { background-color: #2a1a1a; border-left: 4px solid #cc2222; padding: 10px; border-radius: 4px; }
    .metric-card  { background-color: #1e1e1e; padding: 15px; border-radius: 8px; text-align: center; }
</style>
""", unsafe_allow_html=True)


# ── Conexão com MT5 ──────────────────────────────────────────

@st.cache_resource
def iniciar_mt5():
    return mt5c.conectar()

mt5_ok = iniciar_mt5()


# ── Sidebar ──────────────────────────────────────────────────

with st.sidebar:
    st.title("📊 Trader Troca de Ações")
    st.markdown("---")

    # Status MT5
    if mt5_ok:
        st.success("✅ MT5 Conectado")
    else:
        st.error("❌ MT5 Desconectado\nVerifique se o MT5 está aberto.")

    st.markdown("---")
    st.markdown(f"**Atualizado:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    st.markdown(f"**Pares monitorados:** {len(PARES)}")
    st.markdown("**Intervalo:** 60 segundos")

    st.markdown("---")
    if st.button("🔄 Atualizar agora"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("**Thresholds:**")
    st.markdown(f"- Entrada: Z ≥ ±{analyzer.Z_ENTRADA}")
    st.markdown(f"- Saída: Z ≤ ±{analyzer.Z_SAIDA}")
    st.markdown(f"- Stop: Z ≥ ±{analyzer.Z_STOP}")


# ── Carrega dados ────────────────────────────────────────────

@st.cache_data(ttl=60)
def carregar_analise():
    if not mt5_ok:
        return []
    return analyzer.analisar_todos_pares(PARES)


# ── Cabeçalho ────────────────────────────────────────────────

st.title("📊 Trader Troca de Ações — Painel de Oportunidades")

if not mt5_ok:
    st.error("⚠️ MT5 não conectado. Abra o MetaTrader 5 na VPS e recarregue a página.")
    st.stop()

resultados = carregar_analise()

if not resultados:
    st.warning("Carregando dados... Aguarde um momento.")
    st.stop()


# ── Métricas rápidas ─────────────────────────────────────────

oportunidades = [r for r in resultados if r.get("sinal") in ("VENDER_A", "COMPRAR_A")]
monitorando   = [r for r in resultados if r.get("sinal") == "MONITORANDO"]
com_erro      = [r for r in resultados if r.get("erro")]

col1, col2, col3, col4 = st.columns(4)
col1.metric("🔥 Oportunidades Agora", len(oportunidades))
col2.metric("🟡 Em Monitoramento",    len(monitorando))
col3.metric("📋 Total de Pares",      len(PARES))
col4.metric("⚠️ Sem Dados",          len(com_erro))

st.markdown("---")


# ── Abas ─────────────────────────────────────────────────────

aba1, aba2, aba3, aba4 = st.tabs([
    "🔥 Oportunidades Agora",
    "📈 Gráficos Z-Score",
    "📋 Todos os Pares",
    "📊 Histórico & Estatísticas",
])


# ══════════════════════════════════════════════════════════════
# ABA 1 — OPORTUNIDADES AGORA
# ══════════════════════════════════════════════════════════════
with aba1:
    if not oportunidades:
        st.info("Nenhuma oportunidade no momento. O sistema está monitorando todos os pares.")
    else:
        st.subheader(f"🔥 {len(oportunidades)} oportunidade(s) detectada(s)")

        for r in oportunidades:
            cor_classe = "oportunidade"
            z = r["zscore_atual"]
            z_abs = abs(z)

            # Barra de intensidade
            intensidade = min(z_abs / analyzer.Z_STOP, 1.0)
            cor_barra = "#00cc44" if r["sinal"] == "COMPRAR_A" else "#ff4444"

            col_info, col_gauge = st.columns([3, 1])

            with col_info:
                st.markdown(f"""
                <div class="{cor_classe}">
                    <h3>{r['emoji']} {r['par_a']} / {r['par_b']} <small>({r['setor']})</small></h3>
                    <p><strong>Sinal:</strong> {r['texto_sinal']}</p>
                    <p><strong>Z-Score:</strong> {z:+.4f} &nbsp;|&nbsp;
                       <strong>Beta (β):</strong> {r['beta']:.4f} &nbsp;|&nbsp;
                       <strong>Correlação:</strong> {r['correlacao']:.4f}</p>
                    <p><strong>Preço {r['par_a']}:</strong> R$ {r['preco_a']:.2f} &nbsp;|&nbsp;
                       <strong>Preço {r['par_b']}:</strong> R$ {r['preco_b']:.2f}</p>
                </div>
                """, unsafe_allow_html=True)

            with col_gauge:
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=z_abs,
                    title={"text": "Z-Score"},
                    gauge={
                        "axis": {"range": [0, analyzer.Z_STOP + 0.5]},
                        "bar":  {"color": cor_barra},
                        "steps": [
                            {"range": [0, analyzer.Z_SAIDA],   "color": "#1a1a2a"},
                            {"range": [analyzer.Z_SAIDA, analyzer.Z_ENTRADA], "color": "#2a2a1a"},
                            {"range": [analyzer.Z_ENTRADA, analyzer.Z_STOP], "color": "#1a3a1a"},
                            {"range": [analyzer.Z_STOP, analyzer.Z_STOP + 0.5], "color": "#3a1a1a"},
                        ],
                        "threshold": {
                            "line": {"color": "white", "width": 2},
                            "thickness": 0.75,
                            "value": analyzer.Z_ENTRADA,
                        },
                    },
                ))
                fig_gauge.update_layout(height=200, margin=dict(t=30, b=0, l=10, r=10))
                st.plotly_chart(fig_gauge, use_container_width=True)

            st.markdown("")


# ══════════════════════════════════════════════════════════════
# ABA 2 — GRÁFICOS Z-SCORE
# ══════════════════════════════════════════════════════════════
with aba2:
    opcoes_pares = [f"{r['par_a']} / {r['par_b']}" for r in resultados if not r.get("erro")]

    if not opcoes_pares:
        st.warning("Nenhum dado disponível para gráfico.")
    else:
        par_selecionado = st.selectbox("Selecione o par:", opcoes_pares)
        idx = opcoes_pares.index(par_selecionado)
        dados = resultados[idx]

        st.subheader(f"📈 {dados['par_a']} / {dados['par_b']} — Z-Score histórico")

        zserie = dados.get("zscore_serie")
        if zserie is not None and len(zserie) > 0:

            # Gráfico Z-score
            fig_z = go.Figure()

            fig_z.add_trace(go.Scatter(
                x=zserie.index, y=zserie.values,
                name="Z-Score", line=dict(color="#4488ff", width=1.5)
            ))
            fig_z.add_hline(y=analyzer.Z_ENTRADA,  line_dash="dash", line_color="red",   annotation_text=f"+{analyzer.Z_ENTRADA} Entrada")
            fig_z.add_hline(y=-analyzer.Z_ENTRADA, line_dash="dash", line_color="green", annotation_text=f"-{analyzer.Z_ENTRADA} Entrada")
            fig_z.add_hline(y=analyzer.Z_SAIDA,    line_dash="dot",  line_color="gray",  annotation_text=f"+{analyzer.Z_SAIDA}")
            fig_z.add_hline(y=-analyzer.Z_SAIDA,   line_dash="dot",  line_color="gray")
            fig_z.add_hline(y=0, line_color="white", line_width=0.5)

            # Pinta zonas de oportunidade
            fig_z.add_hrect(y0=analyzer.Z_ENTRADA,  y1=analyzer.Z_STOP, fillcolor="red",   opacity=0.05)
            fig_z.add_hrect(y0=-analyzer.Z_STOP, y1=-analyzer.Z_ENTRADA, fillcolor="green", opacity=0.05)

            fig_z.update_layout(
                title=f"Z-Score — {dados['par_a']} / {dados['par_b']}",
                xaxis_title="Data",
                yaxis_title="Z-Score",
                template="plotly_dark",
                height=400,
            )
            st.plotly_chart(fig_z, use_container_width=True)

            # Gráfico de preços normalizados
            st.subheader("📊 Preços normalizados (base 100)")
            preco_a = dados.get("zscore_serie")  # reutilizamos o índice

            df_mt5 = mt5c.buscar_historico_par(dados["par_a"], dados["par_b"])
            if df_mt5 is not None:
                norm_a = (df_mt5[dados["par_a"]] / df_mt5[dados["par_a"]].iloc[0]) * 100
                norm_b = (df_mt5[dados["par_b"]] / df_mt5[dados["par_b"]].iloc[0]) * 100

                fig_p = go.Figure()
                fig_p.add_trace(go.Scatter(x=norm_a.index, y=norm_a.values, name=dados["par_a"], line=dict(color="#ff8800")))
                fig_p.add_trace(go.Scatter(x=norm_b.index, y=norm_b.values, name=dados["par_b"], line=dict(color="#00aaff")))
                fig_p.update_layout(
                    title="Preços normalizados",
                    xaxis_title="Data",
                    yaxis_title="Valor (base 100)",
                    template="plotly_dark",
                    height=350,
                )
                st.plotly_chart(fig_p, use_container_width=True)

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Z-Score Atual",  f"{dados['zscore_atual']:+.4f}")
        col_m2.metric("Beta (β)",        f"{dados['beta']:.4f}")
        col_m3.metric("Correlação",      f"{dados['correlacao']:.4f}")


# ══════════════════════════════════════════════════════════════
# ABA 3 — TODOS OS PARES
# ══════════════════════════════════════════════════════════════
with aba3:
    st.subheader("📋 Status de todos os pares")

    linhas = []
    for r in resultados:
        linhas.append({
            "Status":      r.get("emoji", "❓"),
            "Par A":       r["par_a"],
            "Par B":       r["par_b"],
            "Setor":       r.get("setor", ""),
            "Z-Score":     r.get("zscore_atual") if r.get("zscore_atual") is not None else "—",
            "Sinal":       r.get("texto_sinal", "—"),
            "Preço A":     f"R$ {r['preco_a']:.2f}" if r.get("preco_a") else "—",
            "Preço B":     f"R$ {r['preco_b']:.2f}" if r.get("preco_b") else "—",
            "Beta":        r.get("beta", "—"),
        })

    df_tabela = pd.DataFrame(linhas)

    def colorir_linha(row):
        z = row.get("Z-Score")
        if z == "—" or z is None:
            return ["background-color: #2a1a1a"] * len(row)
        if abs(float(z)) >= analyzer.Z_ENTRADA:
            return ["background-color: #1a3a1a"] * len(row)
        if abs(float(z)) > analyzer.Z_SAIDA:
            return ["background-color: #2a2a1a"] * len(row)
        return [""] * len(row)

    st.dataframe(
        df_tabela.style.apply(colorir_linha, axis=1),
        use_container_width=True,
        height=500,
    )


# ══════════════════════════════════════════════════════════════
# ABA 4 — HISTÓRICO & ESTATÍSTICAS
# ══════════════════════════════════════════════════════════════
with aba4:
    st.subheader("📊 Histórico de oportunidades")

    df_hist = analyzer.carregar_historico_df()
    stats   = analyzer.estatisticas_historico()

    if df_hist.empty:
        st.info("Nenhuma oportunidade registrada ainda. O histórico é preenchido automaticamente quando oportunidades são detectadas.")
    else:
        # Métricas gerais
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total de Oportunidades", stats.get("total_oportunidades", 0))
        c2.metric("Pares com Ocorrências",  stats.get("pares_ativos", 0))
        c3.metric("Z-Score Médio",          stats.get("zscore_medio", 0))
        c4.metric("Setor Mais Ativo",       stats.get("setor_mais_ativo", "—"))

        st.markdown("---")

        # Gráfico de ocorrências por par
        contagem = df_hist.groupby("par").size().reset_index(name="ocorrencias")
        contagem = contagem.sort_values("ocorrencias", ascending=True)

        fig_bar = px.bar(
            contagem,
            x="ocorrencias",
            y="par",
            orientation="h",
            title="Oportunidades por Par",
            template="plotly_dark",
            color="ocorrencias",
            color_continuous_scale="Viridis",
        )
        fig_bar.update_layout(height=400)
        st.plotly_chart(fig_bar, use_container_width=True)

        # Gráfico de ocorrências por setor
        if "setor" in df_hist.columns:
            contagem_setor = df_hist.groupby("setor").size().reset_index(name="ocorrencias")
            fig_pizza = px.pie(
                contagem_setor,
                names="setor",
                values="ocorrencias",
                title="Distribuição por Setor",
                template="plotly_dark",
            )
            st.plotly_chart(fig_pizza, use_container_width=True)

        # Tabela completa
        st.subheader("📋 Tabela completa do histórico")
        st.dataframe(
            df_hist[["data", "hora", "par", "setor", "zscore", "texto", "preco_a", "preco_b"]],
            use_container_width=True,
            height=400,
        )

        # Exportar CSV
        csv = df_hist.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Baixar histórico em CSV",
            data=csv,
            file_name="historico_oportunidades.csv",
            mime="text/csv",
        )
