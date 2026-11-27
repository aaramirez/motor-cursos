import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import motor  # noqa: E402


def curso(tmp_path, **cambios):
    datos = dict(salida=tmp_path, nombre="Curso X", marca="Curso <b>X</b>", eyebrow="Ojo", pie="<span>Pie</span>",
                 prefijo="x-")
    datos.update(cambios)
    return motor.Curso(**datos)


def test_markdown_basico_y_codigo_con_pestanas():
    html = motor.md_a_html("Hola **mundo**.\n\n```\n# Windows\nipconfig\n# macOS y Linux\nifconfig\n```")
    assert "<p>Hola <b>mundo</b>.</p>" in html
    assert 'data-so="win">Windows</button>' in html and 'data-so="mac linux">macOS y Linux</button>' in html
    assert html.count('class="copiar"') == 2


def test_bloques_practica_e_investiga_usan_la_unidad_del_curso(tmp_path):
    f = motor.Fuentes(figuras=tmp_path, labs=tmp_path)
    lineas = ["## Uno", ':::practica donde="navegador"', "Mira", "Abre la página.", ":::",
              ":::investiga", "- ¿Qué es un GHz?", ":::"]
    html = motor.render_cuerpo(f, lineas, [], motor.Textos(unidad="módulo"))
    assert '<span class="tag">En el navegador</span><h3>Mira</h3>' in html
    assert "no se responden en el módulo" in html


def test_pagina_con_la_identidad_del_curso_y_gtm(tmp_path):
    p = motor.Pagina(slug="uno", archivo="01-uno", numero="01", corto="Uno", titulo="Uno largo",
                     contenido="<section>X</section>", rotulo="MÓDULO 01 DE 2", scripts=["<script>a()</script>"])
    html = motor.pagina_html(curso(tmp_path, meta_extra='<meta name="m" content="1">'), p)
    assert "<title>Uno · Curso X</title>\n<meta name=\"m\" content=\"1\">\n<meta name=\"description\"" in html
    assert '<a class="brand" href="index.html">Curso <b>X</b></a><span class="eyebrow">Ojo</span>' in html
    assert '<header class="page-head"><span class="num">MÓDULO 01 DE 2</span><h1>Uno largo</h1></header>' in html
    assert 'id="got"' in html and "<footer>" + motor.pie_comun() + "</footer>" in html and "<span>Pie</span>" not in html
    assert html.index('src="assets/lab.js"') < html.index("<script>a()</script>")
    assert "GTM-KX76XF8R" in html.split("</head>")[0] and "ns.html?id=GTM-KX76XF8R" in html


def test_pagina_sin_casilla_ni_rotulo(tmp_path):
    p = motor.Pagina(slug="r", archivo="r", numero="", corto="R", titulo="R", marcar=False)
    html = motor.pagina_html(curso(tmp_path), p)
    assert 'id="got"' not in html and '<span class="num">' not in html


def test_tarjetas_y_etapa_de_portada():
    m = motor.Pagina(slug="uno", archivo="01-uno", numero="01", corto="Uno", titulo="Uno largo", tarjeta="Uno",
                     resumen="Res.")
    extra = motor.Pagina(slug="r", archivo="recursos", numero="", corto="R", titulo="Recursos", n_portada="+")
    html = motor.bloque_etapa("etapa-1", "Bases", [m, extra], abierta=True, cuenta="1")
    assert '<details class="stage" id="etapa-1" open>' in html and 'data-etapa-cuenta="1"' in html
    assert '<a class="mod" data-id="uno" href="01-uno.html"><span class="n">01</span><b>Uno</b><p>Res.</p></a>' in html
    assert '<a class="mod" href="recursos.html"><span class="n">+</span>' in html


