# -*- coding: utf-8 -*-
"""
Procesa el dataset real (data/raw/, resultados internacionales 1872-2026)
y genera los CSVs que consume el dashboard:

- world_cup_data.csv : GF/GC por partido y forma (últimos 5) calculados con
  resultados REALES de los últimos 2 años. Ranking FIFA, corners y tarjetas
  se mantienen de la semilla calibrada (el dataset no los incluye).
- matches.csv : los 72 partidos oficiales de grupos del dataset (con sede
  real) + 32 de eliminación directa con las fechas oficiales del torneo.

Ejecutar:  .venv/bin/python process_data.py
"""

import os
from datetime import date

import pandas as pd

from generate_data import TEAMS, GROUP_DRAW

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE_DIR, "data", "raw")
OUT = os.path.join(BASE_DIR, "data")

VENTANA_INICIO = "2024-06-11"   # últimos 2 años de partidos jugados
HOY = "2026-06-10"

# Dataset (inglés) -> nombres del dashboard (español)
NOMBRES = {
    "Algeria": "Argelia", "Argentina": "Argentina", "Australia": "Australia",
    "Austria": "Austria", "Belgium": "Bélgica",
    "Bosnia and Herzegovina": "Bosnia y Herzegovina", "Brazil": "Brasil",
    "Canada": "Canadá", "Cape Verde": "Cabo Verde", "Colombia": "Colombia",
    "Croatia": "Croacia", "Curaçao": "Curazao",
    "Czech Republic": "República Checa", "DR Congo": "RD Congo",
    "Ecuador": "Ecuador", "Egypt": "Egipto", "England": "Inglaterra",
    "France": "Francia", "Germany": "Alemania", "Ghana": "Ghana",
    "Haiti": "Haití", "Iran": "Irán", "Iraq": "Irak",
    "Ivory Coast": "Costa de Marfil", "Japan": "Japón", "Jordan": "Jordania",
    "Mexico": "México", "Morocco": "Marruecos", "Netherlands": "Países Bajos",
    "New Zealand": "Nueva Zelanda", "Norway": "Noruega", "Panama": "Panamá",
    "Paraguay": "Paraguay", "Portugal": "Portugal", "Qatar": "Catar",
    "Saudi Arabia": "Arabia Saudita", "Scotland": "Escocia",
    "Senegal": "Senegal", "South Africa": "Sudáfrica",
    "South Korea": "Corea del Sur", "Spain": "España", "Sweden": "Suecia",
    "Switzerland": "Suiza", "Tunisia": "Túnez", "Turkey": "Turquía",
    "United States": "Estados Unidos", "Uruguay": "Uruguay",
    "Uzbekistan": "Uzbekistán",
}

# Ciudad del dataset -> sede metropolitana (como se conoce comercialmente)
SEDES = {
    "Arlington": "Dallas", "East Rutherford": "Nueva York/Nueva Jersey",
    "Foxborough": "Boston", "Inglewood": "Los Ángeles",
    "Guadalupe": "Monterrey", "Zapopan": "Guadalajara",
    "Santa Clara": "San Francisco", "Miami Gardens": "Miami",
    "Mexico City": "Ciudad de México", "Philadelphia": "Filadelfia",
}


def cargar_resultados() -> pd.DataFrame:
    r = pd.read_csv(os.path.join(RAW, "results.csv"))
    r["home_team"] = r.home_team.map(NOMBRES).fillna(r.home_team)
    r["away_team"] = r.away_team.map(NOMBRES).fillna(r.away_team)
    return r


def metricas_reales(r: pd.DataFrame) -> pd.DataFrame:
    """GF/GC por partido AJUSTADOS POR FUERZA DEL RIVAL y forma (pts últimos 5).

    Los promedios brutos sesgan el modelo: un equipo que golea rivales débiles
    en eliminatorias parece mejor de lo que es. Corrección iterativa (estilo
    Dixon-Coles simplificado) usando TODOS los países como contexto:
        ataque_t  = media( gf_i / (μ · defensa_rival_i) )
        defensa_t = media( gc_i / (μ · ataque_rival_i) )
    y al converger:  gf_pp = μ·ataque_t  (goles esperados vs rival promedio)."""
    jugados = r.dropna(subset=["home_score", "away_score"])
    jugados = jugados[(jugados.date >= VENTANA_INICIO) & (jugados.date <= HOY)]

    # Vista "larga": una fila por equipo y partido (todos los países,
    # para estimar bien la fuerza de cada rival)
    local = jugados.rename(columns={"home_team": "equipo", "away_team": "rival",
                                    "home_score": "gf", "away_score": "gc"})
    visita = jugados.rename(columns={"away_team": "equipo", "home_team": "rival",
                                     "away_score": "gf", "home_score": "gc"})
    largo = pd.concat([local, visita])[["date", "equipo", "rival", "gf", "gc"]]
    largo = largo.sort_values("date")

    mu = largo.gf.mean()  # goles promedio por equipo por partido
    ataque = pd.Series(1.0, index=largo.equipo.unique())
    defensa = pd.Series(1.0, index=largo.equipo.unique())
    for _ in range(20):  # iteración de punto fijo (converge en ~10 pasos)
        ataque_n = (largo.gf / (mu * largo.rival.map(defensa))) \
            .groupby(largo.equipo).mean()
        defensa_n = (largo.gc / (mu * largo.rival.map(ataque))) \
            .groupby(largo.equipo).mean()
        ataque, defensa = ataque_n / ataque_n.mean(), defensa_n / defensa_n.mean()

    # Puntos por partido: 3 victoria, 1 empate
    largo["pts"] = (largo.gf > largo.gc) * 3 + (largo.gf == largo.gc) * 1
    solo48 = largo[largo.equipo.isin(NOMBRES.values())]

    agg = solo48.groupby("equipo").agg(
        partidos_2a=("gf", "size"),
        gf_pp_bruto=("gf", "mean"),
        gc_pp_bruto=("gc", "mean"),
    )
    # Reescalado al contexto mundialista: la fuerza se expresa relativa al
    # CLASIFICADO promedio (no al país promedio del mundo, que incluye
    # selecciones muy débiles) y se amortigua (^0.7) para evitar extremos.
    # μ_wc = 1.30 goles/equipo/partido (promedio histórico de Mundiales).
    MU_WC, DAMP = 1.30, 0.7
    atq_rel = ataque[agg.index] / ataque[agg.index].mean()
    def_rel = defensa[agg.index] / defensa[agg.index].mean()
    agg["gf_pp"] = (MU_WC * atq_rel ** DAMP).round(2)   # ajustado por rival
    agg["gc_pp"] = (MU_WC * def_rel ** DAMP).round(2)   # ajustado por rival
    agg["forma_5"] = solo48.groupby("equipo").pts.apply(lambda s: s.tail(5).sum())
    return agg.round({"gf_pp_bruto": 2, "gc_pp_bruto": 2})


