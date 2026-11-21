#!/usr/bin/env python3
"""Extract text, tables, comments and figures from manuscript files (.docx / .pptx).

Usage:
    python extract_manuscript.py FILE [FILE ...] --out WORKDIR [--no-render]

For each input file writes into WORKDIR:
    <stem>.md              text dump (paragraph ids [P1].., tables, footnotes, comments)
    <stem>_media/          embedded images
    <stem>_slides/         PNG render of each slide (.pptx, needs LibreOffice + pdftoppm)
and an INVENTORY.md summarising everything.

Requires python-docx and python-pptx (pip install python-docx python-pptx).
"""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

SECTION_WORDS = (
    "abstract|introduction|background|methods?|materials? and methods?|patients? and methods?|"
    "results?|discussion|conclusions?|references?|acknowledge?ments?|funding|"
    "figure legends?|tables?|supplementary.*|declarations?|data availability.*|"
    "author contributions?|conflicts? of interest.*|competing interests?.*|ethics.*|keywords?"
)
SECTION_RE = re.compile(rf"^\s*(\d+[.)]?\s*)?({SECTION_WORDS})\s*:?\s*$", re.I)


def words(text):
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’\-./%]*", text))


def accepted_text(p_el):
    """Paragraph text as if all tracked changes were accepted.

    python-docx's Paragraph.text skips runs inside <w:ins>, so it silently drops
    inserted text. Walk the XML instead: keep <w:t> (insertions included), skip
    anything inside <w:del> / <w:moveFrom> (deleted text uses <w:delText> anyway).
    """
    out = []

    def walk(el):
        tag = el.tag.split("}")[-1]
        if tag in ("del", "moveFrom"):
            return
        if tag == "t":
            out.append(el.text or "")
        elif tag == "tab":
            out.append("\t")
        elif tag in ("br", "cr"):
            out.append("\n")
        for c in el:
            walk(c)

    walk(p_el)
    return "".join(out)


def cell_text(cell):
    texts = (accepted_text(p._p).strip() for p in cell.paragraphs)
    return " ".join(t for t in texts if t).replace("|", "\\|")


def table_md(table):
    rows = []
    for row in table.rows:
        seen, cells = set(), []
        for c in row.cells:  # merged cells repeat the same underlying element
            if id(c._tc) in seen:
                continue
            seen.add(id(c._tc))
            cells.append(cell_text(c))
        rows.append(cells)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(out)


def zip_xml(zf, name):
    try:
        return ET.fromstring(zf.read(name))
    except KeyError:
        return None


def node_text(node):
    return "".join(t.text or "" for t in node.iter(f"{W}t")).strip()


def save_media(zf, prefix, dest):
    names = [n for n in zf.namelist() if n.startswith(prefix) and not n.endswith("/")]
    if names:
        dest.mkdir(parents=True, exist_ok=True)
        for n in names:
            (dest / Path(n).name).write_bytes(zf.read(n))
    return len(names)


def extract_docx(path, out):
    import docx
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    doc = docx.Document(str(path))
    lines, sections = [f"# {path.name}", ""], []
    current, pid, tid = "(front matter)", 0, 0
    counts = {current: 0}

    for child in doc.element.body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            p = Paragraph(child, doc)
            text = accepted_text(child).strip()
            if not text:
                continue
            style = (p.style.name if p.style is not None else "") or ""
            is_heading = style.lower().startswith(("heading", "title")) or (
                len(text) < 60 and SECTION_RE.match(text)
            )
            if is_heading:
                level = 2
                m = re.search(r"(\d)", style)
                if style.lower().startswith("heading") and m:
                    level = min(int(m.group(1)) + 1, 6)
                lines += ["", "#" * level + " " + text, ""]
                current = text
                counts.setdefault(current, 0)
                sections.append(current)
            else:
                pid += 1
                counts[current] += words(text)
                lines += [f"[P{pid}] {text}", ""]
        elif tag == "tbl":
            tid += 1
            lines += [f"**[Table block T{tid}]**", "", table_md(Table(child, doc)), ""]

    with zipfile.ZipFile(path) as zf:
        notes = []
        for part, label in (("word/footnotes.xml", "Footnote"), ("word/endnotes.xml", "Endnote")):
            root = zip_xml(zf, part)
            if root is None:
                continue
            for n in root:
                t = node_text(n)
                if t:
                    notes.append(f"- {label} {n.get(W + 'id')}: {t}")
        if notes:
            lines += ["", "## [Footnotes / endnotes]", ""] + notes

        comments = []
        root = zip_xml(zf, "word/comments.xml")
        if root is not None:
            for c in root.iter(f"{W}comment"):
                comments.append(f"- {c.get(W + 'author') or '?'}: {node_text(c)}")
        if comments:
            lines += ["", "## [Reviewer / co-author comments in file]", ""] + comments

        body = zf.read("word/document.xml").decode("utf8", "ignore")
        ins, dele = len(re.findall(r"<w:ins\b", body)), len(re.findall(r"<w:del\b", body))
        fields = len(re.findall(r"ADDIN (EN\.CITE|ZOTERO_ITEM|CSL_CITATION|Mendeley)", body, re.I))
        n_media = save_media(zf, "word/media/", out / f"{path.stem}_media")

    (out / f"{path.stem}.md").write_text("\n".join(lines), encoding="utf8")

    info = [f"- Paragraphs: {pid}; table blocks: {tid}; embedded images: {n_media}"]
    info.append(f"- Total words (body paragraphs, excl. tables): {sum(counts.values())}")
    info.append("- Words by section: " + "; ".join(f"{k}: {v}" for k, v in counts.items() if v))
    if ins or dele:
        info.append(
            f"- WARNING: unaccepted tracked changes present ({ins} insertions, {dele} deletions). "
            "The extracted text shows all changes ACCEPTED; confirm with the author that this "
            "is the version they mean."
        )
    if comments:
        info.append(f"- {len(comments)} comment(s) in file - READ THESE, see end of the .md dump")
    info += audit_text("\n".join(lines))
    if fields:
        info.append(
            f"- Reference-manager field codes detected ({fields} citations): restyle via the "
            "reference manager's output style where possible; plain-text edits are overwritten "
            "on refresh."
        )
    return info


