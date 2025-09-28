
import os
from flask import Blueprint, render_template, request, redirect, url_for, send_file, flash
from .models.parser_xml import cargar_configuracion_desde_xml
from .models.entidades import Sistema
from .models.simulador import Simulador
from .models.entidades import buscar_invernadero_por_nombre
from .models.simulador import generar_reporte_html_plan, graficar_tdas_en_t

bp = Blueprint("routes", __name__)

SISTEMA = Sistema()

@bp.route("/")
def index():
    nombres_invernaderos = SISTEMA.nombres_invernaderos_iterable()
    return render_template("index.html", invernaderos=nombres_invernaderos)

@bp.route("/cargar", methods=["POST"])
def cargar():
    if "archivo" not in request.files:
        flash("No se adjuntó archivo")
        return redirect(url_for("routes.index"))
    f = request.files["archivo"]
    if f.filename == "":
        flash("Archivo inválido")
        return redirect(url_for("routes.index"))
    path = os.path.join(os.path.dirname(__file__), "uploads", "entrada.xml")
    f.save(path)
    ok, msg = cargar_configuracion_desde_xml(path, SISTEMA)
    if not ok:
        flash("Error al cargar XML: " + msg)
    else:
        flash("Configuración cargada correctamente.")
    return redirect(url_for("routes.index"))

@bp.route("/invernadero/<nombre>")
def ver_invernadero(nombre):
    inv = buscar_invernadero_por_nombre(SISTEMA, nombre)
    if inv is None:
        flash("Invernadero no encontrado.")
        return redirect(url_for("routes.index"))
    planes = inv.nombres_planes_iterable()
    return render_template("invernadero.html", invernadero=inv, planes=planes)

@bp.route("/simular", methods=["GET"])
def simular():
    nombre = request.args.get("invernadero", "")
    plan_nombre = request.args.get("plan", "")
    inv = buscar_invernadero_por_nombre(SISTEMA, nombre)
    if inv is None:
        flash("Invernadero no encontrado.")
        return redirect(url_for("routes.index"))
    plan = inv.buscar_plan_por_nombre(plan_nombre)
    if plan is None:
        flash("Plan no encontrado.")
        return redirect(url_for("routes.ver_invernadero", nombre=nombre))
    sim = Simulador()
    resultado, timeline = sim.simular(inv, plan)
    # Generar reporte HTML y guardar archivo en /reports
    reporte_path = generar_reporte_html_plan(inv, plan, resultado, timeline)
    return render_template("plan_resultado.html",
                           invernadero=inv,
                           plan=plan,
                           resultado=resultado,
                           timeline=timeline,
                           reporte_path=os.path.basename(reporte_path))

@bp.route("/reporte/<nombre>/<plan>")
def descargar_reporte(nombre, plan):
    # archivo ya se generó en la simulación
    rp_dir = os.path.join(os.path.dirname(__file__), "reports")
    fname = f"ReporteInvernadero_{nombre.replace(' ','_')}_{plan.replace(' ','_')}.html"
    full = os.path.join(rp_dir, fname)
    if not os.path.isfile(full):
        flash("Primero ejecute la simulación para generar el reporte.")
        return redirect(url_for("routes.index"))
    return send_file(full, as_attachment=True)

@bp.route("/tda")
def tda():
    nombre = request.args.get("invernadero", "")
    plan_nombre = request.args.get("plan", "")
    t_seg = request.args.get("t", "0")
    try:
        t = int(t_seg)
    except:
        t = 0
    inv = buscar_invernadero_por_nombre(SISTEMA, nombre)
    if inv is None:
        flash("Invernadero no encontrado.")
        return redirect(url_for("routes.index"))
    plan = inv.buscar_plan_por_nombre(plan_nombre)
    if plan is None:
        flash("Plan no encontrado.")
        return redirect(url_for("routes.ver_invernadero", nombre=nombre))
    path_dot, path_img = graficar_tdas_en_t(inv, plan, t)
    # preferimos entregar png si existe, si no, el .dot
    if path_img is not None and os.path.isfile(path_img):
        return send_file(path_img, as_attachment=True)
    return send_file(path_dot, as_attachment=True)

@bp.route("/salida_xml")
def salida_xml():
    # Genera salida.xml para TODOS los invernaderos y planes del sistema
    from .models.parser_xml import generar_salida_xml
    out_dir = os.path.join(os.path.dirname(__file__), "output")
    full = os.path.join(out_dir, "salida.xml")
    sim = Simulador()
    ok, msg = generar_salida_xml(SISTEMA, sim, full)
    if not ok:
        flash("Error al generar salida.xml: " + msg)
        return redirect(url_for("routes.index"))
    return send_file(full, as_attachment=True)

@bp.route("/ayuda")
def ayuda():
    return render_template("ayuda.html")
