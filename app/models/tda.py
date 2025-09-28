
# TDAs propios: Nodo simple, ListaSimple, Cola.
# Sin uso de list/dict/tuple/set en almacenamiento del problema.

class Nodo:
    __slots__ = ("valor", "siguiente")
    def __init__(self, valor=None):
        self.valor = valor
        self.siguiente = None

class ListaSimple:
    __slots__ = ("cabeza", "cola", "_len")
    def __init__(self):
        self.cabeza = None
        self.cola = None
        self._len = 0

    def agregar_final(self, valor):
        n = Nodo(valor)
        if self.cabeza is None:
            self.cabeza = n
            self.cola = n
        else:
            self.cola.siguiente = n
            self.cola = n
        self._len += 1
        return n

    def agregar_inicio(self, valor):
        n = Nodo(valor)
        if self.cabeza is None:
            self.cabeza = n
            self.cola = n
        else:
            n.siguiente = self.cabeza
            self.cabeza = n
        self._len += 1
        return n

    def esta_vacia(self):
        return self.cabeza is None

    def limpiar(self):
        self.cabeza = None
        self.cola = None
        self._len = 0

    def __len__(self):
        return self._len

    def __iter__(self):
        actual = self.cabeza
        while actual is not None:
            yield actual.valor
            actual = actual.siguiente

    def buscar_primero(self, predicado):
        actual = self.cabeza
        while actual is not None:
            if predicado(actual.valor):
                return actual.valor
            actual = actual.siguiente
        return None

    def eliminar_primero(self, predicado):
        anterior = None
        actual = self.cabeza
        while actual is not None:
            if predicado(actual.valor):
                if anterior is None:
                    self.cabeza = actual.siguiente
                else:
                    anterior.siguiente = actual.siguiente
                if actual is self.cola:
                    self.cola = anterior
                self._len -= 1
                return True
            anterior = actual
            actual = actual.siguiente
        return False

class Cola:
    __slots__ = ("_lista", )
    def __init__(self):
        self._lista = ListaSimple()

    def encolar(self, valor):
        self._lista.agregar_final(valor)

    def desencolar(self):
        # eliminar cabeza
        if self._lista.cabeza is None:
            return None
        n = self._lista.cabeza
        self._lista.cabeza = n.siguiente
        if self._lista.cabeza is None:
            self._lista.cola = None
        self._lista._len -= 1
        return n.valor

    def ver_frente(self):
        if self._lista.cabeza is None:
            return None
        return self._lista.cabeza.valor

    def esta_vacia(self):
        return self._lista.cabeza is None

    def __len__(self):
        return len(self._lista)

    def __iter__(self):
        return iter(self._lista)
