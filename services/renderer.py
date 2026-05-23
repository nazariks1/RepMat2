import re
import io
import textwrap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams
rcParams["font.family"] = "DejaVu Sans"
rcParams["mathtext.fontset"] = "dejavusans"
PAGE_WIDTH_INCHES = 9
FONT_SIZE = 13
LINE_SPACING = 1.6
PADDING = 0.4
MAX_CHARS_PER_LINE = 80
_MATH_REPLACEMENTS = [
    (r"\implies",       r"\Rightarrow"),
    (r"\impliedby",     r"\Leftarrow"),
    (r"\iff",           r"\Leftrightarrow"),
    (r"\therefore",     r"\Rightarrow"),
    (r"\because",       r"\Leftarrow"),
    (r"\forall",        r"\forall"),
    (r"\exists",        r"\exists"),
    (r"\nexists",       r"\not\exists"),
    (r"\land",          r"\wedge"),
    (r"\lor",           r"\vee"),
    (r"\lnot",          r"\neg"),
    (r"\top",           r"\top"),
    (r"\bot",           r"\bot"),
    (r"\emptyset",      r"\varnothing"),
    (r"\varnothing",    r"\varnothing"),
    (r"\setminus",      r"\backslash"),
    (r"\complement",    r"^{c}"),
    (r"\subseteq",      r"\subseteq"),
    (r"\supseteq",      r"\supseteq"),
    (r"\subsetneq",     r"\subset"),
    (r"\supsetneq",     r"\supset"),
    (r"\longrightarrow",  r"\rightarrow"),
    (r"\longleftarrow",   r"\leftarrow"),
    (r"\Longrightarrow",  r"\Rightarrow"),
    (r"\Longleftarrow",   r"\Leftarrow"),
    (r"\longleftrightarrow", r"\leftrightarrow"),
    (r"\Longleftrightarrow", r"\Leftrightarrow"),
    (r"\hookrightarrow",  r"\rightarrow"),
    (r"\hookleftarrow",   r"\leftarrow"),
    (r"\mapsto",          r"\to"),
    (r"\longmapsto",      r"\to"),
    (r"\nearrow",         r"\nearrow"),
    (r"\searrow",         r"\searrow"),
    (r"\nrightarrow",     r"\not\rightarrow"),
    (r"\nleftarrow",      r"\not\leftarrow"),
    (r"\nRightarrow",     r"\not\Rightarrow"),
    (r"\leqslant",      r"\leq"),
    (r"\geqslant",      r"\geq"),
    (r"\leqq",          r"\leq"),
    (r"\geqq",          r"\geq"),
    (r"\lneq",          r"\lneq"),
    (r"\gneq",          r"\gneq"),
    (r"\ll",            r"\ll"),
    (r"\gg",            r"\gg"),
    (r"\doteq",         r"\doteq"),
    (r"\triangleq",     r"="),
    (r"\approxeq",      r"\approx"),
    (r"\eqcirc",        r"="),
    (r"\coloneqq",      r":="),
    (r"\colonequals",   r":="),
    (r"\eqqcolon",      r"=:"),
    (r"\divides",       r"\mid"),
    (r"\nmid",          r"\nmid"),
    (r"\smallsetminus", r"\backslash"),
    (r"\varpropto",     r"\propto"),
    (r"\dagger",        r"\dag"),
    (r"\ddagger",       r"\ddag"),
    (r"\mathbb{R}",     r"\mathbb{R}"),
    (r"\mathbb{Z}",     r"\mathbb{Z}"),
    (r"\mathbb{N}",     r"\mathbb{N}"),
    (r"\mathbb{Q}",     r"\mathbb{Q}"),
    (r"\mathbb{C}",     r"\mathbb{C}"),
    (r"\mathfrak",      r"\mathrm"),
    (r"\mathscr",       r"\mathcal"),
    (r"\boldsymbol",    r"\mathbf"),
    (r"\bm",            r"\mathbf"),
    (r"\pmb",           r"\mathbf"),
    (r"\phantom",       r""),
    (r"\hphantom",      r""),
    (r"\vphantom",      r""),
    (r"\mathstrut",     r""),
    (r"\strut",         r""),
    (r"\vspace",        r""),
    (r"\hspace",        r""),
    (r"\quad",          r"\ "),
    (r"\qquad",         r"\ \ "),
    (r"\,",             r"\ "),
    (r"\;",             r"\ "),
    (r"\:",             r"\ "),
    (r"\!",             r""),
    (r"\mkern",         r""),
    (r"\mskip",         r""),
    (r"\text",          r"\mathrm"),
    (r"\operatorname",  r"\mathrm"),
    (r"\DeclareMathOperator", r""),
    (r"\tag",           r""),
    (r"\label",         r""),
    (r"\ref",           r""),
    (r"\eqref",         r""),
    (r"\nonumber",      r""),
    (r"\notag",         r""),
    (r"\displaystyle",  r""),
    (r"\textstyle",     r""),
    (r"\scriptstyle",   r""),
    (r"\scriptscriptstyle", r""),
    (r"\limits",        r""),
    (r"\nolimits",      r""),
    (r"\biggl",         r"\left"),
    (r"\biggr",         r"\right"),
    (r"\Biggl",         r"\left"),
    (r"\Biggr",         r"\right"),
    (r"\bigl",          r"\left"),
    (r"\bigr",          r"\right"),
    (r"\Bigl",          r"\left"),
    (r"\Bigr",          r"\right"),
    (r"\ge",            r"\geq"),
    (r"\le",            r"\leq"),
    (r"\ne",            r"\neq"),
    (r"\to",            r"\rightarrow"),
    (r"\gets",          r"\leftarrow"),
]
_COMMANDS_STRIP_ARG = [
    r"\hspace", r"\vspace", r"\mkern", r"\mskip", r"\kern",
    r"\phantom", r"\hphantom", r"\vphantom",
    r"\tag", r"\label", r"\ref", r"\eqref",
    r"\DeclareMathOperator",
]

