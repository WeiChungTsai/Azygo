#!/usr/bin/env python3
"""Apply edits to a .docx as real Word tracked changes, plus author queries.

    python revise_docx.py SOURCE.docx EDITS.json --out REVISED.docx [--log change_log.md]

The author opens the result in Word and accepts or rejects each edit one by one,
which is the only form of language editing a corresponding author can actually
audit. Edits are addressed the same way the appraisal cites the manuscript —
by the [P12] ids `extract_manuscript.py` prints — so a concern can be carried
straight into an edit without re-finding the text by hand.

EDITS.json:
{
  "author": "Claude (medical-manuscript-review)",   # optional
  "edits": [
    {"para":"P33", "find":"divided into", "new":"categorised into",
     "reason":"'divided' implies allocation; this was not randomised",
     "ref":"m-lang"},                                # optional concern id
    {"para":"P48", "find":"may partially explain the mortality", "new":"",
     "reason":"unsupported inference from PVCs to mortality", "ref":"M8"},
    {"para":"P40", "find":"a direct index", "query":
     "SCNA is an indirect surrogate — confirm you want to keep 'direct'"}
  ]
}

`new` empty deletes the found text; `find` empty with `new` set inserts at the
end of the paragraph. An entry with `query` adds a Word comment anchored to the
found text and changes nothing. Every edit is reported, applied or not: a `find`
that no longer matches is listed in the log rather than silently dropped, since
a silently skipped edit is how a revision ships half-done.

Requires python-docx. Writes nothing to the source file.
"""
import argparse
import copy
import json
import re
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn, nsmap

W = qn  # shorthand

COMMENTS_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    "{body}</w:comments>"
)
CT_COMMENTS = ("application/vnd.openxmlformats-officedocument"
               ".wordprocessingml.comments+xml")
REL_COMMENTS = ("http://schemas.openxmlformats.org/officeDocument/2006/"
                "relationships/comments")


def accepted_text(p_el):
    """Paragraph text as if all existing tracked changes were accepted."""
    out = []

    def walk(el):
        tag = el.tag.split("}")[-1]
        if tag in ("del", "moveFrom"):
            return
        if tag == "t":
            out.append(el.text or "")
        for c in el:
            walk(c)

    walk(p_el)
    return "".join(out)


def body_paragraphs(doc):
    """The [P..] numbering extract_manuscript.py prints: non-empty, non-heading."""
    from docx.text.paragraph import Paragraph

    SECTION = re.compile(
        r"^\s*(\d+[.)]?\s*)?(abstract|introduction|background|methods?|materials? and methods?|"
        r"patients? and methods?|results?|discussion|conclusions?|references?|"
        r"acknowledge?ments?|funding|figure legends?|tables?|supplementary.*|declarations?|"
        r"data availability.*|author contributions?|conflicts? of interest.*|"
        r"competing interests?.*|ethics.*|keywords?)\s*:?\s*$", re.I)
    out, pid = {}, 0
    for child in doc.element.body.iterchildren():
        if child.tag.split("}")[-1] != "p":
            continue
        p = Paragraph(child, doc)
        text = accepted_text(child).strip()
        if not text:
            continue
        style = (p.style.name if p.style is not None else "") or ""
        if style.lower().startswith(("heading", "title")) or (
                len(text) < 60 and SECTION.match(text)):
            continue
        pid += 1
        out[f"P{pid}"] = p
    return out


