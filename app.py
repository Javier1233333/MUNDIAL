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
                   layout="wide", initial_sidebar_state="expanded")

# Tema visual amigable. Se usan colores translúcidos (rgba con grises neutros)
# para que las tarjetas se vean bien tanto en modo claro como oscuro.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], button, input, select { font-family: 'Inter', sans-serif; }

/* ---------- Banner principal (hero) ---------- */
.hero {
    background: linear-gradient(120deg, #15a05a 0%, #1379b0 52%, #7b46c4 100%);
    color: #fff; padding: 1.5rem 1.7rem; border-radius: 18px;
    margin-bottom: 1.3rem; box-shadow: 0 10px 28px rgba(20,30,60,.18);
}
.hero h1 { color:#fff !important; margin:0 0 .25rem; font-size:1.85rem;
           font-weight:800; line-height:1.15; }
.hero p { margin:0; opacity:.93; font-size:1.02rem; }
.hero .pills { margin-top:.85rem; }
.hero .pill { display:inline-block; background:rgba(255,255,255,.20);
    padding:.28rem .75rem; border-radius:999px; font-size:.82rem;
    margin:.15rem .4rem .15rem 0; font-weight:600; backdrop-filter:blur(4px); }

/* ---------- Tarjetas de métricas ---------- */
div[data-testid="stMetric"] {
    background: rgba(130,130,150,.07);
    border: 1px solid rgba(130,130,150,.20);
    border-radius: 14px; padding: 0.95rem 1.05rem;
    box-shadow: 0 2px 8px rgba(20,30,50,.05);
    transition: transform .12s ease, box-shadow .12s ease;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px); box-shadow: 0 7px 18px rgba(20,30,50,.12);
}
div[data-testid="stMetricLabel"] { font-weight:600; opacity:.8; }
div[data-testid="stMetricValue"] { font-weight:800; }

/* ---------- Avisos (success / error / warning / info) ---------- */
div[data-testid="stAlert"] { border-radius:13px; border-left-width:5px; }

/* ---------- Pestañas y selectores ---------- */
button[data-baseweb="tab"] { font-weight:600; font-size:.95rem; }
div[data-testid="stExpander"] { border-radius:13px; }

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] { box-shadow: 2px 0 12px rgba(0,0,0,.05); }
section[data-testid="stSidebar"] div[role="radiogroup"] label {
    padding:.35rem .55rem; border-radius:10px; transition:background .12s ease;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: rgba(130,130,150,.12);
}

/* ---------- Tablas ---------- */
div[data-testid="stDataFrame"] { border-radius:12px; overflow:hidden; }

