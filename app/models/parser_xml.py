
# Carga XML a estructuras propias y genera salida.xml
# Evitar uso de list/dict/tuple/set en el modelado. Para parseo se usa ElementTree.
import xml.etree.ElementTree as ET
from .entidades import Sistema, Invernadero, Planta, Dron, Plan, PasoPlan
from .tda import ListaSimple

def _leer_entero(texto):
    # eliminar espacios
    s = "".join(ch for ch in texto if ch not in ("\n","\r","\t"," "))
    try:
        return int(s)
    except:
        return 0

def _leer_flotante(texto):
    s = "".join(ch for ch in texto if ch not in ("\n","\r","\t"," "))
    try:
        return float(s)
    except:
        return 0.0

def _trim(s):
    # elimina espacios a ambos lados sin usar split
    if s is None:
        return ""
    ini = 0
    fin = len(s) - 1
    while ini <= fin and s[ini] in (" ","\n","\r","\t"):
        ini += 1
    while fin >= ini and s[fin] in (" ","\n","\r","\t"):
        fin -= 1
    return s[ini:fin+1]

def _parsear_pasos_plan(cadena):
    """
    Convierte "H1-P2, H2-P1" en una ListaSimple de PasoPlan
    (sin usar split/list). Se extraen tokens H<d>-P<d>.
    """
    pasos = ListaSimple()
    i = 0
    n = len(cadena)
    while i < n:
        # buscar 'H'
        while i < n and cadena[i] != 'H':
            i += 1
        if i >= n:
            break
        i += 1  # después de H
        # número de hilera
        hil = 0
        while i < n and cadena[i].isdigit():
            hil = hil * 10 + (ord(cadena[i]) - 48)
            i += 1
        # buscar '-P'
        if i < n and cadena[i] == '-':
            i += 1
        if i < n and (cadena[i] == 'P' or cadena[i] == 'p'):
            i += 1
        # número de posición
        pos = 0
        while i < n and cadena[i].isdigit():
            pos = pos * 10 + (ord(cadena[i]) - 48)
            i += 1
        if hil > 0 and pos > 0:
            pasos.agregar_final(PasoPlan(hil, pos))
        # avanzar hasta la próxima coma (si hubiera)
        while i < n and cadena[i] != 'H':
            i += 1
    return pasos

def cargar_configuracion_desde_xml(ruta:str, sistema:Sistema):
    try:
        tree = ET.parse(ruta)
        root = tree.getroot()
    except Exception as e:
        return False, f"XML inválido: {e}"

    # Limpia sistema previo
    sistema.limpiar()

    # Mapa ligero de drones por id (sin dict: usamos dos listas ligadas paralelas)
    ids = ListaSimple()
    nombres = ListaSimple()

    # listaDrones
    for dron_elem in root.iter("dron"):
        # Sólo los de la sección listaDrones (que no tengan 'hilera')
        hil_attr = dron_elem.get("hilera")
        if hil_attr is not None:
            continue
        id_attr = dron_elem.get("id")
        nom_attr = dron_elem.get("nombre")
        if id_attr is None or nom_attr is None:
            continue
        # guardar en listas paralelas
        ids.agregar_final(id_attr)
        nombres.agregar_final(nom_attr)

    # listaInvernaderos
    for inv_elem in root.iter("invernadero"):
        nombre_inv = inv_elem.get("nombre") or "Invernadero"
        nh = 0
        pxh = 0
        for child in inv_elem:
            tag = child.tag
            if tag == "numeroHileras":
                nh = _leer_entero(child.text or "0")
            elif tag == "plantasXhilera":
                pxh = _leer_entero(child.text or "0")

        inv = Invernadero(nombre_inv, nh, pxh)

        # listaPlantas
        for pl in inv_elem.iter("planta"):
            hil = _leer_entero(pl.get("hilera") or "0")
            pos = _leer_entero(pl.get("posicion") or "0")
            litros = _leer_flotante(pl.get("litrosAgua") or "0")
            gramos = _leer_flotante(pl.get("gramosFertilizante") or "0")
            nombre_pl = _trim(pl.text or "")
            inv.agregar_planta(Planta(hil, pos, litros, gramos, nombre_pl))

        # asignacionDrones
        for asg in inv_elem.iter("dron"):
            hil_attr = asg.get("hilera")
            if hil_attr is None:
                continue
            hil = _leer_entero(hil_attr)
            idref = asg.get("id") or ""
            # resolver nombre por idref recorriendo listas paralelas
            nom = None
            n_id = ids.cabeza
            n_nm = nombres.cabeza
            while n_id is not None and n_nm is not None:
                if (n_id.valor == idref):
                    nom = n_nm.valor
                    break
                n_id = n_id.siguiente
                n_nm = n_nm.siguiente
            if nom is None:
                nom = "DRX"
            inv.agregar_dron(Dron(int(_leer_entero(idref)), nom, hil))

        # planesRiego
        for plan_elem in inv_elem.iter("plan"):
            nombre = plan_elem.get("nombre") or "Plan"
            cadena = plan_elem.text or ""
            p = Plan(nombre)
            p.pasos = _parsear_pasos_plan(cadena)
            inv.agregar_plan(p)

        sistema.agregar_invernadero(inv)

    return True, "OK"

