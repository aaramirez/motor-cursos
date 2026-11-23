"""Crea un curso nuevo a partir de su temario.yml: la fuente privada y el sitio público, listos para publicar.

Uso:
  python scripts/nuevo_curso.py RUTA/temario.yml [--raiz ..] [--github]

- Crea <raiz>/<slug>-source con temario.yml, generar.py, CLAUDE.md, README.md, curso.css y .gitignore
  (referencias/ local), y <raiz>/<slug> con el sitio generado, README.md y .nojekyll.
- Inicia git en los dos con el autor soyalexanderramirez@gmail.com y hace el primer commit.
- Con --github crea aaramirez/<slug>-source (privado) y aaramirez/<slug> (público), hace push y activa Pages.
No toca nada si <slug>-source o <slug> ya existen.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

MOTOR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(MOTOR))
from motor.temario import capitulos_de, generar, leer_temario  # noqa: E402

AUTOR = ("Alexander A. Ramírez M.", "soyalexanderramirez@gmail.com")

GENERAR = '''"""Genera el sitio público del curso (../{slug}) con el motor de cursos. Todo sale de temario.yml.

Uso: python generar.py   (escribe en ../{slug}, o donde diga la variable CURSO_SITIO)
"""
import os
import sys
from pathlib import Path

FUENTE = Path(__file__).resolve().parent
sys.path.insert(0, os.environ.get("MOTOR_CURSOS", str(FUENTE.parent / "motor-cursos")))
from motor.temario import generar  # noqa: E402

if __name__ == "__main__":
    sitio = os.environ.get("CURSO_SITIO")
    print(f"{{generar(FUENTE, Path(sitio) if sitio else None)}} páginas generadas")
'''

CLAUDE = """# {slug}-source: instrucciones para Claude

