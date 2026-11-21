---
name: medical-manuscript-review
description: >-
  Edits, reformats, critiques and peer-reviews biomedical / clinical manuscript drafts
  (main text .docx, supplementary files, figures as .pptx). Four services: (1) professional
  medical-English language and grammar editing, (2) reformatting the manuscript and reference
  list to a target journal's author guidelines, (3) a hard-nosed critical appraisal with 10-20
  major and minor concerns and firm recommendations from basic-science and clinical viewpoints,
  (4) a simulated panel of three independent peer reviewers plus an editor's synthesis.
  Use this skill whenever the user uploads or mentions a paper, manuscript, 論文, 論文草稿, 文稿,
  投稿, supplementary, figure legends, cover letter or response to reviewers and asks for
  anything like 修改文法, 潤稿, 英文編修, 改成某期刊格式, reference 格式, author guidelines,
  審稿, 評讀, reviewer comments, major/minor concerns, "is this ready to submit", or
  "which journal fits" - even if they name only one of the four services or do not say "review".
---

# Medical manuscript review

Help a clinician-researcher get a manuscript from draft to submission-ready. The user is the
author. They know their data better than you do, but they are too close to the paper to see
what a sceptical reviewer will see, and English is often not their first language. Your value
is precise medical English, exact compliance with a journal's rules, and the honest, specific
criticism that co-authors are usually too polite to give.

## Two ways to work

**The staged pipeline (A-G)** — read `references/pipeline.md`. Adapted from
google-research/paper-orchestra: profile → PubMed literature → figure audit →
appraisal → reviewer panel → revise the .docx with tracked changes → an
independent re-review that scores the round and reverts it if it did not
improve. Use this when the user wants the manuscript actually revised, not
just critiqued, and when they are driving it from the local runner in
`tools/runner/`.

**A single service on its own** — the table below. Use this when the user asks
for one thing ("just the reviewer comments", "reformat for this journal").

## The four services

| # | Service | Reference to read first | Main deliverable |
|---|---------|-------------------------|------------------|
| 1 | Language and grammar editing | `references/language-editing.md` | Edited .docx with tracked changes + change log |
| 2 | Journal formatting, including references | `references/journal-formatting.md` | Reformatted .docx + compliance checklist |
| 3 | Critical appraisal (10-20 concerns) | `references/critical-appraisal.md` | Numbered major / minor concerns report |
| 4 | Three-reviewer panel | `references/reviewer-panel.md` | Three reviewer reports + editor's synthesis |

Run only what the user asked for. If they ask for "everything" or do not specify, run in the
order **3 → 4 → 1 → 2**: there is no point polishing sentences in a paragraph the appraisal
says must be rewritten, and formatting comes last because it depends on final word counts and
the final reference list. Say this order in one line so the user can object.

Only two things are worth stopping to ask about, because guessing them wastes the whole run:

