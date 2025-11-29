🎲 El dado de Schrödinger – Panel Euromillones

El dado de Schrödinger es una aplicación local en Streamlit para:
	•	Explorar el histórico del Euromillones.
	•	Generar combinaciones optimizadas por series A/B/C según distintas estrategias.
	•	Guardar y revisar tus combinaciones.
	•	Simular, vía Monte Carlo, cómo se comportan las distintas estrategias a largo plazo.

La idea es tener tu propio “laboratorio Euromillones” en local, con una interfaz neobrutalista: tarjetas con bordes gruesos, sombras duras, colores vivos y un gato ludópata vigilándolo todo. 😼🎲

⸻

🧱 Estado actual del proyecto (v1)

La app se organiza en cuatro pestañas principales:

1. 📊 Explorador histórico

Trabaja sobre data/historico_euromillones.csv (histórico real).
	•	Filtros
	•	Selector de rango de fechas.
	•	Ventana de “curiosidades” (últimos N sorteos).
	•	Resumen histórico
	•	Número de sorteos en rango.
	•	Primera y última fecha del rango.
	•	Frecuencias
	•	Números (1–50) con barras coloreadas por tramos de frecuencia:
	•	≥ 200, 180–199, 160–179, 140–159, < 140 apariciones.
	•	Estrellas (1–12) calculadas solo desde el inicio de la era de 12 estrellas (27/09/2016), también agrupadas por cuantiles (muy alta, alta, media, baja, muy baja).
	•	Curiosidades
	•	🔥 Número más caliente (últimos N sorteos) y número más atrasado.
	•	✨ Estrella más caliente y estrella más atrasada.
	•	🧱 Patrones estructurales:
	•	Distribución por decenas (≥ 3 decenas distintas, ≥ 4 en una misma decena…).
	•	Sorteos tipo “fecha” (4 o 5 números ≤ 31).
	•	Rachas de consecutivos (pares, ternas, rachas ≥ 4).
	•	🔁 Combinaciones repetidas:
	•	Usa TODO el histórico para detectar combinaciones 5+2 repetidas.
	•	Muestra la combinación más repetida y ejemplos de repeticiones.
	•	Sumas de los 5 números
	•	Mediana de la suma.
	•	% de sorteos en las bandas:
	•	≤ 100 (muy bajas)
	•	101–125 (medias-bajas)
	•	126–154 (medias-altas)
	•	≥ 155 (altas)
	•	Vista rápida del histórico
	•	Tabla con los 20 últimos sorteos dentro del rango filtrado.

⸻

2. 🎲 Generador A/B/C

Genera bloques de combinaciones divididos en Series A, B y C respetando varias reglas.
	•	Configuración
	•	Modo de generación:
	•	Estándar
	•	Momentum
	•	Rareza
	•	Experimental
	•	Game Theory
	•	Total de líneas del bloque (5–25, en pasos de 5).
	•	Nº de líneas para la Serie A y B (la Serie C se calcula automáticamente).
	•	Límites por serie (solo suma de números, sin estrellas)
Las bandas están pensadas para cubrir aproximadamente el rango útil [100–158]:

		Serie	Rango suma
		A	141–158
		B	121–140
		C	100–120


	•	Reglas anti-clon (aplicadas en todos los modos)
	•	Nunca repite una quinteta de números que ya haya salido en TODO el histórico (desde 2004).
	•	Nunca repite una combinación completa 5+2 que ya haya salido en la era de 12 estrellas (desde 27/09/2016).
	•	No repite combinaciones dentro del mismo bloque generado.
	•	Modos de generación
	•	🟩 Estándar
	•	Pesos uniformes para todos los números y estrellas.
	•	La “inteligencia” la ponen las reglas anti-clon y los rangos de suma A/B/C.
	•	📈 Momentum
	•	Números y estrellas con más frecuencia reciente tienen más peso.
	•	Utiliza todo el histórico (estrellas solo desde 2016) para calcular frecuencias.
	•	🧊 Rareza
	•	Justo al revés: favorece los números/estrellas que menos han salido.
	•	Útil para explorar zonas poco transitadas del espacio de combinaciones.
	•	🧪 Experimental
	•	Mezcla al 50% los pesos de Momentum y Rareza (ni tan “caliente” ni tan “frío”).
	•	Intenta equilibrar zonas frecuentes e infrecuentes del histórico.
	•	🎭 Game Theory
	•	Introduce penalizaciones a patrones “muy humanos”:
	•	Escaleras claras (1–2–3, 10–20–30–40–50, etc.).
	•	Quintetas con 5 números ≤ 31 (fechas puras).
	•	Demasiados números en una misma decena.
	•	Busca generar combinaciones menos populares visualmente, intentando evitar que acabes compartiendo premio con medio continente.
	•	Guardar bloques generados
	•	Tras generar un bloque, se muestra:
	•	Desglose por Serie A/B/C.
	•	Botón “💾 Guardar este bloque”.
	•	Los bloques se guardan en data/combinaciones_generadas.csv con campos como:
	•	timestamp, mode, serie, nums, s1, s2, sum, etc.
	•	Combinación manual
	•	Formulario con N1–N5 y E1–E2.
	•	Al pulsar “Analizar combinación manual”:
	•	Comprueba que números y estrellas sean distintos.
	•	Calcula la suma y te dice en qué Serie teóricamente caería (A/B/C) o si sale de rango.
	•	Comprueba contra TODO el histórico:
	•	Si ya salió exactamente la combinación 5+2 (muestra fechas).
	•	Si el quinteto de números ya ha salido con otras estrellas.
	•	Si es inédita en el histórico.
	•	Permite guardar la combinación manual en combinaciones_generadas.csv.

