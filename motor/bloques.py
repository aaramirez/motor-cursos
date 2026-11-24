"""Bloques ::: de los cursos y el cuerpo de una página (secciones ## con prosa y bloques).

Bloques: analogia, caso-real, en-la-practica (recuadros), diagrama (SVG incrustado), lab (fragmento HTML;
sus <script> van al final de la página), pruebate, para-saber-mas, practica (terminal o navegador) e
investiga. Los textos visibles de cada curso (rótulos de recuadros, «en el capítulo») salen de Textos.

Libros de matemática: definicion, teorema, lema, proposicion, corolario, ejemplo y observacion (numerados,
con id="…" para citarlos con [@id] y nombre="…"), demostracion (plegable; de="id" la une a su enunciado),
ejercicio (numerado; nivel="1|2|3"), pista y solucion (plegables) y prompt (texto para copiar a una IA).
"""
import re
from dataclasses import dataclass, field
from pathlib import Path

from .matematica import ENUNCIADOS, Numeracion, marca_ejercicio, marca_enunciado, numerar, resolver_refs
from .md import _inline, e, md_a_html

_ABRE = re.compile(r"^:::([\w-]+)(.*)$")
_ATTR = re.compile(r'(\w+)="([^"]*)"')
PRACTICAS = {"terminal": "En la terminal", "navegador": "En el navegador"}


@dataclass
class Textos:
    """Lo que cambia de un curso a otro en los bloques."""
    recuadros: dict = field(default_factory=lambda: {
        "analogia": ("analogia", "Imagínalo así"), "caso-real": ("caso", "Así lo hace un operador"),
        "en-la-practica": ("ml", "En la práctica")})
    unidad: str = "capítulo"  # «Estas preguntas no se responden en el capítulo»


@dataclass
class Fuentes:
    """Dónde están las figuras y los laboratorios de un curso."""
    figuras: Path
    labs: Path


def sin_prologo(svg: str) -> str:
    svg = re.sub(r"<!--.*?-->", "", svg, flags=re.S)
    return re.sub(r"^\s*<\?xml[^>]*\?>\s*", "", svg).strip()


def directiva(fuentes: Fuentes, nombre: str, attrs: dict, texto: str, scripts: list,
              textos: Textos | None = None) -> str:
    textos = textos or Textos()
    texto = re.sub(r"<!--.*?-->", "", texto, flags=re.S).strip()
    if nombre in textos.recuadros:
        clase, rotulo = textos.recuadros[nombre]
        return f'<div class="{clase}"><b>{rotulo}</b>{md_a_html(texto)}</div>'
    if nombre == "diagrama":
        id_ = attrs.get("id", "")
        fig = fuentes.figuras / f"{id_}.svg"
        svg = sin_prologo(fig.read_text(encoding="utf-8")) if fig.exists() else \
            f'<p class="falta">Diagrama {e(id_)} en preparación</p>'
        return (f'<figure class="fig fig-{attrs.get("tipo", "esquema")}" id="{e(id_)}"><div class="lienzo">{svg}</div>'
                f"<figcaption>{_inline(' '.join(texto.split()))}</figcaption></figure>")
    if nombre == "lab":
        id_ = attrs.get("id", "")
        frag = fuentes.labs / f"{id_}.html"
        cuerpo = frag.read_text(encoding="utf-8") if frag.exists() else ""
        scripts += re.findall(r"<script>.*?</script>", cuerpo, flags=re.S)
        cuerpo = re.sub(r"<script>.*?</script>", "", cuerpo, flags=re.S).strip()
        lineas = texto.splitlines() or [""]
        pista = md_a_html("\n".join(lineas[1:])).replace("<p>", '<p class="hint">')
        return (f'<div class="lab" id="{e(id_)}"><div class="lab-title"><span class="tag">Laboratorio</span>'
                f"<h3>{_inline(lineas[0])}</h3></div>{pista}{cuerpo}</div>")
    if nombre == "pruebate":
        items = []
        for l in texto.splitlines():
            if l.startswith("- ") and " :: " in l:
                q, a = l[2:].split(" :: ", 1)
                items.append(f"<details><summary>{_inline(q)}</summary><p>{_inline(a)}</p></details>")
        return '<div class="quiz"><h3>Pruébate</h3>' + "".join(items) + "</div>" if items else ""
    if nombre == "para-saber-mas":
        enlaces = []
        for l in texto.splitlines():
            if m := re.match(r"^- \[([^\]]+)\]\((\S+)\)(?:\s*·\s*(.+))?$", l):
                nota = f" <small>{_inline(m.group(3), enlaces=False)}</small>" if m.group(3) else ""
                enlaces.append(f'<a class="vid" href="{m.group(2)}" target="_blank" rel="noopener">'
                               f"{_inline(m.group(1), enlaces=False)}{nota}</a>")
        return '<div class="vids"><span>Para saber más</span>' + "".join(enlaces) + "</div>" if enlaces else ""
    if nombre == "practica":
        lineas = texto.splitlines() or [""]
        rotulo = PRACTICAS.get(attrs.get("donde", ""), "Práctica")
        return (f'<div class="practica"><div class="practica-title"><span class="tag">{rotulo}</span>'
                f"<h3>{_inline(lineas[0])}</h3></div>{md_a_html(chr(10).join(lineas[1:]))}</div>")
    if nombre in ENUNCIADOS or nombre == "ejercicio":
        id_ = attrs.get("id", "")
        titulo = _inline(attrs["nombre"]) if attrs.get("nombre") else ""
        if nombre == "ejercicio":
            clase, marca = "ejercicio", marca_ejercicio(id_)
            nivel = attrs.get("nivel", "")
            extra = (f' <span class="nivel" aria-label="Dificultad {nivel} de 3">{"★" * int(nivel)}'
                     f'{"☆" * (3 - int(nivel))}</span>') if nivel in ("1", "2", "3") else ""
        else:
            clase, marca = f"enunciado enunciado-{nombre}", marca_enunciado(nombre, id_, titulo)
            extra = f' <span class="nombre">({titulo})</span>' if titulo else ""
        atr = f' id="{e(id_)}"' if id_ else ""
        return f'<div class="{clase}"{atr}><p class="enunciado-t"><b>{marca}</b>{extra}</p>{md_a_html(texto)}</div>'
    if nombre == "demostracion":
        de = f" · \x03{attrs['de']}\x03" if attrs.get("de") else ""
        abierta = " open" if "abierta" in attrs else ""
        return (f'<details class="demostracion"{abierta}><summary>Demostración{de}</summary>{md_a_html(texto)}'
                '<p class="qed" aria-hidden="true">∎</p></details>')
    if nombre in ("pista", "solucion"):
        rotulo = {"pista": "Pista", "solucion": "Solución"}[nombre]
        return f'<details class="{nombre}"><summary>{rotulo}</summary>{md_a_html(texto)}</details>'
    if nombre == "prompt":
        lineas = texto.splitlines() or [""]
        return (f'<div class="prompt"><div class="prompt-title"><span class="tag">Prompt para la IA</span>'
                f"<h3>{_inline(lineas[0])}</h3></div><div class=\"code-copia\"><pre><code>"
                f'{e(chr(10).join(lineas[1:]).strip(), quote=False)}</code></pre>'
                '<button type="button" class="copiar copiar-todo">Copiar</button></div></div>')
    if nombre == "investiga":
        items = []
        for l in texto.splitlines():
            if l.startswith("- "):
                q, _, pista = l[2:].partition(" :: ")
                items.append(f"<li>{_inline(q)}" + (f"<small>{_inline(pista)}</small>" if pista else "") + "</li>")
        return ('<div class="investiga"><h3>Para investigar</h3><p class="hint">Estas preguntas no se responden '
                f'en el {textos.unidad}: búscalas por tu cuenta.</p><ol>' + "".join(items) + "</ol></div>") if items else ""
    return ""


