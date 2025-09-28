
# IPC2_Proyecto2_201503980 — GuateRiegos 2.0

Aplicación web (Flask) para simular el riego y aplicación de fertilizante en invernaderos con drones, **sin usar** estructuras nativas de Python (`list`, `dict`, `tuple`, `set`) para almacenar la información del problema. Se implementan **TDAs propios** (listas ligadas y colas).

> **Importante:** El parseo y templates usan librerías estándar de Python/Flask para E/S y render; en el **código del estudiante** que modela y procesa los datos **no** se usan listas/diccionarios/tuplas/conjuntos.

## Requisitos
- Python 3.10+
- Flask (se instala con `pip install -r requirements.txt`)
- Graphviz (opcional para generar `.png` desde `.dot`; si no está, se generan archivos `.dot`).

## Ejecución
```bash
cd IPC2_Proyecto2_201503980
python3 -m venv .venv
source .venv/bin/activate  # en Windows: .venv\Scripts\activate
pip install -r requirements.txt

export FLASK_APP=app.main:app       # en Windows: set FLASK_APP=app.main:app
flask run
# Abrir http://127.0.0.1:5000
```

## Flujo
1. **Cargar XML** de configuración (menú Inicio).
2. **Seleccionar invernadero y plan** y simular.
3. Visualizar **estadísticas**, **tabla de instrucciones** y **generar Reporte HTML** (se guarda en `app/reports`).
4. Generar **grafo de TDAs en tiempo _t_** (genera `.dot` y, si hay Graphviz, `.png`).
5. Generar **salida.xml** para **todos** los invernaderos y planes (en `app/output/salida.xml`).

## Estructura principal
- `app/models/tda.py` — Nodo, ListaSimple, Cola y utilidades iterables.
- `app/models/entidades.py` — Plantas, Drones, Hileras, Invernaderos, Planes.
- `app/models/simulador.py` — Motor de simulación paso a paso (por segundo).
- `app/models/parser_xml.py` — Carga/validación del XML y generación de `salida.xml`.
- `app/controllers.py` — Rutas Flask (carga, simulación, reportes, ayuda).
- `app/templates/` — Plantillas Jinja2.
- `app/static/` — estilos.
- `app/reports/` — reportes HTML y grafos.
- `app/output/` — salida.xml

## Restricciones cubiertas
- **POO**: Clases por entidad y motor de simulación.
- **TDAs propios**: Sin `list`, `dict`, `tuple`, `set` en el modelado/algoritmo; se usan listas ligadas y colas personalizadas.
- **Flask**: UI totalmente web.
- **Graphviz**: grafo del **estado de TDAs** en tiempo `t`.
- **XML**: Entrada/salida acorde al enunciado.
- **Reportes HTML**: Por invernadero/plan con tablas de asignaciones, instrucciones y estadísticas.

## Notas
- El **tiempo óptimo** reporta el segundo en el que ocurre el **último riego** (coincide con el ejemplo del enunciado).
- Si Graphviz no está instalado, se genera sólo el `.dot` (descargable).

## Nombre del repositorio
Sugerido: `IPC2_Proyecto2_201503980`

