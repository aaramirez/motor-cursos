"""Motor de cursos: lo que comparten los cursos visuales e interactivos (telco, mate y los que vengan).

- md: Markdown mínimo, bloques de código con pestañas por sistema operativo y botón «Copiar».
- bloques: bloques ::: (recuadros, diagramas, laboratorios, pruébate, prácticas, para investigar).
- matematica: enunciados y ecuaciones numerados, referencias cruzadas [@id] e índice de enunciados.
- sitio: plantillas de página y portada, navegación por etapas y los archivos compartidos style.css y lab.js.

Un cambio de formato se hace aquí una vez y llega a todos los cursos al regenerarlos.
"""
from .md import COPIAR, _bloque_codigo, _inline, _rfc, _tabla, e, md_a_html  # noqa: F401
from .matematica import ENUNCIADOS, Numeracion, indice_enunciados, numerar, resolver_refs  # noqa: F401
from .bloques import (Fuentes, Textos, cuerpo, directiva, render_cuerpo, separar_scripts,  # noqa: F401
                      sin_prologo)
from .sitio import (Curso, Pagina, bloque_etapa, cabecera, datos_navegacion, escribir,  # noqa: F401
                    escribir_assets, pagina_html, portada_html, tarjeta)
