"""Importa un libro bookdown (.Rmd) a borradores en el Markdown del motor, un archivo por capítulo.

El borrador es material de trabajo: sirve para estudiar el libro de origen y planificar la reescritura.
Su texto no se publica (va a referencias/, sin versionar); el capítulo publicado se escribe de nuevo.

Qué convierte:
- Capítulos «# Título» (los «{-}» sin número, el prefacio y los apéndices de software se omiten).
- Entornos ```{definition}, {theorem, label="x", name="y"}, {proof}, … → bloques :::definicion id="x" nombre="y".
  Una demostración se une al enunciado anterior con de="id". Un entorno que se abre sin cerrar el
  anterior (frecuente con proof) cierra el anterior.
- Referencias \\@ref(thm:x) → [@x]; ecuaciones (\\#eq:x) → $$ … $$ {#eq:x}; citas [@clave] → [cita: clave].
- $$…$$ en medio de un párrafo → bloque propio.
- Chunks de R → bloque ```r con la marca «<!-- R: … -->» para decidir si se pasa a Python o a un laboratorio.
"""
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

ENTORNOS = {"definition": "definicion", "theorem": "teorema", "lemma": "lema", "proposition": "proposicion",
            "corollary": "corolario", "example": "ejemplo", "remark": "observacion", "exercise": "ejercicio",
            "proof": "demostracion", "solution": "solucion", "conjecture": "observacion", "hypothesis": "observacion"}
_ABRE = re.compile(r"^```\{(\w+)\s*(?:[ ,]\s*(.*))?\}\s*$")
_REF = re.compile(r"\\@ref\((?:thm|lem|def|cor|prp|exm|exr|rem|cnj|hyp|eq|fig|tab)?:?([\w:.-]+)\)")
_REF_EQ = re.compile(r"\\@ref\(eq:([\w.-]+)\)")
_CITA = re.compile(r"\[(-?@[\w:.-]+(?:\s*;\s*-?@[\w:.-]+)*)\]")
_EQ_ETIQUETA = re.compile(r"\s*\(\\#eq:([\w.-]+)\)")
_OMITIR = re.compile(r"^\\(mainmatter|frontmatter|backmatter|appendix)\s*$")


@dataclass
class Capitulo:
    numero: int
    titulo: str
    lineas: list = field(default_factory=list)

    @property
    def slug(self) -> str:
        return slugify(self.titulo)


@dataclass
class Informe:
    capitulos: list = field(default_factory=list)       # (archivo, título, {tipo: n}, chunks R)
    sin_destino: list = field(default_factory=list)     # referencias [@id] sin enunciado con ese id


def slugify(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"\$[^$]*\$", "", t)
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:40] or "capitulo"


def titulo_normal(t: str) -> str:
    """«CONSTRUYENDO UNA MEDIDA» → «Construyendo una medida» (deja las fórmulas como están)."""
    t = re.sub(r"\s*\{[-.#][^}]*\}\s*$", "", t).strip()
    partes = re.split(r"(\$[^$]*\$)", t)
    letras = "".join(p for p in partes if not p.startswith("$"))
    if letras.upper() == letras and any(c.isalpha() for c in letras):
        t = "".join(p if p.startswith("$") else p.lower() for p in partes)
        t = t[0].upper() + t[1:] if t else t
    return t


def _atributos(resto: str) -> tuple[str, str]:
    """label y name de «label="x", name="y"», «x» o «x, name="y"»."""
    resto = (resto or "").strip()
    label = re.search(r'label\s*=\s*["\']([^"\']+)', resto)
    name = re.search(r'name\s*=\s*["\']([^"\']+)', resto)
    if label:
        id_ = label.group(1)
    else:
        primero = resto.split(",")[0].strip()
        id_ = primero if re.fullmatch(r"[\w:.-]+", primero or "-") and "=" not in primero else ""
    return id_, name.group(1) if name else ""


