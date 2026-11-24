"""Markdown mínimo de los cursos: párrafos, listas, tablas, código (con pestañas por sistema operativo y
botón «Copiar»), enlaces, énfasis y enlaces automáticos a los RFC."""
import html
import re

e = html.escape


# ---------- Markdown mínimo ----------

_RFC = re.compile(r"\bRFC (\d{3,4})((?:(?: \([^)]*\))?(?:, | y | o | a |/)\d{3,4}\b)*)")


def _rfc_url(n: str, texto: str) -> str:
    return f'<a href="https://www.rfc-editor.org/rfc/rfc{n}" target="_blank" rel="noopener">{texto}</a>'


def _rfc(t: str) -> str:
    """«RFC 2865, 2866 y 5176» → cada número enlazado a su documento en rfc-editor.org."""
    def enlazar(m):
        resto = re.sub(r"\([^)]*\)|\d{3,4}",
                       lambda n: n.group(0) if n.group(0).startswith("(") else _rfc_url(n.group(0), n.group(0)),
                       m.group(2))
        return _rfc_url(m.group(1), f"RFC {m.group(1)}") + resto
    return _RFC.sub(enlazar, t)


# Fórmula en línea: $…$ pegado al texto por dentro y sin letras ni $ por fuera («$5 y $10» no es fórmula)
_MATH = re.compile(r"(?<![\w$\\])\$(?=\S)([^$\n]+?)(?<=\S)\$(?![\w$])")
_REF = re.compile(r"\[@([\w:.-]+)\]")


def _inline(texto: str, enlaces: bool = True) -> str:
    """Código, fórmulas $…$, referencias [@id], enlaces, RFC, negrita y cursiva. Con enlaces=False (texto que
    ya va dentro de un <a>), sin enlaces."""
    codigos = []

    def apartar(html_):
        codigos.append(html_)
        return f"\0{len(codigos) - 1}\0"

    t = e(texto, quote=False)
    t = re.sub(r"`([^`]+)`", lambda m: apartar(f"<code>{m.group(1)}</code>"), t)
    t = t.replace("\\$", apartar("$"))
    t = _MATH.sub(lambda m: apartar(f'<span class="math">{m.group(1)}</span>'), t)
    t = _REF.sub(lambda m: apartar(f"\x03{m.group(1)}\x03"), t)
    if not enlaces:
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        t = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?![\*\w])", r"<i>\1</i>", t)
        return re.sub(r"\0(\d+)\0", lambda m: codigos[int(m.group(1))], t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
               lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener">{m.group(1)}</a>'
               if m.group(2).startswith("http") else f'<a href="{m.group(2)}">{m.group(1)}</a>', t)
    t = "".join(p if p.startswith("<a ") else _rfc(p) for p in re.split(r"(<a .*?</a>)", t))
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?![\*\w])", r"<i>\1</i>", t)
    return re.sub(r"\0(\d+)\0", lambda m: codigos[int(m.group(1))], t)


