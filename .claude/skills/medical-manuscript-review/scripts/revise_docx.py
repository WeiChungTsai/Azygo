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


def has_pending_revisions(p_el):
    """True if this paragraph already carries unaccepted tracked changes."""
    for tag in ("w:ins", "w:del", "w:moveFrom", "w:moveTo"):
        if p_el.find(W(tag)) is not None:
            return True
    return False


def accept_all_changes(doc):
    """Accept every pending tracked change in the document.

    Rewriting a paragraph cannot preserve somebody else's pending revisions
    inside it, so a run over a manuscript that still has co-author edits would
    quietly discard them. Accepting them first makes that explicit and
    recoverable: the author still has their own copy, and the log says it
    happened.
    """
    body = doc.element.body
    ins = dele = 0
    for node in list(body.iter(W("w:del"))) + list(body.iter(W("w:moveFrom"))):
        parent = node.getparent()
        if parent is not None:
            parent.remove(node)
            dele += 1
    for node in list(body.iter(W("w:ins"))) + list(body.iter(W("w:moveTo"))):
        parent = node.getparent()
        if parent is None:
            continue
        idx = list(parent).index(node)
        for child in reversed(list(node)):
            parent.insert(idx, child)
        parent.remove(node)
        ins += 1
    return ins, dele


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
    def __init__(self, author, first_comment_id=0):
        self.author = author
        self._next_comment = first_comment_id
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

    def rewrite(self, par, spans, template):
        """Rebuild the paragraph with every edit applied as one tracked pass.

        `spans` is [(start, end, new_text)] over the paragraph's accepted text,
        sorted and non-overlapping. All of a paragraph's edits are applied
        together because a rewrite replaces the paragraph's runs wholesale:
        applying them one at a time would make each edit discard the previous
        one's markup. Several edits in one paragraph is the normal case — an
        abstract usually takes four or five.
        """
        full = accepted_text(par._p)
        for r in list(par._p.findall(W("w:r"))):
            par._p.remove(r)
        for wrapper in ("w:ins", "w:del", "w:moveFrom", "w:moveTo"):
            for n in list(par._p.findall(W(wrapper))):
                par._p.remove(n)
        cursor = 0
        for start, end, new_text in spans:
            if start > cursor:
                par._p.append(self._text_run(template, full[cursor:start]))
            old = full[start:end]
            if old:
                d = self._rev_attrs(OxmlElement("w:del"))
                d.append(self._text_run(template, old, deleted=True))
                par._p.append(d)
            if new_text:
                i = self._rev_attrs(OxmlElement("w:ins"))
                i.append(self._text_run(template, new_text))
                par._p.append(i)
            cursor = end
        if cursor < len(full):
            par._p.append(self._text_run(template, full[cursor:]))

    def add_comment(self, par, anchor_text, body):
        """Anchor a Word comment to `anchor_text` inside this paragraph."""
        cid = self._next_comment
        self._next_comment += 1
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
        """Just the <w:comment> elements, for merging into an existing part."""
        parts = []
        for cid, body in self.comments:
            parts.append(
                f'<w:comment w:id="{cid}" w:author="{_esc(self.author)}" '
                f'w:date="{self.when}" w:initials="C">'
                f'<w:p><w:r><w:t xml:space="preserve">{_esc(body)}</w:t></w:r></w:p>'
                f"</w:comment>")
        return "".join(parts)


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def existing_comment_ids(path):
    """The w:id values already used by comments in this document.

    A manuscript in circulation usually carries co-author comments. New ones
    must not reuse their ids, and the part must be merged rather than replaced
    — writing a second word/comments.xml produces a file Word repairs by
    throwing comments away.
    """
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/comments.xml").decode("utf8", "ignore")
    except (KeyError, zipfile.BadZipFile):
        return set(), None
    ids = {int(m) for m in re.findall(r'<w:comment[^>]*\sw:id="(\d+)"', xml)}
    return ids, xml


