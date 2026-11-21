#!/usr/bin/env python3
"""Build a point-by-point response-to-reviewers template from structured comments.

Usage:
    python make_response_template.py comments.json --out DIR [--basename response]

Writes <basename>.docx and <basename>.md. The .docx is what journals want uploaded;
the .md is for working on the text with the author before it is final.

The input JSON schema (see the skill's reference for a worked example):

{
  "title":        "manuscript title",
  "journal":      "target journal or '' if undecided",
  "manuscript_id":"",
  "intro":        ["paragraphs of the covering note"],
  "usage_notes":  ["lines telling the author how to use the file; deleted before submission"],
  "issue_map":    [{"issue": "...", "raised_by": ["R1.M2","R3.M1"], "effort": "...",
                    "answer_in": "R1.M2"}],
  "reviewers": [
    {"id": "1", "role": "...", "recommendation": "...",
     "comments": [
       {"id": "R1.M1", "kind": "major", "tag": "新實驗",
        "text": "the reviewer's comment, quoted",
        "draft": "a pre-written response where one can honestly be written, else ''",
        "todo":  ["what the author must still decide or supply"],
        "fallback": "the defensible answer if the requested work is impossible",
        "cross": ["R2.M6"]}]}
  ],
  "checklist": [{"group": "...", "items": ["..."]}]
}

Only "title", "reviewers" and each comment's "id"/"text" are required; everything
else is optional and simply omitted from the output when absent.
"""
import argparse
import json
import sys
from pathlib import Path

RULE = "─" * 70

KIND_LABEL = {"major": "Major comment", "minor": "Minor comment", "general": "General comment"}


# ---------------------------------------------------------------- markdown ---

def md_doc(d):
    L = [f"# Point-by-point response to reviewers", ""]
    L += [f"**Manuscript:** {d['title']}"]
    if d.get("journal"):
        L.append(f"**Journal:** {d['journal']}")
    if d.get("manuscript_id"):
        L.append(f"**Manuscript ID:** {d['manuscript_id']}")
    L.append("")

    if d.get("usage_notes"):
        L += ["> ## 使用說明（投稿前請整段刪除）", ">"]
        L += [f"> {n}" for n in d["usage_notes"]]
        L += [""]

    if d.get("intro"):
        L += ["## Covering note", ""] + [p + "\n" for p in d["intro"]]

    if d.get("issue_map"):
        L += ["## 共通議題對照表", "",
              "同一個問題被多位 reviewer 提出時，**只要寫一次完整回覆**，其餘位置交叉引用即可"
              "（例如 \"Please see our response to Reviewer 1, Major comment 2.\"）。"
              "這樣可以避免自相矛盾，也讓編輯容易核對。", "",
              "| # | 議題 | 提出者 | 性質 | 完整回覆寫在 |",
              "|---|------|--------|------|--------------|"]
        for i, it in enumerate(d["issue_map"], 1):
            L.append(f"| {i} | {it['issue']} | {', '.join(it['raised_by'])} | "
                     f"{it.get('effort','')} | **{it.get('answer_in','')}** |")
        L.append("")

    for r in d["reviewers"]:
        L += [RULE, "", f"# Response to Reviewer {r['id']}", ""]
        if r.get("role"):
            L.append(f"*{r['role']}*")
        if r.get("recommendation"):
            L.append(f"**Recommendation:** {r['recommendation']}")
        L.append("")
        if r.get("opening"):
            L += [r["opening"], ""]
        for c in r["comments"]:
            L += md_comment(c)
    if d.get("checklist"):
        L += [RULE, "", "# 投稿前檢查清單", ""]
        for g in d["checklist"]:
            L.append(f"### {g['group']}")
            L += [f"- [ ] {i}" for i in g["items"]]
            L.append("")
    return "\n".join(L)


def md_comment(c):
    head = f"## {c['id']}"
    if c.get("kind"):
        head += f" — {KIND_LABEL.get(c['kind'], c['kind'])}"
    if c.get("tag"):
        head += f"  `[{c['tag']}]`"
    L = [head, ""]
    L += ["> **Reviewer comment:**", ">"]
    L += [f"> {ln}" if ln.strip() else ">" for ln in c["text"].split("\n")]
    L.append("")
    if c.get("cross"):
        L += [f"*同一議題亦見於：{', '.join(c['cross'])}*", ""]
    L.append("**Response:**")
    L.append("")
    L.append(c.get("draft") or "_（待填）_")
    L.append("")
    if c.get("todo"):
        L.append("**作者需決定／補充：**")
        L += [f"- {t}" for t in c["todo"]]
        L.append("")
    if c.get("fallback"):
        L += ["**若無法執行所要求的工作，可用的防守說法：**", "", f"> {c['fallback']}", ""]
    L += ["**Changes in the manuscript:** page ____, line ____", "", ""]
    return L


# -------------------------------------------------------------------- docx ---

