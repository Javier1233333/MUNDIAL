# -*- coding: utf-8 -*-
"""
Generador de datos semilla para el Mundial 2026 (48 equipos, 104 partidos).

- data/world_cup_data.csv : métricas por equipo (ranking FIFA, goles, corners, tarjetas, forma)
- data/matches.csv        : calendario de los 104 partidos (72 de grupos + 32 de eliminación)

NOTA: Grupos según el sorteo oficial (dic 2025) + repechajes confirmados
(República Checa, Bosnia y Herzegovina, Suecia, Turquía, RD Congo, Irak).
Las métricas de rendimiento son datos semilla realistas (últimos 2 años),
calibradas por nivel de cada selección.
"""

import csv
import os
from datetime import date, timedelta

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# ---------------------------------------------------------------------------
# 1) EQUIPOS: (nombre, confederación, ranking FIFA, puntos FIFA,
#              GF/partido, GC/partido, corners a favor, corners en contra,
#              amarillas/partido, rojas/partido, forma últimos 5 (0-15 pts))
# ---------------------------------------------------------------------------
TEAMS = [
    # CONMEBOL
    ("Argentina",      "CONMEBOL", 1,  1867, 2.4, 0.6, 6.1, 3.2, 2.1, 0.09, 13),
    ("Brasil",         "CONMEBOL", 5,  1776, 1.9, 0.9, 5.9, 3.6, 2.3, 0.12, 10),
    ("Colombia",       "CONMEBOL", 13, 1679, 1.7, 0.8, 5.4, 3.9, 2.4, 0.10, 11),
    ("Uruguay",        "CONMEBOL", 15, 1672, 1.6, 0.8, 5.2, 4.0, 2.6, 0.15, 9),
    ("Ecuador",        "CONMEBOL", 23, 1588, 1.3, 0.7, 4.8, 4.2, 2.5, 0.13, 10),
    ("Paraguay",       "CONMEBOL", 39, 1503, 1.1, 0.8, 4.3, 4.5, 2.7, 0.14, 9),
    # UEFA
    ("España",         "UEFA",     2,  1854, 2.5, 0.5, 6.5, 2.8, 1.7, 0.06, 14),
    ("Francia",        "UEFA",     3,  1830, 2.1, 0.7, 5.8, 3.3, 1.9, 0.08, 12),
    ("Inglaterra",     "UEFA",     4,  1813, 2.2, 0.5, 6.2, 3.0, 1.6, 0.05, 13),
    ("Portugal",       "UEFA",     6,  1770, 2.3, 0.8, 6.0, 3.1, 1.9, 0.11, 11),
    ("Países Bajos",   "UEFA",     7,  1759, 2.1, 0.8, 5.7, 3.3, 1.8, 0.07, 12),
    ("Bélgica",        "UEFA",     8,  1740, 1.9, 1.0, 5.5, 3.6, 1.8, 0.07, 10),
    ("Alemania",       "UEFA",     9,  1724, 2.0, 1.0, 5.9, 3.4, 1.7, 0.06, 10),
    ("Croacia",        "UEFA",     10, 1717, 1.8, 0.9, 5.3, 3.7, 2.0, 0.09, 11),
    ("Suiza",          "UEFA",     17, 1655, 1.7, 0.9, 5.1, 3.8, 1.8, 0.07, 10),
    ("Austria",        "UEFA",     18, 1652, 1.8, 1.0, 5.2, 3.8, 2.0, 0.08, 11),
    ("Noruega",        "UEFA",     29, 1553, 2.0, 0.9, 5.3, 3.7, 1.9, 0.08, 13),
    ("Escocia",        "UEFA",     38, 1507, 1.2, 1.1, 4.6, 4.3, 2.1, 0.09, 9),
    ("Turquía",        "UEFA",     27, 1572, 1.6, 1.2, 5.0, 4.0, 2.8, 0.16, 10),  # repechaje
    ("República Checa","UEFA",     31, 1542, 1.5, 1.0, 4.8, 4.1, 2.1, 0.09, 10),  # repechaje
    ("Bosnia y Herzegovina","UEFA",34, 1525, 1.4, 1.0, 4.6, 4.2, 2.4, 0.12, 10),  # repechaje
    ("Suecia",         "UEFA",     37, 1510, 1.5, 1.1, 4.9, 4.0, 1.9, 0.07, 8),   # repechaje
    # CONCACAF
    ("México",         "CONCACAF", 14, 1675, 1.6, 0.9, 5.3, 3.8, 2.2, 0.11, 10),
    ("Estados Unidos", "CONCACAF", 16, 1670, 1.7, 0.9, 5.2, 3.8, 2.0, 0.09, 10),
    ("Canadá",         "CONCACAF", 26, 1574, 1.5, 0.9, 4.9, 4.0, 2.1, 0.10, 11),
    ("Panamá",         "CONCACAF", 33, 1535, 1.3, 0.9, 4.6, 4.2, 2.5, 0.13, 10),
    ("Curazao",        "CONCACAF", 68, 1338, 1.1, 0.9, 4.0, 4.6, 2.4, 0.12, 10),
    ("Haití",          "CONCACAF", 84, 1289, 1.0, 1.2, 3.8, 4.9, 2.6, 0.14, 9),
    # AFC
    ("Japón",          "AFC",      19, 1645, 2.0, 0.7, 5.6, 3.5, 1.6, 0.05, 12),
    ("Irán",           "AFC",      20, 1618, 1.7, 0.8, 5.0, 3.9, 2.2, 0.11, 10),
    ("Corea del Sur",  "AFC",      22, 1599, 1.7, 0.9, 5.1, 3.9, 2.0, 0.08, 10),
    ("Australia",      "AFC",      25, 1583, 1.5, 0.8, 4.9, 4.0, 1.9, 0.07, 10),
    ("Catar",          "AFC",      51, 1445, 1.2, 1.2, 4.3, 4.5, 2.6, 0.13, 8),
    ("Arabia Saudita", "AFC",      60, 1390, 1.1, 1.0, 4.2, 4.5, 2.5, 0.12, 8),
    ("Jordania",       "AFC",      64, 1372, 1.2, 0.9, 4.2, 4.4, 2.4, 0.11, 10),
    ("Uzbekistán",     "AFC",      55, 1419, 1.3, 0.8, 4.4, 4.3, 2.3, 0.10, 11),
    ("Irak",           "AFC",      58, 1402, 1.1, 1.0, 4.1, 4.5, 2.7, 0.15, 9),   # repechaje
    # CAF
    ("Marruecos",      "CAF",      11, 1710, 1.9, 0.6, 5.6, 3.4, 2.1, 0.09, 13),
    ("Senegal",        "CAF",      24, 1587, 1.6, 0.7, 5.1, 3.8, 2.3, 0.11, 11),
    ("Egipto",         "CAF",      32, 1540, 1.5, 0.7, 4.8, 4.0, 2.2, 0.10, 11),
    ("Argelia",        "CAF",      35, 1521, 1.6, 0.9, 4.9, 4.0, 2.4, 0.12, 10),
    ("Costa de Marfil","CAF",      42, 1487, 1.5, 0.8, 4.8, 4.1, 2.3, 0.11, 11),
    ("Túnez",          "CAF",      43, 1480, 1.3, 0.7, 4.5, 4.2, 2.4, 0.12, 11),
    ("Ghana",          "CAF",      72, 1320, 1.3, 1.1, 4.4, 4.4, 2.5, 0.13, 9),
    ("Cabo Verde",     "CAF",      70, 1330, 1.1, 0.9, 4.0, 4.6, 2.3, 0.11, 10),
    ("Sudáfrica",      "CAF",      61, 1386, 1.3, 0.9, 4.4, 4.4, 2.3, 0.11, 10),
    ("RD Congo",       "CAF",      56, 1410, 1.2, 0.9, 4.3, 4.4, 2.5, 0.13, 10),  # repechaje
    # OFC
    ("Nueva Zelanda",  "OFC",      86, 1280, 1.2, 1.1, 4.1, 4.7, 1.9, 0.08, 9),
]

