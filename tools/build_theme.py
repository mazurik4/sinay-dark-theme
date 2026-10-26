"""Generates theme-toggle/theme-dark.css (graphite dark theme) and demo/index.html.

The site's own CSS is scanned for colour declarations; each one is re-emitted under
html[data-theme="dark"] with the colour swapped for a palette variable, so the dark
theme follows the existing layout exactly. Re-run after the site's CSS changes:

    python3 tools/build_theme.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "site"
OUT = ROOT / "theme-toggle"

SCOPE = 'html[data-theme="dark"]'

# Graphite palette. Brand blue, green and yellow are kept from the light theme.
PALETTE = {
    "bg": ("#121417", "page background"),
    "surface": ("#1b1e23", "cards, header, inputs (was #fff)"),
    "surface2": ("#24282f", "raised blocks, hover (was #2d264b)"),
    "border": ("#363b44", "borders (was #c7c7c7)"),
    "text": ("#ececec", "main text (was #000)"),
    "muted": ("#9ba1aa", "secondary text (was #999)"),
    "brand": ("#1d71b8", "brand blue for buttons/backgrounds - unchanged"),
    "link": ("#4f9be0", "brand blue for text on dark - lighter for contrast"),
    "green": ("#34c472", "\"in stock\" green (was #27ae60)"),
    "yellow": ("#fff155", "catalog button yellow - unchanged"),
    "deep": ("#0b0c0e", "footer and darkest areas"),
    "shadow": ("rgba(0,0,0,.5)", "card shadows"),
}

WHITES = {"#fff", "#ffffff", "white"}
LIGHT_BG = {"#fafafa", "#f8f8f8", "#eee", "#e3e3e3"}
DARK_TEXT = {"#000", "#000000", "black", "#2f2f2f", "#000b28"}


def map_color(prop, c):
    c = c.lower().replace(" ", "")
    is_bg = prop.startswith("background")
    if c in WHITES:
        # White borders/outlines blend into white cards in the light theme -> blend into dark cards.
        if is_bg or prop.startswith(("border", "outline")):
            return "var(--surface)"
        return None  # white text on blue buttons stays white
    if c in LIGHT_BG:
        return "var(--bg)" if is_bg else "var(--border)"
    if c in DARK_TEXT:
        return "var(--deep)" if is_bg else "var(--text)"
    if c == "#1d71b8":
        return "var(--brand)" if is_bg or prop.startswith("border") else "var(--link)"
    if c == "#27ae60":
        return "var(--green)"
    if c in {"#c7c7c7", "rgba(199,199,199,.5)"}:
        return "var(--border)"
    if c == "#999999":
        return "var(--muted)"
    if c == "#2d264b":
        return "var(--surface2)"
    if c.startswith("rgba(0,0,0,.0"):
        return "var(--shadow)"
    return None


COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,6}\b|rgba?\([^)]*\)|\bwhite\b|\bblack\b")
COLOR_PROPS = re.compile(r"^(color|background(-color)?|border(-[a-z]+)?(-color)?|box-shadow|outline(-color)?|fill|stroke)$")


def convert_decls(body):
    out = []
    for decl in body.split(";"):
        if ":" not in decl:
            continue
        prop, val = decl.split(":", 1)
        prop = prop.strip().lower()
        if not COLOR_PROPS.match(prop) or "url(" in val or "gradient" in val:
            continue
        changed = False

        def sub(m):
            nonlocal changed
            r = map_color(prop, m.group(0))
            if r:
                changed = True
                return r
            return m.group(0)

        new = COLOR_RE.sub(sub, val)
        if changed:
            out.append(f"{prop}:{new.strip()}")
    return ";".join(out)


def scope(sel):
    parts = []
    for s in sel.split(","):
        s = s.strip()
        if s.startswith("html"):
            parts.append(SCOPE + s[4:])
        elif s.startswith(":root"):
            parts.append(SCOPE + s[5:])
        elif s:
            parts.append(f"{SCOPE} {s}")
    return ",".join(parts)


def block_end(text, j):
    depth, k = 1, j + 1
    while depth and k < len(text):
        depth += {"{": 1, "}": -1}.get(text[k], 0)
        k += 1
    return k


def walk(text, indent=""):
    out, i = [], 0
    while i < len(text):
        j = text.find("{", i)
        if j < 0:
            break
        head = text[i:j].strip()
        if head.startswith(("@media", "@supports")):
            k = block_end(text, j)
            inner = walk(text[j + 1:k - 1], indent + "  ")
            if inner:
                out.append(f"{indent}{head}{{\n" + "\n".join(inner) + f"\n{indent}}}")
            i = k
            continue
        if head.startswith("@"):  # keyframes, font-face
            i = block_end(text, j)
            continue
        k = text.find("}", j)
        decls = convert_decls(text[j + 1:k])
        if decls and head:
            out.append(f"{indent}{scope(head)}{{{decls}}}")
        i = k + 1
    return out


def build_css():
    css = (SRC / "orig.css").read_text() + "\n" + (SRC / "main.css").read_text()
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    variables = "\n".join(f"  --{k}: {v};  /* {note} */" for k, (v, note) in PALETTE.items())
    manual = (OUT / "theme-dark.manual.css").read_text()
    generated = "\n".join(walk(css))
    return f"""/* ==========================================================================
   Sinay.ua — тёмная тема «Графит»
   Включается атрибутом <html data-theme="dark"> (его ставит theme-toggle.js).
   Без этого атрибута ни одно правило ниже не действует — светлая тема не меняется.
   Файл сгенерирован tools/build_theme.py; правки вручную вносите в
   theme-dark.manual.css, а палитру — в PALETTE внутри скрипта.
   ========================================================================== */

