"""Importa un libro bookdown a borradores en el Markdown del motor.

Uso: python scripts/importar_bookdown.py <carpeta-con-los-Rmd> <destino>

El destino debe ser la carpeta privada referencias/ del curso (por ejemplo
../medida-source/referencias/importado): el borrador conserva el texto del libro de origen,
que no se publica. Escribe un NN-slug.md por capítulo e INFORME.md con lo que encontró.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from motor.bookdown import importar, informe_md  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    origen, destino = Path(argv[0]), Path(argv[1])
    if "referencias" not in destino.parts:
        print("El destino debe estar dentro de una carpeta referencias/ (privada y sin versionar).")
        return 2
    inf = importar(origen, destino)
    texto = informe_md(inf)
    (destino / "INFORME.md").write_text(texto, encoding="utf-8")
    print(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
