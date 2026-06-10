# -*- coding: utf-8 -*-
"""
Dashboard Mundial 2026 — Analítica para apuestas estadísticas.
48 equipos, 104 partidos. Ejecutar con:  streamlit run app.py
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils import analytics as an

st.set_page_config(page_title="Mundial 2026 · Analítica", page_icon="⚽",
                   layout="wide")


# ---------------------------------------------------------------------------
# Carga cacheada de datos y proyección del torneo
# ---------------------------------------------------------------------------
@st.cache_data
def get_teams():
    return an.load_teams()


@st.cache_data
def get_matches():
    return an.load_matches()


@st.cache_data
def get_proyeccion():
    return an.proyectar_torneo(get_teams(), get_matches())


teams = get_teams()
matches = get_matches()

st.sidebar.title("⚽ Mundial 2026")
st.sidebar.caption("48 equipos · 104 partidos · Modelo Poisson + Monte Carlo")
seccion = st.sidebar.radio("Sección", [
    "🎯 Simulador 1v1",
    "🟨 Tarjetas (Over/Under)",
    "🚩 Corners",
    "📅 Explorador de 104 Partidos",
])
st.sidebar.divider()
st.sidebar.caption("Datos semilla calibrados (últimos 2 años). "
                   "Repechajes y sorteo oficial dic-2025. "
                   "Uso educativo: apuesta con responsabilidad.")


def selector_equipos(key: str):
    """Par de selectores de equipo sin repetición."""
    c1, c2 = st.columns(2)
    nombres = sorted(teams.equipo)
    ea = c1.selectbox("Equipo A", nombres, index=nombres.index("México"), key=f"{key}_a")
    eb = c2.selectbox("Equipo B", [n for n in nombres if n != ea],
                      index=0, key=f"{key}_b")
    return teams.loc[ea], teams.loc[eb]


# ===========================================================================
# 1) SIMULADOR 1v1
# ===========================================================================
if seccion == "🎯 Simulador 1v1":
    st.title("🎯 Simulador de Probabilidades 1v1")
    st.caption("Modelo de Poisson: λ combina ataque propio, defensa rival, "
               "forma reciente (últimos 5) y diferencia de puntos FIFA.")

    a, b = selector_equipos("sim")
    usar_mc = st.toggle("Validar con Monte Carlo (10,000 simulaciones)", value=True)

    p = an.probabilidades_1v1(a, b)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Victoria {a.equipo}", f"{p['p_win']:.1%}")
    c2.metric("Empate", f"{p['p_draw']:.1%}")
    c3.metric(f"Victoria {b.equipo}", f"{p['p_loss']:.1%}")
    c4.metric("Goles esperados", f"{p['lam_a']:.2f} – {p['lam_b']:.2f}")

    col_izq, col_der = st.columns(2)
    with col_izq:
        fig = go.Figure(go.Bar(
            x=[f"Gana {a.equipo}", "Empate", f"Gana {b.equipo}"],
            y=[p["p_win"], p["p_draw"], p["p_loss"]],
            marker_color=["#2ecc71", "#95a5a6", "#e74c3c"],
            text=[f"{v:.1%}" for v in (p["p_win"], p["p_draw"], p["p_loss"])],
            textposition="outside"))
        fig.update_layout(title="Probabilidades 1X2 (Poisson)",
                          yaxis_tickformat=".0%", showlegend=False)
        st.plotly_chart(fig, width="stretch")

        st.subheader("Mercados de goles")
        df_mkt = pd.DataFrame({
            "Mercado": [f"Over {l}" for l in p["overs"]] + ["Ambos anotan (BTTS)"],
            "Probabilidad": list(p["overs"].values()) + [p["btts"]],
        })
        df_mkt["Cuota justa"] = (1 / df_mkt.Probabilidad).round(2)
        df_mkt["Probabilidad"] = df_mkt.Probabilidad.map("{:.1%}".format)
        st.dataframe(df_mkt, hide_index=True, width="stretch")

    with col_der:
        # Mapa de calor de marcadores (matriz de Poisson truncada a 5 goles)
        m = an.matriz_poisson(p["lam_a"], p["lam_b"])[:6, :6]
        fig = px.imshow(m, text_auto=".1%", color_continuous_scale="Greens",
                        labels=dict(x=f"Goles {b.equipo}", y=f"Goles {a.equipo}"))
        fig.update_layout(title="Probabilidad por marcador exacto",
                          coloraxis_showscale=False)
        st.plotly_chart(fig, width="stretch")

        st.subheader("Marcadores más probables")
        st.dataframe(pd.DataFrame(
            [{"Marcador": f"{i} - {j}", "Probabilidad": f"{pr:.1%}"}
             for i, j, pr in p["marcadores"]]),
            hide_index=True, width="stretch")

    if usar_mc:
        mc = an.monte_carlo_1v1(a, b)
        st.subheader("Validación Monte Carlo (10,000 partidos simulados)")
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Victoria {a.equipo}", f"{mc['p_win']:.1%}",
                  f"{mc['p_win'] - p['p_win']:+.1%} vs Poisson")
        c2.metric("Empate", f"{mc['p_draw']:.1%}",
                  f"{mc['p_draw'] - p['p_draw']:+.1%} vs Poisson")
        c3.metric(f"Victoria {b.equipo}", f"{mc['p_loss']:.1%}",
                  f"{mc['p_loss'] - p['p_loss']:+.1%} vs Poisson")
        diff = mc["goles_a"] - mc["goles_b"]
        fig = px.histogram(pd.DataFrame({"Diferencia de goles (A - B)": diff}),
                           x="Diferencia de goles (A - B)", nbins=13,
                           histnorm="probability",
                           title="Distribución de la diferencia de goles")
        fig.update_layout(yaxis_tickformat=".0%", bargap=0.05)
        st.plotly_chart(fig, width="stretch")

# ===========================================================================
# 2) TARJETAS
# ===========================================================================
elif seccion == "🟨 Tarjetas (Over/Under)":
    st.title("🟨 Módulo de Tarjetas")
    st.caption("Total esperado = suma de promedios de ambos equipos × factor "
               "de rivalidad. Over/Under con distribución de Poisson.")

    tab1, tab2 = st.tabs(["Predicción por enfrentamiento", "Propensión por equipo"])

    with tab1:
        a, b = selector_equipos("tar")
        eliminacion = st.toggle("Partido de eliminación directa (factor 1.15)")
        t = an.prediccion_tarjetas(a, b, 1.15 if eliminacion else 1.0)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Amarillas esperadas", f"{t['amarillas_esp']:.2f}")
        c2.metric("Rojas esperadas", f"{t['rojas_esp']:.2f}")
        c3.metric("Total esperado", f"{t['total_esp']:.2f}")
        c4.metric("P(al menos 1 roja)", f"{t['p_roja']:.1%}")

        df_ou = pd.DataFrame({
            "Línea": [f"Over {l}" for l in t["overs"]],
            "Probabilidad": list(t["overs"].values()),
        })
        fig = px.bar(df_ou, x="Línea", y="Probabilidad", text_auto=".1%",
                     color="Probabilidad", color_continuous_scale="YlOrRd",
                     title="Probabilidad Over líneas de tarjetas (Poisson)")
        fig.update_layout(yaxis_tickformat=".0%", coloraxis_showscale=False)
        st.plotly_chart(fig, width="stretch")
        df_ou["Cuota justa"] = (1 / df_ou.Probabilidad).round(2)
        df_ou["Under (prob.)"] = (1 - df_ou.Probabilidad).map("{:.1%}".format)
        df_ou["Probabilidad"] = df_ou.Probabilidad.map("{:.1%}".format)
        st.dataframe(df_ou, hide_index=True, width="stretch")

    with tab2:
        df = teams.copy()
        df["total_pp"] = df.amarillas_pp + df.rojas_pp
        df = df.sort_values("total_pp", ascending=False)
        fig = go.Figure()
        fig.add_bar(name="Amarillas/partido", x=df.equipo, y=df.amarillas_pp,
                    marker_color="#f1c40f")
        fig.add_bar(name="Rojas/partido", x=df.equipo, y=df.rojas_pp,
                    marker_color="#c0392b")
        fig.update_layout(barmode="stack", title="Propensión a tarjetas por equipo",
                          height=500)
        st.plotly_chart(fig, width="stretch")
        st.dataframe(df[["equipo", "grupo", "amarillas_pp", "rojas_pp", "total_pp"]]
                     .rename(columns={"total_pp": "total_por_partido"}),
                     hide_index=True, width="stretch")

# ===========================================================================
# 3) CORNERS
# ===========================================================================
elif seccion == "🚩 Corners":
    st.title("🚩 Módulo de Tiros de Esquina")
    st.caption("E[corners A] = (corners a favor de A + corners en contra de B)/2 "
               "× rol. Favorito ×1.12, no favorito ×0.90 (dominio de posesión).")

    tab1, tab2 = st.tabs(["Predicción por enfrentamiento", "Ranking por rol"])

    with tab1:
        a, b = selector_equipos("cor")
        c = an.prediccion_corners(a, b)
        rol_a = "favorito" if an.es_favorito(a, b) else "no favorito"

        c1, c2, c3 = st.columns(3)
        c1.metric(f"{a.equipo} ({rol_a})", f"{c['corners_a']:.2f}")
        c2.metric(f"{b.equipo} ({'favorito' if rol_a == 'no favorito' else 'no favorito'})",
                  f"{c['corners_b']:.2f}")
        c3.metric("Total esperado", f"{c['total']:.2f}")

        df_ou = pd.DataFrame({
            "Línea": [f"Over {l}" for l in c["overs"]],
            "Probabilidad": list(c["overs"].values()),
        })
        fig = px.bar(df_ou, x="Línea", y="Probabilidad", text_auto=".1%",
                     color="Probabilidad", color_continuous_scale="Blues",
                     title="Probabilidad Over líneas de corners totales")
        fig.update_layout(yaxis_tickformat=".0%", coloraxis_showscale=False)
        st.plotly_chart(fig, width="stretch")
        df_ou["Cuota justa"] = (1 / df_ou.Probabilidad).round(2)
        df_ou["Probabilidad"] = df_ou.Probabilidad.map("{:.1%}".format)
        st.dataframe(df_ou, hide_index=True, width="stretch")

    with tab2:
        filtro_rol = st.radio("Comportamiento según rol", ["Como favorito",
                              "Como no favorito"], horizontal=True)
        df = an.tabla_corners_rol(teams)
        col = ("corners_como_favorito" if filtro_rol == "Como favorito"
               else "corners_como_no_favorito")
        df = df.sort_values(col, ascending=False)
        fig = px.bar(df.head(20), x="equipo", y=col, text_auto=".2f",
                     color="diferencial", color_continuous_scale="RdYlGn",
                     title=f"Top 20 corners esperados — {filtro_rol.lower()}")
        st.plotly_chart(fig, width="stretch")
        st.dataframe(df, hide_index=True, width="stretch")

# ===========================================================================
# 4) EXPLORADOR DE 104 PARTIDOS
# ===========================================================================
else:
    st.title("📅 Explorador de los 104 Partidos")
    st.caption("Fase de grupos con calendario oficial; la eliminación directa "
               "se proyecta con el modelo (siembra por puntos esperados, "
               "simplificación del bracket oficial).")

    with st.spinner("Proyectando el torneo completo..."):
        proy = get_proyeccion()

    campeon = proy.attrs.get("campeon_proyectado", "—")
    st.success(f"🏆 **Campeón proyectado por el modelo: {campeon}**")

    c1, c2, c3 = st.columns(3)
    fases = ["Todas"] + proy.fase.unique().tolist()
    f_fase = c1.selectbox("Fase", fases)
    grupos = ["Todos"] + sorted(g for g in proy.grupo.dropna().unique() if g)
    f_grupo = c2.selectbox("Grupo", grupos)
    f_equipo = c3.selectbox("Equipo", ["Todos"] + sorted(teams.equipo))

    df = proy.copy()
    if f_fase != "Todas":
        df = df[df.fase == f_fase]
    if f_grupo != "Todos":
        df = df[df.grupo == f_grupo]
    if f_equipo != "Todos":
        df = df[(df.equipo_a == f_equipo) | (df.equipo_b == f_equipo)]

    vista = df[["partido_id", "fecha", "fase", "grupo", "sede",
                "equipo_a", "equipo_b",
                "prob_a", "prob_empate", "prob_b", "goles_esp_a", "goles_esp_b",
                "ganador_proyectado"]].rename(columns={
        "prob_a": "P(A)", "prob_empate": "P(X)", "prob_b": "P(B)",
        "goles_esp_a": "xG A", "goles_esp_b": "xG B"})
    st.dataframe(vista, hide_index=True, width="stretch", height=420,
                 column_config={
                     "P(A)": st.column_config.ProgressColumn(format="percent",
                                                             min_value=0, max_value=1),
                     "P(X)": st.column_config.ProgressColumn(format="percent",
                                                             min_value=0, max_value=1),
                     "P(B)": st.column_config.ProgressColumn(format="percent",
                                                             min_value=0, max_value=1),
                 })

    st.subheader("Tabla proyectada de fase de grupos (puntos esperados)")
    standings = an.puntos_esperados_grupo(teams, matches)
    g = st.selectbox("Ver grupo", sorted(standings.grupo.unique()))
    st.dataframe(standings[standings.grupo == g], hide_index=True,
                 width="stretch")

    fig = px.bar(standings.sort_values("pts_esperados", ascending=False).head(16),
                 x="equipo", y="pts_esperados", color="grupo", text_auto=".2f",
                 title="Top 16 — puntos esperados en fase de grupos")
    st.plotly_chart(fig, width="stretch")