/* ---------- Responsivo (teléfono) ---------- */
@media (max-width: 640px) {
    .block-container { padding: 2.4rem 0.8rem 2rem; }
    .hero { padding:1.2rem 1.1rem; border-radius:14px; }
    .hero h1 { font-size:1.4rem; }
    .hero p { font-size:.92rem; }

    div[data-testid="stHorizontalBlock"] { flex-wrap: wrap; row-gap: 0.5rem; }

    div[data-testid="stColumn"] {
        flex: 1 1 100% !important;
        width: 100% !important;
        min-width: 100% !important;
    }

    /* Las métricas se acomodan en cuadrícula de 2 por fila */
    div[data-testid="stColumn"]:has(div[data-testid="stMetric"]) {
        flex: 1 1 calc(50% - 0.5rem) !important;
        width: calc(50% - 0.5rem) !important;
        min-width: calc(50% - 0.5rem) !important;
    }

    div[data-testid="stMetricValue"] { font-size: 1.3rem; }
    div[data-testid="stMetricLabel"] { font-size: 0.78rem; }
    h1 { font-size: 1.5rem; }
    h2, h3 { font-size: 1.12rem; }
}
</style>
""", unsafe_allow_html=True)


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

# ---------------------------------------------------------------------------
# Barra lateral: navegación amigable
# ---------------------------------------------------------------------------
st.sidebar.title("⚽ Mundial 2026")
st.sidebar.caption("Tu centro de analítica para el torneo")

seccion = st.sidebar.radio("¿Qué quieres analizar?", [
    "🏠 Inicio",
    "🎯 Simulador 1v1",
    "💰 Momios y Valor (EV)",
    "🟨 Tarjetas (Over/Under)",
    "🚩 Corners",
    "📅 Explorador de 104 Partidos",
])

with st.sidebar.expander("❓ ¿Cómo se calcula todo esto?"):
    st.markdown(
        "- **Modelo de Poisson**: estima los goles esperados de cada equipo "
        "según su ataque, la defensa rival, su forma reciente y el ranking FIFA.\n"
        "- **Monte Carlo**: simula 10,000 partidos para confirmar las probabilidades.\n"
        "- **Cancha neutral** para todos, salvo los anfitriones 🏠 (USA, "
        "Canadá y México), que tienen ventaja de local.")

st.sidebar.divider()
st.sidebar.caption("📊 48 equipos · 104 partidos\n\n"
                   "Datos calibrados (últimos 2 años) · Sorteo oficial dic-2025")
st.sidebar.warning("🔞 Uso educativo. Apuesta con responsabilidad: nunca "
                   "apuestes más de lo que puedes permitirte perder.")


# ---------------------------------------------------------------------------
# Banner principal (hero) dinámico según la sección
# ---------------------------------------------------------------------------
HEROS = {
    "🏠 Inicio": ("¡Bienvenido a tu centro de analítica! ⚽",
                  "Explora probabilidades, detecta apuestas con valor y proyecta "
                  "el torneo completo. Empieza eligiendo una sección a la izquierda.",
                  ["48 equipos", "104 partidos", "Modelo Poisson + Monte Carlo"]),
    "🎯 Simulador 1v1": ("Simulador de partidos 1 vs 1 🎯",
                         "Elige dos selecciones y mira quién tiene ventaja, los "
                         "goles esperados y los marcadores más probables.",
                         ["Probabilidades 1X2", "Over/Under", "Ambos anotan"]),
    "💰 Momios y Valor (EV)": ("¿Vale la pena esta apuesta? 💰",
                               "Escribe los momios de tu casa de apuestas y te decimos "
                               "al instante si tienen valor según el modelo.",
                               ["Detecta Value Bets", "Margen de la casa", "Kelly"]),
    "🟨 Tarjetas (Over/Under)": ("Mercado de tarjetas 🟨",
                                 "Cuántas tarjetas esperar en un partido y la "
                                 "probabilidad de cada línea Over/Under.",
                                 ["Amarillas", "Rojas", "Over/Under"]),
    "🚩 Corners": ("Mercado de tiros de esquina 🚩",
                   "Corners esperados por equipo y probabilidades de las líneas "
                   "totales del partido.",
                   ["Corners por equipo", "Líneas totales", "Por rol"]),
    "📅 Explorador de 104 Partidos": ("El torneo completo, partido por partido 📅",
                                      "Proyección de los 104 partidos, la tabla de "
                                      "grupos y el campeón que predice el modelo.",
                                      ["Fase de grupos", "Eliminatorias", "Campeón"]),
}


def hero(seccion: str):
    """Dibuja el banner superior con título, subtítulo y 'pills' de la sección."""
    titulo, subtitulo, pills = HEROS[seccion]
    chips = "".join(f'<span class="pill">{p}</span>' for p in pills)
    st.markdown(
        f'<div class="hero"><h1>{titulo}</h1><p>{subtitulo}</p>'
        f'<div class="pills">{chips}</div></div>', unsafe_allow_html=True)


hero(seccion)


def glosario():
    """Expander reutilizable que explica los términos de apuestas en simple."""
    with st.expander("📖 ¿Qué significan estos términos? (toca para abrir)"):
        st.markdown(
            "- **Momio / cuota**: lo que paga la casa. *Decimal* 2.50 = ganas 2.50 "
            "por cada 1 apostado (incluye tu apuesta). *Americano* +150 / −200.\n"
            "- **Probabilidad implícita**: la probabilidad que la casa le asigna a "
            "un resultado = 1 ÷ momio decimal.\n"
            "- **Margen (overround)**: la comisión oculta de la casa. Si las "
            "probabilidades implícitas suman más de 100%, ese excedente es su ganancia.\n"
            "- **Valor Esperado (EV)**: ganancia promedio por unidad apostada. "
            "**EV positivo = apuesta de valor** (la casa paga de más según el modelo).\n"
            "- **Cuota justa**: el momio mínimo en el que la apuesta empieza a "
            "tener valor (1 ÷ probabilidad del modelo).\n"
            "- **Kelly**: qué porcentaje de tu dinero apostar para crecer sin "
            "arriesgar de más.\n"
            "- **Over / Under**: apostar a que habrá *más* (Over) o *menos* (Under) "
            "de cierta cantidad (goles, tarjetas, corners).")


def selector_equipos(key: str):
    """Par de selectores de equipo sin repetición, con ayuda y un 'VS' al centro."""
    nombres = sorted(teams.equipo)
    c1, cvs, c2 = st.columns([5, 1, 5])
    ea = c1.selectbox("🔵 Equipo A", nombres, index=nombres.index("México"),
                      key=f"{key}_a", help="Selecciona el primer equipo.")
    cvs.markdown("<div style='text-align:center;font-weight:800;opacity:.6;"
                 "padding-top:1.9rem;'>VS</div>", unsafe_allow_html=True)
    eb = c2.selectbox("🔴 Equipo B", [n for n in nombres if n != ea],
                      index=0, key=f"{key}_b", help="Selecciona el rival.")
    return teams.loc[ea], teams.loc[eb]


# ===========================================================================
# 0) INICIO
# ===========================================================================
if seccion == "🏠 Inicio":
    st.subheader("👋 ¿Por dónde empezar?")
    st.markdown(
        "Esta app convierte estadísticas del Mundial en **probabilidades claras** "
        "para que tomes mejores decisiones. Elige una herramienta en el menú de la "
        "izquierda — aquí tienes un resumen de cada una:")

    c1, c2 = st.columns(2)
    with c1:
        st.info("🎯 **Simulador 1v1**\n\nElige dos equipos y mira quién gana, los "
                "goles esperados y los marcadores más probables.")
        st.success("💰 **Momios y Valor (EV)**\n\nEscribe los momios de tu casa de "
                   "apuestas y descubre al instante si la apuesta tiene valor.")
        st.warning("🟨 **Tarjetas**\n\nCuántas tarjetas esperar y la probabilidad "
                   "de cada línea Over/Under.")
    with c2:
        st.info("🚩 **Corners**\n\nTiros de esquina esperados por equipo y las "
                "líneas totales del partido.")
        st.success("📅 **Explorador de 104 Partidos**\n\nLa proyección completa del "
                   "torneo, la tabla de grupos y el campeón del modelo.")
        st.warning("🏠 **Anfitriones con ventaja**\n\nTodo es cancha neutral, salvo "
                   "USA, Canadá y México, que juegan en casa.")

    st.divider()
    st.subheader("🏆 Los 8 más fuertes según ranking FIFA")
    top = teams.sort_values("puntos_fifa", ascending=False).head(8)
    fig = px.bar(top, x="equipo", y="puntos_fifa", text_auto=".0f",
                 color="puntos_fifa", color_continuous_scale="Greens",
                 labels={"equipo": "", "puntos_fifa": "Puntos FIFA"})
    fig.update_layout(coloraxis_showscale=False,
                      title="Favoritos por puntos FIFA (un vistazo rápido)")
    st.plotly_chart(fig, width="stretch")

    glosario()
    st.caption("👉 Listo para empezar: abre **🎯 Simulador 1v1** o "
               "**💰 Momios y Valor (EV)** en el menú de la izquierda.")

# ===========================================================================
# 1) SIMULADOR 1v1
# ===========================================================================
elif seccion == "🎯 Simulador 1v1":
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
# 1.5) ANALIZADOR DE MOMIOS Y VALOR ESPERADO (EV)
# ===========================================================================
elif seccion == "💰 Momios y Valor (EV)":
    st.caption("Compara en tiempo real las probabilidades del modelo contra los "
               "momios del mercado. Detecta apuestas de valor (EV+) y revela la "
               "comisión oculta (margen) de la casa. Todo se recalcula al teclear, "
               "sin botón de envío.")
    glosario()

    formato = st.radio("Formato de momio", ["Decimal", "Americano"],
                       horizontal=True, key="ev_fmt",
                       help="Decimal: 2.50. Americano: +150 o −200. "
                            "Se convierte automáticamente para los cálculos.")

    def a_decimal(valor: float) -> float:
        """Normaliza el momio tecleado al formato decimal para los cálculos."""
        return float(valor) if formato == "Decimal" else an.americano_a_decimal(valor)

    def fmt_momio(d: float) -> str:
        """Muestra el momio en el formato elegido por el usuario."""
        if formato == "Decimal" or d <= 1:
            return f"{d:.2f}"
        # Decimal -> americano para el texto de ayuda
        amer = (d - 1) * 100 if d >= 2 else -100 / (d - 1)
        return f"{amer:+.0f}"

    # Valores por defecto según formato (mismas cuotas, distinta notación)
    if formato == "Decimal":
        paso, defaults_1x2 = 0.01, (2.10, 3.30, 3.60)
        d_over, d_under = 1.90, 1.90
        rango = (1.01, 1000.0)
    else:
        paso, defaults_1x2 = 5.0, (110.0, 230.0, 260.0)
        d_over, d_under = -110.0, -110.0
        rango = (-100000.0, 100000.0)

    mercado = st.selectbox("Mercado a analizar", [
        "Resultado 1X2 (Equipo A / Empate / Equipo B)",
        "⚽ Goles Totales Over/Under",
        "Tarjetas Over/Under",
        "Corners Over/Under",
    ], key="ev_mkt")

    st.divider()

    # -----------------------------------------------------------------------
    # A) MERCADO 1X2
    # -----------------------------------------------------------------------
    if mercado.startswith("Resultado"):
        a, b = selector_equipos("ev")

        def con_casa(equipo: str) -> str:
            """Marca al anfitrión con 🏠 (ventaja de local); el resto, neutral."""
            return f"{equipo} 🏠" if equipo in an.ANFITRIONES else equipo

        hay_anfitrion = a.equipo in an.ANFITRIONES or b.equipo in an.ANFITRIONES
        if hay_anfitrion:
            st.info(f"🏠 Hay anfitrión en cancha: la ventaja de local "
                    f"(+{(an.VENTAJA_LOCAL - 1):.0%} goles esperados) aplica solo a "
                    f"USA, Canadá y México. El resto se juega en suelo neutral.")
        else:
            st.caption("Partido en suelo neutral: ser equipo A o B no da ventaja.")

        p = an.probabilidades_1v1(a, b)
        prob_modelo = {"Local": p["p_win"], "Empate": p["p_draw"],
                       "Visitante": p["p_loss"]}

        st.subheader("Momios del mercado")
        cL, cE, cV = st.columns(3)
        mL = cL.number_input(con_casa(a.equipo), value=defaults_1x2[0],
                             step=paso, min_value=rango[0], max_value=rango[1],
                             key="ev_mL")
        mE = cE.number_input("Empate", value=defaults_1x2[1], step=paso,
                             min_value=rango[0], max_value=rango[1], key="ev_mE")
        mV = cV.number_input(con_casa(b.equipo), value=defaults_1x2[2],
                             step=paso, min_value=rango[0], max_value=rango[1],
                             key="ev_mV")

        dL, dE, dV = a_decimal(mL), a_decimal(mE), a_decimal(mV)
        ov = an.margen_overround(dL, dE, dV)
        resultados = {
            "Local": an.valor_esperado(prob_modelo["Local"], dL),
            "Empate": an.valor_esperado(prob_modelo["Empate"], dE),
            "Visitante": an.valor_esperado(prob_modelo["Visitante"], dV),
        }

        # Margen de la casa
        st.subheader("Margen de la casa (overround)")
        m1, m2, m3 = st.columns(3)
        m1.metric("Suma prob. implícitas", f"{ov['suma_implicitas']:.1%}",
                  help="Un mercado justo suma 100%. El excedente es el margen.")
        m2.metric("Margen (vig)", f"{ov['margen']:.2%}",
                  help="Comisión oculta de la casa sobre este mercado 1X2.")
        m3.metric("Comisión efectiva", f"{ov['comision_pct']:.2%}",
                  help="Margen como fracción del total apostado.")

        # Tarjetas de EV por resultado, actualizadas al teclear
        st.subheader("Valor esperado por resultado")
        etiquetas = {"Local": con_casa(a.equipo), "Empate": "Empate",
                     "Visitante": con_casa(b.equipo)}
        cols = st.columns(3)
        for col, clave in zip(cols, ["Local", "Empate", "Visitante"]):
            r = resultados[clave]
            col.metric(
                f"Gana {etiquetas[clave]}" if clave != "Empate" else "Empate",
                f"EV {r['ev']:+.1%}",
                f"Modelo {r['prob_modelo']:.1%} vs Casa {r['implicita']:.1%}",
                delta_color="normal" if r["es_valor"] else "inverse",
            )

        # Alertas de color por cada resultado
        for clave in ["Local", "Empate", "Visitante"]:
            r = resultados[clave]
            nombre = etiquetas[clave] if clave == "Empate" else f"gana {etiquetas[clave]}"
            if r["es_valor"]:
                st.success(
                    f"✅ **Apuesta de valor — {nombre}**: el modelo asigna "
                    f"{r['prob_modelo']:.1%} vs {r['implicita']:.1%} implícito. "
                    f"EV **{r['ev']:+.1%}**, cuota justa **{r['cuota_justa']:.2f}** "
                    f"(la casa paga {fmt_momio(r['momio_decimal'])}). "
                    f"Kelly sugerido: {r['kelly']:.1%} del bankroll.")
            else:
                st.error(
                    f"❌ **Sin valor — {nombre}**: la cuota "
                    f"{fmt_momio(r['momio_decimal'])} implica {r['implicita']:.1%}, "
                    f"por encima del {r['prob_modelo']:.1%} del modelo. "
                    f"EV **{r['ev']:+.1%}** (necesitarías ≥ {r['cuota_justa']:.2f}).")

        # Gráfico: Modelo vs Implícita de la casa (barras horizontales)
        etq = [f"Gana {con_casa(a.equipo)}", "Empate", f"Gana {con_casa(b.equipo)}"]
        modelo_vals = [resultados[k]["prob_modelo"] for k in
                       ["Local", "Empate", "Visitante"]]
        casa_vals = [resultados[k]["implicita"] for k in
                     ["Local", "Empate", "Visitante"]]
        fig = go.Figure()
        fig.add_bar(y=etq, x=modelo_vals, name="Probabilidad del Modelo",
                    orientation="h", marker_color="#2ecc71",
                    text=[f"{v:.1%}" for v in modelo_vals], textposition="auto")
        fig.add_bar(y=etq, x=casa_vals, name="Implícita de la Casa",
                    orientation="h", marker_color="#e74c3c",
                    text=[f"{v:.1%}" for v in casa_vals], textposition="auto")
        fig.update_layout(barmode="group", xaxis_tickformat=".0%",
                          title="Probabilidad del Modelo vs Implícita de la Casa",
                          legend=dict(orientation="h", y=-0.2), height=420)
        st.plotly_chart(fig, width="stretch")

    # -----------------------------------------------------------------------
    # B) GOLES TOTALES OVER/UNDER — ¿cuántos goles cree la casa?
    # -----------------------------------------------------------------------
    elif mercado.startswith("⚽ Goles"):
        st.markdown("Escribe los momios **Over/Under de goles** y la app despeja "
                    "**cuántos goles totales creen las casas** que habrá (su "
                    "expectativa implícita), y lo compara con el modelo.")
        a, b = selector_equipos("evgo")
        p = an.probabilidades_1v1(a, b)
        lam_modelo = p["lam_a"] + p["lam_b"]

        lineas_disp = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
        lineas_sel = st.multiselect(
            "Líneas de goles a analizar", lineas_disp, default=[1.5, 2.5, 3.5],
            help="Mientras más líneas ingreses, más estable es la estimación de "
                 "lo que cree la casa.")

        if not lineas_sel:
            st.warning("Selecciona al menos una línea de goles para analizar.")
        else:
            st.subheader("Momios Over/Under por línea")
            pares_fair = []     # (línea, P(Over) justa de la casa) para ajustar λ
            filas = []
            evaluaciones = []   # para la recomendación global
            for l in sorted(lineas_sel):
                cl, cO, cU = st.columns([1.2, 2, 2])
                cl.markdown(f"<div style='padding-top:1.9rem;font-weight:700;'>"
                            f"⚽ {l} goles</div>", unsafe_allow_html=True)
                mO = cO.number_input(f"Over {l}", value=d_over, step=paso,
                                     min_value=rango[0], max_value=rango[1],
                                     key=f"go_o_{l}")
                mU = cU.number_input(f"Under {l}", value=d_under, step=paso,
                                     min_value=rango[0], max_value=rango[1],
                                     key=f"go_u_{l}")
                dO, dU = a_decimal(mO), a_decimal(mU)
                dv = an.devig_dos_vias(dO, dU)        # quita el margen
                pares_fair.append((l, dv["fair_a"]))  # fair_a = Over

                # Probabilidad del modelo y EV de cada lado
                p_over_mod = an.prob_over_poisson(l, lam_modelo)
                rO = an.valor_esperado(p_over_mod, dO)
                rU = an.valor_esperado(1 - p_over_mod, dU)
                evaluaciones += [(f"Over {l}", rO, p_over_mod),
                                 (f"Under {l}", rU, 1 - p_over_mod)]
                filas.append({
                    "Línea": l,
                    "Over (casa)": f"{dv['fair_a']:.1%}",
                    "Over (modelo)": f"{p_over_mod:.1%}",
                    "EV Over": f"{rO['ev']:+.1%}",
                    "EV Under": f"{rU['ev']:+.1%}",
                    "Margen casa": f"{dv['margen']:.1%}",
                })

            # ¿Cuántos goles cree la casa? (λ ajustada a todas las líneas)
            lam_casa = an.lambda_implicita_casa(pares_fair)
            st.subheader("🏦 ¿Cuántos goles totales cree la casa?")
            m1, m2, m3 = st.columns(3)
            m1.metric("Goles totales · CASA", f"{lam_casa:.2f}",
                      help="Goles esperados que implican los momios de la casa.")
            m2.metric("Goles totales · MODELO", f"{lam_modelo:.2f}",
                      f"{lam_modelo - lam_casa:+.2f} vs casa",
                      help="Goles esperados según nuestro modelo de Poisson.")
            diff = lam_modelo - lam_casa
            m3.metric("Diferencia", f"{abs(diff):.2f} goles",
                      "Modelo espera más" if diff > 0 else "Casa espera más")

            if abs(diff) < 0.15:
                st.info("🤝 La casa y el modelo casi coinciden en los goles "
                        "esperados: mercado eficiente, poco margen de valor.")
            elif diff > 0:
                st.success(f"📈 El modelo espera **{diff:.2f} goles más** que la "
                           f"casa → el lado **Over** tiende a tener valor.")
            else:
                st.error(f"📉 El modelo espera **{abs(diff):.2f} goles menos** que "
                         f"la casa → el lado **Under** tiende a tener valor.")

            # Distribución de goles totales: casa vs modelo
            k = list(range(9))
            dcasa = an.dist_goles_totales(lam_casa, 8)
            dmod = an.dist_goles_totales(lam_modelo, 8)
            fig = go.Figure()
            fig.add_bar(x=k, y=dcasa, name=f"Casa (λ={lam_casa:.2f})",
                        marker_color="#e74c3c",
                        text=[f"{v:.0%}" for v in dcasa], textposition="outside")
            fig.add_bar(x=k, y=dmod, name=f"Modelo (λ={lam_modelo:.2f})",
                        marker_color="#2ecc71",
                        text=[f"{v:.0%}" for v in dmod], textposition="outside")
            fig.update_layout(barmode="group", yaxis_tickformat=".0%",
                              xaxis_title="Goles totales en el partido",
                              title="Probabilidad de cada total de goles: casa vs modelo",
                              legend=dict(orientation="h", y=-0.2), height=420)
            st.plotly_chart(fig, width="stretch")

            # Tabla por línea (probabilidades y EV)
            st.subheader("Detalle por línea")
            st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")

            # Recomendación global: mejor EV entre todas las líneas y lados
            st.subheader("Recomendación")
            etiqueta, mejor, prob = max(evaluaciones, key=lambda e: e[1]["ev"])
            if mejor["es_valor"]:
                st.success(
                    f"🎯 **Apostar {etiqueta} goles** — es la jugada con más valor. "
                    f"El modelo le da **{prob:.1%}** y la casa solo implica "
                    f"{mejor['implicita']:.1%} con su cuota "
                    f"{fmt_momio(mejor['momio_decimal'])}. "
                    f"EV **{mejor['ev']:+.1%}** · cuota justa {mejor['cuota_justa']:.2f} "
                    f"· Kelly {mejor['kelly']:.1%} del bankroll.")
            else:
                st.warning(
                    f"⚠️ **Ninguna línea ofrece valor** con estos momios. La menos "
                    f"mala sería {etiqueta} (EV {mejor['ev']:+.1%}), pero no compensa. "
                    f"Mejor no apostar este mercado.")

    # -----------------------------------------------------------------------
    # C) OVER/UNDER (Tarjetas o Corners)
    # -----------------------------------------------------------------------
    else:
        es_tarjetas = mercado.startswith("Tarjetas")
        a, b = selector_equipos("evou")
        if es_tarjetas:
            elim = st.toggle("Eliminación directa (factor 1.15)", key="ev_elim")
            pred = an.prediccion_tarjetas(a, b, 1.15 if elim else 1.0)
            unidad = "tarjetas"
        else:
            pred = an.prediccion_corners(a, b)
            unidad = "corners"

        total_esp = pred["total_esp"] if es_tarjetas else pred["total"]
        lineas = list(pred["overs"].keys())
        linea = st.selectbox(f"Línea de {unidad}", lineas, key="ev_linea")
        p_over = pred["overs"][linea]
        p_under = 1.0 - p_over

        st.caption(f"Total esperado del modelo: **{total_esp:.2f} {unidad}**.")

        st.subheader("Momios del mercado")
        co, cu = st.columns(2)
        mO = co.number_input(f"Over {linea}", value=d_over, step=paso,
                             min_value=rango[0], max_value=rango[1], key="ev_mO")
        mU = cu.number_input(f"Under {linea}", value=d_under, step=paso,
                             min_value=rango[0], max_value=rango[1], key="ev_mU")

        dO, dU = a_decimal(mO), a_decimal(mU)
        ov = an.margen_overround(dO, 1e9, dU)  # mercado de 2 vías: empate neutro
        rO = an.valor_esperado(p_over, dO)
        rU = an.valor_esperado(p_under, dU)

        st.subheader("Margen y valor esperado")
        m1, m2, m3 = st.columns(3)
        m1.metric("Margen (vig)", f"{ov['margen']:.2%}",
                  help="Comisión de la casa en este mercado Over/Under.")
        m2.metric(f"Over {linea} · EV", f"{rO['ev']:+.1%}",
                  f"Modelo {p_over:.1%} vs Casa {rO['implicita']:.1%}",
                  delta_color="normal" if rO["es_valor"] else "inverse")
        m3.metric(f"Under {linea} · EV", f"{rU['ev']:+.1%}",
                  f"Modelo {p_under:.1%} vs Casa {rU['implicita']:.1%}",
                  delta_color="normal" if rU["es_valor"] else "inverse")

        for etiqueta, r, prob in [(f"Over {linea}", rO, p_over),
                                  (f"Under {linea}", rU, p_under)]:
            if r["es_valor"]:
                st.success(
                    f"✅ **Apuesta de valor — {etiqueta} {unidad}**: modelo "
                    f"{prob:.1%} vs {r['implicita']:.1%} implícito. "
                    f"EV **{r['ev']:+.1%}**, cuota justa **{r['cuota_justa']:.2f}** "
                    f"(la casa paga {fmt_momio(r['momio_decimal'])}). "
                    f"Kelly: {r['kelly']:.1%} del bankroll.")
            else:
                st.error(
                    f"❌ **Sin valor — {etiqueta} {unidad}**: cuota "
                    f"{fmt_momio(r['momio_decimal'])} implica {r['implicita']:.1%} "
                    f"vs {prob:.1%} del modelo. EV **{r['ev']:+.1%}** "
                    f"(necesitarías ≥ {r['cuota_justa']:.2f}).")

        # Recomendación: qué lado apostar según los momios dados
        st.subheader("Recomendación")
        mejor = rO if rO["ev"] >= rU["ev"] else rU
        lado = "OVER" if mejor is rO else "UNDER"
        prob_lado = p_over if mejor is rO else p_under
        if mejor["es_valor"]:
            st.success(
                f"🎯 **Apostar {lado} {linea} {unidad}** — es el lado con valor. "
                f"El modelo le da **{prob_lado:.1%}** de probabilidad y la casa "
                f"solo implica {mejor['implicita']:.1%} con su cuota "
                f"{fmt_momio(mejor['momio_decimal'])}. "
                f"Ventaja (edge): **{mejor['edge']:+.1%}** · EV **{mejor['ev']:+.1%}** · "
                f"apuesta sugerida {mejor['kelly']:.1%} del bankroll (Kelly).")
        else:
            st.warning(
                f"⚠️ **Ningún lado ofrece valor** con estos momios. El menos malo "
                f"sería {lado} {linea} (EV {mejor['ev']:+.1%}), pero la cuota "
                f"{fmt_momio(mejor['momio_decimal'])} no compensa: el modelo da "
                f"{prob_lado:.1%} y necesitarías al menos {mejor['cuota_justa']:.2f}. "
                f"Mejor no apostar este mercado.")

        # Tabla de TODAS las líneas: porcentajes del modelo y cuotas justas,
        # para comparar contra cualquier momio que ofrezca la casa.
        st.subheader(f"Todas las líneas de {unidad} (referencia del modelo)")
        filas = []
        for l in lineas:
            po = pred["overs"][l]
            pu = 1.0 - po
            filas.append({
                "Línea": l,
                "Over (modelo)": f"{po:.1%}",
                "Cuota justa Over": round(1 / po, 2) if po > 0 else float("inf"),
                "Under (modelo)": f"{pu:.1%}",
                "Cuota justa Under": round(1 / pu, 2) if pu > 0 else float("inf"),
                "Lado favorecido": "Over" if po >= pu else "Under",
            })
        st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
        st.caption("Apuesta a un lado solo si el momio que te ofrecen es **mayor** "
                   "que su cuota justa: ahí el pago supera el riesgo real (EV+).")

        etq = [f"Over {linea}", f"Under {linea}"]
        modelo_vals = [p_over, p_under]
        casa_vals = [rO["implicita"], rU["implicita"]]
        fig = go.Figure()
        fig.add_bar(y=etq, x=modelo_vals, name="Probabilidad del Modelo",
                    orientation="h", marker_color="#2ecc71",
                    text=[f"{v:.1%}" for v in modelo_vals], textposition="auto")
        fig.add_bar(y=etq, x=casa_vals, name="Implícita de la Casa",
                    orientation="h", marker_color="#e74c3c",
                    text=[f"{v:.1%}" for v in casa_vals], textposition="auto")
        fig.update_layout(barmode="group", xaxis_tickformat=".0%",
                          title="Probabilidad del Modelo vs Implícita de la Casa",
                          legend=dict(orientation="h", y=-0.3), height=320)
        st.plotly_chart(fig, width="stretch")


# ===========================================================================
# 2) TARJETAS
# ===========================================================================
elif seccion == "🟨 Tarjetas (Over/Under)":
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
