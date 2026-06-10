# ⚽ Dashboard Mundial 2026 — Analítica para Apuestas Estadísticas

Dashboard interactivo en Streamlit para los **48 equipos** y **104 partidos** del
Mundial 2026. Modelo de **Distribución de Poisson** validado con **Monte Carlo**.

## Cómo correrlo desde la terminal

```bash
cd ~/MUNDIAL

# 1. (Solo la primera vez) crear entorno e instalar dependencias
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. (Opcional) reprocesar el dataset real (archive.zip ya extraído en data/raw/)
.venv/bin/python process_data.py

# 3. Levantar el dashboard
.venv/bin/streamlit run app.py
```

Se abre en **http://localhost:8501**. Para detenerlo: `Ctrl+C`.

## Estructura

```
MUNDIAL/
├── app.py                  # Interfaz Streamlit (4 secciones)
├── process_data.py         # Procesa el dataset real (data/raw/) → CSVs del dashboard
├── generate_data.py        # Grupos oficiales + semilla (corners, tarjetas, ranking)
├── requirements.txt
├── utils/
│   └── analytics.py        # Poisson, Monte Carlo, tarjetas, corners, bracket
└── data/
    ├── raw/                # Dataset real: resultados internacionales 1872-2026
    ├── world_cup_data.csv  # Métricas por equipo (goles/forma reales ajustados)
    └── matches.csv         # 104 partidos (72 oficiales con sede real)
```

## Secciones

1. **🎯 Simulador 1v1** — Probabilidad Victoria/Empate/Derrota (Poisson + Monte
   Carlo 10,000 sims), mapa de calor de marcadores, Over/Under de goles, BTTS y
   cuotas justas. Entradas: ranking FIFA, GF/GC por partido y forma reciente.
2. **🟨 Tarjetas** — Propensión por equipo y predicción del total de tarjetas
   por enfrentamiento con líneas Over/Under (2.5 a 5.5).
3. **🚩 Corners** — Promedios a favor/en contra y filtro de comportamiento como
   favorito (×1.12) vs no favorito (×0.90).
4. **📅 Explorador de 104 Partidos** — Predicciones automatizadas de todo el
   torneo: fase de grupos oficial + eliminación directa proyectada por el
   modelo (siembra por puntos esperados) hasta el campeón.

## Modelo

- `λ_equipo = μ · (ataque/μ) · (defensa_rival/μ) · F_forma · F_ranking`, con
  μ = 1.30 goles por equipo por partido (promedio histórico de Mundiales).
- 1X2 con la matriz de Poisson `P[i,j] = P(A=i)·P(B=j)`; goles totales como
  `Poisson(λA + λB)`.
- Tarjetas y corners: totales esperados de ambos equipos con Over/Under vía
  Poisson; factor de rivalidad 1.15 en eliminación directa.

## Notas sobre los datos

- **Goles y forma reales**: calculados con `process_data.py` a partir del
  dataset de resultados internacionales (data/raw/, 1,211 partidos jugados por
  los 48 clasificados entre jun-2024 y jun-2026).
- **Ajuste por fuerza del rival**: los promedios brutos se corrigen con una
  estimación iterativa de ataque/defensa (estilo Dixon-Coles simplificado)
  para no premiar goleadas contra rivales débiles; luego se reescalan al
  contexto mundialista (rival promedio = clasificado promedio, μ = 1.30) con
  amortiguación ^0.7. Las columnas `gf_pp_bruto`/`gc_pp_bruto` conservan los
  promedios sin ajustar.
- **Calendario de grupos oficial** (72 partidos con fecha y sede) tomado del
  propio dataset; eliminatorias con fechas oficiales hasta la final del 19 de
  julio en el MetLife Stadium.
- **Corners, tarjetas y ranking FIFA**: el dataset no los incluye, se mantienen
  como semilla calibrada (editables en `generate_data.py` → TEAMS).
- El bracket de eliminación se simplifica con siembra 1-32 por puntos esperados.
- Uso educativo. Apuesta con responsabilidad.
