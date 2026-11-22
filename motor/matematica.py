"""Estructura de un libro de matemática: enunciados numerados, ecuaciones con número y referencias cruzadas.

Los bloques y el Markdown dejan marcas; numerar() las convierte en números y resolver_refs() en enlaces.

- Enunciados (definición, teorema, lema, proposición, corolario, ejemplo, observación) comparten un contador
  por capítulo: Definición 3.1, Teorema 3.2. Los ejercicios y las ecuaciones llevan contadores propios.
- Una ecuación en bloque recibe número solo si tiene etiqueta: «$$ … $$ {#eq:nombre}».
- [@id] en el texto se convierte en un enlace con el nombre del enunciado («Teorema 3.2») o el número de la
  ecuación («(3.1)»). Entre capítulos, el generador comparte refs y registro y llama a resolver_refs() al final.
"""
import re
from dataclasses import dataclass, field

from .md import e

ENUNCIADOS = {"definicion": "Definición", "teorema": "Teorema", "lema": "Lema", "proposicion": "Proposición",
              "corolario": "Corolario", "ejemplo": "Ejemplo", "observacion": "Observación"}
EN_INDICE = ("definicion", "teorema", "lema", "proposicion", "corolario")

_MARCA = re.compile(r"\x02(enunciado|ejercicio|ecuacion)\|([^\x02]*)\x02")
_REF = re.compile(r"\x03([^\x03]+)\x03")


def marca_enunciado(tipo: str, id_: str, nombre: str) -> str:
    return f"\x02enunciado|{tipo}|{id_}|{nombre.replace('|', '¦')}\x02"


def marca_ejercicio(id_: str) -> str:
    return f"\x02ejercicio|ejercicio|{id_}|\x02"


@dataclass
class Numeracion:
    """Contadores de un capítulo. refs y registro se comparten entre los capítulos de un libro."""
    capitulo: str = ""            # «3»: los números salen «3.1»; vacío: «1»
    archivo: str = ""             # nombre del .html del capítulo, sin extensión
    refs: dict = field(default_factory=dict)       # id → (texto del enlace, archivo)
    registro: list = field(default_factory=list)   # enunciados para el índice del libro
    contadores: dict = field(default_factory=dict)

    def siguiente(self, clase: str) -> str:
        self.contadores[clase] = self.contadores.get(clase, 0) + 1
        n = self.contadores[clase]
        return f"{self.capitulo}.{n}" if self.capitulo else str(n)


def numerar(html: str, num: Numeracion) -> str:
    def reemplazar(m):
        clase, datos = m.group(1), m.group(2).split("|")
        n = num.siguiente(clase)
        if clase == "ecuacion":
            id_ = datos[0]
            if id_:
                num.refs[id_] = (f"({n})", num.archivo)
            return f"\\tag{{{n}}}"
        tipo, id_, nombre = datos[0], datos[1], datos[2].replace("¦", "|")
        etiqueta = f"{'Ejercicio' if clase == 'ejercicio' else ENUNCIADOS[tipo]} {n}"
        if id_:
            num.refs[id_] = (etiqueta, num.archivo)
        if tipo in EN_INDICE:
            num.registro.append({"tipo": tipo, "etiqueta": etiqueta, "nombre": nombre, "id": id_,
                                 "archivo": num.archivo, "capitulo": num.capitulo})
        return etiqueta
    return _MARCA.sub(reemplazar, html)


def resolver_refs(html: str, refs: dict, archivo: str = "") -> str:
    """[@id] → enlace al enunciado o a la ecuación, en esta página o en la de otro capítulo."""
    def enlazar(m):
        id_ = m.group(1)
        if id_ not in refs:
            return f'<span class="ref falta">[?{e(id_)}]</span>'
        texto, destino = refs[id_]
        href = f"#{id_}" if not destino or destino == archivo else f"{destino}.html#{id_}"
        return f'<a class="ref" href="{e(href)}">{texto}</a>'
    return _REF.sub(enlazar, html)


def indice_enunciados(registro: list) -> str:
    """Lista de definiciones y resultados del libro, por capítulo, con enlace a cada uno."""
    grupos: dict = {}
    for r in registro:
        grupos.setdefault(r["capitulo"], []).append(r)
    partes = []
    for capitulo, filas in grupos.items():
        items = "".join(
            f'<li><a href="{e(r["archivo"])}.html#{e(r["id"])}"><b>{r["etiqueta"]}</b> {r["nombre"]}</a></li>'
            if r["id"] else f'<li><b>{r["etiqueta"]}</b> {r["nombre"]}</li>' for r in filas)
        titulo = f"<h3>Capítulo {e(capitulo)}</h3>" if capitulo else ""
        partes.append(f'{titulo}<ul class="indice-enunciados">{items}</ul>')
    return "".join(partes)