def write_teams(agg: pd.DataFrame):
    """Combina métricas reales (goles/forma) con la semilla calibrada
    (ranking FIFA, corners, tarjetas, que el dataset no trae)."""
    grupo = {t: g for g, ts in GROUP_DRAW.items() for t in ts}
    filas = []
    for (nombre, conf, rk, pts, gf_s, gc_s, cf, cc, am, ro, forma_s) in TEAMS:
        real = agg.loc[nombre] if nombre in agg.index else None
        filas.append({
            "equipo": nombre, "confederacion": conf, "grupo": grupo[nombre],
            "ranking_fifa": rk, "puntos_fifa": pts,
            "gf_pp": real.gf_pp if real is not None else gf_s,
            "gc_pp": real.gc_pp if real is not None else gc_s,
            "gf_pp_bruto": real.gf_pp_bruto if real is not None else gf_s,
            "gc_pp_bruto": real.gc_pp_bruto if real is not None else gc_s,
            "corners_favor_pp": cf, "corners_contra_pp": cc,
            "amarillas_pp": am, "rojas_pp": ro,
            "forma_5": int(real.forma_5) if real is not None else forma_s,
            "partidos_2a": int(real.partidos_2a) if real is not None else 0,
        })
    df = pd.DataFrame(filas).sort_values(["grupo", "ranking_fifa"])
    df.to_csv(os.path.join(OUT, "world_cup_data.csv"), index=False)
    print(f"OK -> world_cup_data.csv ({len(df)} equipos, "
          f"{df.partidos_2a.sum()} partidos reales agregados)")


def write_matches(r: pd.DataFrame):
    """72 partidos oficiales de grupos (del dataset, con sede real)
    + 32 de eliminación directa con fechas oficiales."""
    wc = r[(r.tournament == "FIFA World Cup") & (r.date >= "2026-06-01")].copy()
    wc = wc.sort_values(["date", "city"]).reset_index(drop=True)
    grupo = {t: g for g, ts in GROUP_DRAW.items() for t in ts}

    rows = []
    for i, m in wc.iterrows():
        rows.append([i + 1, "Grupos", grupo[m.home_team], m.date,
                     m.home_team, m.away_team, SEDES.get(m.city, m.city)])

    ko = [
        ("Dieciseisavos", [date(2026, 6, 28)] * 3 + [date(2026, 6, 29)] * 3
                        + [date(2026, 6, 30)] * 3 + [date(2026, 7, 1)] * 3
                        + [date(2026, 7, 2)] * 2 + [date(2026, 7, 3)] * 2),
        ("Octavos", [date(2026, 7, 4)] * 2 + [date(2026, 7, 5)] * 2
                  + [date(2026, 7, 6)] * 2 + [date(2026, 7, 7)] * 2),
        ("Cuartos", [date(2026, 7, 9), date(2026, 7, 9),
                     date(2026, 7, 10), date(2026, 7, 11)]),
        ("Semifinal", [date(2026, 7, 14), date(2026, 7, 15)]),
        ("Tercer Puesto", [date(2026, 7, 18)]),
        ("Final", [date(2026, 7, 19)]),
    ]
    mid = len(rows) + 1
    for fase, fechas in ko:
        for d in fechas:
            sede = ("MetLife Stadium, Nueva York/Nueva Jersey"
                    if fase == "Final" else "Por confirmar")
            rows.append([mid, fase, "", d.isoformat(),
                         f"POR_DEFINIR_{mid}A", f"POR_DEFINIR_{mid}B", sede])
            mid += 1

    df = pd.DataFrame(rows, columns=["partido_id", "fase", "grupo", "fecha",
                                     "equipo_a", "equipo_b", "sede"])
    df.to_csv(os.path.join(OUT, "matches.csv"), index=False)
    print(f"OK -> matches.csv ({len(df)} partidos, 72 oficiales del dataset)")


if __name__ == "__main__":
    r = cargar_resultados()
    write_teams(metricas_reales(r))
    write_matches(r)
