"""Páginas, portada, navegación y archivos compartidos (style.css y lab.js) de un curso."""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .md import e

AQUI = Path(__file__).resolve().parent
PLANTILLAS = AQUI / "plantillas"
ASSETS = AQUI / "assets"
MARCAR = '<label class="got"><input type="checkbox" id="got"> Lo tengo claro</label>\n'
# KaTeX dibuja las fórmulas ($…$ y $$…$$); solo se carga en las páginas que tienen alguna
_KATEX = "https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.11/"
KATEX = (f'<link rel="stylesheet" href="{_KATEX}katex.min.css" '
         'integrity="sha384-nB0miv6/jRmo5UMMR1wu3Gz6NLsoTkbqJghGIsx//Rlm+ZU03BU6SQNC66uf4l5+" '
         'crossorigin="anonymous" referrerpolicy="no-referrer">\n'
         f'<script defer src="{_KATEX}katex.min.js" '
         'integrity="sha384-7zkQWkzuo3B5mTepMUcHkMB5jZaolc2xDwL6VFqjFALcbeS9Ggm/Yr2r3Dy4lfFg" '
         'crossorigin="anonymous" referrerpolicy="no-referrer"></script>\n')


@dataclass
class Curso:
    """Lo que identifica a un curso en sus páginas."""
    salida: Path                  # carpeta donde se escribe el sitio
    nombre: str                   # «Cómo funciona un telco»: va en el <title>
    marca: str                    # HTML del enlace de la barra superior
    eyebrow: str                  # texto pequeño a la derecha de la marca
    pie: str                      # HTML dentro de <footer>
    prefijo: str                  # prefijo de las claves de avance en localStorage («telco-»)
    aria_pager: str = "Capítulo anterior y siguiente"
    meta_extra: str = ""          # etiquetas <meta> adicionales
    extra_css: str = ""           # estilos propios del curso: se agregan al final de style.css


@dataclass
class Pagina:
    slug: str                     # data-page y clave de avance
    archivo: str                  # nombre del .html, sin extensión
    numero: str                   # «01», «A»; vacío si no cuenta como capítulo
    corto: str                    # título en la ruta de la izquierda
    titulo: str                   # <h1> (HTML ya escapado)
    contenido: str = ""           # HTML de <main>, sin la cabecera
    titulo_pagina: str = ""       # <title>; si falta, el corto
    descripcion: str = ""         # <meta name="description"> (escapado)
    lede: str = ""                # entradilla bajo el título (HTML)
    rotulo: str = ""              # «CAPÍTULO 01 DE 49»
    etapa: object = 0
    en_preparacion: bool = False
    scripts: list = field(default_factory=list)
    simbolos: str = ""            # sprite SVG compartido
    resumen: str = ""             # texto de la tarjeta en la portada (escapado)
    tarjeta: str = ""             # título de la tarjeta, si es distinto del <h1>
    n_portada: str = ""           # lo que muestra la tarjeta en lugar del número («+»)
    marcar: bool = True           # casilla «Lo tengo claro» al final


def _plantilla(nombre: str) -> str:
    return (PLANTILLAS / nombre).read_text(encoding="utf-8")


def _comunes(curso: Curso, t: str) -> str:
    return (t.replace("{{NOMBRE}}", curso.nombre).replace("{{MARCA}}", curso.marca)
            .replace("{{EYEBROW}}", curso.eyebrow).replace("{{PIE}}", curso.pie)
            .replace("{{ARIA_PAGER}}", curso.aria_pager)
            .replace("{{META_EXTRA}}", curso.meta_extra + "\n" if curso.meta_extra else ""))


def cabecera(p: Pagina) -> str:
    return ('<header class="page-head">' + (f'<span class="num">{p.rotulo}</span>' if p.rotulo else "")
            + f"<h1>{p.titulo}</h1>" + (f'<p class="lede">{p.lede}</p>' if p.lede else "") + "</header>")


