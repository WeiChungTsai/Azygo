# Service 2 - Formatting to a journal's author guidelines

Goal: a manuscript that passes the journal's technical check on first submission, with a
checklist showing what was changed and what the author still has to do.

## Contents
1. Get the guidelines
2. Extract the requirements
3. Apply to the manuscript
4. References
5. Figures and supplementary files
6. Compliance checklist (deliverable)
7. Reference style cheat-sheet

## 1. Get the guidelines

Author guidelines change several times a year, and differ by **article type** within one
journal. Always work from the live page.

1. Identify the journal exactly (full title, publisher) and the article type the manuscript
   fits (Original Article, Brief Report, Research Letter, Review, Case Report ...).
2. Fetch the journal's "Instructions for Authors" / "Author Guidelines" / "Submission
   Guidelines" page, and any linked pages for article types, reference style, figure
   preparation, and reporting / data-sharing policy.
3. If the fetch fails (paywall, blocked host, PDF only): tell the user plainly and ask them
   to paste the text or upload the PDF. Do **not** fall back on memory and call the result
   compliant. You may give a provisional format from the cheat-sheet below, clearly labelled
   "provisional - not checked against current guidelines".
4. Record the URL and the date accessed at the top of the checklist.

If the user has not chosen a journal, offer a shortlist of 3-5: match scope, study design,
typical sample size / level of evidence, article-type limits, open-access cost, and whether
the reference list already cites that journal. Give a realistic tier spread (one ambitious,
two or three realistic, one safe). Do not quote impact factors from memory as facts - say
they should be verified.

## 2. Extract the requirements

Pull these into a table before touching the manuscript. Leave a cell as "not stated" rather
than guessing.

| Item | Requirement | Source section |
|------|-------------|----------------|
| Article type and its definition | | |
| Main-text word limit (and what it excludes) | | |
| Abstract: structured or not, headings, word limit | | |
| Title: character / word limit; running title | | |
| Keywords: number, MeSH required? | | |
| Extra boxes: Key Points, Highlights, "What is known / What this adds", plain-language or lay summary, graphical abstract | | |
| Section order and required headings | | |
| Max. number of references | | |
| Max. number of tables + figures | | |
| Reference style: in-text (numbered superscript / bracket / author-year), list format, et al. rule, journal-name abbreviation, DOI required? | | |
| Title page contents: authors, degrees, affiliations, ORCID, corresponding author, word counts | | |
| Blinding: single / double-anonymised (need separate title page, removal of identifying text?) | | |
| Declarations: ethics / IRB number, consent, trial registration, funding, conflicts of interest, author contributions (CRediT?), data availability, acknowledgements, AI-use statement | | |
| Reporting guideline checklist required? (CONSORT, STROBE, PRISMA ...) | | |
| Text format: font, size, spacing, line numbers, page numbers, file type | | |
| Tables: editable, placement (in-text or end), footnote symbols | | |
| Figures: file type, resolution (dpi), colour mode, size, fonts, legends location | | |
| Supplementary material: allowed formats, naming, citation style ("Supplementary Table S1" vs "eTable 1") | | |
| Units, spelling (US / UK), abbreviations policy | | |
| Cover letter requirements; suggested reviewers | | |
| Fees (APC, page / colour charges) - for the author's information | | |

## 3. Apply to the manuscript

Work on a copy. Order of work:

1. **Structure**: reorder / rename sections and headings; build the title page; add missing
   mandatory sections as headed placeholders with a clear `[AUTHOR TO COMPLETE: ...]` -
   never write an ethics number, funding source or conflict statement for the author.
2. **Abstract**: restructure to the required headings; trim to the limit without dropping
   the primary outcome's numbers.
3. **Length**: count main-text words the way the journal defines them. If over, do not cut
   content silently - propose specific cuts (which paragraph, how many words saved, where
   to move it, e.g. to the supplement) and apply only the safe ones (redundancy, repetition
   of table data in text).
4. **Style**: spelling variety, units, abbreviation rules, number style, P-value style.
5. **Citations and references**: see section 4.
6. **Display items**: renumber figures / tables / supplementary items in order of first
   citation; rename to the journal's convention; move legends where the journal wants them.
7. **Layout**: font, spacing, line and page numbering, margins.
8. If double-anonymised: separate title page; strip identifying details from text, file
   properties, acknowledgements and self-citations phrased as "we previously showed".

## 4. References

The single most error-prone part of any manuscript. Two separate jobs:

**A. Verify** (do this even if the style is already right)
- Each reference exists and its details are correct. Look it up - PubMed tool if present,
  otherwise Crossref / the DOI resolver. Check authors, title, journal, year, volume, pages
  or e-locator, DOI.
- Flag: retracted articles, references that cannot be found, duplicates, preprints since
  published (cite the published version), citations of abstracts or personal communications
  where the journal forbids them, heavy self-citation, and references older than needed
  when a recent guideline or meta-analysis exists.
- Spot-check that the cited paper actually supports the sentence citing it, at least for
  the claims the argument depends on. A wrong citation is a common reviewer catch.
- Anything you cannot verify stays as the author wrote it, marked `[VERIFY]`. Do not fill
  in a plausible-looking volume, page or DOI - a fabricated reference is worse than an
  incomplete one.

**B. Restyle**
- In-text: convert to the required system (superscript, bracketed number, author-year);
  position relative to punctuation per the journal; ranges ("3-5") and lists ("1,4,7").
- Renumber strictly by order of first appearance, including citations that first appear in
  tables and figure legends (most journals number these at the point the table / figure is
  first cited in the text).
- List: author-count and et al. rule, initials format, title capitalisation, journal
  abbreviation (NLM Catalog), italics / bold, year-volume-issue-pages punctuation, DOI form.
