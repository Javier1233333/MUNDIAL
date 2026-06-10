# -*- coding: utf-8 -*-
"""
Lógica matemática del dashboard: modelo de Poisson, Monte Carlo,
tarjetas, corners y proyección del torneo completo (104 partidos).

Modelo base (Poisson bivariado independiente):
    λ_A = μ * (ataque_A / μ) * (defensa_B / μ) * F_forma(A) * F_ranking(A,B)
donde μ es el promedio de goles por equipo por partido del torneo (~1.3).
P(goles = k) = e^(-λ) * λ^k / k!   (scipy.stats.poisson)
"""

import os
import numpy as np
import pandas as pd
from scipy.stats import poisson

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

MU_GOLES = 1.30      # promedio histórico de goles por equipo por partido en Mundiales
MAX_GOLES = 10       # truncamiento de la matriz de Poisson
VENTAJA_FAVORITO = 1.12   # multiplicador de corners cuando el equipo es favorito
CASTIGO_NO_FAVORITO = 0.90


# ---------------------------------------------------------------------------
# Carga de datos
# ---------------------------------------------------------------------------
def load_teams() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(DATA_DIR, "world_cup_data.csv"))
    return df.set_index("equipo", drop=False)


def load_matches() -> pd.DataFrame:
    return pd.read_csv(os.path.join(DATA_DIR, "matches.csv"))


# ---------------------------------------------------------------------------
# 1) SIMULADOR DE PROBABILIDADES (Poisson / Monte Carlo)
# ---------------------------------------------------------------------------
def factor_forma(forma_5: float) -> float:
    """Forma reciente (0-15 pts en últimos 5 partidos) → multiplicador 0.90-1.10.
    7.5 pts (50% de rendimiento) es neutro (factor = 1.0)."""
    return 0.90 + (forma_5 / 15.0) * 0.20


def factor_ranking(pts_a: float, pts_b: float) -> float:
    """Diferencia de puntos FIFA → multiplicador del ataque (acotado ±12%).
    Cada ~100 pts de diferencia mueven el factor ~3.5%."""
    return float(np.clip(1.0 + (pts_a - pts_b) / 2800.0, 0.88, 1.12))


def lambdas_partido(a: pd.Series, b: pd.Series) -> tuple[float, float]:
    """Goles esperados (λ) de cada equipo combinando ataque propio,
    defensa rival, forma y ranking FIFA."""
    # Fuerza de ataque/defensa relativa al promedio del torneo
    lam_a = MU_GOLES * (a.gf_pp / MU_GOLES) * (b.gc_pp / MU_GOLES) \
        * factor_forma(a.forma_5) * factor_ranking(a.puntos_fifa, b.puntos_fifa)
    lam_b = MU_GOLES * (b.gf_pp / MU_GOLES) * (a.gc_pp / MU_GOLES) \
        * factor_forma(b.forma_5) * factor_ranking(b.puntos_fifa, a.puntos_fifa)
    return max(lam_a, 0.15), max(lam_b, 0.15)


def matriz_poisson(lam_a: float, lam_b: float) -> np.ndarray:
    """Matriz P[i, j] = P(A anota i) * P(B anota j), goles 0..MAX_GOLES."""
    k = np.arange(MAX_GOLES + 1)
    pa = poisson.pmf(k, lam_a)
    pb = poisson.pmf(k, lam_b)
    return np.outer(pa, pb)


def probabilidades_1v1(a: pd.Series, b: pd.Series) -> dict:
    """Probabilidades 1X2, over/under, ambos anotan y marcadores más probables."""
    lam_a, lam_b = lambdas_partido(a, b)
    m = matriz_poisson(lam_a, lam_b)
    p_win = float(np.tril(m, -1).sum())   # i > j → gana A
    p_draw = float(np.trace(m))           # i = j → empate
    p_loss = float(np.triu(m, 1).sum())   # i < j → gana B

    # Goles totales: suma de Poissons independientes ~ Poisson(λA + λB)
    lam_total = lam_a + lam_b
    overs = {linea: float(1 - poisson.cdf(int(linea), lam_total))
             for linea in (1.5, 2.5, 3.5)}
    btts = float((1 - poisson.pmf(0, lam_a)) * (1 - poisson.pmf(0, lam_b)))

    # Top 5 marcadores más probables
    idx = np.dstack(np.unravel_index(np.argsort(m, axis=None)[::-1][:5], m.shape))[0]
    marcadores = [(int(i), int(j), float(m[i, j])) for i, j in idx]

    return {"lam_a": lam_a, "lam_b": lam_b,
            "p_win": p_win, "p_draw": p_draw, "p_loss": p_loss,
            "overs": overs, "btts": btts, "marcadores": marcadores}