def _normalize_math(expr: str) -> str:
    for cmd in _COMMANDS_STRIP_ARG:
        expr = re.sub(re.escape(cmd) + r"\s*\{[^{}]*\}", "", expr)
        expr = re.sub(re.escape(cmd) + r"\b", "", expr)
    expr = re.sub(r"\\operatorname\s*\{([^{}]*)\}", r"\\mathrm{\1}", expr)
    expr = re.sub(r"\\text\s*\{([^{}]*)\}", r"\\mathrm{\1}", expr)
    expr = re.sub(r"\\boldsymbol\s*\{([^{}]*)\}", r"\\mathbf{\1}", expr)
    expr = re.sub(r"\\bm\s*\{([^{}]*)\}", r"\\mathbf{\1}", expr)
    expr = re.sub(r"\\pmb\s*\{([^{}]*)\}", r"\\mathbf{\1}", expr)
    expr = re.sub(r"\\mathscr\s*\{([^{}]*)\}", r"\\mathcal{\1}", expr)
    expr = re.sub(r"\\mathfrak\s*\{([^{}]*)\}", r"\\mathrm{\1}", expr)
    for old, new in _MATH_REPLACEMENTS:
        _new = new  # захватываем в замыкание
        if old[-1].isalpha():
            expr = re.sub(re.escape(old) + r"(?![a-zA-Z])", lambda m, s=_new: s, expr)
        else:
            expr = expr.replace(old, new)
    expr = re.sub(r"\\begin\{[^{}]*\}", "", expr)
    expr = re.sub(r"\\end\{[^{}]*\}", "", expr)
    expr = re.sub(r"\\\\", r"\ ", expr)
    expr = expr.replace("&", "")
    return expr.strip()

def _split_into_segments(text: str) -> list[dict]:
    pattern = re.compile(
        r"(\$\$[\s\S]+?\$\$"
        r"|\\\[[\s\S]+?\\\]"
        r"|\$[^\$\n]+?\$"
        r"|\\\(.+?\\\))",
        re.DOTALL
    )
    segments = []
    last = 0
    for m in pattern.finditer(text):
        if m.start() > last:
            segments.append({"type": "text", "value": text[last:m.start()]})
        raw = m.group()
        if raw.startswith("$$") and raw.endswith("$$"):
            expr = raw[2:-2].strip()
            block = True
        elif raw.startswith(r"\[") and raw.endswith(r"\]"):
            expr = raw[2:-2].strip()
            block = True
        elif raw.startswith("$") and raw.endswith("$"):
            expr = raw[1:-1].strip()
            block = False
        else:
            expr = raw[2:-2].strip()
            block = False
        segments.append({"type": "math", "value": expr, "block": block})
        last = m.end()
    if last < len(text):
        segments.append({"type": "text", "value": text[last:]})
    return segments