- If over the reference limit, propose which to drop (redundant support for the same point,
  older of two equivalent citations) - let the author decide.
- If the manuscript uses EndNote / Zotero / Mendeley field codes, tell the user: changing
  the output style in the reference manager is safer than editing the text, and plain-text
  edits will be overwritten on the next refresh. Give them the style name to select, and
  still deliver the verification results.

## 5. Figures and supplementary files

Figures arrive as .pptx. Check each slide / panel against the journal's rules and report:

- Count vs. limit; multi-panel labelling (A, B, C - capital or lower case, position).
- Font family and minimum size at final print width; line weights.
- Colour: colour-blind-safe palette, no red / green only contrasts; RGB vs. CMYK.
- Resolution: PowerPoint exports at 96 dpi by default, which most journals reject. Tell the
  user the required dpi and the export route (vector PDF / EPS / TIFF at 300-600 dpi).
- Legends: self-contained - what is shown, n per group, what error bars represent, the
  statistical test, definition of symbols (* / ** / ns) and all abbreviations, scale bars,
  staining / magnification for micrographs.
- Image integrity: no spliced lanes without dividing lines, uncropped blots available for
  the supplement if the journal asks, no selectively adjusted contrast.
- Patient images: consent stated; identifying features removed.
- Reused or adapted figures: permission and credit line.

Supplementary: single PDF or separate files as required; own numbering series; each item
cited in the main text; a title page / table of contents if the journal wants one.

## 6. Compliance checklist (deliverable)

`05_<journal>_compliance_checklist.md`:

```markdown
# <Journal> - <Article type> - compliance checklist
Guidelines source: <URL>   Accessed: <date>

## Summary
<3-5 lines: ready / not ready, the blocking items>

## Requirements
| # | Requirement | Journal rule | Manuscript now | Status | Action |
|---|-------------|--------------|----------------|--------|--------|
| 1 | Main-text words | <= 3000 | 3412 | Not met | Cut 412 words - see proposals |
Status: Done (fixed by me) / Met (already compliant) / Not met - author action / Not stated

## Author must complete
<numbered list of [AUTHOR TO COMPLETE] placeholders and why each is needed>

## Proposed cuts (if over length)
## Reference verification
| Ref | Issue | Detail |
## Figure and supplementary issues
## Submission package still needed
<cover letter, reporting checklist, ICMJE forms, suggested reviewers, graphical abstract ...>
```

Offer to draft the cover letter and fill in the reporting-guideline checklist with page /
line numbers - both are usually required and authors usually leave them to the last minute.

## 7. Reference style cheat-sheet

For recognising and producing styles. The journal's own guidelines override this table -
many journals use a house variant (author count before et al. is the usual difference).

**Vancouver / ICMJE / NLM** (most clinical journals)
In-text: numbers in order of appearance, (1) or [1] or superscript.
`Halpern SD, Ubel PA, Caplan AL. Solid-organ transplantation in HIV-infected patients. N Engl J Med. 2002;347(4):284-7.`
List 6 authors then et al. (NLM lists all; many journals cut to 3 or 6). Abbreviated journal
title, no italics, elided page ranges.

**AMA 11th** (JAMA network and many US journals)
In-text: superscript numbers after punctuation.
`Halpern SD, Ubel PA, Caplan AL. Solid-organ transplantation in HIV-infected patients. *N Engl J Med*. 2002;347(4):284-287. doi:10.1056/NEJMsb020632`
Up to 6 authors; if 7 or more, first 3 then et al. Journal italic, full page range, doi
without URL prefix.

**NEJM**
`Halpern SD, Ubel PA, Caplan AL. Solid-organ transplantation in HIV-infected patients. N Engl J Med 2002;347:284-7.`
Up to 6 authors; 7 or more: first 3 then et al. No full stop after journal title, no issue.

**The Lancet**
`Halpern SD, Ubel PA, Caplan AL. Solid-organ transplantation in HIV-infected patients. *N Engl J Med* 2002; **347:** 284-87.`
Up to 6 authors; more than 6: first 3 then et al. Journal italic, volume bold.

**BMJ**
`Halpern SD, Ubel PA, Caplan AL. Solid-organ transplantation in HIV-infected patients. *N Engl J Med* 2002;347:284-7. doi:10.1056/NEJMsb020632`
Up to 6 authors; 7 or more: first 3 then et al. Superscript in-text.

**Nature**
`Halpern, S. D., Ubel, P. A. & Caplan, A. L. Solid-organ transplantation in HIV-infected patients. *N. Engl. J. Med.* **347**, 284-287 (2002).`
Superscript numbers; up to 5 authors, 6 or more: first author et al. Journal abbreviated
with full stops and italic, volume bold, year last in parentheses.

**Cell / Cell Press**
Numbered in-text (changed from author-year in 2022-23; check the journal).
`Halpern, S.D., Ubel, P.A., and Caplan, A.L. (2002). Solid-organ transplantation in HIV-infected patients. N. Engl. J. Med. *347*, 284-287.`
Up to 10 authors, then et al.

**APA 7th** (psychology, nursing, some public-health journals)
In-text: (Halpern et al., 2002).
`Halpern, S. D., Ubel, P. A., & Caplan, A. L. (2002). Solid-organ transplantation in HIV-infected patients. *New England Journal of Medicine, 347*(4), 284-287. https://doi.org/10.1056/NEJMsb020632`
Up to 20 authors; full journal title; alphabetical list.

**Harvard / author-year house styles** (Elsevier "Harvard", Springer "Basic")
In-text: (Halpern et al., 2002). Alphabetical list. Details vary by publisher - follow the
journal's examples literally.

Non-journal items (books, chapters, websites, preprints, datasets, software, guidelines)
each have their own pattern in every style - copy the journal's own example for that type.