PLACEHOLDER_RE = re.compile(
    r"(X{3,}|\bTBD\b|\bTODO\b|\bFIXME\b|\bN/?A\?|\[insert[^\]]*\]|\bxxx\b|\?\?\?+"
    r"|\b(?:lorem ipsum)\b)", re.I)


def audit_text(md):
    """Deterministic checks that are cheap to run and expensive to miss.

    Every finding here cost a reviewer real credibility in at least one real
    manuscript: an unfilled "XXXX" in the methods, a reference that is listed but
    never cited, a paragraph left holding a single full stop. They are mechanical,
    so let the script find them rather than spending reading attention on them.
    """
    out = []
    body = re.sub(r"^\[P\d+\]\s*", "", md, flags=re.M)

    hits = []
    for m in PLACEHOLDER_RE.finditer(body):
        line = body[: m.start()].count("\n")
        ctx = body.splitlines()[line][:110] if line < len(body.splitlines()) else ""
        hits.append(f'"{m.group(0)}" in: {ctx.strip()}')
    if hits:
        out.append(f"- PLACEHOLDERS LEFT IN TEXT ({len(hits)}):")
        out += [f"    * {h}" for h in dict.fromkeys(hits)]

    stray = [f"[P{m.group(1)}]" for m in re.finditer(r"\[P(\d+)\]\s*[.,;:]?\s*$", md, re.M)]
    if stray:
        out.append(f"- Empty / stray paragraphs: {', '.join(stray[:10])}")

    # Reference list: "1.<tab>Author..." lines. Compare with numbers cited in the body.
    listed = [int(n) for n in re.findall(r"^\[P\d+\]\s*(\d{1,3})\.\t", md, re.M)]
    if len(listed) >= 5:
        pre_ref = md[: md.rfind("## References")] if "## References" in md else md
        txt = re.sub(r"^\[P\d+\]\s*", "", pre_ref, flags=re.M)
        for pat in (r"p\s*[=<>≤≥]\s*0?\.\d+", r"\bN\s*=\s*\d+", r"\d+\.\d+\s*±\s*\d+\.\d+",
                    r"\b0\.\d+\b", r"\b(?:19|20)\d\d\b", r"6-OHDA", r"C57BL/6",
                    r"\d+\s*[-–]\s*\d+[,\d]*\s*(?:Hz|dB|kHz|°C|ms|s|min|mg|µL|mL)",
                    r"\b\d+\s*(?:Hz|dB|kHz|°C|ms|min|mg|kg|µL|mL|µV|mV|bpm|days?|weeks?)\b",
                    r"Figures?\s+S?\d+[A-Za-z]?(?:\s*[-–]\s*S?\d*[A-Za-z]?)?",
                    r"Tables?\s+S?\d+"):
            txt = re.sub(pat, " ", txt, flags=re.I)
        cited = set()
        for m in re.finditer(r"(?<=[A-Za-z\)\.,;])\s?(\d{1,3}(?:\s*[,\-–]\s*\d{1,3})*)(?=[\s.,;)]|$)", txt):
            for part in re.split(r",", m.group(1)):
                part = part.strip()
                rng = re.match(r"^(\d+)\s*[-–]\s*(\d+)$", part)
                if rng:
                    cited.update(range(int(rng.group(1)), int(rng.group(2)) + 1))
                elif part.isdigit():
                    cited.add(int(part))
        hi = max(listed)
        never = sorted(set(listed) - {c for c in cited if 1 <= c <= hi})
        out.append(f"- Reference list: {len(listed)} entries (1-{hi}).")
        if never:
            out.append(f"    * NEVER CITED in the text (verify by hand): {never}")

    sup = sorted({int(n) for n in re.findall(r"Figure\s+S(\d+)", md)})
    if sup:
        out.append(f"- Supplementary figures referred to anywhere in this file: S{sup}")
    return out


