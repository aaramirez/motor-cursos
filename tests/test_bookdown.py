from motor.bookdown import capitulos, convertir, importar, titulo_normal


def conv(texto):
    return "\n".join(convertir(texto.splitlines())[0])


def test_titulo_en_mayusculas():
    assert titulo_normal("CONSTRUYENDO UNA MEDIDA") == "Construyendo una medida"
    assert titulo_normal("INTEGRACIÓN EN $\\mathbb{R}^{n}$") == "Integración en $\\mathbb{R}^{n}$"
    assert titulo_normal("Prefacio {-}") == "Prefacio"


def test_capitulos_omite_sin_numero():
    caps = capitulos("# Prefacio {-}\ntexto\n# Vacío\n\n# UNO\n```{remark}\nr\n```\n```{r}\nx\n```\na\n"
                     "# Dos\nb\n# (APPENDIX) Apéndice {-}\n# Software\nc\n")
    assert [(c.numero, c.titulo) for c in caps] == [(1, "Uno"), (2, "Dos")]


def test_entornos_y_demostracion_unida():
    t = conv('```{theorem, label="bolzano", name="Bolzano"}\nSi $f$...\n```\n\n```{proof}\nPor bisección.\n```')
    assert ':::teorema id="bolzano" nombre="Bolzano"' in t
    assert ':::demostracion de="bolzano"' in t
    assert t.count(":::\n") + t.endswith(":::") >= 2


def test_demostracion_anidada_cierra_el_enunciado():
    t = conv("```{proposition}\nEnunciado.\n```{proof}\nPrueba.\n```\n")
    assert t.splitlines() == [":::proposicion", "Enunciado.", ":::", ":::demostracion", "Prueba.", ":::"]


def test_etiqueta_corta():
    assert ':::ejemplo id="ejemplo17"' in conv("```{example, ejemplo17}\nx\n```")
    assert ':::ejemplo id="ejemplo18"' in conv('```{example, label="ejemplo18"}\nx\n```')


def test_referencias_y_citas():
    t = conv("Por el ejemplo \\@ref(exm:ejemplo17) y (\\@ref(eq:cubica)), ver [@xie2015; @rudin].")
    assert "[@ejemplo17]" in t and "[@eq:cubica]" in t and "[cita: xie2015, rudin]" in t


def test_display_en_parrafo():
    t = conv("El límite es $$\\limsup x_n$$ y sigue.")
    assert t.splitlines() == ["El límite es", "", "$$", "\\limsup x_n", "$$", "", "y sigue."]


def test_ecuacion_con_etiqueta_multilinea():
    t = conv("$$\nx^2 = 1 (\\#eq:uno)\n$$")
    assert t.splitlines() == ["$$", "x^2 = 1", "$$ {#eq:uno}"]


def test_chunk_r_marcado():
    t = conv("```{r grafica, echo=FALSE}\nplot(1:10)\n```")
    assert t.startswith("<!-- R: grafica, echo=FALSE -->") and "```r\nplot(1:10)\n```" in t


def test_importar_escribe_capitulos_e_informe(tmp_path):
    origen = tmp_path / "libro"
    origen.mkdir()
    (origen / "index.Rmd").write_text("# Prefacio {-}\nhola\n", encoding="utf-8")
    (origen / "010-a.Rmd").write_text("# MEDIDA\n\n```{definition, label=\"m\"}\nUna medida.\n```\n"
                                      "Ver \\@ref(def:m) y \\@ref(thm:falta).\n", encoding="utf-8")
    inf = importar(origen, tmp_path / "referencias" / "imp")
    assert [c[0] for c in inf.capitulos] == ["01-medida.md"]
    assert inf.sin_destino == ["falta"]
    md = (tmp_path / "referencias" / "imp" / "01-medida.md").read_text(encoding="utf-8")
    assert ':::definicion id="m"' in md and "[@m]" in md


def test_sangria_dentro_de_un_entorno():
    assert conv("```{definition}\n    Una medida es...\n```").splitlines() == [":::definicion", "Una medida es...", ":::"]