class Reviser:
    def __init__(self, author):
        self.author = author
        self.when = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self._id = 0
        self.comments = []        # (id, text) for the comments part

    def _rev_attrs(self, el):
        self._id += 1
        el.set(W("w:id"), str(self._id))
        el.set(W("w:author"), self.author)
        el.set(W("w:date"), self.when)
        return el

    @staticmethod
    def _blank_run(template):
        """A copy of a run keeping its formatting but none of its text."""
        r = copy.deepcopy(template)
        for tag in ("w:t", "w:delText", "w:br", "w:tab"):
            for n in r.findall(W(tag)):
                r.remove(n)
        return r

    def _text_run(self, template, text, deleted=False):
        r = self._blank_run(template)
        t = OxmlElement("w:delText" if deleted else "w:t")
        t.set(qn("xml:space"), "preserve")
        t.text = text
        r.append(t)
        return r

    def rewrite(self, par, before, old, new, template):
        """Replace the paragraph's runs with before + del(old) + ins(new) + after."""
        after_start = len(before) + len(old)
        full = accepted_text(par._p)
        after = full[after_start:]
        for r in list(par._p.findall(W("w:r"))):
            par._p.remove(r)
        for wrapper in ("w:ins", "w:del"):
            for n in list(par._p.findall(W(wrapper))):
                par._p.remove(n)
        if before:
            par._p.append(self._text_run(template, before))
        if old:
            d = self._rev_attrs(OxmlElement("w:del"))
            d.append(self._text_run(template, old, deleted=True))
            par._p.append(d)
        if new:
            i = self._rev_attrs(OxmlElement("w:ins"))
            i.append(self._text_run(template, new))
            par._p.append(i)
        if after:
            par._p.append(self._text_run(template, after))

    def add_comment(self, par, anchor_text, body):
        """Anchor a Word comment to `anchor_text` inside this paragraph."""
        cid = len(self.comments)
        self.comments.append((cid, body))
        full = accepted_text(par._p)
        idx = full.find(anchor_text) if anchor_text else -1
        start = OxmlElement("w:commentRangeStart")
        start.set(W("w:id"), str(cid))
        end = OxmlElement("w:commentRangeEnd")
        end.set(W("w:id"), str(cid))
        ref_run = OxmlElement("w:r")
        rpr = OxmlElement("w:rPr")
        style = OxmlElement("w:rStyle")
        style.set(W("w:val"), "CommentReference")
        rpr.append(style)
        ref_run.append(rpr)
        ref = OxmlElement("w:commentReference")
        ref.set(W("w:id"), str(cid))
        ref_run.append(ref)
        if idx < 0:
            par._p.insert(0, start)
        else:
            par._p.insert(0, start)
        par._p.append(end)
        par._p.append(ref_run)
        return cid

    def comments_xml(self):
        parts = []
        for cid, body in self.comments:
            parts.append(
                f'<w:comment w:id="{cid}" w:author="{_esc(self.author)}" '
                f'w:date="{self.when}" w:initials="C">'
                f'<w:p><w:r><w:t xml:space="preserve">{_esc(body)}</w:t></w:r></w:p>'
                f"</w:comment>")
        return COMMENTS_XML.format(body="".join(parts))


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def attach_comments_part(path, xml):
    """Add word/comments.xml plus its content-type and relationship."""
    tmp = Path(str(path) + ".tmp")
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(
            tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "[Content_Types].xml":
                s = data.decode("utf8")
                if "comments+xml" not in s:
                    s = s.replace(
                        "</Types>",
                        f'<Override PartName="/word/comments.xml" '
                        f'ContentType="{CT_COMMENTS}"/></Types>')
                data = s.encode("utf8")
            elif item.filename == "word/_rels/document.xml.rels":
                s = data.decode("utf8")
                if "comments.xml" not in s:
                    rid = "rIdComments100"
                    s = s.replace(
                        "</Relationships>",
                        f'<Relationship Id="{rid}" Type="{REL_COMMENTS}" '
                        f'Target="comments.xml"/></Relationships>')
                data = s.encode("utf8")
            zout.writestr(item, data)
        zout.writestr("word/comments.xml", xml)
    tmp.replace(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("source", type=Path)
    ap.add_argument("edits", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--log", type=Path)
    ap.add_argument("--author", default=None)
    a = ap.parse_args()

    spec = json.loads(a.edits.read_text(encoding="utf8"))
    author = a.author or spec.get("author") or "Claude (medical-manuscript-review)"
    shutil.copyfile(a.source, a.out)

    doc = docx.Document(str(a.out))
    paras = body_paragraphs(doc)
    rev = Reviser(author)

    applied, skipped, queries = [], [], []
    for n, e in enumerate(spec.get("edits", []), 1):
        pid = e.get("para")
        par = paras.get(pid) if pid else None
        find = e.get("find", "")
        if par is None and find:                      # fall back to a global search
            for k, p in paras.items():
                if find in accepted_text(p._p):
                    par, pid = p, k
                    break
        if par is None:
            skipped.append((n, e, f"找不到段落 {pid or '(未指定)'}"))
            continue
        full = accepted_text(par._p)
        if find and find not in full:
            skipped.append((n, e, f"{pid} 裡找不到要修改的文字"))
            continue
        runs = par._p.findall(W("w:r"))
        if not runs:
            skipped.append((n, e, f"{pid} 沒有可複製格式的 run"))
            continue
        template = runs[0]

        if "query" in e:
            rev.add_comment(par, find, e["query"])
            queries.append((n, pid, find, e["query"]))
            continue

        new = e.get("new", "")
        if not find and not new:
            skipped.append((n, e, "find 與 new 都是空的"))
            continue
        before = full[:full.index(find)] if find else full
        rev.rewrite(par, before, find, new, template)
        applied.append((n, pid, find, new, e.get("reason", ""), e.get("ref", "")))

    doc.save(str(a.out))
    if rev.comments:
        attach_comments_part(a.out, rev.comments_xml())

    print(f"套用 {len(applied)} 處修訂、{len(queries)} 則作者提問"
          f"，{len(skipped)} 處未套用 → {a.out}")
    for n, e, why in skipped:
        print(f"  ! #{n} {why}: {str(e.get('find',''))[:60]}")

    if a.log:
        L = [f"# 修改紀錄 — {a.out.name}", "",
             f"來源：`{a.source.name}`　作者標記：{author}　"
             f"時間：{rev.when}", "",
             f"套用 **{len(applied)}** 處追蹤修訂、**{len(queries)}** 則作者提問"
             f"，**{len(skipped)}** 處未套用。", "",
             "在 Word 開啟後用「校閱 → 接受／拒絕」逐項處理。", ""]
        if applied:
            L += ["## 修訂", "", "| # | 段落 | 原文 | 改為 | 理由 | 對應條目 |",
                  "|---|------|------|------|------|----------|"]
            for n, pid, old, new, reason, ref in applied:
                L.append(f"| {n} | {pid} | {_md(old)} | {_md(new) or '（刪除）'} "
                         f"| {_md(reason)} | {ref} |")
            L.append("")
        if queries:
            L += ["## 作者提問（Word 註解）", "",
                  "| # | 段落 | 錨定文字 | 問題 |", "|---|------|----------|------|"]
            for n, pid, anchor, q in queries:
                L.append(f"| {n} | {pid} | {_md(anchor)} | {_md(q)} |")
            L.append("")
        if skipped:
            L += ["## 未套用", "",
                  "這些要人工處理——通常是稿件已經改過，原文對不上了。", "",
                  "| # | 原因 | 要找的文字 |", "|---|------|------------|"]
            for n, e, why in skipped:
                L.append(f"| {n} | {why} | {_md(str(e.get('find','')))} |")
            L.append("")
        a.log.write_text("\n".join(L), encoding="utf8")
        print(f"修改紀錄 → {a.log}")
    return 0


def _md(s):
    s = str(s).replace("|", "\\|").replace("\n", " ").strip()
    return s if len(s) <= 90 else s[:87] + "…"


if __name__ == "__main__":
    sys.exit(main())
