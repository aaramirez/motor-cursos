"""Cursos definidos por un temario.yml: la ficha del curso y su tabla de contenido completa.

Un curso <slug>-source tiene temario.yml y, a medida que se escribe, capitulos/NN-slug.md, labs/ y figuras/.
generar(fuente) escribe el sitio: la portada con las partes y los capítulos (los que no tienen archivo salen
«en preparación»), temario.html con la tabla de contenido detallada y cada capítulo escrito.

Campos de temario.yml:
  slug, nombre, marca, eyebrow, prefijo, descripcion, lede_temario   (obligatorios)
  rotulo_patron     título del cierre de cada capítulo en temario.html («El patrón que nace aquí»)
  rotulo_caso       rótulo de los recuadros :::caso-real (por omisión «Un caso real»)
  aviso             nota que se muestra arriba en la portada, la tabla de contenido y cada capítulo
  titular, entrada, para_quien, como   la portada, si el curso no tiene inicio.html
  partes: [{numero, nombre, idea?, capitulos: [{slug, corto, titulo, resumen, secciones, labs?, practicas?, patron?}]}]
"""
import json
from pathlib import Path

import yaml

from .bloques import Fuentes, Textos, render_cuerpo
from .matematica import Numeracion, resolver_refs
from .md import e
from .sitio import (Curso, Pagina, bloque_etapa, datos_navegacion, escribir, escribir_assets, pagina_html,
                    portada_html)

GTM = "GTM-KX76XF8R"  # Google Tag Manager: obligatorio en todas las páginas
OBLIGATORIOS = ("slug", "nombre", "marca", "eyebrow", "prefijo", "descripcion", "lede_temario", "partes")
DE_CAPITULO = ("slug", "corto", "titulo", "resumen", "secciones")


def leer_temario(ruta: Path) -> dict:
    t = yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))
    errores = validar(t)
    if errores:
        raise ValueError(f"{ruta}: " + "; ".join(errores))
    return t


def validar(t: dict) -> list[str]:
    errores = [f"falta «{k}»" for k in OBLIGATORIOS if not t.get(k)]
    slugs = []
    for p in t.get("partes") or []:
        for k in ("numero", "nombre", "capitulos"):
            if not p.get(k):
                errores.append(f"parte {p.get('numero', '?')}: falta «{k}»")
        for c in p.get("capitulos") or []:
            errores += [f"capítulo {c.get('slug', '?')}: falta «{k}»" for k in DE_CAPITULO if not c.get(k)]
            slugs.append(c.get("slug"))
    errores += [f"slug de capítulo repetido: {s}" for s in sorted({s for s in slugs if slugs.count(s) > 1})]
    return errores


def _ficha(ruta: Path) -> tuple[dict, list[str]]:
    texto = ruta.read_text(encoding="utf-8")
    if not texto.startswith("---\n"):
        raise ValueError(f"{ruta.name}: falta la ficha entre líneas ---")
    fin = texto.index("\n---\n", 4)
    ficha = {}
    for linea in texto[4:fin].splitlines():
        clave, _, valor = linea.partition(": ")
        ficha[clave.strip()] = json.loads(valor)
    return ficha, texto[fin + 5:].splitlines()


def _sin_titulo(lineas: list[str]) -> list[str]:
    """Quita el título # del capítulo, pero no los rótulos «# Windows»… de dentro de los bloques de código."""
    salida, en_codigo = [], False
    for l in lineas:
        if l.lstrip().startswith(("```", "~~~")):
            en_codigo = not en_codigo
        if en_codigo or not l.startswith("# "):
            salida.append(l)
    return salida


def capitulos_de(t: dict) -> list[dict]:
    return [c for p in t["partes"] for c in p["capitulos"]]


def inicio_html(t: dict, n_caps: int, escritos: int = 0) -> str:
    """Cabecera de la portada a partir del temario (para cursos sin inicio.html)."""
    titular = t.get("titular", t["nombre"])
    entrada = t.get("entrada", t["descripcion"])
    tabla = '<a href="temario.html">tabla de contenido</a>'
    if escritos >= n_caps:
        estado = (f"Curso completo: los {n_caps} capítulos tienen sus laboratorios, diagramas y prácticas. "
                  f"Empieza por la {tabla} o por el primer capítulo.")
    elif escritos:
        estado = (f"El curso está en preparación: ya están escritos {escritos} de los {n_caps} capítulos. "
                  f"La {tabla} tiene todos, con sus secciones y sus laboratorios.")
    else:
        estado = (f"El curso está en preparación. La {tabla} ya tiene los {n_caps} capítulos con sus secciones "
                  "y sus laboratorios, y está en revisión.")
    parrafos = [f"<p><b>Estado.</b> {estado}</p>"]
    if t.get("para_quien"):
        parrafos.append(f"<p><b>Para quién es.</b> {e(t['para_quien'])}</p>")
    if t.get("como"):
        parrafos.append(f"<p><b>Cómo está hecho.</b> {e(t['como'])}</p>")
    return (f'<header class="hero">\n  <span class="eyebrow">{e(t["eyebrow"])}</span>\n  <h1>{e(titular)}</h1>\n'
            f'  <p class="lede">{e(entrada)}</p>\n</header>\n\n<section>\n  <h2>Cómo usar este curso</h2>\n'
            f'  <div class="prose">\n    ' + "\n    ".join(parrafos) + "\n  </div>\n</section>")