def cuerpo(ruta: Path) -> list[str]:
    """Líneas del archivo sin el front matter ni el título H1 (los comentarios # del código se conservan)."""
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    if lineas and lineas[0] == "---":
        lineas = lineas[lineas.index("---", 1) + 1:]
    salida, en_codigo = [], False
    for l in lineas:
        if l.startswith("```"):
            en_codigo = not en_codigo
        if en_codigo or not l.startswith("# "):
            salida.append(l)
    return salida


def render_cuerpo(fuentes: Fuentes, lineas: list[str], scripts: list | None = None,
                  textos: Textos | None = None, num: Numeracion | None = None) -> str:
    """Contenido de <main> (sin la cabecera): una <section> por cada ##, con prosa y bloques.

    Numera enunciados, ejercicios y ecuaciones. Sin num, la numeración es de la página («Teorema 1») y las
    referencias [@id] se resuelven aquí. Con num (un libro con capítulos), los números salen «3.1» y las
    referencias quedan pendientes: el generador llama a resolver_refs() cuando ya numeró todos los capítulos.
    """
    scripts = [] if scripts is None else scripts
    secciones, actual, texto = [], {"h2": None, "partes": []}, []

    def volcar():
        if "".join(texto).strip():
            html_ = md_a_html("\n".join(texto))
            if html_:
                actual["partes"].append(f'<div class="prose">{html_}</div>')
        texto.clear()

    i, en_codigo = 0, False
    while i < len(lineas):
        l = lineas[i]
        if l.lstrip().startswith(("```", "~~~")):
            en_codigo = not en_codigo
            texto.append(l)
        elif en_codigo:
            texto.append(l)
        elif l.startswith("## "):
            volcar()
            secciones.append(actual)
            actual = {"h2": l[3:].strip(), "partes": []}
        elif (m := _ABRE.match(l)) and m.group(1) != "":
            volcar()
            fin = i + 1
            while fin < len(lineas) and lineas[fin].strip() != ":::":
                fin += 1
            actual["partes"].append(directiva(fuentes, m.group(1), dict(_ATTR.findall(m.group(2))),
                                              "\n".join(lineas[i + 1:fin]), scripts, textos))
            i = fin
        else:
            texto.append(l)
        i += 1
    volcar()
    secciones.append(actual)
    salida = []
    for s in secciones:
        partes = "".join(p for p in s["partes"] if p)
        if not partes and not s["h2"]:
            continue
        h2 = f"<h2>{_inline(s['h2'])}</h2>" if s["h2"] else ""
        salida.append(f"<section>{h2}{partes}</section>")
    html_ = "\n".join(salida)
    if num is not None:
        return numerar(html_, num)
    local = Numeracion()
    return resolver_refs(numerar(html_, local), local.refs)


def separar_scripts(html_: str) -> tuple[str, list[str]]:
    """Contenido HTML escrito a mano: los <script> salen para ir al final de la página, después de lab.js."""
    scripts = re.findall(r"<script>.*?</script>", html_, flags=re.S)
    return re.sub(r"\s*<script>.*?</script>", "", html_, flags=re.S), scripts
