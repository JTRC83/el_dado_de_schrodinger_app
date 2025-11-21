# 🎲 El dado de Schrödinger – Panel Euromillones

**El dado de Schrödinger** es una aplicación local en Streamlit para analizar el histórico del Euromillones y generar combinaciones optimizadas según distintas estrategias (Series A/B/C, sumas en rangos, frecuencia, momentum, rareza, etc.).

El objetivo es tener **tu propio “laboratorio Euromillones”**, sin depender de hojas de cálculo sueltas ni de ChatGPT, con:

- Visualización del histórico (frecuencias, repeticiones, curiosidades).
- Generador de combinaciones por bloques A/B/C.
- Más adelante: memoria de combinaciones jugadas y comprobación automática de resultados.

La interfaz sigue un estilo **neobrutalista** con colores vivos y bloques bien marcados.

---

## 🧱 Estado actual del proyecto (v0)

Funcionalidades ya implementadas:

- Carga del histórico de resultados desde `data/historico_euromillones.csv`.
- UI básica en Streamlit con dos pestañas:
  - 📊 **Explorador histórico**:
    - Filtro por rango de fechas.
    - Frecuencia de números (1–50).
    - Frecuencia de estrellas (1–12).
    - Detección de **combinaciones repetidas**.
    - “Curiosidades”:
      - Número más caliente (últimos N sorteos).
      - Número más atrasado (backlog de sorteos sin salir).
      - Estrella más caliente / más atrasada.
  - 🎲 **Generador A/B/C (v0)**:
    - Selección de total de líneas del bloque.
    - Reparto entre Series A, B y C.
    - Generador simple (por ahora aleatorio) con formato:
      - `Números: X-X-X-X-X | Estrellas: E1-E2`
- Estilo visual neobrutalista:
  - Bloques con bordes gruesos, sombras duras y colores vivos.
  - Botones “gordos” para acciones importantes.

---

## 🧩 Stack tecnológico

- **Python 3.10+** (probado en macOS con Apple Silicon).
- **Streamlit** – UI web local.
- **pandas / numpy** – manejo de datos y métricas.
- **matplotlib / Streamlit charts** – gráficos básicos.
- **requests** – para futuras integraciones (actualización automática desde API).

---

## 📂 Estructura del proyecto

```text
el_dado_de_schrodinger_app/
├─ app.py                     # entrypoint de Streamlit
├─ requirements.txt           # dependencias del proyecto
├─ .gitignore
├─ app/
│  ├─ __init__.py
│  ├─ data_loader.py          # carga y normalización del CSV histórico
│  ├─ metrics.py              # frecuencias, curiosidades, repetidos, etc.
│  ├─ ui_theme.py             # estilos neobrutalistas (CSS inyectado)
│  ├─ updater.py              # (en progreso) actualización automática desde API
├─ data/
│  ├─ historico_euromillones.csv  # histórico de resultados del Euromillones
│  └─ (futuro) combinaciones_generadas.csv

📊 Formato del histórico (data/historico_euromillones.csv)

El archivo de histórico actualmente esperado tiene este formato (similar al CSV oficial):
FECHA;COMB. GANADORA;;;;;ESTRELLAS;
4/11/2025;6;9;25;28;45;1;4
31/10/2025;3;12;19;34;47;2;8
...

data_loader.py lo convierte internamente a un DataFrame con columnas normalizadas:
	•	date – fecha del sorteo (datetime).
	•	n1..n5 – 5 números principales.
	•	s1, s2 – 2 estrellas.

    🧠 Ideas y roadmap (por implementar)

Próximas funcionalidades planeadas:

1. Generador avanzado A/B/C
	•	Incorporar reglas ya definidas en el “GPT Euromillones”:
	•	Series A / B / C con distintas bandas de suma (baja / IQR / alta).
	•	Control de paridad, decenas, consecutivos, sumas en [107,148], etc.
	•	Pesos de:
	•	frecuencia 2016–2025,
	•	momentum (50/100/200),
	•	coocurrencias,
	•	backlog (números “atrasados”),
	•	penalización de formas populares.
	•	Política de estrellas (parejas “de viernes” prioritarias, etc.).
	•	Hard limits:
	•	Evitar 1–2–3–4–5, 10–20–30–40–50, 5 números ≤31, etc.

2. Histórico de combinaciones generadas
	•	Nuevo archivo data/combinaciones_generadas.csv con:
	•	timestamp, block_id, line_id, played, serie, mode,
	•	nums, s1, s2,
	•	config_json (snapshot de los parámetros usados).
	•	Sección en la UI para:
	•	ver bloques anteriores,
	•	marcar qué bloques se jugaron realmente.

3. Checker de resultados / premios
	•	Evaluar bloques generados contra:
	•	el último sorteo,
	•	los últimos N sorteos,
	•	un rango de fechas concreto.
	•	Para cada línea:
	•	calcular patrón X+Y (aciertos números + estrellas),
	•	asociarlo a su rango de premio (5+2, 5+1, etc.).
	•	(Nivel avanzado) cruzar con datos reales de premios por sorteo para estimar euros aproximados ganados.

4. Más visualizaciones y “curiosidades”
	•	Distribución por decenas (1–10, 11–20, …, 41–50).
	•	Conteo de líneas tipo “fecha” (5 números ≤31).
	•	Análisis de consecutivos (pares, ternas, rachas máximas).
	•	Histogramas de sumas de los 5 números.

⸻

📝 Licencia

Pendiente de decidir.
De momento, uso personal / experimental.

⸻

🤝 Contribuciones

El proyecto está pensado inicialmente como herramienta personal, pero cualquier idea o sugerencia (issues, PRs o notas en el README) es bienvenida.