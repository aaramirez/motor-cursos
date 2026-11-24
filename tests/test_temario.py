"""Cursos definidos por temario.yml: validación, portada y tabla de contenido."""
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from motor.temario import generar, inicio_html, temario_md, validar  # noqa: E402

TEMARIO = {
    "slug": "prueba", "nombre": "Curso de prueba", "marca": "Curso <b>prueba</b>", "eyebrow": "Prueba",
    "prefijo": "prueba-", "descripcion": "Un curso para las pruebas.", "lede_temario": "Los capítulos.",
    "rotulo_patron": "El patrón",
    "partes": [
        {"numero": 1, "nombre": "Primera", "idea": "La idea de la parte.", "capitulos": [
            {"slug": "uno", "corto": "Uno", "titulo": "El capítulo uno", "resumen": "Resumen uno.",
             "secciones": ["Sección A", "Sección B"], "labs": ["Lab A"], "practicas": ["Práctica A"], "patron": "Patrón A"},
            {"slug": "dos", "corto": "Dos", "titulo": "El capítulo dos", "resumen": "Resumen dos.",
             "secciones": ["Sección C"]}]},
        {"numero": 2, "nombre": "Segunda", "capitulos": [
            {"slug": "tres", "corto": "Tres", "titulo": "El capítulo tres", "resumen": "Resumen tres.",
             "secciones": ["Sección D"]}]},
    ],
}


def test_validar_ok_y_errores():
    assert validar(TEMARIO) == []
    malo = {**TEMARIO, "prefijo": "", "partes": [{"numero": 1, "nombre": "X", "capitulos": [
        {"slug": "a", "corto": "A", "titulo": "A", "resumen": "r", "secciones": ["s"]},
        {"slug": "a", "corto": "A", "titulo": "A", "resumen": "r"}]}]}
    errores = validar(malo)
    assert "falta «prefijo»" in errores
    assert "capítulo a: falta «secciones»" in errores
    assert "slug de capítulo repetido: a" in errores


def test_temario_md_numera_y_cierra_con_patron():
    md = "\n".join(temario_md(TEMARIO))
    assert "### 01. El capítulo uno" in md and "### 03. El capítulo tres" in md
    assert "**El patrón:** Patrón A" in md
    assert "- Lab A" in md
    assert "**Prácticas**" in md and "- Práctica A" in md


def test_inicio_sin_archivo_cuenta_capitulos():
    html = inicio_html({**TEMARIO, "para_quien": "Para todos."}, 3)
    assert "los 3 capítulos" in html and "Para todos." in html and 'href="temario.html"' in html


def test_generar_portada_temario_y_gtm(tmp_path):
    fuente = tmp_path / "prueba-source"
    fuente.mkdir()
    (fuente / "temario.yml").write_text(yaml.safe_dump(TEMARIO, allow_unicode=True), encoding="utf-8")
    n = generar(fuente, tmp_path / "prueba")
    assert n == 2  # portada y temario: los capítulos están en preparación
    index = (tmp_path / "prueba" / "index.html").read_text(encoding="utf-8")
    temario = (tmp_path / "prueba" / "temario.html").read_text(encoding="utf-8")
    assert index.count("GTM-KX76XF8R") >= 2 and temario.count("GTM-KX76XF8R") >= 2
    assert "El capítulo tres" in index and 'href="temario.html"' in index
    assert "Sección D" in temario and "Laboratorios" in temario
    assert not (tmp_path / "prueba" / "01-uno.html").exists()


def test_capitulo_conserva_rotulos_de_sistema_en_comandos(tmp_path):
    fuente = tmp_path / "prueba-source"
    (fuente / "capitulos").mkdir(parents=True)
    (fuente / "temario.yml").write_text(yaml.safe_dump(TEMARIO, allow_unicode=True), encoding="utf-8")
    (fuente / "capitulos" / "01-uno.md").write_text(
        '---\ntitulo: "El capítulo uno"\n---\n\n# El capítulo uno\n\n## Sección A\n\n'
        "```\n# Windows\nipconfig\n\n# macOS y Linux\nip addr\n```\n", encoding="utf-8")
    generar(fuente, tmp_path / "prueba")
    html = (tmp_path / "prueba" / "01-uno.html").read_text(encoding="utf-8")
    assert 'role="tab"' in html and "macOS y Linux" in html


def test_caso_real_con_rotulo_generico(tmp_path):
    fuente = tmp_path / "prueba-source"
    (fuente / "capitulos").mkdir(parents=True)
    (fuente / "temario.yml").write_text(yaml.safe_dump(TEMARIO, allow_unicode=True), encoding="utf-8")
    (fuente / "capitulos" / "01-uno.md").write_text(
        '---\ntitulo: "Uno"\n---\n\n# Uno\n\n## Sección A\n\n:::caso-real\nUn caso.\n:::\n', encoding="utf-8")
    generar(fuente, tmp_path / "prueba")
    html = (tmp_path / "prueba" / "01-uno.html").read_text(encoding="utf-8")
    assert "Un caso real" in html and "Así lo hace un operador" not in html