def _tabla(lineas):
    filas = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lineas
             if not re.match(r"^\|[\s:|-]+\|$", l.strip())]
    cab, cuerpo = filas[0], filas[1:]
    return ('<div class="tbl"><table><thead><tr>' + "".join(f"<th>{_inline(c)}</th>" for c in cab)
            + "</tr></thead><tbody>" + "".join(
                "<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in f) + "</tr>" for f in cuerpo)
            + "</tbody></table></div>")


_SO = re.compile(r"^# ((?:Windows|macOS|Linux)(?:(?:, | y )(?:Windows|macOS|Linux))*)")
_CLAVE_SO = {"Windows": "win", "macOS": "mac", "Linux": "linux"}
COPIAR = '<button type="button" class="copiar">Copiar</button>'


def _bloque_codigo(codigo: str, info: str = "") -> str:
    """Bloque ``` con rótulos «# Windows», «# macOS», «# Linux»: una pestaña por sistema y «Copiar» en
    cada comando. Sin rótulos de sistema: el bloque se muestra entero con un botón para copiarlo."""
    grupos = {}  # rótulo → {"notas": [...], "lineas": [...]}
    previas, actual = [], None
    for l in codigo.splitlines():
        if m := _SO.match(l):
            actual = grupos.setdefault(m.group(1), {"notas": [], "lineas": []})
            if l[2:].strip() != m.group(1):
                actual["notas"].append(l[2:].strip())
        elif actual is not None:
            actual["lineas"].append(l)
        else:
            previas.append(l)
    if grupos and any(l.strip() for l in previas):  # lo que va antes del primer rótulo vale para todos
        grupos = {"Windows, macOS y Linux": {"notas": [], "lineas": previas}, **grupos}
    if not grupos and info == "comandos":
        grupos = {"Windows, macOS y Linux": {"notas": [], "lineas": previas, "sin_nota": True}}
    # Un grupo compartido («macOS y Linux») se reparte si cada uno de sus sistemas ya tiene pestaña propia
    sistemas = lambda r: re.findall(r"Windows|macOS|Linux", r)
    solos = {r for r in grupos if len(sistemas(r)) == 1}
    for r in [r for r in grupos if len(sistemas(r)) > 1 and set(sistemas(r)) <= solos]:
        for s in sistemas(r):
            grupos[s]["lineas"] += grupos[r]["lineas"]
        del grupos[r]
    # Un grupo para todos («Windows, macOS y Linux») junto a otros: sus líneas van al principio de cada pestaña
    for r in [r for r in grupos if len(grupos) > 1 and set(sistemas(r)) >= {s for o in grupos if o != r for s in sistemas(o)}]:
        comun = grupos.pop(r)
        cubiertos = {s for o in grupos for s in sistemas(o)}
        for g in grupos.values():
            g["lineas"] = comun["lineas"] + [""] + g["lineas"]
        faltan = [s for s in sistemas(r) if s not in cubiertos]
        if faltan:
            grupos[" y ".join(faltan)] = {"notas": [], "lineas": list(comun["lineas"])}
    orden = {"Windows": 0, "macOS": 1, "Linux": 2}
    grupos = dict(sorted(grupos.items(), key=lambda kv: orden[sistemas(kv[0])[0]]))
    if not grupos:
        return (f'<div class="code-copia"><pre><code>{e(codigo, quote=False)}</code></pre>'
                '<button type="button" class="copiar copiar-todo">Copiar</button></div>')

    def panel(rotulo, g, so):
        notas = g["notas"] or ([rotulo] if len(grupos) == 1 and not g.get("sin_nota") else [])
        html_ = "".join(f'<p class="cmd-nota">{e(n)}</p>' for n in notas)
        for l in g["lineas"]:
            if not l.strip():
                continue
            if l.lstrip().startswith("#"):
                html_ += f'<div class="cmd-c">{e(l, quote=False)}</div>'
            else:
                html_ += f'<div class="cmd-l"><code>{e(l, quote=False)}</code>{COPIAR}</div>'
        return f'<div class="cmd-panel" role="tabpanel" data-so="{so}">{html_}</div>'

    claves = {r: " ".join(_CLAVE_SO[s] for s in re.findall(r"Windows|macOS|Linux", r)) for r in grupos}
    if len(grupos) == 1:
        rotulo, g = next(iter(grupos.items()))
        return '<div class="cmds">' + panel(rotulo, g, claves[rotulo]).replace(' role="tabpanel"', "") + "</div>"
    pestanas = "".join(f'<button type="button" role="tab" data-so="{claves[r]}">{e(r)}</button>' for r in grupos)
    return ('<div class="cmds"><div class="cmd-tabs" role="tablist" aria-label="Sistema operativo">'
            + pestanas + "</div>" + "".join(panel(r, g, claves[r]) for r, g in grupos.items()) + "</div>")


def md_a_html(texto: str) -> str:
    texto = re.sub(r"<!--.*?-->", "", texto, flags=re.S)
    codigos = []

    def guardar(m):
        codigos.append(_bloque_codigo(m.group(2), m.group(1).strip()))
        return f"\n\n\x01{len(codigos) - 1}\x01\n\n"

    texto = re.sub(r"^```([^\n]*)\n(.*?)\n```[ \t]*$", guardar, texto, flags=re.S | re.M)

    def formula(m):
        tex, id_ = m.group(1).strip(), m.group(2)
        marca = f"\x02ecuacion|{id_}\x02" if id_ else ""
        atr = f' id="{e(id_)}"' if id_ else ""
        codigos.append(f'<div class="math-display"{atr}>{e(tex, quote=False)}{marca}</div>')
        return f"\n\n\x01{len(codigos) - 1}\x01\n\n"

    etiqueta = r"(?:[ \t]*\{#([\w:.-]+)\})?[ \t]*$"
    texto = re.sub(r"^\$\$[ \t]*\n(.*?)\n[ \t]*\$\$" + etiqueta, formula, texto, flags=re.S | re.M)
    texto = re.sub(r"\$\$(?=\S)([^$\n]+?)\$\$" + etiqueta, formula, texto, flags=re.M)
    salida = []
    for bloque in re.split(r"\n\s*\n", texto.strip()):
        lineas = [l for l in bloque.splitlines() if l.strip()]
        if not lineas:
            continue
        if m := re.fullmatch(r"\x01(\d+)\x01", bloque.strip()):
            salida.append(codigos[int(m.group(1))])
        elif all(l.startswith("- ") for l in lineas):
            salida.append("<ul>" + "".join(f"<li>{_inline(l[2:])}</li>" for l in lineas) + "</ul>")
        elif all(re.match(r"^\d+\. ", l) for l in lineas):
            n0 = int(re.match(r"^(\d+)\.", lineas[0]).group(1))
            inicio = f' start="{n0}" style="counter-reset:st {n0 - 1}"' if n0 > 1 else ""
            salida.append(f'<ol class="steps"{inicio}>' + "".join(
                f"<li><span>{_inline(l.split('. ', 1)[1])}</span></li>" for l in lineas) + "</ol>")
        elif all(l.strip().startswith("|") for l in lineas):
            salida.append(_tabla(lineas))
        elif lineas[0].startswith("### "):
            salida.append(f"<h3>{_inline(lineas[0][4:])}</h3>")
            if lineas[1:]:
                salida.append(md_a_html("\n".join(lineas[1:])))
        else:
            salida.append(f"<p>{_inline(' '.join(l.strip() for l in lineas))}</p>")
    return "".join(salida)