⸻

3. ✅ Comprobar resultados

Pestaña dedicada a comparar tus combinaciones guardadas con el último sorteo real (según el histórico cargado).
	•	Toma el último registro de historico_euromillones.csv como sorteo de referencia.
	•	Carga data/combinaciones_generadas.csv (todas las combinaciones que hayas guardado).
	•	Para cada combinación:
	•	Cuenta aciertos de números (0–5).
	•	Cuenta aciertos de estrellas (0–2).
	•	Construye el patrón X+Y (por ejemplo 3+1, 4+0, etc.).
	•	Muestra una tabla con:
	•	modo / serie / combinación / aciertos números / aciertos estrellas / patrón.
	•	Esto permite saber rápidamente si alguna de tus combinaciones ha tocado algo, aunque solo sea un 2+1.

⸻

4. 🧮 Simulador Monte Carlo de estrategias

Pestaña para hacer simulaciones masivas (trials) y comparar el rendimiento de las estrategias sin gastar un euro.
	•	Configuración del simulador
	•	Modo a simular:
	•	Estándar, Momentum, Rareza, Experimental, Game Theory.
	•	Líneas totales por bloque (5–25).
	•	Reparto simulado A/B/C.
	•	Número de sorteos simulados (n_trials, típicamente 1.000–5.000).
	•	Qué hace un trial
	•	Genera un bloque A/B/C usando el modo elegido (con las mismas reglas que el generador real).
	•	Genera un sorteo aleatorio (5 números + 2 estrellas).
	•	Para cada línea:
	•	Calcula aciertos de números y estrellas.
	•	Actualiza la distribución de patrones de acierto.
	•	Resultados mostrados
	•	Distribución de aciertos para el modo seleccionado:
	•	Tabla con columnas:
	•	aciertos_numeros, aciertos_estrellas, veces, prob, prob_%.
	•	Gráfico de barras de probabilidad por patrón X+Y.
	•	Resumen del modo simulado:
	•	Líneas simuladas totales.
	•	P(≥3 números) – probabilidad de que una línea tenga al menos 3 aciertos de número.
	•	P(al menos un premio) – aproximación a la probabilidad de que una línea caiga en algún rango premiado (según tus umbrales).
	•	Comparación rápida entre modos:
	•	Opción para simular automáticamente Estándar, Momentum, Rareza, Experimental y Game Theory con la misma configuración.
	•	Tabla comparativa:
	•	modo, líneas simuladas, P(≥3 números)%, P(al menos un premio)%.
	•	Interpretación: cuanto más alta sea P(≥3 números) y, sobre todo, P(al menos un premio), mejor se comporta esa estrategia en las simulaciones.

⸻

🧩 Stack tecnológico
	•	Python 3.10+ (probado en macOS con Apple Silicon).
	•	Streamlit – UI web local.
	•	pandas / numpy – manejo de datos y métricas.
	•	Altair – gráficos de barras personalizados con colores por rangos.
	•	requests – actualización opcional del histórico vía API externa.
	•	CSV plano como “base de datos”:
	•	data/historico_euromillones.csv
	•	data/combinaciones_generadas.csv

⸻

📂 Estructura del proyecto

	el_dado_de_schrodinger_app/
	├─ app.py                         # entrypoint de Streamlit
	├─ requirements.txt               # dependencias del proyecto
	├─ README.md
	├─ app/
	│  ├─ __init__.py
	│  ├─ data_loader.py              # carga y normalización del CSV histórico
	│  ├─ metrics.py                  # frecuencias, curiosidades, repetidos, etc.
	│  ├─ ui_theme.py                 # estilos neobrutalistas (CSS inyectado)
	│  ├─ updater.py                  # actualización del histórico desde API externa
	│  ├─ generator.py                # lógica de generación A/B/C y modos (Estándar, Momentum, Rareza, Experimental, Game Theory)
	│  ├─ combinations_store.py       # guardado/carga de combinaciones generadas
	│  ├─ simulator.py                # simulador Monte Carlo de estrategias
	├─ data/
	│  ├─ historico_euromillones.csv  # histórico real de Euromillones
	│  ├─ combinaciones_generadas.csv # combinaciones que decides guardar
	└─ assets/
	├─ gato_dado.png               # gato protagonista del sidebar

Formato de historico_euromillones.csv

El loader espera un CSV con columnas equivalentes a:
	•	Fecha o similar → convertida internamente a date (datetime).
	•	5 columnas de números principales → n1..n5.
	•	2 columnas de estrellas → s1, s2.

data_loader.py se encarga de adaptar el formato inicial (por ejemplo el oficial de Euromillones) a este esquema interno.

⸻

🔮 Estado futuro

La versión actual ya es plenamente funcional como herramienta personal:
	•	Exploración avanzada del histórico.
	•	Generación con múltiples estrategias.
	•	Guardado de bloques.
	•	Checker de resultados.
	•	Simulador Monte Carlo con comparación de modos.

Cualquier ajuste futuro seguramente será refinamiento visual, nuevos filtros o pequeñas reglas adicionales, pero la base está ya sólida.

⸻

📝 Licencia

Uso personal / experimental.

⸻

🤝 Contribuciones

El proyecto nació como herramienta personal, pero:
	•	Ideas, sugerencias y PRs son bienvenidos.
	•	Se agradecen issues con:
	•	Nuevas heurísticas para las estrategias.
	•	Ajustes de rangos A/B/C.
	•	Mejores visualizaciones para el simulador.

⸻
