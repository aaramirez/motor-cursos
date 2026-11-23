# Motor de cursos

Lo que comparten los cursos visuales e interactivos: [Cómo funciona un telco](https://aaramirez.github.io/telco/), [Mate para ML](https://aaramirez.github.io/mate/) y los que vengan. Un cambio de formato se hace aquí una vez y llega a todos los cursos al regenerarlos.

## Qué trae

```
motor/md.py          Markdown mínimo: párrafos, listas, tablas, enlaces, énfasis, enlaces a los RFC, fórmulas
                     $…$ y $$…$$, referencias [@id] y bloques de código con pestañas por sistema operativo
                     y botón «Copiar» en cada línea
motor/bloques.py     Bloques ::: (analogia, caso-real, en-la-practica, diagrama, lab, pruebate,
                     para-saber-mas, practica, investiga; y para matemática: definicion, teorema, lema,
                     proposicion, corolario, ejemplo, observacion, demostracion, ejercicio, pista,
                     solucion, prompt) y el cuerpo de una página por secciones ##
motor/matematica.py  Numeración de enunciados, ejercicios y ecuaciones por capítulo, referencias cruzadas
                     entre capítulos e índice de enunciados
motor/bookdown.py    Importa un libro bookdown (.Rmd) a borradores en el Markdown del motor (scripts/importar_bookdown.py)
motor/sitio.py       Curso y Pagina, plantillas de página y portada, etapas desplegables, navegación;
                     KaTeX solo en las páginas con fórmulas
motor/plantillas/    pagina.html y portada.html (con Google Tag Manager GTM-KX76XF8R)
motor/assets/        curso.css y lab.js: se copian a cada curso como assets/style.css y assets/lab.js
docs/                libro-de-matematicas.md: estructura de un libro y de un capítulo de matemática
tests/               pytest
```

Para un libro de matemática, lee [docs/libro-de-matematicas.md](docs/libro-de-matematicas.md).

## Importar un libro bookdown

```bash
python scripts/importar_bookdown.py <carpeta-con-los-Rmd> ../<curso>-source/referencias/importado
```

Escribe un `NN-slug.md` por capítulo, con los entornos de bookdown convertidos en bloques del motor (`:::teorema id="…"`, `:::demostracion de="…"`), las referencias en `[@id]` y las ecuaciones con etiqueta, más un `INFORME.md` con lo que encontró. El borrador conserva el texto del libro de origen: solo sirve para estudiar qué cubre cada capítulo. Por eso el destino tiene que estar en `referencias/`, que no se versiona. El capítulo que se publica se reescribe completo.

## Cómo lo usa un curso

El curso se clona al lado de este repositorio (o se indica la ruta en la variable de entorno `MOTOR_CURSOS`) y su generador hace:

```python
import motor

cfg = motor.Curso(salida=..., nombre="Mate para ML", marca="Mate para <b>ML</b>", eyebrow="...",
                  pie="<span>...</span>", prefijo="mate-ml-", extra_css="...")
paginas = [motor.Pagina(slug="limites", archivo="06-limites", numero="06", corto="Límites", titulo="...",
                        contenido=motor.render_cuerpo(fuentes, lineas, scripts), etapa=3, scripts=scripts)]
motor.escribir_assets(cfg, *motor.datos_navegacion(paginas, [[3, "Etapa 3 · Cálculo"]]))
html = motor.pagina_html(cfg, paginas[0])
```

- `prefijo` separa las claves del avance guardado en el navegador de cada curso («telco-», «mate-ml-»).
- `extra_css` agrega los estilos propios del curso al final de `style.css`.
- Un contenido escrito a mano en HTML se publica tal cual: `motor.separar_scripts` saca sus `<script>` para ponerlos después de `lab.js`.

Generadores que lo usan: `telco-source/scripts/generar_curso.py` y `mate-source/generar.py` (cada curso: fuente privada `<curso>-source` → sitio público `<curso>`).

## Reglas que el motor ya cumple

- Google Tag Manager en todas las páginas.
- Prácticas con «Qué observar» y preguntas para investigar sin respuestas publicadas.
- Comandos con una pestaña por sistema operativo, la del lector elegida y recordada, y «Copiar» por línea.
- Ruta por etapas desplegable y plegable, avance por etapa, sin desborde a 390 px.

## Tests

```bash
python -m pytest tests -q
```

Antes de publicar un cambio, regenera los cursos y corre sus propias verificaciones (en telco, sus tests y `validar.py`).