- **Service 2 needs a target journal.** If none is named, ask (and offer to shortlist 3-5
  suitable journals from the manuscript's scope and study design).
- **Missing files.** If the text cites figures or supplementary tables that were not uploaded,
  list which ones are missing and continue with what you have.

Everything else - study type, field, article type - infer from the manuscript and state your
inference.

## Step 1: Take inventory and extract

Extract every uploaded file before forming any opinion:

```bash
python scripts/extract_manuscript.py <file1.docx> <file2.pptx> ... --out <workdir>
```

This writes, per file, a markdown text dump (headings, paragraphs with stable `[P12]` ids,
tables, footnotes, comments, and whether unaccepted tracked changes are present) and, for
.pptx, per-slide text, speaker notes, embedded images and - when LibreOffice is installed -
a PNG render of every slide. Read `<workdir>/INVENTORY.md` first; it lists what was found and
gives word counts per section.

**Look at the figures, do not just read their text.** Open the rendered slide PNGs (or the
embedded images) with your image-reading ability. Most figure problems - unlabelled axes,
missing error-bar definitions, n not shown, inconsistent colours between panels, numbers that
disagree with the text - are invisible in the extracted text.

**Read the comments left in the file.** `INVENTORY.md` flags them and the text dump lists
them at the end. Co-authors' and supervisors' unresolved comments tell you what the team
already knows is unfinished, which figure was inserted without renumbering the rest, and
which paragraph a senior author has already asked to be rewritten. Raising those as if you
found them independently wastes everyone's time; confirming them adds weight. Comments are
often in the authors' own language - read them in whatever language they are in.

PDF inputs: read them directly. Other formats (.xlsx supplementary tables, .csv): open with
the usual tools.

Then build a one-screen **manuscript profile** and show it to the user before the main output,
so that a wrong inference is caught early:

- Title, article type, study design (RCT, cohort, case-control, cross-sectional, diagnostic
  accuracy, systematic review / meta-analysis, case report / series, animal, in-vitro,
  mixed translational, prediction model, qualitative ...)
- Clinical field, population, exposure / intervention, comparator, primary outcome
- Central claim in one sentence
- Applicable reporting guideline (see table in `references/critical-appraisal.md`)
- File inventory: what was received, what is cited but missing

## Step 2: Cross-check consistency

Do this once, whichever service was requested; every service depends on it, and these are the
errors authors most fear a reviewer finding. `INVENTORY.md` already reports placeholders left
in the text, stray empty paragraphs and references that are never cited - start from those,
then do the checks a script cannot:

- **Tabulate the n per group from every figure, table and panel, side by side.** Group sizes
  that cannot all be true of the same animals or patients are among the most damaging things
  a reviewer finds, and the mismatch is invisible unless you lay the numbers out together.
  Measurements described as simultaneous must share an n; a downstream analysis cannot have
  a larger n than the upstream one it derives from.
- **Recompute every statistic you can** from the counts and summary values printed in the
  text and figures: percentages, totals, a Fisher exact or chi-square from a 2×2, a
  fold-change from two means. Two things come out of this - you confirm which test produced
  a reported P value, and you find the comparisons the authors describe in words but never
  actually tested. Also check that a stated SD or SEM is compatible with the plotted range
  (for N observations, SEM × √N must be a credible SD for data spanning that range).
- **Check numbers against physiology before accepting them.** A time window, threshold, dose
  or cut-off that is reasonable in one species may be nonsense in another - a 0.2 s coupling
  window spans more than one cardiac cycle in a mouse. Work out what the number means in the
  organism studied.
- **Check instrument settings against the analysis.** Sampling rate and amplifier bandwidth
  must support the frequency band analysed; filter settings must match what is claimed to be
  isolated. A paper cannot analyse content its hardware never acquired.
- Participant/animal flow: do the numbers at each stage add up; do denominators change
  silently? Is there a flow diagram at all?
- Every figure, table and supplementary item is cited in the text, in order, and exists.
  Supplementary items are the usual casualty - check each one's number against the panel
  references inside its own legend, which drift out of step when a figure is inserted.
- Every in-text citation has a reference-list entry and vice versa; numbering is sequential;
  no reference appears twice under different numbers.
- Abbreviations defined at first use in abstract and again in main text; used consistently.
- Methods ↔ Results: every analysis described is reported; every result has a method.
  Watch for analyses run several ways (two instruments, three settings) where only the
  variant that produced a result is presented as the pre-planned one.
- Conclusions ↔ Results: does the abstract's conclusion claim more than the data show? Is
  every claim in the abstract and conclusions traceable to a reported, tested comparison?

## Step 3: Run the requested service(s)

Read the matching reference file before starting each service; they hold the standards,
templates and worked examples. Summary of what each demands:

**Service 1 - Language.** Edit for accuracy, concision and conventional medical register
without changing scientific meaning. Never alter a number, a result, or the strength of a
claim silently; if a sentence is ambiguous, flag it with a query to the author instead of
guessing. Deliver tracked changes so the author can accept or reject each edit.

**Service 2 - Formatting.** Work from the journal's *current* author guidelines, fetched
live - these change often and memory is unreliable. If the page cannot be fetched, say so and
ask the user to paste the guidelines or upload the PDF; do not format from recollection and
present it as compliant. Reformat references to the journal's style, verifying each against
PubMed / Crossref where a tool is available, and never invent or "complete" bibliographic
details you cannot verify - mark them `[VERIFY]` instead.

**Service 3 - Critical appraisal.** Produce 10-20 numbered concerns, split into Major and
Minor, each tied to a specific location in the manuscript, each with a firm, concrete
recommendation. Be tough: the aim is to surface every reason a reviewer could reject the
paper while the author can still fix it. Tough means specific and evidence-based, not rude.

**Service 4 - Reviewer panel.** Three reviewers with different expertise read the paper
independently, then an editor synthesises. Independence matters - real reviewers disagree,
and the disagreement is informative. Where subagents are available, give each reviewer a
separate subagent that has not seen the others' reports.

## Step 4: Deliver

Write outputs as files in the user's working directory (not buried in chat) and give a short
summary in chat with the top findings.

Default file names:

- `01_manuscript_profile.md`
- `02_critical_appraisal.md` (service 3)
- `03_reviewer_panel.md` (service 4)
- `04_<name>_language_edited.docx` + `04_language_change_log.md` (service 1)
- `05_<name>_<journal>_formatted.docx` + `05_<journal>_compliance_checklist.md` (service 2)
- `06_response_to_reviewers.docx` / `.md` - the point-by-point reply, built with
  `scripts/make_response_template.py`. Offer it after service 4, and whenever the user
  brings back a real decision letter; `references/reviewer-panel.md` says how to fill it.

Pipeline runs use the stage names and outputs in `references/pipeline.md` instead.

## Scripts

| Script | What it does |
|--------|--------------|
| `extract_manuscript.py` | .docx/.pptx → markdown with `[P..]` ids, slide renders, and an audit of placeholders, stray paragraphs and uncited references |
| `extract_references.py` | the reference list → a structured worklist for PubMed verification |
| `revise_docx.py` | an edits JSON → a .docx with real tracked changes and Word comments |
| `refine_gate.py` | two review JSONs → ACCEPT or REVERT for a revision round |
| `make_response_template.py` | reviewer comments → a point-by-point response .docx |

For .docx output with tracked changes, use the `docx` skill if one is available in the
session - it handles tracked-change markup properly. If not, produce the clean edited .docx
with python-docx plus a change log (original → revised, with paragraph id and reason), so
that the author still sees every change. Work on a copy; never overwrite the uploaded file.

Figures in .pptx: do not redraw the user's figures unless asked. Report figure problems
(per slide / panel) and fix only text-level items that are safe - legends, panel labels,
font and size required by the journal - on a copy.

## Language of the output

- Text that goes **into the manuscript** (edited sentences, legends, cover letter, reviewer
  reports written as a journal would send them): English.
- **Explanations to the user** (profile, summaries, reasons for edits, the appraisal's
  commentary): the language the user writes in. A user writing in Traditional Chinese gets
  繁體中文 commentary with key terms and quoted manuscript text kept in English.
- If the user states a preference, follow it.

## Integrity rules

These protect the author; breaking them can cause a retraction.

- **Do not fabricate.** No invented data, statistics, citations, DOIs, ethics approval
  numbers or trial registrations. When something is missing, say it is missing.
- **Do not change the science while editing language.** "Associated with" must not become
  "caused"; "may" must not become "does"; P = 0.06 must not become "significant".
- **Separate fact from inference.** "The Methods do not state how missing data were handled"
  is a fact. "The authors probably used complete-case analysis" is an inference - label it.
- **Confidentiality.** A draft is unpublished work and may contain patient information. Do
  not send manuscript text to external services beyond what the task needs (looking up a
  reference by its citation is fine; pasting the abstract into a third-party site is not).
  If you notice identifiable patient information (names, chart numbers, faces, exact dates),
  flag it prominently.
- **AI-use disclosure.** Many journals require authors to disclose AI assistance in writing.
  Remind the user once, in the delivery summary, to check the target journal's policy.
- **Be honest about limits.** You cannot re-run the analysis or see raw data. Say what you
  could not verify rather than implying it was checked.