/* ---------- 1. Палитра ---------- */
{SCOPE} {{
{variables}
}}

/* ---------- 2. Ручные правки (кнопка темы, фон, футер, картинки) ---------- */
{manual}
/* ---------- 3. Автоматически перекрашенные правила из CSS сайта ---------- */
{generated}
"""


# Demo pages: local name -> path on sinay.ua. Each page is saved in RU and UA
# (<name>.html and <name>-uk.html; the homepage UA copy is uk.html), and the RU/UA
# switcher on every page is pointed at the local copy so it never leaves the demo.
DEMO_PAGES = {
    "index": "",
    "catalog": "catalog/svicki-parafin",
    "product": "catalog/svicki-parafin/svickogasnik-latun-grecia",
    "cart": "cart",
    "contacts": "contacts",
}
LANGS = ("ru", "uk")


def demo_name(name, lang):
    if lang == "ru":
        return f"{name}.html"
    return "uk.html" if name == "index" else f"{name}-uk.html"


def source_page(name, lang):
    """Cached copy of the live page (downloaded once into site/pages/)."""
    path = SRC / "pages" / f"{name}-{lang}.html"
    if not path.exists():
        import urllib.request
        path.parent.mkdir(exist_ok=True)
        url = f"https://sinay.ua/{lang}/{DEMO_PAGES[name]}".rstrip("/")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh)"})
        path.write_bytes(urllib.request.urlopen(req).read())
    return path.read_text()


def localize_lang_links(html):
    for name, slug in DEMO_PAGES.items():
        for lang in LANGS:
            live = re.escape(f"https://sinay.ua/{lang}/{slug}".rstrip("/")) + "/?"
            html = re.sub(f'href="{live}"( title="(?:UA|RU)")', f'href="{demo_name(name, lang)}"\\1', html)
    return html


def build_demo(name, lang):
    html = source_page(name, lang)
    snippet_head = (OUT / "snippet-head.html").read_text()
    snippet_button = (OUT / "snippet-button.html").read_text()
    snippet_body = (OUT / "snippet-body-end.html").read_text()
    # Point the site's root-relative assets at the live server; our own files stay local.
    html = re.sub(r'((?:src|href|data-pagespeed-lazy-src)=")/(?!/)', r"\1https://sinay.ua/", html)
    html = localize_lang_links(html)
    html = re.sub(r"""(["'(])/(css|js|img|storage|assets|pagespeed_static|fonts)/""", r"\1https://sinay.ua/\2/", html)
    snippet_head = snippet_head.replace('href="/theme-toggle/', 'href="../theme-toggle/')
    snippet_body = snippet_body.replace('src="/theme-toggle/', 'src="../theme-toggle/')
    # Demo only: the site's webfont is blocked cross-origin on localhost.
    font = '<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">'
    # The demo is a public copy of sinay.ua: keep it out of search results (duplicate content).
    noindex = '<meta name="robots" content="noindex, nofollow">\n'
    html = html.replace('<head id="head-tag">', '<head id="head-tag">\n' + noindex + snippet_head + font, 1)
    anchor = '<div class="languages">'
    assert anchor in html, "header anchor not found"
    html = html.replace(anchor, snippet_button + "\n" + anchor, 1)
    html = html.replace("</body>", snippet_body + "</body>", 1)
    (ROOT / "demo").mkdir(exist_ok=True)
    (ROOT / "demo" / demo_name(name, lang)).write_text(html)


if __name__ == "__main__":
    (OUT / "theme-dark.css").write_text(build_css())
    for name in DEMO_PAGES:
        for lang in LANGS:
            build_demo(name, lang)
    print("ok")
