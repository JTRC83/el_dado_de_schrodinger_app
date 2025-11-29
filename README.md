# 🎲 El dado de Schrödinger – Panel Euromillones

**El dado de Schrödinger** es una aplicación local en **Streamlit** para analizar el histórico del Euromillones y generar combinaciones optimizadas según distintas estrategias:

- Series **A / B / C** con rangos de suma diferenciados.  
- Modos de generación: **Estándar**, **Momentum**, **Rareza** y **Experimental**.  
- Reglas anti-clon sobre el histórico real (no repetir quintetas ni combinaciones completas).  

La idea es tener **tu propio “laboratorio Euromillones”** en local, sin depender de hojas de cálculo ni de prompts sueltos:

- Exploración visual del histórico (frecuencias, patrones, curiosidades).  
- Generador de bloques A/B/C con distintos “sabores” (momentum, rareza, mezcla).  
- Memoria de combinaciones generadas y **checker** del último sorteo.

La interfaz sigue un estilo **neobrutalista** con colores vivos, bloques bien marcados y un gatete jugador de dados en la barra lateral 🐱🎲.

---

## 🧱 Estado actual del proyecto

### ✅ Datos e infraestructura

- Carga del histórico desde `data/historico_euromillones.csv`.
- Botón en la **sidebar** para **actualizar el histórico desde una API externa** (`updater.py`):
  - Descarga todos los sorteos.
  - Normaliza el formato.
  - Fusiona con el CSV local sin duplicados.
- Normalización interna a `DataFrame` con columnas:
  - `date` (datetime), `n1..n5` (números), `s1`, `s2` (estrellas).

---

### 📊 Pestaña 1 — Explorador histórico

Herramientas para entender el comportamiento del juego:

- **Filtros**:
  - Rango de fechas seleccionable.
  - Ventana de curiosidades para últimos `N` sorteos (50 / 100 / 200).

- **Resumen histórico**:
  - Número de sorteos en el rango.
  - Primera y última fecha.

- **Frecuencia de números (1–50)**:
  - Gráfico de barras con colores por rango de frecuencia:
    - ≥200, 180–199, 160–179, 140–159, <140.
  - Leyenda centrada bajo el gráfico.

- **Frecuencia de estrellas (1–12)**:
  - Solo se usan sorteos desde **27/09/2016** (inicio de la era de 12 estrellas).
  - Coloreado por cuantiles (top 20 %, 20–40 %, … último 20 %).
  - Nota explicativa del corte temporal.

- **Curiosidades (números)**:
  - Número más **caliente** en los últimos N sorteos.
  - Número más **atrasado** (sorteos consecutivos sin salir).
  - **Momentum extendido**: Top 5 números más calientes y top 5 más fríos.

- **Curiosidades (estrellas)**:
  - Estrella más caliente / más atrasada (últimos N sorteos sobre la era 12).

- **Curiosidades (combinaciones repetidas)**:
  - Cálculo sobre **todo el histórico**.
  - Máximo número de repeticiones de una misma combinación (5+2).
  - Listado de las combinaciones más repetidas con sus veces.

- **Curiosidades (sumas de los 5 números)**:
  - Mediana de la suma de los 5 números.
  - Porcentaje de sorteos en cada banda:
    - ≤100 (muy bajas),
    - 101–125 (medias-bajas),
    - 126–154 (medias-altas),
    - ≥155 (altas).

- **Patrones de estructura (decenas, “fechas”, consecutivos)**:
  - % de sorteos con ≥3 decenas distintas.
  - % con ≥4 números en la misma decena.
  - % de líneas “tipo fecha”:
    - 4 números ≤31,
    - 5 números ≤31 (fechas puras).
  - Análisis de consecutivos:
    - sin consecutivos,
    - al menos un par,
    - rachas de ≥3,
    - rachas de ≥4 (vetadas en el generador).

- **Vista del histórico**:
  - Tabla con los **últimos 20 sorteos** del rango seleccionado.