def attach_comments_part(path, new_comments_xml, had_part):
    """Merge new comments into word/comments.xml, adding the part if absent."""
    tmp = Path(str(path) + ".tmp")
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(
            tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == "word/comments.xml":
                continue                      # replaced below, never duplicated
            data = zin.read(item.filename)
            if item.filename == "[Content_Types].xml":
                t = data.decode("utf8")
                if "comments+xml" not in t:
                    t = t.replace(
                        "</Types>",
                        f'<Override PartName="/word/comments.xml" '
                        f'ContentType="{CT_COMMENTS}"/></Types>')
                data = t.encode("utf8")
            elif item.filename == "word/_rels/document.xml.rels":
                t = data.decode("utf8")
                if "comments.xml" not in t:
                    t = t.replace(
                        "</Relationships>",
                        f'<Relationship Id="rIdComments100" Type="{REL_COMMENTS}" '
                        f'Target="comments.xml"/></Relationships>')
                data = t.encode("utf8")
            zout.writestr(item, data)
        if had_part:
            merged = had_part.replace("</w:comments>", new_comments_xml + "</w:comments>")
        else:
            merged = COMMENTS_XML.format(body=new_comments_xml)
        zout.writestr("word/comments.xml", merged)
    tmp.replace(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("source", type=Path)
    ap.add_argument("edits", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--log", type=Path)
    ap.add_argument("--author", default=None)
    ap.add_argument("--accept-existing", action="store_true",
                    help="先接受稿件裡所有未處理的修訂，再套用新修訂。"
                         "不加這個旗標時，有未處理修訂的段落會被跳過而不是被覆蓋。")
    a = ap.parse_args()

    spec = json.loads(a.edits.read_text(encoding="utf8"))
    author = a.author or spec.get("author") or "Claude (medical-manuscript-review)"
    shutil.copyfile(a.source, a.out)

    doc = docx.Document(str(a.out))
    accepted = None
    if a.accept_existing:
        accepted = accept_all_changes(doc)
        print(f"先接受了稿件原有的 {accepted[0]} 處插入、{accepted[1]} 處刪除")
    paras = body_paragraphs(doc)
    used_ids, had_part = existing_comment_ids(a.out)
    rev = Reviser(author, first_comment_id=(max(used_ids) + 1) if used_ids else 0)
    if used_ids:
        print(f"稿件原有 {len(used_ids)} 則註解，新註解從 id {max(used_ids)+1} 開始")

    applied, skipped, queries = [], [], []
    pending_before = {k for k, p_ in paras.items() if has_pending_revisions(p_._p)}

    def resolve(e):
        """Which paragraph this edit lands in, or a reason it cannot."""
        pid = e.get("para")
        par = paras.get(pid) if pid else None
        find = e.get("find", "")
        if par is None and find:
            for k, p_ in paras.items():
                if find in accepted_text(p_._p):
                    return k, p_, None
        if par is None:
            return None, None, f"找不到段落 {pid or '(未指定)'}"
        if find and find not in accepted_text(par._p):
            return pid, par, f"{pid} 裡找不到要修改的文字"
        return pid, par, None

    # queries first: a comment does not rewrite the paragraph
    groups = {}
    for n, e in enumerate(spec.get("edits", []), 1):
        pid, par, why = resolve(e)
        if why:
            skipped.append((n, e, why))
            continue
        if "query" in e:
            rev.add_comment(par, e.get("find", ""), e["query"])
            queries.append((n, pid, e.get("find", ""), e["query"]))
            continue
        if pid in pending_before:
            skipped.append((n, e, f"{pid} 還有未處理的修訂——"
                                  "先在 Word 接受／拒絕，或加 --accept-existing"))
            continue
        if not e.get("find") and not e.get("new"):
            skipped.append((n, e, "find 與 new 都是空的"))
            continue
        groups.setdefault(pid, []).append((n, e))

    for pid, items in groups.items():
        par = paras[pid]
        full = accepted_text(par._p)
        runs = par._p.findall(W("w:r"))
        if not runs:
            for n, e in items:
                skipped.append((n, e, f"{pid} 沒有可複製格式的 run"))
            continue
        template = runs[0]
        spans = []
        for n, e in items:
            find = e.get("find", "")
            start = full.find(find) if find else len(full)
            end = start + len(find)
            if any(not (end <= s0 or start >= e0) for s0, e0, _, _ in spans):
                skipped.append((n, e, f"{pid} 這處與同段落另一筆修訂重疊"))
                continue
            spans.append((start, end, e.get("new", ""), (n, e)))
        spans.sort(key=lambda x: x[0])
        rev.rewrite(par, [(s0, e0, nt) for s0, e0, nt, _ in spans], template)
        for s0, e0, nt, (n, e) in spans:
            applied.append((n, pid, e.get("find", ""), nt,
                            e.get("reason", ""), e.get("ref", "")))
    applied.sort(key=lambda x: x[0])

    doc.save(str(a.out))
    if rev.comments:
        attach_comments_part(a.out, rev.comments_xml(), had_part)

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
        if accepted:
            L += [f"> ⚠ 本次先接受了稿件原有的 {accepted[0]} 處插入與 {accepted[1]} 處刪除"
                  f"（`--accept-existing`），因此下面的修訂是疊加在「全部接受」之後的版本上。"
                  f"原始檔沒有被改動。", ""]
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