def build_docx(d, path):
    import docx
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt, RGBColor, Inches

    doc = docx.Document()
    for s in ("Normal",):
        f = doc.styles[s].font
        f.name, f.size = "Calibri", Pt(10.5)

    GREY = RGBColor(0x59, 0x59, 0x59)
    RED = RGBColor(0xA0, 0x20, 0x20)
    BLUE = RGBColor(0x1F, 0x3B, 0x73)

    def para(text="", *, bold=False, italic=False, color=None, size=None,
             space_after=6, indent=None, style=None):
        p = doc.add_paragraph(style=style)
        r = p.add_run(text)
        r.bold, r.italic = bold, italic
        if color is not None:
            r.font.color.rgb = color
        if size:
            r.font.size = Pt(size)
        p.paragraph_format.space_after = Pt(space_after)
        if indent:
            p.paragraph_format.left_indent = Inches(indent)
        return p

    doc.add_heading("Point-by-point response to reviewers", 0)
    para(d["title"], bold=True, size=12)
    if d.get("journal"):
        para(f"Journal: {d['journal']}")
    if d.get("manuscript_id"):
        para(f"Manuscript ID: {d['manuscript_id']}")

    if d.get("usage_notes"):
        doc.add_heading("使用說明（投稿前請整段刪除）", 1)
        for n in d["usage_notes"]:
            para(n, color=RED, indent=0.2, space_after=3)

    if d.get("intro"):
        doc.add_heading("Covering note", 1)
        for p_ in d["intro"]:
            para(p_)

    if d.get("issue_map"):
        doc.add_heading("共通議題對照表", 1)
        para("同一議題只寫一次完整回覆，其餘位置交叉引用，避免自相矛盾。", italic=True,
             color=GREY)
        t = doc.add_table(rows=1, cols=5)
        t.style = "Light Grid Accent 1"
        for i, h in enumerate(["#", "議題", "提出者", "性質", "完整回覆寫在"]):
            cell = t.rows[0].cells[i]
            cell.text = ""
            run = cell.paragraphs[0].add_run(h)
            run.bold = True
        for i, it in enumerate(d["issue_map"], 1):
            cells = t.add_row().cells
            for j, v in enumerate([str(i), it["issue"], ", ".join(it["raised_by"]),
                                   it.get("effort", ""), it.get("answer_in", "")]):
                cells[j].text = ""
                cells[j].paragraphs[0].add_run(v).font.size = Pt(9)

    for r in d["reviewers"]:
        doc.add_page_break()
        doc.add_heading(f"Response to Reviewer {r['id']}", 1)
        if r.get("role"):
            para(r["role"], italic=True, color=GREY)
        if r.get("recommendation"):
            para(f"Recommendation: {r['recommendation']}", bold=True)
        if r.get("opening"):
            para(r["opening"])
        for c in r["comments"]:
            head = c["id"]
            if c.get("kind"):
                head += f" — {KIND_LABEL.get(c['kind'], c['kind'])}"
            if c.get("tag"):
                head += f"  [{c['tag']}]"
            doc.add_heading(head, 2)

            para("Reviewer comment:", bold=True, color=BLUE, space_after=2)
            for ln in c["text"].split("\n"):
                if ln.strip():
                    para(ln, italic=True, color=GREY, indent=0.25, space_after=2)
            if c.get("cross"):
                para(f"同一議題亦見於：{', '.join(c['cross'])}", italic=True,
                     color=RED, indent=0.25)

            para("Response:", bold=True, color=BLUE, space_after=2)
            para(c.get("draft") or "［待填］", indent=0.25,
                 color=None if c.get("draft") else RED)

            if c.get("todo"):
                para("作者需決定／補充：", bold=True, color=RED, space_after=2)
                for t_ in c["todo"]:
                    para("• " + t_, color=RED, indent=0.4, space_after=2)
            if c.get("fallback"):
                para("若無法執行，可用的防守說法：", bold=True, color=RED, space_after=2)
                para(c["fallback"], italic=True, indent=0.4)

            para("Changes in the manuscript: page ____, line ____", bold=True,
                 space_after=14)

    if d.get("checklist"):
        doc.add_page_break()
        doc.add_heading("投稿前檢查清單", 1)
        for g in d["checklist"]:
            doc.add_heading(g["group"], 2)
            for i in g["items"]:
                para("☐  " + i, indent=0.2, space_after=3)

    doc.save(str(path))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("comments", type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--basename", default="response_to_reviewers")
    a = ap.parse_args()
    d = json.loads(a.comments.read_text(encoding="utf8"))
    a.out.mkdir(parents=True, exist_ok=True)

    md_path = a.out / f"{a.basename}.md"
    md_path.write_text(md_doc(d), encoding="utf8")
    docx_path = a.out / f"{a.basename}.docx"
    build_docx(d, docx_path)

    n = sum(len(r["comments"]) for r in d["reviewers"])
    print(f"{n} comments from {len(d['reviewers'])} reviewer(s)")
    print(f"wrote {md_path}")
    print(f"wrote {docx_path}")


if __name__ == "__main__":
    sys.exit(main())