def pagina_html(curso: Curso, p: Pagina) -> str:
    t = _comunes(curso, _plantilla("pagina.html"))
    con_formulas = re.search(r'class="math(?:-display)?"', p.contenido + p.lede + p.titulo)
    t = t.replace("{{CABEZA}}", KATEX if con_formulas else "")
    return (t.replace("{{TITULO_PAGINA}}", p.titulo_pagina or p.corto).replace("{{DESCRIPCION}}", p.descripcion)
            .replace("{{SIMBOLOS}}", p.simbolos + "\n" if p.simbolos else "").replace("{{SLUG}}", p.slug)
            .replace("{{CABECERA}}", cabecera(p)).replace("{{CONTENIDO}}", p.contenido)
            .replace("{{MARCAR}}", MARCAR if p.marcar else "")
            .replace("{{SCRIPTS}}", "\n".join(p.scripts)))


def portada_html(curso: Curso, inicio: str, etapas: str, apendices: str, descripcion: str) -> str:
    t = _comunes(curso, _plantilla("portada.html"))
    return (t.replace("{{DESCRIPCION}}", descripcion).replace("{{INICIO}}", inicio)
            .replace("{{ETAPAS}}", etapas).replace("{{APENDICES}}", apendices))


def tarjeta(p: Pagina) -> str:
    interior = f'<span class="n">{p.n_portada or p.numero}</span><b>{p.tarjeta or p.titulo}</b><p>{p.resumen}</p>'
    if p.en_preparacion:
        return f'\n    <div class="mod soon" data-id="{p.slug}">{interior}</div>'
    data_id = f' data-id="{p.slug}"' if p.numero else ""
    return f'\n    <a class="mod"{data_id} href="{p.archivo}.html">{interior}</a>'


def bloque_etapa(id_: str, titulo_h2: str, paginas: list, abierta: bool = False, cuenta: str = "") -> str:
    """Una etapa de la portada como grupo desplegable, con sus tarjetas."""
    tarjetas = "".join(tarjeta(p) for p in paginas)
    span = f'<span class="cuenta" data-etapa-cuenta="{cuenta}"></span>' if cuenta else ""
    return (f'\n<details class="stage" id="{id_}"{" open" if abierta else ""}><summary>'
            f"<h2>{titulo_h2}</h2>{span}</summary>"
            f'\n  <div class="mods">{tarjetas}\n  </div>\n</details>\n')


def datos_navegacion(paginas: list, etapas: list) -> tuple[list, list]:
    """PAGES: [slug, archivo, número, título corto, en preparación, etapa]; ETAPAS: [etapa, rótulo]."""
    pages = [["index", "index.html", "", "Inicio", 0, 0]] + [
        [p.slug, p.archivo + ".html", p.numero, p.corto, 1 if p.en_preparacion else 0, p.etapa] for p in paginas]
    return pages, [list(x) for x in etapas]


def escribir_assets(curso: Curso, pages: list, etapas: list) -> None:
    """style.css y lab.js del motor en <salida>/assets, con los datos de este curso."""
    destino = curso.salida / "assets"
    destino.mkdir(parents=True, exist_ok=True)
    css = (ASSETS / "curso.css").read_text(encoding="utf-8")
    if curso.extra_css:
        css = css.rstrip("\n") + "\n\n/* ---- Propio de este curso ---- */\n" + curso.extra_css.strip("\n") + "\n"
    (destino / "style.css").write_text(css, encoding="utf-8")
    js = (ASSETS / "lab.js").read_text(encoding="utf-8")
    datos = ("const CURSO=" + json.dumps({"prefijo": curso.prefijo}, ensure_ascii=False) + ";\n"
             + "const PAGES=" + json.dumps(pages, ensure_ascii=False) + ";\n"
             + "const ETAPAS=" + json.dumps(etapas, ensure_ascii=False) + ";\n")
    js, n = re.subn(r'const CURSO=\{.*?\};\nconst PAGES=\[\];\nconst ETAPAS=\[\];\n', lambda _: datos, js, count=1)
    if n != 1:
        raise ValueError("lab.js del motor: no encuentro los marcadores de CURSO, PAGES y ETAPAS")
    (destino / "lab.js").write_text(js, encoding="utf-8")


def escribir(ruta: Path, texto: str) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")


__all__ = ["Curso", "Pagina", "cabecera", "pagina_html", "portada_html", "tarjeta", "bloque_etapa",
           "datos_navegacion", "escribir_assets", "escribir", "e"]