Fuente privada del curso «{nombre}». El sitio público es `../{slug}` (https://aaramirez.github.io/{slug}/). Para cualquier trabajo del curso usa la skill `cursos-visuales`.

- **Qué se edita:** `temario.yml` (ficha y tabla de contenido completa), `capitulos/NN-slug.md`, `labs/`, `figuras/`, `curso.css` y, si se quiere una portada propia, `inicio.html`. Después corre `python generar.py`, que escribe en `../{slug}`. Nunca edites a mano `../{slug}/*.html` ni `../{slug}/assets/`.
- **Tabla de contenido:** `temario.yml` es la fuente de la portada y de `temario.html`. El número de cada capítulo sale de su orden; un capítulo sin archivo en `capitulos/` aparece «en preparación». Si cambias el orden, renombra los archivos de `capitulos/`.
- **Plan del área:** `../biblioteca-source/planes/` dice qué tema es de qué curso. Lo que es de otro curso se usa en una línea y se enlaza, no se repite.
- **Lineamientos:** los lineamientos de desarrollo se presentan como «algunos lineamientos de referencia», sin el nombre de la empresa y sin copiar su texto.
- **Fuentes de synergyvision:** se usan solo después de que el usuario apruebe el caso; los libros se reescriben por completo.
- **Visual e interactivo:** cada capítulo lleva laboratorios donde el lector cambia algo y ve la consecuencia.
- **Analítica (no se olvida):** toda página lleva Google Tag Manager `GTM-KX76XF8R`. Lo ponen las plantillas del motor y el generador se detiene si falta.
- **Commits:** autor `soyalexanderramirez@gmail.com`, sin líneas sobre el modelo. Commit y push aquí y en `../{slug}`. Al publicar capítulos, actualiza `biblioteca-source/catalogo.yml`.
- **Avance de los lectores:** el prefijo `{prefijo}` de `temario.yml` guarda el avance en el navegador. No lo cambies.
"""

README_FUENTE = """# {nombre} (fuente)

Fuente privada del curso visual e interactivo [{nombre}](https://aaramirez.github.io/{slug}/). Se genera con [motor-cursos](https://github.com/aaramirez/motor-cursos).

```
python generar.py        # escribe el sitio en ../{slug}
```

| Archivo o carpeta | Qué tiene |
|---|---|
| `temario.yml` | Ficha del curso y tabla de contenido: partes, capítulos, secciones, laboratorios |
| `capitulos/NN-slug.md` | Un capítulo por archivo: ficha entre `---` y el Markdown del motor |
| `labs/<id>.html` | Laboratorios interactivos (`:::lab id="…"`) |
| `figuras/<id>.svg` | Diagramas (`:::diagrama id="…"`) |
| `curso.css` | Estilos propios del curso |
"""

CSS = """/* Tabla de contenido: separa cada capítulo */
[data-page="temario"] .prose h3{margin-top:2rem;padding-top:1.4rem;border-top:1px solid var(--line)}
"""


def git(carpeta: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=carpeta, check=True, stdout=subprocess.DEVNULL)


def iniciar_repo(carpeta: Path, mensaje: str) -> None:
    git(carpeta, "init", "-q", "-b", "main")
    git(carpeta, "config", "user.name", AUTOR[0])
    git(carpeta, "config", "user.email", AUTOR[1])
    git(carpeta, "add", "-A")
    git(carpeta, "commit", "-q", "-m", mensaje)


def crear(temario: Path, raiz: Path, github: bool = False) -> tuple[Path, Path]:
    t = leer_temario(temario)
    slug = t["slug"]
    fuente, sitio = raiz / f"{slug}-source", raiz / slug
    for c in (fuente, sitio):
        if c.exists():
            raise SystemExit(f"{c} ya existe: no lo toco")
    fuente.mkdir(parents=True)
    shutil.copyfile(temario, fuente / "temario.yml")
    datos = {"slug": slug, "nombre": t["nombre"], "prefijo": t["prefijo"]}
    (fuente / "generar.py").write_text(GENERAR.format(**datos), encoding="utf-8")
    (fuente / "CLAUDE.md").write_text(CLAUDE.format(**datos), encoding="utf-8")
    (fuente / "README.md").write_text(README_FUENTE.format(**datos), encoding="utf-8")
    (fuente / "curso.css").write_text(CSS, encoding="utf-8")
    (fuente / ".gitignore").write_text("referencias/\n__pycache__/\n", encoding="utf-8")
    generar(fuente, sitio)
    filas = "\n".join(f"| {i:02d} | {c['titulo']} |" for i, c in enumerate(capitulos_de(t), 1))
    (sitio / "README.md").write_text(
        f"# {t['nombre']}\n\n{t['descripcion']}\n\n**Ver en línea:** https://aaramirez.github.io/{slug}/\n\n"
        "Este repositorio solo tiene el sitio generado. El curso está en preparación: la tabla de contenido ya está "
        f"publicada para revisión.\n\n| # | Capítulo |\n|---|---|\n{filas}\n", encoding="utf-8")
    (sitio / ".nojekyll").write_text("", encoding="utf-8")
    iniciar_repo(fuente, "Fuente del curso: tabla de contenido para revisión")
    iniciar_repo(sitio, "Portada y tabla de contenido para revisión")
    if github:
        for carpeta, vis in ((fuente, "--private"), (sitio, "--public")):
            subprocess.run(["gh", "repo", "create", f"aaramirez/{carpeta.name}", vis, "--source", ".", "--push"],
                           cwd=carpeta, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["gh", "api", "-X", "POST", f"repos/aaramirez/{slug}/pages", "-f", "source[branch]=main",
                        "-f", "source[path]=/"], check=True, stdout=subprocess.DEVNULL)
    return fuente, sitio


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("temario", type=Path)
    ap.add_argument("--raiz", type=Path, default=MOTOR.parent)
    ap.add_argument("--github", action="store_true")
    a = ap.parse_args()
    fuente, sitio = crear(a.temario.resolve(), a.raiz.resolve(), a.github)
    print(f"Creados {fuente} y {sitio}")


if __name__ == "__main__":
    main()