def test_assets_con_datos_del_curso_y_css_propio(tmp_path):
    cfg = curso(tmp_path, extra_css=".propio{color:red}")
    p = motor.Pagina(slug="uno", archivo="01-uno", numero="01", corto="Uno", titulo="Uno", etapa=1)
    motor.escribir_assets(cfg, *motor.datos_navegacion([p], [[1, "Etapa 1 · Bases"]]))
    js = (tmp_path / "assets" / "lab.js").read_text(encoding="utf-8")
    assert 'const CURSO={"prefijo": "x-"};' in js
    assert 'const PAGES=[["index", "index.html", "", "Inicio", 0, 0], ["uno", "01-uno.html", "01", "Uno", 0, 1]];' in js
    assert 'const ETAPAS=[[1, "Etapa 1 · Bases"]];' in js and "PREF+'so'" in js
    css = (tmp_path / "assets" / "style.css").read_text(encoding="utf-8")
    assert css.rstrip().endswith(".propio{color:red}") and ".practica" in css


def test_separar_scripts_de_html_a_mano():
    html, scripts = motor.separar_scripts("<section>A</section>\n<script>\nf()\n</script>")
    assert html == "<section>A</section>" and scripts == ["<script>\nf()\n</script>"]


def test_para_saber_mas_no_anida_enlaces_de_rfc(tmp_path):
    f = motor.Fuentes(figuras=tmp_path, labs=tmp_path)
    html = motor.directiva(f, "para-saber-mas", {}, "- [RFC 5176: CoA](https://www.rfc-editor.org/rfc/rfc5176) · norma",
                           [])
    assert html.count("<a ") == 1 and "RFC 5176: CoA" in html


def test_titulos_de_figura_y_encabezados_conservan_mayusculas_y_minusculas():
    # f(x) y F(x), dBm y DBM, ŷ e Ŷ significan cosas distintas: el CSS no puede pasarlos a mayúsculas
    import re
    css = (Path(motor.__file__).parent / "assets" / "curso.css").read_text(encoding="utf-8")
    for selector in (r"\.cap\{", r"\nth\{"):
        regla = re.search(selector + r"[^}]*\}", css).group(0)
        assert "uppercase" not in regla, regla


def test_enlace_al_indice_de_todos_los_cursos(tmp_path):
    import motor
    cfg = motor.Curso(salida=tmp_path, nombre="N", marca="M", eyebrow="E", pie="P", prefijo="x-")
    p = motor.Pagina(slug="a", archivo="a", numero="01", corto="A", titulo="A")
    for html in (motor.pagina_html(cfg, p), motor.portada_html(cfg, "", "", "", "d")):
        assert 'class="al-sitio" href="https://aaramirez.github.io/"' in html and "{{SITIO}}" not in html


def test_codigo_en_practicas_corta_la_linea():
    css = (Path(__file__).resolve().parent.parent / "motor" / "assets" / "curso.css").read_text(encoding="utf-8")
    assert ".practica code" in css and ".investiga code" in css and ".practica a" in css


def test_lista_numerada_sigue_despues_de_un_bloque():
    from motor.md import md_a_html
    html = md_a_html("1. Uno\n2. Dos\n\n```\nls\n```\n\n3. Tres\n4. Cuatro")
    assert 'start="3"' in html and "counter-reset:st 2" in html


def test_boton_copiar_no_tapa_el_codigo_en_celular():
    css = (Path(__file__).resolve().parent.parent / "motor" / "assets" / "curso.css").read_text(encoding="utf-8")
    assert ".code-copia .copiar-todo{position:static" in css


def test_titulo_dentro_de_bloque_de_codigo_no_parte_la_seccion():
    from motor.bloques import Fuentes, render_cuerpo
    f = Fuentes(figuras=Path("."), labs=Path("."))
    html = render_cuerpo(f, ["## Uno", "", "```", "## no es titulo", "texto", "```"])
    assert html.count("<section>") == 1 and "## no es titulo" in html


def test_codigo_sin_ligaduras():
    """La fuente del código no junta «!=» en «≠» ni «<|» en un triángulo: se ve lo que se escribe."""
    css = (Path(__file__).resolve().parent.parent / "motor" / "assets" / "curso.css").read_text(encoding="utf-8")
    assert "code,pre,.mono{font-variant-ligatures:none}" in css
    # Las reglas que usan el atajo «font:» reinician las ligaduras: hay que apagarlas otra vez.
    assert ".fig .t-mono{font-family:var(--f-mono);font-variant-ligatures:none}" in css
    regla_cmd = css[css.index(".cmd-c{"):].split("}", 1)[0]
    assert "font-variant-ligatures:none" in regla_cmd