# ---------------------------------------------------------------------------
# 2) GRUPOS OFICIALES (sorteo de diciembre 2025)
# ---------------------------------------------------------------------------
GROUPS = list("ABCDEFGHIJKL")  # 12 grupos de 4

GROUP_DRAW = {
    "A": ["México", "Sudáfrica", "Corea del Sur", "República Checa"],
    "B": ["Canadá", "Bosnia y Herzegovina", "Catar", "Suiza"],
    "C": ["Brasil", "Marruecos", "Haití", "Escocia"],
    "D": ["Estados Unidos", "Paraguay", "Australia", "Turquía"],
    "E": ["Alemania", "Costa de Marfil", "Ecuador", "Curazao"],
    "F": ["Países Bajos", "Japón", "Suecia", "Túnez"],
    "G": ["Bélgica", "Egipto", "Irán", "Nueva Zelanda"],
    "H": ["España", "Uruguay", "Arabia Saudita", "Cabo Verde"],
    "I": ["Francia", "Senegal", "Noruega", "Irak"],
    "J": ["Argentina", "Argelia", "Austria", "Jordania"],
    "K": ["Portugal", "Colombia", "Uzbekistán", "RD Congo"],
    "L": ["Inglaterra", "Croacia", "Ghana", "Panamá"],
}

def assign_groups():
    assignment = {team: g for g, teams in GROUP_DRAW.items() for team in teams}
    missing = {t[0] for t in TEAMS} - set(assignment)
    assert not missing, f"Equipos sin grupo: {missing}"
    return assignment