def generar_salida_xml(sistema:Sistema, simulador, ruta_salida:str):
    # Construir el árbol de salida
    from xml.dom.minidom import Document
    doc = Document()
    datosSalida = doc.createElement("datosSalida")
    doc.appendChild(datosSalida)

    listaInv = doc.createElement("listaInvernaderos")
    datosSalida.appendChild(listaInv)

    # recorrer invernaderos
    inv_node = sistema.invernaderos.cabeza
    while inv_node is not None:
        inv = inv_node.valor
        inv_xml = doc.createElement("invernadero")
        inv_xml.setAttribute("nombre", inv.nombre)
        listaInv.appendChild(inv_xml)

        listaPlanes = doc.createElement("listaPlanes")
        inv_xml.appendChild(listaPlanes)

        # recorrer planes
        pl_node = inv.planes.cabeza
        while pl_node is not None:
            plan = pl_node.valor
            res, tl = simulador.simular(inv, plan)

            plan_xml = doc.createElement("plan")
            plan_xml.setAttribute("nombre", plan.nombre)

            t_opt = doc.createElement("tiempoOptimoSegundos")
            t_opt.appendChild(doc.createTextNode(str(res.tiempo_optimo)))
            plan_xml.appendChild(t_opt)

            a_req = doc.createElement("aguaRequeridaLitros")
            a_req.appendChild(doc.createTextNode(str(int(res.agua_total) if res.agua_total.is_integer() else str(res.agua_total))))
            plan_xml.appendChild(a_req)

            f_req = doc.createElement("fertilizanteRequeridoGramos")
            f_req.appendChild(doc.createTextNode(str(int(res.fert_total) if res.fert_total.is_integer() else str(res.fert_total))))
            plan_xml.appendChild(f_req)

            eff = doc.createElement("eficienciaDronesRegadores")
            # eficiencias por dron
            e_node = res.eficiencias.cabeza
            while e_node is not None:
                e = e_node.valor
                dr = doc.createElement("dron")
                dr.setAttribute("nombre", e.nombre)
                dr.setAttribute("litrosAgua", str(int(e.litros) if float(e.litros).is_integer() else str(e.litros)))
                dr.setAttribute("gramosFertilizante", str(int(e.gramos) if float(e.gramos).is_integer() else str(e.gramos)))
                eff.appendChild(dr)
                e_node = e_node.siguiente
            plan_xml.appendChild(eff)

            # instrucciones
            insts = doc.createElement("instrucciones")
            t_node = tl.cabeza
            while t_node is not None:
                t = t_node.valor
                t_elem = doc.createElement("tiempo")
                t_elem.setAttribute("segundos", str(t.segundo))
                # acciones de ese segundo
                a_node = t.acciones.cabeza
                while a_node is not None:
                    acc = a_node.valor
                    dr = doc.createElement("dron")
                    dr.setAttribute("nombre", acc.nombre)
                    dr.setAttribute("accion", acc.accion)
                    t_elem.appendChild(dr)
                    a_node = a_node.siguiente
                insts.appendChild(t_elem)
                t_node = t_node.siguiente

            plan_xml.appendChild(insts)
            listaPlanes.appendChild(plan_xml)

            pl_node = pl_node.siguiente

        inv_node = inv_node.siguiente

    # escribir archivo
    xml_str = doc.toprettyxml(indent="  ", encoding="utf-8")
    try:
        with open(ruta_salida, "wb") as f:
            f.write(xml_str)
        return True, "OK"
    except Exception as e:
        return False, str(e)