def temario_md(t: dict) -> list[str]:
    lineas, i = [], 0
    for parte in t["partes"]:
        lineas += [f"## Parte {parte['numero']} · {parte['nombre']}", ""]
        if parte.get("idea"):
            lineas += [parte["idea"], ""]
        for c in parte["capitulos"]:
            i += 1
            lineas += [f"### {i:02d}. {c['titulo']}", "", c["resumen"], ""]
            lineas += [f"- {s}" for s in c["secciones"]] + [""]
            if c.get("labs"):
                lineas += ["**Laboratorios**", ""] + [f"- {l}" for l in c["labs"]] + [""]
            if c.get("practicas"):
                lineas += ["**Prácticas**", ""] + [f"- {p}" for p in c["practicas"]] + [""]
            if c.get("patron"):
                lineas += [f"**{t.get('rotulo_patron', 'Lo que te llevas')}:** {c['patron']}", ""]
    return lineas


def generar(fuente: Path, sitio: Path | None = None) -> int:
    """Escribe el sitio del curso de `fuente` en `sitio` (por omisión ../<slug>). Devuelve las páginas escritas."""
    fuente = Path(fuente)
    t = leer_temario(fuente / "temario.yml")
    sitio = Path(sitio) if sitio else fuente.parent / t["slug"]
    nombre, descripcion, caps = t["nombre"], t["descripcion"], capitulos_de(t)
    css = fuente / "curso.css"
    cfg = Curso(salida=sitio, nombre=nombre, marca=t["marca"], eyebrow=t["eyebrow"], prefijo=t["prefijo"],
                meta_extra='<meta name="claude:viewport-fit-sides" content="cover">',
                extra_css=css.read_text(encoding="utf-8") if css.exists() else "")
    fuentes = Fuentes(figuras=fuente / "figuras", labs=fuente / "labs")
    textos = Textos()
    textos.recuadros["caso-real"] = ("caso", t.get("rotulo_caso", "Un caso real"))

    refs, registro, paginas, i = {}, [], [], 0
    for parte in t["partes"]:
        for c in parte["capitulos"]:
            i += 1
            n = f"{i:02d}"
            archivo = f"{n}-{c['slug']}"
            p = Pagina(slug=c["slug"], archivo=archivo, numero=n, corto=c["corto"], titulo=c["titulo"],
                       etapa=parte["numero"], resumen=c["resumen"], descripcion=descripcion,
                       rotulo=f"CAPÍTULO {n} DE {len(caps)}", tarjeta=c["titulo"])
            ruta = fuente / "capitulos" / f"{archivo}.md"
            if not ruta.exists():
                p.en_preparacion = True
            else:
                ficha, lineas = _ficha(ruta)
                num = Numeracion(capitulo=str(i), archivo=f"{archivo}.html", refs=refs, registro=registro)
                p.contenido = render_cuerpo(fuentes, _sin_titulo(lineas), p.scripts, textos=textos, num=num)
                p.titulo, p.lede = ficha.get("titulo", c["titulo"]), ficha.get("lede", "")
                p.titulo_pagina = f"{c['corto']} · {nombre}"
                p.resumen = ficha.get("resumen", c["resumen"])
            paginas.append(p)
    for p in paginas:
        if p.contenido:
            p.contenido = resolver_refs(p.contenido, refs, f"{p.archivo}.html")

    tabla = Pagina(slug="temario", archivo="temario", numero="", corto="Tabla de contenido",
                   titulo="Tabla de contenido", etapa="temario", marcar=False, n_portada="≡",
                   lede=t["lede_temario"], contenido=render_cuerpo(fuentes, temario_md(t)), descripcion=descripcion,
                   resumen="Cada capítulo con sus secciones y sus laboratorios.",
                   titulo_pagina=f"Tabla de contenido · {nombre}")
    todas = [tabla] + paginas
    aviso = f'<p class="aviso-curado" role="note">{e(t["aviso"])}</p>\n' if t.get("aviso") else ""
    if aviso:
        for p in todas:
            if p.contenido:
                p.contenido = aviso + p.contenido
    partes = [(p["numero"], p["nombre"]) for p in t["partes"]]
    escribir_assets(cfg, *datos_navegacion(todas, [["temario", "Tabla de contenido"]]
                                           + [[k, f"Parte {k} · {nom}"] for k, nom in partes]))
    etapas = bloque_etapa("temario", '<span class="pn">Empieza aquí</span> Tabla de contenido', [tabla], abierta=True)
    etapas += "".join(bloque_etapa(f"parte-{k}", f'<span class="pn">Parte {k}</span> {e(nom)}',
                                   [p for p in paginas if p.etapa == k], abierta=True, cuenta=str(k))
                      for k, nom in partes)
    ini = fuente / "inicio.html"
    inicio = ini.read_text(encoding="utf-8").rstrip("\n") if ini.exists() else inicio_html(t, len(caps), sum(not p.en_preparacion for p in paginas))
    inicio = aviso + inicio
    sitio.mkdir(parents=True, exist_ok=True)
    portada = portada_html(cfg, inicio, etapas, "", descripcion)
    if portada.count(GTM) < 2:
        raise SystemExit(f"index: falta Google Tag Manager {GTM}")
    escribir(sitio / "index.html", portada)
    hechas = 1
    for p in todas:
        if not p.en_preparacion:
            html = pagina_html(cfg, p)
            if html.count(GTM) < 2:   # analítica obligatoria en toda página (head y noscript)
                raise SystemExit(f"{p.archivo}: falta Google Tag Manager {GTM}")
            escribir(sitio / f"{p.archivo}.html", html)
            hechas += 1
        if 'class="ref falta"' in p.contenido:
            print(f"Aviso: {p.archivo} cita un id que no existe ([?id] en la página)")
    return hechas