# ---------------------------------------------------------------------------
# 3) ESCRITURA DE CSVs
# ---------------------------------------------------------------------------
def write_teams(assignment):
    path = os.path.join(OUT_DIR, "world_cup_data.csv")
    cols = ["equipo", "confederacion", "grupo", "ranking_fifa", "puntos_fifa",
            "gf_pp", "gc_pp", "corners_favor_pp", "corners_contra_pp",
            "amarillas_pp", "rojas_pp", "forma_5"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for t in sorted(TEAMS, key=lambda t: (assignment[t[0]], t[2])):
            w.writerow([t[0], t[1], assignment[t[0]], *t[2:]])
    print(f"OK -> {path} ({len(TEAMS)} equipos)")

# Jornada 1 oficial: (día de junio, grupo, equipo_a, equipo_b, sede)
JORNADA_1 = [
    (11, "A", "México", "Sudáfrica", "Ciudad de México"),
    (11, "A", "Corea del Sur", "República Checa", "Guadalajara"),
    (12, "B", "Canadá", "Bosnia y Herzegovina", "Toronto"),
    (12, "D", "Estados Unidos", "Paraguay", "Los Ángeles"),
    (13, "C", "Haití", "Escocia", "Boston"),
    (13, "D", "Australia", "Turquía", "Vancouver"),
    (13, "C", "Brasil", "Marruecos", "Nueva York/Nueva Jersey"),
    (13, "B", "Catar", "Suiza", "San Francisco"),
    (14, "E", "Alemania", "Curazao", "Houston"),
    (14, "F", "Países Bajos", "Japón", "Dallas"),
    (14, "E", "Costa de Marfil", "Ecuador", "Filadelfia"),
    (14, "F", "Suecia", "Túnez", "Monterrey"),
    (15, "H", "España", "Cabo Verde", "Atlanta"),
    (15, "G", "Bélgica", "Egipto", "Seattle"),
    (15, "H", "Arabia Saudita", "Uruguay", "Miami"),
    (15, "G", "Irán", "Nueva Zelanda", "Los Ángeles"),
    (16, "I", "Francia", "Senegal", "Nueva York/Nueva Jersey"),
    (16, "I", "Irak", "Noruega", "Boston"),
    (16, "J", "Argentina", "Argelia", "Kansas City"),
    (16, "J", "Austria", "Jordania", "San Francisco"),
    (17, "K", "Portugal", "RD Congo", "Houston"),
    (17, "L", "Inglaterra", "Croacia", "Dallas"),
    (17, "L", "Ghana", "Panamá", "Toronto"),
    (17, "K", "Uzbekistán", "Colombia", "Ciudad de México"),
]

def write_matches(assignment):
    """72 partidos de grupos (J1 oficial + J2/J3 derivadas del round-robin)
    + 32 de eliminación directa con las fechas oficiales del torneo."""
    path = os.path.join(OUT_DIR, "matches.csv")
    rows, mid = [], 1

    # --- Jornada 1 (calendario oficial con sedes) ---
    j1_pairs = {}  # grupo -> [(a, b), (c, d)] para derivar J2 y J3
    for dia, g, ea, eb, sede in JORNADA_1:
        rows.append([mid, "Grupos", g, date(2026, 6, dia).isoformat(), ea, eb, sede])
        j1_pairs.setdefault(g, []).append((ea, eb))
        mid += 1

    # --- Jornadas 2 y 3 derivadas del round-robin de 4 equipos ---
    # Si J1 = (a-b, c-d), entonces J2 = (a-c, b-d) y J3 = (a-d, b-c).
    # J2: 2 grupos por día (18-23 jun); J3: 3 grupos por día, partidos
    # simultáneos dentro del grupo (24-27 jun). Sedes por confirmar.
    orden = ["A", "B", "D", "C", "E", "F", "G", "H", "I", "J", "K", "L"]
    for i, g in enumerate(orden):
        (a, b), (c, d) = j1_pairs[g]
        fecha = date(2026, 6, 18 + i // 2)
        for ea, eb in [(a, c), (b, d)]:
            rows.append([mid, "Grupos", g, fecha.isoformat(), ea, eb, "Por confirmar"])
            mid += 1
    for i, g in enumerate(GROUPS):
        (a, b), (c, d) = j1_pairs[g]
        fecha = date(2026, 6, 24 + i // 3)
        for ea, eb in [(a, d), (b, c)]:
            rows.append([mid, "Grupos", g, fecha.isoformat(), ea, eb, "Por confirmar"])
            mid += 1

    # --- Eliminación directa (fechas oficiales del torneo) ---
    # La app resuelve los marcadores de posición con el modelo predictivo.
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
    for fase, fechas in ko:
        for d in fechas:
            sede = ("MetLife Stadium, Nueva York/Nueva Jersey"
                    if fase == "Final" else "Por confirmar")
            rows.append([mid, fase, "", d.isoformat(),
                         f"POR_DEFINIR_{mid}A", f"POR_DEFINIR_{mid}B", sede])
            mid += 1

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["partido_id", "fase", "grupo", "fecha",
                    "equipo_a", "equipo_b", "sede"])
        w.writerows(rows)
    print(f"OK -> {path} ({len(rows)} partidos)")

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    assignment = assign_groups()
    write_teams(assignment)
    write_matches(assignment)