---

### 🎲 Pestaña 2 — Generador A/B/C

Generación de bloques de combinaciones siguiendo distintas estrategias.

#### Modos de generación

Selector:

- **Estándar**
  - Pesos **uniformes** para números y estrellas.
  - El “cerebro” lo ponen las reglas:
    - No repetir nunca una quinteta de números que ya haya salido en el histórico completo.
    - No repetir una combinación completa (5+2) ya vista en la era de 12 estrellas.
    - Respetar rangos de suma por serie (ver abajo).

- **Momentum**
  - Más peso a los números y estrellas **más frecuentes** en el histórico.
  - “Empuja” hacia lo que más ha estado saliendo últimamente.

- **Rareza**
  - Más peso a los números y estrellas **menos frecuentes**.
  - Ideal para buscar combinaciones poco visitadas por el historial.

- **Experimental**
  - Mezcla de Momentum y Rareza (50/50).
  - Resultado: combinación “de compromiso” entre caliente y frío.

Todas las modalidades comparten las mismas reglas de seguridad anti-clon.

#### Series A / B / C y rangos de suma

Para cada combinación se calcula la suma de los 5 números:

- **Serie A** → suma en **[141, 158]** (bloque alto).  
- **Serie B** → suma en **[121, 140]** (bloque medio).  
- **Serie C** → suma en **[100, 120]** (bloque bajo).

Al generar el bloque:

- Se elige el número total de líneas.
- Se reparte entre A y B (C se calcula automáticamente).
- Cada línea se fuerza a caer en el rango de suma correspondiente a su serie.

#### Reglas anti-clon (para todos los modos)

Al generar una línea:

1. Se generan 5 números y 2 estrellas conforme a los pesos del modo.  
2. Se descartan las combinaciones que:
   - no cumplen el rango de suma para la serie,
   - repiten una quinteta de números que **ya haya salido alguna vez**,
   - repiten una combinación completa (5+2) de la **era de 12 estrellas**,
   - ya han salido dentro del **mismo bloque** que se está generando.

Si tras varios intentos no se encuentra una combinación que cumpla todo, se devuelve la última válida como “fallback” defensivo.

#### Bloques generados y guardado

- Cada vez que se genera un bloque:
  - Se guarda en `st.session_state["last_block"]` con su metainformación (modo, líneas A/B/C, total).
  - Se muestra en la UI separado por series A, B y C, con formato:
    - `Números: X-X-X-X-X | Estrellas: E1-E2`.

- Botón **💾 Guardar este bloque**:
  - Guarda las líneas en `data/combinaciones_generadas.csv` mediante `combinations_store.py`.
  - Columnas: `timestamp`, `block_id`, `line_in_block`, `serie`, `mode`, `nums`, `s1`, `s2`, `note`.

#### Combinación manual

En la misma pestaña:

- Inputs para introducir una combinación manual:
  - 5 números (1–50) y 2 estrellas (1–12), con validación de no repetidos.
- Al pulsar **“🧮 Analizar combinación manual”**:
  - Se calcula la suma y se indica en qué serie caería (A/B/C) o si queda fuera de rango.
  - Se comprueba contra el histórico:
    - Si la combinación completa 5+2 ya ha salido → se muestran las fechas.
    - Si solo la quinteta ya ha salido con otras estrellas → se avisa y se listan fechas.
    - Si no aparece → se marca como combinación inédita.
- La última combinación manual válida se guarda en sesión y puede ofrecerse para guardarse también en `combinaciones_generadas.csv`.

---

### ✅ Pestaña 3 — Comprobar resultados

Herramienta para cruzar **combinaciones guardadas** con el **último sorteo** del histórico.

- Se toma el último sorteo disponible en `historico_euromillones.csv`.
- Se cargan las combinaciones desde `data/combinaciones_generadas.csv`.
- Para cada combinación:
  - Se extraen los 5 números (`nums`) y las 2 estrellas (`s1`, `s2`).
  - Se calculan:
    - `aciertos_numeros` → cuántos números coinciden con el último sorteo.
    - `aciertos_estrellas` → cuántas estrellas coinciden.