def monte_carlo_1v1(a: pd.Series, b: pd.Series, n: int = 10_000,
                    seed: int = 42) -> dict:
    """Simulación de Monte Carlo: n partidos con marcadores ~ Poisson(λ)."""
    lam_a, lam_b = lambdas_partido(a, b)
    rng = np.random.default_rng(seed)
    ga = rng.poisson(lam_a, n)
    gb = rng.poisson(lam_b, n)
    return {"p_win": float((ga > gb).mean()), "p_draw": float((ga == gb).mean()),
            "p_loss": float((ga < gb).mean()), "goles_a": ga, "goles_b": gb}


# ---------------------------------------------------------------------------
# 2) MÓDULO DE TARJETAS
# ---------------------------------------------------------------------------
def prediccion_tarjetas(a: pd.Series, b: pd.Series,
                        factor_rivalidad: float = 1.0) -> dict:
    """Total esperado de tarjetas del partido = suma de promedios de ambos
    equipos, ajustado por rivalidad/fase (eliminación directa ≈ 1.15).
    Over/Under con Poisson sobre el total esperado."""
    amarillas = (a.amarillas_pp + b.amarillas_pp) * factor_rivalidad
    rojas = (a.rojas_pp + b.rojas_pp) * factor_rivalidad
    total = amarillas + rojas
    overs = {linea: float(1 - poisson.cdf(int(linea), total))
             for linea in (2.5, 3.5, 4.5, 5.5)}
    p_roja = float(1 - poisson.pmf(0, rojas))  # P(al menos una roja)
    return {"amarillas_esp": amarillas, "rojas_esp": rojas,
            "total_esp": total, "overs": overs, "p_roja": p_roja}


# ---------------------------------------------------------------------------
# 3) MÓDULO DE CORNERS
# ---------------------------------------------------------------------------
def es_favorito(a: pd.Series, b: pd.Series) -> bool:
    return a.puntos_fifa >= b.puntos_fifa


def prediccion_corners(a: pd.Series, b: pd.Series) -> dict:
    """Corners esperados de cada equipo:
        E[corners_A] = (corners_favor_A + corners_contra_B) / 2 * rol
    El favorito domina la posesión → genera más corners (factor 1.12);
    el no favorito cede iniciativa (factor 0.90)."""
    rol_a = VENTAJA_FAVORITO if es_favorito(a, b) else CASTIGO_NO_FAVORITO
    rol_b = VENTAJA_FAVORITO if es_favorito(b, a) else CASTIGO_NO_FAVORITO
    esp_a = (a.corners_favor_pp + b.corners_contra_pp) / 2 * rol_a
    esp_b = (b.corners_favor_pp + a.corners_contra_pp) / 2 * rol_b
    total = esp_a + esp_b
    overs = {linea: float(1 - poisson.cdf(int(linea), total))
             for linea in (7.5, 8.5, 9.5, 10.5, 11.5)}
    return {"corners_a": esp_a, "corners_b": esp_b, "total": total, "overs": overs}


def tabla_corners_rol(teams: pd.DataFrame) -> pd.DataFrame:
    """Promedios de corners por equipo según rol (favorito vs no favorito)."""
    df = teams.copy()
    df["corners_como_favorito"] = (df.corners_favor_pp * VENTAJA_FAVORITO).round(2)
    df["corners_como_no_favorito"] = (df.corners_favor_pp * CASTIGO_NO_FAVORITO).round(2)
    df["diferencial"] = (df.corners_favor_pp - df.corners_contra_pp).round(2)
    return df[["equipo", "grupo", "corners_favor_pp", "corners_contra_pp",
               "corners_como_favorito", "corners_como_no_favorito", "diferencial"]]


