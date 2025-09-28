
import os
import subprocess
from .tda import ListaSimple, Cola
from .entidades import Dron, PasoPlan

class InstruccionDron:
    __slots__ = ("nombre","accion")
    def __init__(self, nombre:str, accion:str):
        self.nombre = nombre
        self.accion = accion

class InstruccionSegundo:
    __slots__ = ("segundo","acciones")
    def __init__(self, segundo:int):
        self.segundo = segundo
        self.acciones = ListaSimple()  # de InstruccionDron

class EficienciaDron:
    __slots__ = ("nombre","litros","gramos")
    def __init__(self, nombre:str, litros:float, gramos:float):
        self.nombre = nombre
        self.litros = litros
        self.gramos = gramos

class ResultadoPlan:
    __slots__ = ("plan_nombre","tiempo_optimo","agua_total","fert_total","eficiencias")
    def __init__(self, plan_nombre:str):
        self.plan_nombre = plan_nombre
        self.tiempo_optimo = 0
        self.agua_total = 0.0
        self.fert_total = 0.0
        self.eficiencias = ListaSimple()  # EficienciaDron

def _buscar_dron_por_hilera(inv, hilera:int):
    for d in inv.drones:
        if d.hilera == hilera:
            return d
    return None

def _preparar_objetivos_por_dron(inv, plan):
    # encolar por dron sus posiciones objetivo según el plan
    for d in inv.drones:
        # limpiar por si había algo previo
        d.objetivos = Cola()
        d.posicion = 0
        d.agua_total = 0.0
        d.fert_total = 0.0
        d.finalizado = False
        d.marcar_fin_proximo_tick = False
    for paso in plan.pasos:
        d = _buscar_dron_por_hilera(inv, paso.hilera)
        if d is not None:
            d.objetivos.encolar(paso.posicion)

def _todos_finalizaron(inv):
    for d in inv.drones:
        if not d.finalizado:
            return False
    return True

def _acciones_de_tick(inv, plan, paso_actual, hubo_riego_en_tick, planta_lookup_f):
    # retorna InstruccionSegundo, y bandera si se consumió un paso del plan
    acciones = InstruccionSegundo(0)  # segundo se establece fuera
    consumio_paso = False

    # 1. Decidir si se riega este segundo
    # Se riega sólo si el dron del paso actual está en su posición objetivo.
    dron_obj = _buscar_dron_por_hilera(inv, paso_actual.hilera)
    if dron_obj is not None and dron_obj.posicion == paso_actual.posicion:
        # REGAR
        acciones.acciones.agregar_final(InstruccionDron(dron_obj.nombre, "Regar"))
        # acumular consumos
        planta = planta_lookup_f(paso_actual.hilera, paso_actual.posicion)
        if planta is not None:
            dron_obj.agua_total += planta.litros
            dron_obj.fert_total += planta.gramos
        # retirar objetivo cumplido
        # si el frente coincide, desencolar
        frente = dron_obj.objetivos.ver_frente()
        if frente is not None and frente == paso_actual.posicion:
            dron_obj.objetivos.desencolar()
        # si se quedó sin objetivos, marcar fin para el siguiente tick
        if dron_obj.objetivos.esta_vacia():
            dron_obj.marcar_fin_proximo_tick = True
        consumio_paso = True
    else:
        # No se riega este segundo
        pass

    # 2. Movimiento paralelo de todos los drones (1m por segundo hacia su siguiente objetivo)
    for d in inv.drones:
        if consumio_paso and d is dron_obj:
            # ya riega este segundo; los demás sí pueden moverse
            continue
        if d.finalizado:
            # no agrega acciones posteriores; se ignora
            continue
        if d.objetivos.esta_vacia():
            # nada pendiente, espera o fin
            if d.marcar_fin_proximo_tick:
                acciones.acciones.agregar_final(InstruccionDron(d.nombre, "FIN"))
                d.finalizado = True
                d.marcar_fin_proximo_tick = False
            else:
                acciones.acciones.agregar_final(InstruccionDron(d.nombre, "Esperar"))
            continue
        proximo = d.objetivos.ver_frente()
        if proximo is None:
            acciones.acciones.agregar_final(InstruccionDron(d.nombre, "Esperar"))
            continue
        if d.posicion < proximo:
            # mover adelante
            d.posicion += 1
            acciones.acciones.agregar_final(InstruccionDron(d.nombre, f"Adelante (H{d.hilera}P{d.posicion})"))
        elif d.posicion > proximo:
            # mover atrás
            d.posicion -= 1
            acciones.acciones.agregar_final(InstruccionDron(d.nombre, f"Atras (H{d.hilera}P{d.posicion})"))
        else:
            # ya está sobre objetivo, pero no es su turno de regar
            acciones.acciones.agregar_final(InstruccionDron(d.nombre, "Esperar"))

    return acciones, consumio_paso

