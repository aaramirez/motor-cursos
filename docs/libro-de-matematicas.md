# Cómo se escribe un libro de matemática con el motor

Los libros de matemática (Licenciatura, Maestría en Modelos Aleatorios y los que vengan) cumplen el contrato de todos los cursos (skill `cursos-visuales`) y agregan esta estructura.

## El libro

| Parte | Qué lleva |
|---|---|
| Portada (`index.html`) | Para quién es, qué se necesita saber antes, cómo usar el libro y la ruta por partes |
| Partes | Grupos de capítulos, por ejemplo «Parte 1 · Límites y continuidad». Son las etapas desplegables del motor |
| Capítulos | Con la estructura de abajo, numerados («Capítulo 03 de 12») |
| Notación | Apéndice con los símbolos del libro y su lectura en voz alta |
| Índice de enunciados | Página con todas las definiciones y resultados, por capítulo y con enlace (`motor.indice_enunciados`) |
| Bibliografía | Las fuentes, incluido el libro de origen si lo hay. El texto del libro de origen nunca se copia: se reescribe completo |

## Si el libro viene de bookdown

`scripts/importar_bookdown.py` convierte los `.Rmd` en un borrador por capítulo dentro de `referencias/importado/` (privado). Úsalo para ver qué temas cubre el original y en qué orden, y después escribe cada capítulo de nuevo con la estructura de abajo: más explicación, ejemplos, laboratorios y ejercicios, y con los errores del original corregidos.

## El capítulo

Cada capítulo sigue este orden. Las secciones `##` se pueden repetir: un capítulo largo tiene varias rondas de idea, enunciados y ejemplos.

1. **La idea**: una pregunta o un problema que motiva el tema, la intuición en palabras y una figura o un laboratorio. Todavía no hay definiciones formales.
2. **Definiciones**: `:::definicion`, cada una seguida de un ejemplo y de un contraejemplo.
3. **Resultados**: `:::teorema`, `:::proposicion`, `:::lema` y `:::corolario`, cada uno con su `:::demostracion`. Antes de la demostración formal va la idea de la demostración en una o dos frases.
4. **Ejemplos y laboratorio**: `:::ejemplo` resueltos paso a paso, y un `:::lab` donde el lector cambia un parámetro y ve la consecuencia.
5. **En la práctica**: dónde aparece el tema fuera del aula (física, finanzas, datos, IA), con un recuadro `:::en-la-practica`.
6. **Ejercicios**: de 5 a 12 `:::ejercicio` con `nivel="1|2|3"`, cada uno con `:::pista` y `:::solucion` plegadas.
7. **Con la IA**: uno o dos `:::prompt` para estudiar con un asistente (otro ejemplo, revisar mi demostración, ejercicios parecidos).
8. **Para investigar**: `:::investiga`, como en todos los cursos.
9. **Pruébate**: `:::pruebate` con preguntas rápidas de repaso.

## Sintaxis

### Fórmulas

```
En línea: la función $f(x)=x^2$ es continua.
Un dólar que no es fórmula se escribe \$5.

En bloque, sin número:

$$
\int_0^1 x^2\,dx = \frac13
$$

En bloque, con número y etiqueta para citarla:

$$
x^3 - x - 1 = 0
$$ {#eq:cubica}
```

- KaTeX las dibuja en el navegador. Solo se carga en las páginas que tienen fórmulas.
- La fórmula en línea va pegada a los `$` por dentro: `$ x $` no es fórmula.
- Las fórmulas largas se deslizan dentro de su caja en el celular, sin mover la página.
- Lista de comandos que KaTeX entiende: https://katex.org/docs/supported.html

### Enunciados

```
:::teorema id="bolzano" nombre="Bolzano"
Si $f$ es continua en $[a,b]$ y $f(a)f(b)<0$, existe $c$ con $f(c)=0$.
:::

:::demostracion de="bolzano"
Por bisección…
:::
```

- Tipos: `definicion`, `teorema`, `lema`, `proposicion`, `corolario`, `ejemplo` y `observacion`. Comparten un contador por capítulo: Definición 3.1, Teorema 3.2, Ejemplo 3.3.
- `id` permite citarlo y `nombre` aparece entre paréntesis. Los dos son opcionales.
- `:::demostracion` sale plegada. `de="id"` muestra a qué enunciado pertenece y `abierta="sí"` la deja abierta.

### Ejercicios

```
:::ejercicio id="ej-raiz" nivel="2"
Encuentra un intervalo de longitud $1/4$ que contenga la raíz.
:::

:::pista
Evalúa en $1{,}25$.
:::

:::solucion
La raíz está en $[1{,}25;\ 1{,}5]$.
:::
```

Los ejercicios llevan su propio contador (Ejercicio 3.1). La dificultad sale con estrellas.

### Referencias cruzadas

`[@bolzano]` se convierte en «Teorema 3.2», con enlace, y `[@eq:cubica]` en «(3.1)». Una referencia que no existe aparece como `[?id]` para que se note al revisar.

Entre capítulos, el generador numera todos los capítulos con una `motor.Numeracion` por capítulo que comparte `refs` y `registro`, y después resuelve cada página:

```python
refs, registro, paginas = {}, [], []
for cap in capitulos:
    num = motor.Numeracion(capitulo=cap.numero, archivo=cap.archivo, refs=refs, registro=registro)
    paginas.append((cap, motor.render_cuerpo(fuentes, motor.cuerpo(cap.ruta), scripts, textos, num=num)))
for cap, html in paginas:
    html = motor.resolver_refs(html, refs, cap.archivo)
indice = motor.indice_enunciados(registro)
```

### Prompt para la IA

```
:::prompt
Otro ejemplo
Explícame el teorema de Bolzano con una función distinta y muéstrame qué falla si no es continua.
:::
```

La primera línea es el título y el resto es el texto que se copia con el botón «Copiar».

### Fórmulas dentro de un laboratorio

Un laboratorio que escribe fórmulas nuevas les pone la clase `math` (o `math-display`) y llama a `Lab.renderMath(contenedor)`.
