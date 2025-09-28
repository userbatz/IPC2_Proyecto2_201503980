
from .tda import ListaSimple, Cola

class Planta:
    __slots__ = ("hilera","posicion","litros","gramos","nombre")
    def __init__(self, hilera:int, posicion:int, litros:float, gramos:float, nombre:str):
        self.hilera = hilera
        self.posicion = posicion
        self.litros = litros
        self.gramos = gramos
        self.nombre = nombre

class Dron:
    __slots__ = ("id","nombre","hilera","posicion","agua_total","fert_total","objetivos","finalizado","marcar_fin_proximo_tick")
    def __init__(self, id:int, nombre:str, hilera:int):
        self.id = id
        self.nombre = nombre
        self.hilera = hilera
        self.posicion = 0
        self.agua_total = 0.0
        self.fert_total = 0.0
        self.objetivos = Cola()  # posiciones objetivo según plan
        self.finalizado = False
        self.marcar_fin_proximo_tick = False

class PasoPlan:
    __slots__ = ("hilera","posicion")
    def __init__(self, hilera:int, posicion:int):
        self.hilera = hilera
        self.posicion = posicion

class Plan:
    __slots__ = ("nombre","pasos")
    def __init__(self, nombre:str):
        self.nombre = nombre
        self.pasos = ListaSimple()

class Hilera:
    __slots__ = ("numero","plantas")
    def __init__(self, numero:int):
        self.numero = numero
        self.plantas = ListaSimple()

    def buscar_planta(self, posicion:int):
        for p in self.plantas:
            if p.posicion == posicion:
                return p
        return None

class Invernadero:
    __slots__ = ("nombre","numero_hileras","plantas_x_hilera","hileras","drones","planes")
    def __init__(self, nombre:str, numero_hileras:int, plantas_x_hilera:int):
        self.nombre = nombre
        self.numero_hileras = numero_hileras
        self.plantas_x_hilera = plantas_x_hilera
        self.hileras = ListaSimple()
        self.drones = ListaSimple()
        self.planes = ListaSimple()
        # inicializar hileras
        i = 1
        while i <= numero_hileras:
            self.hileras.agregar_final(Hilera(i))
            i += 1

    def obtener_hilera(self, numero:int):
        for h in self.hileras:
            if h.numero == numero:
                return h
        return None

    def agregar_planta(self, planta:Planta):
        h = self.obtener_hilera(planta.hilera)
        if h is not None:
            h.plantas.agregar_final(planta)

    def agregar_dron(self, dron:Dron):
        self.drones.agregar_final(dron)

    def agregar_plan(self, plan:Plan):
        self.planes.agregar_final(plan)

    def nombres_planes_iterable(self):
        # devuelve iterable simple de nombres (sin listas nativas)
        class _It:
            def __init__(self, lista):
                self._n = lista.cabeza
            def __iter__(self):
                return self
            def __next__(self):
                if self._n is None:
                    raise StopIteration
                val = self._n.valor.nombre
                self._n = self._n.siguiente
                return val
        return _It(self.planes)

    def buscar_plan_por_nombre(self, nombre:str):
        for p in self.planes:
            if p.nombre == nombre:
                return p
        return None

class Sistema:
    __slots__ = ("invernaderos",)
    def __init__(self):
        self.invernaderos = ListaSimple()

    def limpiar(self):
        self.invernaderos.limpiar()

    def agregar_invernadero(self, inv:Invernadero):
        self.invernaderos.agregar_final(inv)

    def nombres_invernaderos_iterable(self):
        class _It:
            def __init__(self, lista):
                self._n = lista.cabeza
            def __iter__(self):
                return self
            def __next__(self):
                if self._n is None:
                    raise StopIteration
                val = self._n.valor.nombre
                self._n = self._n.siguiente
                return val
        return _It(self.invernaderos)

def buscar_invernadero_por_nombre(sistema:Sistema, nombre:str):
    for inv in sistema.invernaderos:
        if inv.nombre == nombre:
            return inv
    return None