class Simulador:
    def simular(self, inv, plan):
        # Prepara objetivos por dron y resetea estado
        _preparar_objetivos_por_dron(inv, plan)

        # Función de búsqueda de planta (evitar estructuras nativas)
        def planta_lookup(hilera:int, pos:int):
            h = inv.obtener_hilera(hilera)
            if h is None:
                return None
            return h.buscar_planta(pos)

        timeline = ListaSimple()  # de InstruccionSegundo
        resultado = ResultadoPlan(plan.nombre)

        # iteración por pasos del plan
        paso_node = plan.pasos.cabeza
        segundo = 0
        ultimo_riego_seg = 0

        while paso_node is not None:
            segundo += 1
            paso_actual = paso_node.valor
            acciones_seg, consumio = _acciones_de_tick(inv, plan, paso_actual, False, planta_lookup)
            acciones_seg.segundo = segundo
            timeline.agregar_final(acciones_seg)
            if consumio:
                ultimo_riego_seg = segundo
                # avanzar a siguiente paso
                paso_node = paso_node.siguiente
            # si todos finalizaron (posible sólo si plan vacío), romper
            if paso_node is None:
                # permitir un tick adicional para colocar FIN de quien quedó con marca
                # si existe algún dron con marcar_fin_proximo_tick True
                alguno_pendiente = False
                for d in inv.drones:
                    if d.marcar_fin_proximo_tick and not d.finalizado:
                        alguno_pendiente = True
                        break
                if alguno_pendiente:
                    segundo += 1
                    acciones_fin = InstruccionSegundo(segundo)
                    # consumir marcas
                    for d in inv.drones:
                        if d.marcar_fin_proximo_tick and not d.finalizado:
                            acciones_fin.acciones.agregar_final(InstruccionDron(d.nombre, "FIN"))
                            d.marcar_fin_proximo_tick = False
                            d.finalizado = True
                    timeline.agregar_final(acciones_fin)

        # Calcular totales
        agua_total = 0.0
        fert_total = 0.0
        for d in inv.drones:
            agua_total += d.agua_total
            fert_total += d.fert_total
            resultado.eficiencias.agregar_final(EficienciaDron(d.nombre, d.agua_total, d.fert_total))

        resultado.tiempo_optimo = ultimo_riego_seg
        resultado.agua_total = agua_total
        resultado.fert_total = fert_total

        return resultado, timeline

def generar_reporte_html_plan(inv, plan, resultado, timeline):
    # se apoya en una plantilla jinja para exportar html y escribir a /reports
    from flask import render_template
    rp_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
    nombre_arch = f"ReporteInvernadero_{inv.nombre.replace(' ','_')}_{plan.nombre.replace(' ','_')}.html"
    full = os.path.join(rp_dir, nombre_arch)
    html = render_template("reporte.html", inv=inv, plan=plan, res=resultado, timeline=timeline)
    with open(full, "w", encoding="utf-8") as f:
        f.write(html)
    return full


def graficar_tdas_en_t(inv, plan, t:int):
    """
    Simula desde estado inicial hasta el tiempo t (en segundos) para graficar
    el **estado de los TDAs** en ese instante, **sin** mutar el invernadero original.
    No calcula consumos; sólo posiciones y colas de objetivos.
    """
    # Construir copia ligera del invernadero: solo drones (nombre, hilera) y plan (pasos)
    from .entidades import Invernadero, Plan, PasoPlan, Dron

    inv_shadow = Invernadero(inv.nombre, inv.numero_hileras, inv.plantas_x_hilera)
    # Copiar drones
    for d in inv.drones:
        inv_shadow.agregar_dron(Dron(d.id, d.nombre, d.hilera))
    # Copiar plan
    plan_shadow = Plan(plan.nombre)
    n = plan.pasos.cabeza
    while n is not None:
        paso = n.valor
        plan_shadow.pasos.agregar_final(PasoPlan(paso.hilera, paso.posicion))
        n = n.siguiente

    # Preparar objetivos y simular hasta t
    _preparar_objetivos_por_dron(inv_shadow, plan_shadow)

    paso_node = plan_shadow.pasos.cabeza
    segundo = 0

    def planta_lookup_none(h, p):
        return None

    while segundo < t and paso_node is not None:
        segundo += 1
        paso_actual = paso_node.valor
        _, consumio = _acciones_de_tick(inv_shadow, plan_shadow, paso_actual, False, planta_lookup_none)
        if consumio:
            paso_node = paso_node.siguiente

    # Generar DOT con el estado actual (inv_shadow y plan_shadow), resaltando el índice t
    dot = "digraph G {\nrankdir=LR;\nnode [shape=record];\n"

    # Drones
    dot += 'subgraph cluster_drones { label="Drones (t=%d)"; color=lightgrey;\n' % (t,)
    for d in inv_shadow.drones:
        cola_label = ""
        primero = True
        for obj in d.objetivos:
            if primero:
                cola_label += f"{obj}"
                primero = False
            else:
                cola_label += f"|{obj}"
        if cola_label == "":
            cola_label = "—"
        dot += f'"{d.nombre}" [label="{{{d.nombre}|Hilera: {d.hilera}|Pos: {d.posicion}|Obj: {cola_label}}}"];\n'
    dot += "}\n"

    # Plan pasos
    dot += 'subgraph cluster_plan { label="Plan"; color=lightblue;\n'
    idx = 0
    n = plan_shadow.pasos.cabeza
    ant_name = None
    while n is not None:
        paso = n.valor
        nodo = f'P{idx}'
        highlight = ",style=filled,fillcolor=yellow" if idx == 0 else ""
        # Resaltamos el **siguiente** paso pendiente (índice 0 de la lista restante)
        dot += f'{nodo} [label="H{paso.hilera}-P{paso.posicion}"{highlight}];\n'
        if ant_name is not None:
            dot += f"{ant_name} -> {nodo};\n"
        ant_name = nodo
        idx += 1
        n = n.siguiente
    dot += "}\n}\n"

    out_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
    base = f"TDAs_{inv.nombre.replace(' ','_')}_{plan.nombre.replace(' ','_')}_{t}"
    dot_path = os.path.join(out_dir, base + ".dot")
    with open(dot_path, "w", encoding="utf-8") as f:
        f.write(dot)

    # intentar generar png con 'dot' si está
    png_path = os.path.join(out_dir, base + ".png")
    try:
        subprocess.run(["dot","-Tpng",dot_path,"-o",png_path], check=True)
        return dot_path, png_path
    except Exception:
        return dot_path, None