def _display_aparte(linea: str) -> list[str]:
    """Un párrafo con $$…$$ adentro: cada fórmula en bloque va en su propio grupo de líneas."""
    if "$$" not in linea or linea.strip() == "$$":
        return [linea]
    trozos = linea.split("$$")
    if len(trozos) % 2 == 0:          # $$ que abre y cierra en otra línea: se deja como está
        return [linea]
    salida = []
    for i, t in enumerate(trozos):
        if i % 2 == 0:
            if t.strip():
                salida.append(t.strip())
        else:
            m = _EQ_ETIQUETA.search(t)
            tex = _EQ_ETIQUETA.sub("", t).strip()
            salida += ["", "$$", tex, "$$" + (f" {{#eq:{m.group(1)}}}" if m else ""), ""]
    return salida


def _ecuaciones_multilinea(lineas: list[str]) -> list[str]:
    """«$$ … (\\#eq:x) … $$» repartida en varias líneas → etiqueta {#eq:x} tras el cierre."""
    salida, dentro, etiqueta = [], False, ""
    for l in lineas:
        if l.strip() == "$$" or (l.strip().startswith("$$") and l.strip().count("$$") == 1):
            if not dentro:
                dentro, etiqueta = True, ""
                salida += ["$$", l.strip()[2:]] if l.strip() != "$$" else ["$$"]
                continue
            dentro = False
            salida.append("$$" + (f" {{#eq:{etiqueta}}}" if etiqueta else ""))
            continue
        if dentro and l.strip().endswith("$$") and l.strip().count("$$") == 1:
            m = _EQ_ETIQUETA.search(l)
            etiqueta = m.group(1) if m else etiqueta
            salida.append(_EQ_ETIQUETA.sub("", l.strip()[:-2]))
            salida.append("$$" + (f" {{#eq:{etiqueta}}}" if etiqueta else ""))
            dentro = False
            continue
        if dentro:
            m = _EQ_ETIQUETA.search(l)
            if m:
                etiqueta = m.group(1)
                l = _EQ_ETIQUETA.sub("", l)
        salida.append(l)
    return salida


def _inline(l: str) -> str:
    l = _CITA.sub(lambda m: "[cita: " + ", ".join(c.strip().lstrip("-@") for c in m.group(1).split(";")) + "]", l)
    l = _REF_EQ.sub(lambda m: f"[@eq:{m.group(1)}]", l)
    l = _REF.sub(lambda m: f"[@{m.group(1)}]", l)
    return l


def capitulos(texto: str) -> list[Capitulo]:
    """Separa un libro (los .Rmd ya concatenados) en capítulos numerados."""
    caps, actual, en_codigo, apendice = [], None, False, False
    for l in texto.splitlines():
        if _ABRE.match(l.strip()) or (l.startswith("```") and l.strip() != "```"):
            en_codigo = True
        elif l.strip() == "```":
            en_codigo = False
        if not en_codigo and re.match(r"^# ", l):
            titulo = l[2:].strip()
            apendice = apendice or "(APPENDIX)" in titulo
            if apendice or "{-}" in titulo or "{.unnumbered}" in titulo:
                actual = None
                continue
            actual = Capitulo(0, titulo_normal(titulo))
            caps.append(actual)
            continue
        if actual is not None:
            actual.lineas.append(l)
    caps = [c for c in caps if "".join(c.lineas).strip()]
    for n, c in enumerate(caps, 1):
        c.numero = n
    return caps


