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
    assert 'id="got"' in html and "<footer><span>Pie</span></footer>" in html
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
    assert ".practica code" in css and ".investiga code" in css


def test_lista_numerada_sigue_despues_de_un_bloque():
    from motor.md import md_a_html
    html = md_a_html("1. Uno\n2. Dos\n\n```\nls\n```\n\n3. Tres\n4. Cuatro")
    assert 'start="3"' in html and "counter-reset:st 2" in html


def test_boton_copiar_no_tapa_el_codigo_en_celular():
    css = (Path(__file__).resolve().parent.parent / "motor" / "assets" / "curso.css").read_text(encoding="utf-8")
    assert ".code-copia .copiar-todo{position:static" in css
