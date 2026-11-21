# Service 1 - Medical language and grammar editing

Goal: the manuscript reads as if written by a careful native-English clinician-scientist, and
says exactly what the authors meant - no more, no less.

## Levels of edit

Apply all three unless the user asks for a light touch.

1. **Mechanical** - grammar, spelling, punctuation, articles (a / an / the), subject-verb
   agreement, singular / plural, prepositions, parallel structure, run-on sentences.
2. **Register and terminology** - conventional medical phrasing, precise terms, consistent
   nomenclature, correct tense by section, units and number style.
3. **Clarity and flow** - one idea per sentence, topic sentences, logical connectors, removal
   of redundancy, paragraph order within a section.

Do not do a fourth level - restructuring the argument or cutting content - without asking.
That is the job of the critical appraisal; mention the need there instead.

## Conventions

**Tense by section**
- Introduction: present for established knowledge; present perfect for the literature
  ("Several studies have shown ..."); past for a specific prior study's findings.
- Methods and Results: past.
- Discussion: past for this study's findings, present for their interpretation.
- Figure / table legends: present.

**Voice.** Prefer active where the actor matters ("We randomised ...") if the journal allows
first person; passive is acceptable in Methods. Do not flip every sentence - consistency
within a section matters more.

**Patient-first, non-stigmatising language** (AMA Manual of Style, 11th ed.)
- "patients with diabetes", not "diabetics"; "participants", not "subjects" (human studies).
- A patient is not a "case"; a case is an instance of disease. "Cases" is fine in a
  case-control design.
- "died", not "expired" or "passed away"; "sex" for biological attribute, "gender" for
  identity - use the one that was actually measured.
- Avoid "suffering from", "victim of", "failed treatment" (the treatment failed).

**Causal language must match design.** Observational data: "was associated with", not "led
to", "reduced", "improved", "effect of". If the authors use causal verbs for a cohort or
cross-sectional study, do not silently soften them (that changes a claim) - soften and flag
it in the change log with the reason, and raise it in the appraisal.

**Statistics wording**
- "statistically significant" - never "significant" alone when a statistical meaning is
  intended, and never "highly / very / marginally significant" or "trend toward
  significance". Report the estimate, CI and exact P value instead.
- P values: exact to two or three decimals; "P < 0.001" for smaller; never "P = 0.000" or
  "P = NS". Capitalisation and italics of P follow the journal.
- "Correlated" only when a correlation was computed. "Incidence" vs. "prevalence",
  "rate" vs. "proportion" vs. "ratio", "risk" vs. "odds" vs. "hazard" - use the one the
  analysis produced.
- "Multivariable" (several predictors) vs. "multivariate" (several outcomes).
- Mean (SD) vs. mean ± SEM: state which; do not use ± for SD if the journal follows AMA.

**Numbers and units**
- SI units unless the journal says otherwise; space between number and unit (5 mg, 37 °C),
  no space before %.
- Spell out numbers that begin a sentence; numerals for all measurements.
- Consistent decimal places within a variable; do not report more precision than measured.
- Leading zero before decimals (0.05), except where the journal's style omits it for P.
- Thousands separator and decimal mark per journal (1,000 vs. 1000 vs. 1 000).

**Nomenclature**
- Genes italic, proteins roman; human genes all caps (*TP53*), mouse first-cap (*Trp53*).
- Species italic, full name at first mention (*Escherichia coli*, then *E. coli*).
- Drugs by generic (INN) name, lower case; brand name and manufacturer in parentheses only
  if needed. Devices / reagents: manufacturer, city, country if the journal requires.
- Abbreviations: define at first use in abstract and again in main text; do not define one
  that is used fewer than three times; no abbreviations in the title unless standard.

**Spelling.** US or UK per target journal; keep whichever the draft uses if no journal is
named, but make it consistent (randomized / randomised, tumor / tumour, hemoglobin /
haemoglobin, -ize / -ise).

## Patterns common in drafts by Chinese- / Mandarin-speaking authors

Watch for these; they are frequent and systematically fixable.

| Draft | Revised | Why |
|-------|---------|-----|
| "Patients were divided into two groups according to ..." (when not randomised) | "Patients were categorised / stratified by ..." | "Divided" suggests allocation |
| "The patient was a 65-year-old male" | "a 65-year-old man" | "male / female" are adjectives for humans |
| "... was significantly higher (P<0.05)" | "... was higher (12.3 vs 8.1 mmol/L; difference 4.2, 95% CI 1.9-6.5; P = 0.003)" | Report the estimate, not only the P value |
| "There were no significant difference" | "There was no statistically significant difference" | Agreement; precision |
| "Besides, ..." / "What's more, ..." | "In addition, ..." / "Furthermore, ..." | Register |
| "researches", "evidences", "informations", "equipments" | "research", "evidence", "information", "equipment" | Uncountable nouns |
| "In recent years, with the development of ..." | Delete, or state the specific gap | Empty opener |
| "It is well known that ..." | State the fact with a citation | Unsupported |
| "play an important / crucial role in" | Say what the role is | Vague |
| "On the one hand ... on the other hand" for non-contrasting points | "First ... Second ..." | Idiom misuse |
| "respectively" attached to a single item, or with mismatched lists | Restructure | Misuse |
| Missing or surplus articles: "the diabetes", "in patient with" | "diabetes", "in patients with" | Articles |
| "compared with control group" | "compared with the control group" | Articles |
| "This study aims to ..." in a completed study | "This study aimed to ..." | Tense |
| "prove", "confirm", "demonstrate clearly" | "suggest", "indicate", "support" (unless truly proven) | Overclaiming |
| "novel", "first", "unique" without a search to support it | Remove, or "To our knowledge, ..." | Unsupported priority claim |

## What never changes without a query

- Any number, unit, P value, CI, sample size, dose, time point.
- The direction or strength of a claim.
- A technical term you do not recognise - it may be field-specific. Query it.
- Reference numbers and their order.

When meaning is unclear, insert an author query rather than choosing an interpretation:
`[AQ3: "the latter group" - does this refer to the high-dose or the placebo group?]`

## Deliverables

1. **Edited manuscript** (.docx, tracked changes; see SKILL.md for the fallback).
2. **Change log** (`04_language_change_log.md`):
   - Summary: number of edits by category, the 5-10 recurring patterns found (so the author
     learns, not just accepts).
   - Substantive edits table - only edits that go beyond mechanics:

     | Para | Original | Revised | Reason |
     |------|----------|---------|--------|

   - Author queries, numbered `AQ1...`, each with location and the specific question.
   - Global decisions: spelling variety, abbreviation list, terminology standardised
     (e.g. "'subjects' → 'participants' throughout").
3. Apply the same edits to **figure legends, table titles / footnotes and supplementary
   text** - they are part of the manuscript and reviewers read them first.