def test_codigo_largo_en_recuadros_corta_la_linea():
    """Un código largo dentro de «Imagínalo así», «Un caso real» o «En la práctica» no desborda el celular."""
    css = (Path(__file__).resolve().parent.parent / "motor" / "assets" / "curso.css").read_text(encoding="utf-8")
    regla = next(l for l in css.splitlines() if l.startswith(".prose code,") and "overflow-wrap:anywhere" in l)
    for sel in (".analogia code", ".caso code", ".ml code"):
        assert sel in regla


def test_enlace_automatico_y_cita():
    from motor.md import md_a_html
    html = md_a_html("Ver <https://example.com/a?b=1&c=2> ahora.")
    assert '<a href="https://example.com/a?b=1&amp;c=2" target="_blank" rel="noopener">https://example.com/a?b=1&amp;c=2</a>' in html
    cita = md_a_html("> Una frase citada\n> en dos líneas, con **énfasis**.")
    assert cita == "<blockquote><p>Una frase citada en dos líneas, con <b>énfasis</b>.</p></blockquote>"


def test_boton_copiar_va_sobre_el_bloque_en_todo_ancho():
    """El botón «Copiar» de un script largo no tapa la primera línea ni en escritorio."""
    css = (Path(__file__).resolve().parent.parent / "motor" / "assets" / "curso.css").read_text(encoding="utf-8")
    assert "position:absolute;top:8px;right:8px" not in css.split(".code-copia .copiar-todo", 1)[1].split("}", 1)[0]


def test_script_largo_con_numeros_de_linea_y_scroll():
    """Un script sin rótulos de sistema: cada línea numerada, alto de 20 líneas con scroll y botón «Copiar»."""
    from motor.md import md_a_html
    codigo = "\n".join(f"x{i} = {i}  # <b>" for i in range(30))
    html = md_a_html(f"```python\n{codigo}\n```")
    assert 'class="code-copia code-lineas"' in html
    assert html.count('<span class="ln">') == 30
    assert '<span class="ln">x0 = 0  # &lt;b&gt;</span>\n<span class="ln">x1 = 1' in html
    assert 'class="copiar copiar-todo"' in html
    css = (Path(__file__).resolve().parent.parent / "motor" / "assets" / "curso.css").read_text(encoding="utf-8")
    assert 'class="ver-todo"' in html and 'aria-expanded="false"' in html
    assert ".code-lineas pre{" in css and "overflow-y:auto" in css.split(".code-lineas pre{", 1)[1].split("}", 1)[0]
    assert "counter-increment:ln" in css and ".code-lineas.abierto pre{max-height:none" in css
    js = (Path(__file__).resolve().parent.parent / "motor" / "assets" / "lab.js").read_text(encoding="utf-8")
    assert ".ver-todo" in js
    corto = md_a_html("```python\nx = 1\n```")
    assert "ver-todo" not in corto
    assert "user-select:none" in css.split(".code-lineas .ln::before", 1)[1].split("}", 1)[0]


def test_pie_comun_de_todas_las_paginas():
    pie = motor.pie_comun(2030)
    assert 'Generado, editado y curado por <a href="https://www.linkedin.com/in/alexander-ramirez-morales/"' in pie
    assert 'href="https://creativecommons.org/licenses/by-sa/4.0/deed.es"' in pie
    assert "CC BY-SA 4.0, Atribución/Reconocimiento-CompartirIgual 4.0 Internacional" in pie
    assert "© 2002–<span data-anio>2030</span> Alexander A. Ramírez M." in pie
    assert 'href="https://github.com/aaramirez"' in pie and "new Date().getFullYear()" in pie
    assert "Ramírez M.</a>.</span>" not in pie and "Código del sitio" not in pie and "Sitio publicado" not in pie