def shape_lines(shape, depth=0):
    """Yield text lines from a shape, descending into groups and tables."""
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    pad = "  " * depth
    if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
        for s in shape.shapes:
            yield from shape_lines(s, depth)
        return
    if getattr(shape, "has_table", False) and shape.has_table:
        yield f"{pad}- [table]"
        for row in shape.table.rows:
            yield f"{pad}  | " + " | ".join(c.text.strip().replace("\n", " ") for c in row.cells) + " |"
        return
    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
        yield f"{pad}- [picture: {shape.name}]"
    if getattr(shape, "has_chart", False) and shape.has_chart:
        chart = shape.chart
        title = chart.chart_title.text_frame.text if chart.has_title else ""
        yield f"{pad}- [native chart: {shape.name}] {title}".rstrip()
        try:
            cats = list(chart.plots[0].categories)
            for s in chart.plots[0].series:
                yield f"{pad}  series '{s.name}': " + ", ".join(
                    f"{c}={v}" for c, v in zip(cats, s.values)
                )
        except Exception:
            pass
    if shape.has_text_frame:
        text = " / ".join(p.text.strip() for p in shape.text_frame.paragraphs if p.text.strip())
        if text:
            yield f"{pad}- {text}"


def render_slides(path, dest):
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    pdftoppm = shutil.which("pdftoppm")
    if not soffice or not pdftoppm:
        return 0, "LibreOffice and/or pdftoppm not installed - slides not rendered"
    with tempfile.TemporaryDirectory() as tmp:
        try:
            subprocess.run(
                [soffice, f"-env:UserInstallation=file://{tmp}/profile", "--headless",
                 "--convert-to", "pdf", "--outdir", tmp, str(path)],
                check=True, capture_output=True, timeout=300,
            )
            pdf = Path(tmp) / (path.stem + ".pdf")
            dest.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [pdftoppm, "-png", "-r", "110", str(pdf), str(dest / "slide")],
                check=True, capture_output=True, timeout=300,
            )
        except Exception as e:  # rendering is a convenience; never fail the extraction
            return 0, f"slide rendering failed ({type(e).__name__})"
    return len(list(dest.glob("slide*.png"))), ""


def extract_pptx(path, out, render=True):
    from pptx import Presentation

    prs = Presentation(str(path))
    lines = [f"# {path.name}", ""]
    for i, slide in enumerate(prs.slides, 1):
        title = slide.shapes.title.text.strip() if slide.shapes.title is not None else ""
        lines += [f"## Slide {i}" + (f" - {title}" if title else ""), ""]
        for shape in slide.shapes:
            lines += list(shape_lines(shape))
        if slide.has_notes_slide:
            note = slide.notes_slide.notes_text_frame.text.strip()
            if note:
                lines += ["", f"**Notes:** {note}"]
        lines.append("")
    (out / f"{path.stem}.md").write_text("\n".join(lines), encoding="utf8")

    with zipfile.ZipFile(path) as zf:
        n_media = save_media(zf, "ppt/media/", out / f"{path.stem}_media")

    w_in, h_in = prs.slide_width / 914400, prs.slide_height / 914400
    info = [f"- Slides: {len(prs.slides)}; embedded images: {n_media}; "
            f"slide size {w_in:.2f} x {h_in:.2f} in"]
    if render:
        n, msg = render_slides(path, out / f"{path.stem}_slides")
        info.append(f"- Slide renders: {n} PNG in {path.stem}_slides/ - VIEW THESE" if n else f"- {msg}; "
                    f"inspect the images in {path.stem}_media/ instead")
    return info


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--no-render", action="store_true", help="skip slide PNG rendering")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    inventory = ["# Inventory", ""]
    for f in args.files:
        inventory.append(f"## {f.name}")
        if not f.exists():
            inventory += ["- NOT FOUND", ""]
            continue
        ext = f.suffix.lower()
        try:
            if ext == ".docx":
                inventory += extract_docx(f, args.out)
            elif ext == ".pptx":
                inventory += extract_pptx(f, args.out, render=not args.no_render)
            elif ext in (".doc", ".ppt"):
                inventory.append("- Legacy format: convert first, e.g. "
                                 f"`soffice --headless --convert-to {ext[1:]}x \"{f}\"`")
            else:
                inventory.append("- Not handled by this script; read it directly")
        except Exception as e:
            inventory.append(f"- ERROR extracting: {type(e).__name__}: {e}")
        inventory.append("")
    (args.out / "INVENTORY.md").write_text("\n".join(inventory), encoding="utf8")
    print("\n".join(inventory))


if __name__ == "__main__":
    sys.exit(main())
