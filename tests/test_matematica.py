"""Fórmulas, enunciados numerados, referencias cruzadas y bloques de los libros de matemática."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import motor  # noqa: E402


def fuentes(tmp_path):
    return motor.Fuentes(figuras=tmp_path, labs=tmp_path)


# ---------- Fórmulas ----------

def test_formula_en_linea_se_protege_del_markdown():
    html = motor.md_a_html(r"Si $a_1 * b_2 < c$ entonces **sí**.")
    assert r'<span class="math">a_1 * b_2 &lt; c</span>' in html and "<b>sí</b>" in html


def test_dolares_que_no_son_formulas():
    html = motor.md_a_html(r"Cuesta $5 y $10. Escapado: \$3. Código: `B$2:B$9`.")
    assert 'class="math"' not in html
    assert "Cuesta $5 y $10." in html and "Escapado: $3." in html and "<code>B$2:B$9</code>" in html


def test_formula_en_bloque_y_en_una_linea():
    html = motor.md_a_html("Antes.\n\n$$\n\\int_0^1 x\\,dx = \\tfrac12\n$$\n\nDespués $$e^{i\\pi}+1=0$$")
    assert '<div class="math-display">\\int_0^1 x\\,dx = \\tfrac12</div>' in html
    assert "<p>Después" in html


def test_codigo_con_dolares_no_cambia():
    html = motor.md_a_html("```\n$x = 1\necho $x\n```")
    assert 'class="math' not in html


# ---------- Enunciados numerados y referencias ----------

LINEAS = [
    "## Continuidad",
    ':::definicion id="continua" nombre="función continua"',
    "$f$ es continua en $a$ si $\\lim_{x\\to a} f(x) = f(a)$.",
    ":::",
    ':::teorema id="bolzano" nombre="Bolzano"',
    "Si $f$ es continua en $[a,b]$ y $f(a)f(b)<0$, existe $c$ con $f(c)=0$.",
    ":::",
    ':::demostracion de="bolzano"',
    "Por bisección.",
    ":::",
    "Por el [@bolzano] y la [@continua], la ecuación [@eq:cubica] tiene raíz.",
    "",
    "$$",
    "x^3 - x - 1 = 0",
    "$$ {#eq:cubica}",
    "",
    ':::ejercicio id="ej-raiz" nivel="2"',
    "Encuentra un intervalo de longitud $1/4$ que contenga la raíz.",
    ":::",
    ":::pista",
    "Evalúa en $1$ y en $2$.",
    ":::",
    ":::solucion",
    "$[1{,}25;\\ 1{,}5]$.",
    ":::",
]


def test_enunciados_numerados_por_capitulo():
    html = motor.render_cuerpo(fuentes(Path(".")), LINEAS, [], num=motor.Numeracion(capitulo="3", archivo="03-x"))
    assert '<div class="enunciado enunciado-definicion" id="continua">' in html
    assert "<b>Definición 3.1</b> <span class=\"nombre\">(función continua)</span>" in html
    assert "<b>Teorema 3.2</b> <span class=\"nombre\">(Bolzano)</span>" in html
    assert "<b>Ejercicio 3.1</b>" in html and 'aria-label="Dificultad 2 de 3"' in html
    assert '<div class="math-display" id="eq:cubica">x^3 - x - 1 = 0\\tag{3.1}</div>' in html


def test_demostracion_pista_y_solucion_plegables():
    html = motor.render_cuerpo(fuentes(Path(".")), LINEAS, [])
    assert '<details class="demostracion"><summary>Demostración · <a class="ref" href="#bolzano">Teorema 2</a>' in html
    assert '<p class="qed" aria-hidden="true">∎</p></details>' in html
    assert '<details class="pista"><summary>Pista</summary>' in html
    assert '<details class="solucion"><summary>Solución</summary>' in html


def test_referencias_en_la_misma_pagina_sin_numeracion_externa():
    html = motor.render_cuerpo(fuentes(Path(".")), LINEAS, [])
    assert '<a class="ref" href="#bolzano">Teorema 2</a>' in html
    assert '<a class="ref" href="#continua">Definición 1</a>' in html
    assert '<a class="ref" href="#eq:cubica">(1)</a>' in html
    assert "\x02" not in html and "\x03" not in html


def test_referencias_entre_capitulos():
    num2 = motor.Numeracion(capitulo="2", archivo="02-limites")
    num3 = motor.Numeracion(capitulo="3", archivo="03-continuidad", refs=num2.refs, registro=num2.registro)
    h2 = motor.render_cuerpo(fuentes(Path(".")), ['Vimos el [@bolzano].'], [], num=num2)
    h3 = motor.render_cuerpo(fuentes(Path(".")), LINEAS, [], num=num3)
    h2 = motor.resolver_refs(h2, num2.refs, "02-limites")
    h3 = motor.resolver_refs(h3, num3.refs, "03-continuidad")
    assert '<a class="ref" href="03-continuidad.html#bolzano">Teorema 3.2</a>' in h2
    assert '<a class="ref" href="#bolzano">Teorema 3.2</a>' in h3
    titulos = [(r["etiqueta"], r["nombre"], r["archivo"]) for r in num3.registro]
    assert ("Definición 3.1", "función continua", "03-continuidad") in titulos
    assert ("Teorema 3.2", "Bolzano", "03-continuidad") in titulos


def test_referencia_desconocida_queda_marcada():
    html = motor.render_cuerpo(fuentes(Path(".")), ["Ver [@nada]."], [])
    assert '<span class="ref falta">[?nada]</span>' in html


def test_indice_de_enunciados():
    num = motor.Numeracion(capitulo="3", archivo="03-x")
    motor.render_cuerpo(fuentes(Path(".")), LINEAS, [], num=num)
    html = motor.indice_enunciados(num.registro)
    assert '<a href="03-x.html#bolzano"><b>Teorema 3.2</b> Bolzano</a>' in html


# ---------- Prompt para la IA ----------

def test_prompt_con_boton_copiar():
    html = motor.render_cuerpo(fuentes(Path(".")), [":::prompt", "Otro ejemplo", "Explícame el <teorema> con $f(x)=x^2$.",
                                                   ":::"], [])
    assert '<span class="tag">Prompt para la IA</span><h3>Otro ejemplo</h3>' in html
    assert "<pre><code>Explícame el &lt;teorema&gt; con $f(x)=x^2$.</code></pre>" in html
    assert 'class="copiar copiar-todo"' in html


# ---------- Página ----------

def curso(tmp_path):
    return motor.Curso(salida=tmp_path, nombre="C", marca="C", eyebrow="", pie="", prefijo="c-")


def test_katex_solo_en_paginas_con_formulas(tmp_path):
    con = motor.Pagina(slug="a", archivo="a", numero="1", corto="A", titulo="A",
                       contenido='<p><span class="math">x</span></p>')
    sin = motor.Pagina(slug="b", archivo="b", numero="2", corto="B", titulo="B", contenido="<p>x</p>")
    h_con, h_sin = motor.pagina_html(curso(tmp_path), con), motor.pagina_html(curso(tmp_path), sin)
    assert "katex.min.js" in h_con and "katex.min.css" in h_con and "katex" not in h_sin.lower()
    cabeza = h_con.split("</head>")[0]
    assert cabeza.index("GTM-KX76XF8R") < cabeza.index("katex.min.css") < cabeza.index("assets/style.css")
    assert 'integrity="sha384-' in cabeza


def test_lab_js_dibuja_las_formulas():
    js = (Path(motor.__file__).parent / "assets" / "lab.js").read_text(encoding="utf-8")
    assert "function renderMath(" in js and "katex.render(" in js