def _wrap_text(line: str, max_chars: int = MAX_CHARS_PER_LINE) -> list[str]:
    if len(line) <= max_chars:
        return [line]
    return textwrap.wrap(line, width=max_chars, break_long_words=False) or [line]

def _render_page(lines: list[dict], page_num: int, total_pages: int) -> bytes:
    base_h = FONT_SIZE / 72
    line_h = base_h * LINE_SPACING
    content_height = len(lines) * line_h + 2 * PADDING
    fig_height = max(content_height, 2.0)
    fig, ax = plt.subplots(figsize=(PAGE_WIDTH_INCHES, fig_height))
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#FAFAFA")
    ax.axis("off")
    x0 = PADDING / PAGE_WIDTH_INCHES
    y = 1.0 - PADDING / fig_height
    for item in lines:
        line_frac = line_h / fig_height
        y -= line_frac
        if item["kind"] == "blank":
            continue
        val = item["value"]

        if item["kind"] == "math":
            normalized = _normalize_math(val)
            try:
                ax.text(
                    x0, y,
                    f"${normalized}$",
                    transform=ax.transAxes,
                    fontsize=FONT_SIZE + (2 if item.get("block") else 0),
                    va="baseline",
                    ha="left",
                    color="#1a1a2e",
                )
            except Exception as e:
                print(f"Ошибка: {e!r}, выражение: {normalized[:80]}")
                ax.text(
                    x0, y,
                    normalized,
                    transform=ax.transAxes,
                    fontsize=FONT_SIZE,
                    va="baseline",
                    ha="left",
                    color="#555555",
                    style="italic",
                )
        else:
            is_heading = val.strip().startswith(("##", "#", "**")) or re.match(r"^\d+\.", val.strip())
            clean = re.sub(r"\*\*(.*?)\*\*", r"\1", val)
            clean = re.sub(r"^#{1,3}\s*", "", clean)
            ax.text(
                x0, y, clean,
                transform=ax.transAxes,
                fontsize=FONT_SIZE + (1 if is_heading else 0),
                fontweight="bold" if is_heading else "normal",
                va="baseline",
                ha="left",
                color="#1a1a2e",
                wrap=False,
            )
    if total_pages > 1:
        ax.text(
            0.5, 0.01,
            f"Страница {page_num} / {total_pages}",
            transform=ax.transAxes,
            fontsize=9,
            ha="center",
            va="bottom",
            color="#888888",
        )

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.read()

def _build_line_list(text: str) -> list[dict]:
    segments = _split_into_segments(text)
    lines = []
    for seg in segments:
        if seg["type"] == "text":
            raw_lines = seg["value"].split("\n")
            for raw in raw_lines:
                if raw.strip() == "":
                    lines.append({"kind": "blank"})
                else:
                    for wrapped in _wrap_text(raw):
                        lines.append({"kind": "text", "value": wrapped})
        else:
            if seg.get("block"):
                lines.append({"kind": "blank"})
            lines.append({"kind": "math", "value": seg["value"], "block": seg.get("block", False)})
            if seg.get("block"):
                lines.append({"kind": "blank"})

    return lines

def render_to_images(text: str, lines_per_page: int = 40) -> list[bytes]:
    all_lines = _build_line_list(text)
    pages = [all_lines[i:i + lines_per_page]
             for i in range(0, len(all_lines), lines_per_page)]

    if not pages:
        pages = [[{"kind": "text", "value": "(пустой ответ)"}]]
    total = len(pages)
    result = []
    for idx, page_lines in enumerate(pages, 1):
        png = _render_page(page_lines, idx, total)
        result.append(png)

    return result