def convertir(lineas: list[str]) -> tuple[list[str], dict, int]:
    """Cuerpo de un capítulo en Markdown del motor; devuelve también la cuenta por tipo y los chunks de R."""
    salida, cuenta, chunks_r = [], {}, 0
    abierto, ultimo_id, i = None, "", 0
    lineas = _ecuaciones_multilinea(lineas)
    while i < len(lineas):
        l = lineas[i].rstrip()
        m = _ABRE.match(l.strip())
        if m and m.group(1) == "r":
            fin = i + 1
            while fin < len(lineas) and not lineas[fin].startswith("```"):
                fin += 1
            chunks_r += 1
            if abierto:
                salida.append(":::")
                abierto = None
            salida += [f"<!-- R: {m.group(2) or ''} -->", "```r", *lineas[i + 1:fin], "```"]
            i = fin + 1
            continue
        if m and m.group(1) in ENTORNOS:
            if abierto:
                salida.append(":::")
            tipo = ENTORNOS[m.group(1)]
            id_, nombre = _atributos(m.group(2))
            attrs = ""
            if tipo == "demostracion" and ultimo_id:
                attrs = f' de="{ultimo_id}"'
            if id_ and tipo not in ("demostracion", "solucion"):
                attrs += f' id="{id_}"'
                ultimo_id = id_
            elif tipo not in ("demostracion", "solucion"):
                ultimo_id = ""
            if nombre:
                attrs += f' nombre="{nombre}"'
            cuenta[tipo] = cuenta.get(tipo, 0) + 1
            salida.append(f":::{tipo}{attrs}")
            abierto = tipo
            i += 1
            continue
        if m:                              # otro entorno (block2, flushright…): se omite con su contenido
            fin = i + 1
            while fin < len(lineas) and not lineas[fin].startswith("```"):
                fin += 1
            i = fin + 1
            continue
        if l.strip() == "```" and abierto:
            salida.append(":::")
            abierto = None
            i += 1
            continue
        if _OMITIR.match(l.strip()) or "include_graphics" in l:
            i += 1
            continue
        if l.startswith("## ") or l.startswith("### "):
            l = l.split(" ", 1)[0] + " " + titulo_normal(l.split(" ", 1)[1])
            if abierto:
                salida.append(":::")
                abierto = None
        l = l.replace("\t", "    ")
        if abierto:                        # dentro de un entorno, la sangría haría un bloque de código
            l = l.lstrip()
        for parte in _display_aparte(_inline(l)):
            salida.append(parte)
        i += 1
    if abierto:
        salida.append(":::")
    texto = re.sub(r"\n{3,}", "\n\n", "\n".join(salida)).strip("\n")
    return texto.splitlines(), cuenta, chunks_r


def importar(carpeta: Path, destino: Path) -> Informe:
    """Lee _bookdown.yml (rmd_files) o los .Rmd por orden de nombre y escribe NN-slug.md en destino."""
    rutas = sorted(p for p in carpeta.glob("*.Rmd") if p.name != "index.Rmd")
    yml = carpeta / "_bookdown.yml"
    if yml.exists() and "rmd_files" in (y := yml.read_text(encoding="utf-8")):
        nombres = re.findall(r'["\']?([\w.-]+\.Rmd)', y.split("rmd_files", 1)[1])
        rutas = [carpeta / n for n in nombres if n != "index.Rmd" and (carpeta / n).exists()]
    texto = "\n".join(r.read_text(encoding="utf-8") for r in rutas)
    destino.mkdir(parents=True, exist_ok=True)
    informe, ids, refs = Informe(), set(), set()
    origen = carpeta.parent.name if carpeta.name == "bookdown" else carpeta.name
    for cap in capitulos(texto):
        cuerpo, cuenta, chunks = convertir(cap.lineas)
        archivo = f"{cap.numero:02d}-{cap.slug}.md"
        cab = ["---", f'titulo: "{cap.titulo}"', f'origen: "{origen}"', "---", "", f"# {cap.titulo}", ""]
        (destino / archivo).write_text("\n".join(cab + cuerpo) + "\n", encoding="utf-8")
        informe.capitulos.append((archivo, cap.titulo, cuenta, chunks))
        cuerpo_txt = "\n".join(cuerpo)
        ids |= set(re.findall(r'\bid="([^"]+)"', cuerpo_txt)) | set(re.findall(r"\{#(eq:[\w.-]+)\}", cuerpo_txt))
        refs |= set(re.findall(r"\[@([\w:.-]+)\]", cuerpo_txt))
    informe.sin_destino = sorted(refs - ids)
    return informe


def informe_md(inf: Informe) -> str:
    filas = ["| Archivo | Capítulo | Enunciados | Ejercicios | Demostraciones | Chunks R |", "|---|---|---|---|---|---|"]
    for archivo, titulo, c, r in inf.capitulos:
        enun = sum(v for k, v in c.items() if k not in ("demostracion", "solucion", "ejercicio"))
        filas.append(f"| {archivo} | {titulo} | {enun} | {c.get('ejercicio', 0)} | {c.get('demostracion', 0)} | {r} |")
    if inf.sin_destino:
        filas += ["", "Referencias sin destino: " + ", ".join(inf.sin_destino)]
    return "\n".join(filas) + "\n"
