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