# ---------------------------------------------------------------------------
# 4) PROYECCIÓN DEL TORNEO COMPLETO (104 partidos)
# ---------------------------------------------------------------------------
def puntos_esperados_grupo(teams: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    """Puntos esperados por equipo en fase de grupos:
    E[pts] = Σ (3·P(victoria) + 1·P(empate)) sobre sus 3 partidos."""
    grupos = matches[matches.fase == "Grupos"]
    pts = {t: 0.0 for t in teams.index}
    dg = {t: 0.0 for t in teams.index}  # diferencia de goles esperada (desempate)
    for _, m in grupos.iterrows():
        a, b = teams.loc[m.equipo_a], teams.loc[m.equipo_b]
        p = probabilidades_1v1(a, b)
        pts[m.equipo_a] += 3 * p["p_win"] + p["p_draw"]
        pts[m.equipo_b] += 3 * p["p_loss"] + p["p_draw"]
        dg[m.equipo_a] += p["lam_a"] - p["lam_b"]
        dg[m.equipo_b] += p["lam_b"] - p["lam_a"]
    out = teams[["equipo", "grupo", "ranking_fifa"]].copy()
    out["pts_esperados"] = out.equipo.map(pts).round(2)
    out["dg_esperada"] = out.equipo.map(dg).round(2)
    return out.sort_values(["grupo", "pts_esperados", "dg_esperada"],
                           ascending=[True, False, False])


def proyectar_torneo(teams: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    """Resuelve los 32 partidos de eliminación directa proyectando la fase de
    grupos con el modelo: clasifican los 12 primeros, 12 segundos y los 8
    mejores terceros; el bracket se arma por siembra 1-32 según puntos
    esperados (simplificación documentada del bracket oficial)."""
    standings = puntos_esperados_grupo(teams, matches)
    standings["pos"] = standings.groupby("grupo").cumcount() + 1

    primeros = standings[standings.pos == 1]
    segundos = standings[standings.pos == 2]
    terceros = standings[standings.pos == 3].nlargest(8, ["pts_esperados", "dg_esperada"])
    clasificados = pd.concat([primeros, segundos, terceros]) \
        .sort_values(["pts_esperados", "dg_esperada"], ascending=False)
    seeds = clasificados.equipo.tolist()  # 32 equipos sembrados

    out = matches.copy()
    out["prob_a"] = np.nan
    out["prob_empate"] = np.nan
    out["prob_b"] = np.nan
    out["goles_esp_a"] = np.nan
    out["goles_esp_b"] = np.nan
    out["ganador_proyectado"] = ""

    def predecir(idx, ea, eb, eliminacion):
        a, b = teams.loc[ea], teams.loc[eb]
        p = probabilidades_1v1(a, b)
        out.loc[idx, ["equipo_a", "equipo_b"]] = [ea, eb]
        out.loc[idx, ["prob_a", "prob_empate", "prob_b"]] = \
            [round(p["p_win"], 3), round(p["p_draw"], 3), round(p["p_loss"], 3)]
        out.loc[idx, ["goles_esp_a", "goles_esp_b"]] = \
            [round(p["lam_a"], 2), round(p["lam_b"], 2)]
        if eliminacion:
            # En eliminación directa no hay empate: avanza el de mayor prob.
            ganador = ea if p["p_win"] >= p["p_loss"] else eb
        else:
            probs = {ea: p["p_win"], "Empate": p["p_draw"], eb: p["p_loss"]}
            ganador = max(probs, key=probs.get)
        out.loc[idx, "ganador_proyectado"] = ganador
        return ganador if eliminacion else None

    # Fase de grupos: solo predicción
    for idx, m in out[out.fase == "Grupos"].iterrows():
        predecir(idx, m.equipo_a, m.equipo_b, eliminacion=False)

    # Bracket: siembra 1v32, 2v31, ... y propagación de ganadores
    ronda = [(seeds[i], seeds[31 - i]) for i in range(16)]
    for fase in ["Dieciseisavos", "Octavos", "Cuartos", "Semifinal"]:
        idxs = out.index[out.fase == fase].tolist()
        ganadores = []
        for idx, (ea, eb) in zip(idxs, ronda):
            ganadores.append(predecir(idx, ea, eb, eliminacion=True))
        perdedores = [a if g == b else b for (a, b), g in zip(ronda, ganadores)]
        ronda = [(ganadores[i], ganadores[i + 1]) for i in range(0, len(ganadores), 2)] \
            if len(ganadores) > 2 else ganadores
        if fase == "Semifinal":
            idx3 = out.index[out.fase == "Tercer Puesto"][0]
            predecir(idx3, perdedores[0], perdedores[1], eliminacion=True)
            idxf = out.index[out.fase == "Final"][0]
            campeon = predecir(idxf, ganadores[0], ganadores[1], eliminacion=True)
            out.attrs["campeon_proyectado"] = campeon
    return out