- Se muestra una tabla filtrable/ordenable con todas las combinaciones y sus aciertos.
- Es la base para, más adelante, mapear estos patrones (5+2, 5+1, 4+2, etc.) a premios reales.

---

## 🧩 Stack tecnológico

- **Python 3.10+** (probado en macOS con Apple Silicon / M-series).
- **Streamlit** – UI web local.
- **pandas** / **numpy** – manejo de datos y métricas.
- **Altair** / charts de Streamlit – gráficos interactivos.
- **requests** – actualización automática de histórico desde API.
- CSS inyectado para el tema **neobrutalista** (`app/ui_theme.py`).

---

## 📂 Estructura del proyecto

```text
el_dado_de_schrodinger_app/
├─ app.py                       # entrypoint principal de Streamlit
├─ requirements.txt             # dependencias
├─ .gitignore
├─ app/
│  ├─ __init__.py
│  ├─ data_loader.py            # carga y normalización del CSV histórico
│  ├─ metrics.py                # frecuencias, curiosidades, repetidos, momentum, etc.
│  ├─ ui_theme.py               # estilos neobrutalistas (CSS inyectado)
│  ├─ updater.py                # actualización automática del histórico desde API
│  ├─ generator.py              # lógica de generación A/B/C + modos Estándar/Momentum/Rareza/Experimental
│  ├─ combinations_store.py     # lectura/escritura de data/combinaciones_generadas.csv
├─ assets/
│  ├─ gato_dado.png             # ilustración del gato jugador (sidebar)
├─ data/
│  ├─ historico_euromillones.csv    # histórico de sorteos normalizado
│  ├─ combinaciones_generadas.csv   # (se crea al guardar bloques / manuales)

📊 Formato del histórico (data/historico_euromillones.csv)

Formato recomendado (normalizado):
date,n1,n2,n3,n4,n5,s1,s2
2004-02-13,16,29,32,36,41,7,9
...

data_loader.py también es capaz de adaptar formatos heredados del tipo:
Fecha;N1;N2;N3;N4;N5;E1;E2
4/11/2025;6;9;25;28;45;1;4
...

y convertirlos a las columnas internas:
	•	date – fecha del sorteo (datetime).
	•	n1..n5 – 5 números principales.
	•	s1, s2 – 2 estrellas.

⸻

🧠 Roadmap / ideas futuras

Aunque muchas piezas del “GPT Euromillones” ya están dentro, todavía hay margen para seguir afinando:
	1.	Checker de resultados avanzado
	•	Comparar bloques contra:
	•	último sorteo,
	•	últimos N sorteos,
	•	rangos de fechas.
	•	Mapear patrones de aciertos (5+2, 5+1, 4+2, etc.) a premios reales usando datos oficiales.
	2.	Metadatos de bloques
	•	Guardar en combinaciones_generadas.csv:
	•	configuración detallada (JSON) de pesos y reglas usadas en cada generación,
	•	flag played para marcar qué bloques se han llegado a jugar.
	3.	Más visualizaciones
	•	Histogramas de sumas en función del tiempo.
	•	Evolución temporal de “momentum” de cada número.
	•	Mapas de calor de coocurrencias (parejas y tríos de números).
	4.	Reglas adicionales en el generador
	•	Control explícito de paridad, decenas y consecutivos.
	•	Penalizar patrones ultra-populares (diagonales, escaleras perfectas, etc.).
	•	Políticas específicas de estrellas (parejas “de viernes”, etc.).

⸻

📝 Licencia

Por ahora, uso personal / experimental.

⸻

🤝 Contribuciones

El proyecto nace como herramienta personal, pero cualquier idea, sugerencia o mejora
(issues, PRs o comentarios en este README) es más que bienvenida.