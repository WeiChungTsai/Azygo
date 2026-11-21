# Service 3 - Critical appraisal: 10-20 major and minor concerns

Goal: tell the author, before a journal does, every substantive reason this paper could be
rejected or sent back for major revision - and exactly what to do about each one.

## Contents
1. Stance
2. How to read the paper
3. What to probe (clinical lens, basic-science lens, statistics, reporting)
4. Major vs. minor
5. Writing a concern
6. Report template
7. Reporting guidelines table

## 1. Stance

Write as a senior reviewer for a journal one tier above the target: rigorous, sceptical of
every claim, uninterested in sparing feelings, but fair. The user asked for hard criticism,
so:

- No praise sandwich. One short paragraph of genuine strengths at the top is enough.
- Do not hedge a real flaw into a suggestion. "The authors may wish to consider discussing
  confounding" is useless. "The association is uninterpretable without adjustment for
  baseline eGFR and diuretic use; add both to the model or remove the causal language" is
  what helps.
- Every concern must be **anchored** (section / paragraph id / table / figure panel, with a
  short quote or the specific number) and **actionable** (a concrete analysis, experiment,
  rewrite or deletion). A concern you cannot anchor is a hunch - drop it or label it as a
  question.
- Tough is not the same as inventing problems. If the paper does something well, do not
  manufacture an objection to fill the list. Ten real concerns beat twenty padded ones;
  the range is 10-20, and the count should follow the paper.
- Distinguish **fatal** (cannot be fixed without new data or a different design), **fixable
  with new analysis / experiments**, and **fixable by rewriting**. Authors need to know
  which they are facing.

## 2. How to read the paper

Read in this order, taking notes with paragraph ids:

1. Title and abstract only. Write down the claim and what evidence you would need to
   believe it. This is the standard the rest of the paper is held to.
2. Figures, tables and their legends, without the text. What do the data show on their own?
3. Methods. Could you repeat the study? Is the design capable of supporting the claim?
4. Results. Do they report what the Methods promised - all of it, in that order?
5. Discussion and conclusions. Do they follow from the results, or from what the authors
   hoped to find?
6. Introduction last. Is the gap real, and is the cited background fair and current?
7. Supplementary material. Is anything hidden there that changes the story (a failed
   sensitivity analysis, a much smaller n, a negative replicate)?

Then ask the three questions an editor asks: **Is it true? Is it new? Does it matter?**
Check novelty honestly - if a literature search tool is available, look for the closest
prior work the authors did not cite; a missed key paper is a major concern.

## 3. What to probe

Apply both lenses to every paper. A clinical paper still makes mechanistic assumptions, and
a bench paper still claims clinical relevance in its last paragraph.

### Clinical / epidemiological lens

- **Question**: is the PICO explicit? Is the primary outcome pre-specified, single, and
  clinically meaningful (hard endpoint vs. surrogate)?
- **Design vs. claim**: can this design support causal language? Was the study registered
  or a protocol published before data collection, and does the paper match it (outcome
  switching)?
- **Selection**: source population, consecutive vs. convenience sampling, inclusion /
  exclusion applied when and by whom, how many screened vs. enrolled vs. analysed. Single
  centre? Referral bias? Is the control group drawn from the same population and period?
- **Bias, by name**: confounding (and confounding by indication), immortal time, selection,
  survivor, lead-time, length-time, detection / ascertainment, recall, misclassification of
  exposure or outcome, attrition, reverse causation, collider bias from conditioning on a
  post-exposure variable, Table 2 fallacy. Name the specific bias and the direction it
  would push the estimate.
- **Measurement**: validated instruments, blinded outcome assessment, inter-rater
  agreement, timing relative to exposure, central vs. local labs.
- **Randomised trials**: sequence generation, allocation concealment, blinding of whom,
  ITT vs. per-protocol, protocol deviations, crossover, early stopping, baseline imbalance,
  adherence, co-interventions, sample-size justification and whether the assumed effect
  was realistic.
- **Diagnostic / prediction studies**: spectrum of patients, reference standard applied to
  all, blinded index test, pre-specified thresholds, calibration as well as discrimination,
  internal and external validation, events per variable, data leakage, clinical utility
  (decision curve), comparison against the existing standard rather than against nothing.
- **Systematic reviews**: registration, search completeness and date, duplicate screening,
  risk-of-bias tool and how it was used, heterogeneity handling, small-study effects,
  certainty of evidence (GRADE), whether pooling was appropriate at all.
- **Follow-up**: duration adequate for the outcome, loss to follow-up by arm, competing
  risks, informative censoring.
- **Clinical meaning**: absolute as well as relative effects, NNT / NNH, minimal clinically
  important difference, harms reported as carefully as benefits.
- **Generalisability**: who was excluded, what setting, what era of standard care, what
  ethnicity / health system - and does the Discussion admit it?
- **Ethics**: IRB approval and number, consent or waiver, trial registration date vs. first
  enrolment, data-sharing statement, patient privacy in images and tables.

### Basic / translational science lens

- **Hypothesis and logic chain**: is each step from observation to mechanism supported by
  an experiment, or bridged by assertion? Correlation between a marker and a phenotype is
  not mechanism. Is there both necessity (loss-of-function) and sufficiency
  (gain-of-function / rescue)?
- **Is the measurement actually measuring what it is named after?** This is the question
  that decides papers built on a new or transferred technique, and it is easy to skip
  because the paper's own name for the signal is used throughout. Ask what else could
  generate it - a neighbouring organ, movement, a sharp electrical transient whose
  high-frequency edge passes the filter - and ask what control would exclude that. The
  decisive control is usually cheap and negative: abolish the true source (pharmacological
  blockade, post-mortem recording, a null preparation) and show the signal goes with it.
  If the authors' own intervention should have abolished the signal and did not, that is
  the finding, whatever the paper concludes.
- **Does the manipulation that carries the causal claim have independent verification?**
  A knockout, a lesion, a denervation or a depletion must be documented, not assumed -
  histology, protein or transmitter content, or a functional assay. Check the protocol is
  reported in enough detail to repeat: dose per body weight, route, schedule, vehicle, and
  the timing relative to the experiment.
- **Acquisition settings vs. analysis settings**: sampling rate, bandwidth, filter order
  and detection thresholds must be reported and must be mutually compatible. Content above
  the acquisition bandwidth does not exist, however it is filtered afterwards.
- **Anaesthesia and sedation**: which agent, what dose per body weight, how depth was
  judged, how long before recording. Many agents profoundly suppress exactly what such
  studies measure. Watch for an agent invoked to explain away a null result while the
  positive results from the same recordings are treated as physiological - that asymmetry
  is indefensible and reviewers pounce on it.
- **Models**: is the cell line / animal model appropriate and authenticated (STR profiling,
  mycoplasma)? One cell line is an anecdote. Sex, age, strain, housing of animals. Does the
  model reflect the human disease stage being discussed? Dose and exposure relevant to
  human pharmacology?
- **Controls**: positive, negative, vehicle, isotype, loading controls; scrambled / off-
  target controls for knock-down (at least two independent siRNA / sgRNA, or rescue);
  antibody validation; littermate controls.
- **Replication and the unit of analysis**: biological vs. technical replicates; n stated
  per experiment and what n is (animals, independent cultures, wells, cells, fields?).
  Pseudoreplication - treating cells or fields from one animal as independent - is among
  the commonest fatal flaws. Was the experiment repeated independently?
- **Rigor**: randomisation and blinding of animal allocation and of outcome assessment;
  pre-specified exclusion criteria; sample-size rationale; representative images that are
  actually representative, with quantification of all samples.
- **Image and data integrity**: blots with loading controls from the same membrane,
  molecular-weight markers, no unmarked splicing; duplicated or re-used panels; saturated
  bands quantified as if linear; scale bars; flow-cytometry gating strategy shown.
- **Omics**: batch effects, multiple-testing correction, validation by an orthogonal
  method, independent cohort, data deposited in a public repository with accession number.
- **Human samples**: how selected, how matched, pre-analytic handling, clinical annotation,
  blinded scoring.
- **Translational leap**: does the final paragraph claim a therapeutic implication that the
  experiments do not approach? What would it actually take to get there?
- **Alternative explanations**: list the two or three most plausible ones and whether any
  experiment rules them out.
- **Reagent reporting**: catalogue numbers, RRIDs, primer sequences, concentrations,
  exposure times - enough to repeat it.

### Statistics (both lenses)

- **Does the analysis match the design the authors declared?** A paper that states a
  factorial design (2 × 2, dose × time) and then reports only pairwise comparisons has not
  tested its own hypothesis: "A is significant and B is not" is not evidence of an
  interaction, and "treatment blocks the effect of exposure" *is* an interaction claim.
  Look for the interaction term; its absence is a major concern, not a quibble.
- **Was the headline comparison actually tested?** Trace every claim in the abstract,
  discussion and conclusions back to a specific reported test. Authors routinely assert
  that one group was protected, or that an effect was abolished, on the strength of one
  comparison being significant and a neighbouring one not being shown at all. Recompute the
  missing comparison where the counts allow; a claim that collapses at p = 0.08 is the most
  valuable thing you can hand the author before a reviewer finds it.
- **Were several analysis variants run?** Two instruments, three filter settings, four
  time points, several scales - if the supplement contains near-duplicate analyses and only
  one appears in the main text, the selection was almost certainly post hoc. Say so, and
  ask for it to be declared in the Methods rather than implied to be pre-planned.
- Test matches data type, distribution, pairing and design (repeated measures analysed as
  independent; t-tests across more than two groups; parametric tests on n = 3).
- Summary statistic matches the test: non-parametric analyses summarised with median (IQR),
  not mean ± SEM. Check that a quoted SD or SEM is arithmetically possible given the range
  of the plotted data.
- Significance threshold stated as < or ≤ - with ≤ 0.05, a result at exactly p = 0.050
  becomes "significant", which is worth catching.
- Multiplicity: number of outcomes, subgroups, time points, comparisons - any correction?
  Any sign of selective reporting or P-hacking (many P values just under 0.05)?
- Effect size with confidence interval reported, not P alone. Non-significant result
  described as "no difference" without considering power.
- Missing data: how much, why, how handled (complete-case, imputation), sensitivity.
- Model building: variables chosen a priori or by univariable screening / stepwise?
  Events per variable, collinearity, proportional-hazards and linearity assumptions
  checked, interaction terms justified, continuous variables dichotomised without reason.
- Subgroup claims without an interaction test; post-hoc analyses presented as planned.
- Matching / propensity scores: balance shown, analysis accounts for matching, residual
  confounding acknowledged, unmeasured-confounder sensitivity (e.g. E-value).
- Numbers that do not add up (see the consistency cross-check in SKILL.md) - report each.
- Software, version, two-sided alpha stated.

### Reporting and presentation

- Reporting-guideline items missing (section 7).
- Title or abstract conclusion overstating the results ("spin").
- Limitations paragraph that is generic or that omits the real limitation.
- Introduction that misrepresents or omits prior work; outdated references.
- Figures: unreadable, missing n / error-bar definition / test, truncated axes, bar charts
  hiding the distribution of small samples (show individual data points).
- Tables: no units, no denominators, inconsistent decimals, Table 1 with P values in an RCT.
- Conflict of interest or funder role not addressed.

## 4. Major vs. minor

**Major** - threatens the validity of the main conclusion, the paper's novelty, or its
ethical standing; or requires new data, new analysis or substantial rewriting. A reviewer
would not recommend acceptance until it is resolved.

**Minor** - affects clarity, completeness or presentation, but the conclusion stands either
way. Fixable in an afternoon.

Typical balance is 5-9 major and 5-11 minor, but report what is there. Do not promote minor
points to look thorough, and do not demote a fatal flaw to be kind. Typos and grammar are
not concerns - at most one collective minor point ("language editing needed throughout;
examples: ..."); the detail belongs to Service 1.

Order major concerns by severity, most damaging first. The author should be able to read
only the first three and know whether the paper is in trouble.

## 5. Writing a concern

Each concern has four parts:

1. **Headline** - the problem in one line, specific to this paper.
2. **Where and what** - location, the quote or number, and what is wrong.
3. **Why it matters** - what conclusion it undermines and in which direction; what a
   reviewer will infer.
4. **Required action** - a firm instruction. If there are alternatives, rank them: the
   proper fix, and the minimum acceptable fallback (usually: tone down the claim and
   declare the limitation explicitly).

Tag each with the kind of fix: `[New data]`, `[New analysis]`, `[Rewrite]`, `[Clarify]`.

**Weak (do not write like this):**
> The sample size is small and there may be some confounding. The authors should discuss
> this in the limitations.

**Strong:**
> **M2. The primary association is confounded by indication and the model does not address
> it.** `[New analysis]`
> *Where:* Methods P14; Table 2. Patients received drug X "at the discretion of the
> treating physician", and Table 1 shows the treated group was younger (61 vs 68 y) with
> higher baseline eGFR (72 vs 58 mL/min/1.73 m²). The Cox model in Table 2 adjusts only for
> age and sex.
> *Why it matters:* healthier patients were preferentially treated, so the reported HR of
> 0.62 for mortality would be expected even if the drug did nothing. As it stands, the
> abstract's conclusion ("X reduces mortality") is not supported.
> *Required:* (a) Adjust for baseline eGFR, heart failure, diabetes and concomitant RAAS
> blockade at minimum; preferably use propensity-score weighting with a balance table
> (standardised mean differences < 0.1). (b) Report an E-value for unmeasured confounding.
> (c) Use a landmark or time-varying exposure analysis - treatment started a median of 9
> days after admission (P16), so the current analysis also carries immortal-time bias.
> (d) If none of this is possible, replace all causal wording ("reduces", "effect",
> "benefit") with "was associated with" in the title, abstract and conclusion, and state
> confounding by indication as the principal limitation.

## 6. Report template

Write commentary in the user's language; keep quoted manuscript text and technical terms in
English.

```markdown
# Critical appraisal - <short title>

## Verdict
<3-5 sentences: the central claim; whether the data support it; the single biggest
threat; likely editorial outcome at the target journal as the paper stands (reject /
major revision / minor revision) and after the fixes below.>

## What the paper does well
<2-4 bullets, genuine only>

## Major concerns
### M1. <headline>  [tag]
**Where:** ...
**Why it matters:** ...
**Required:** ...
### M2. ...

## Minor concerns
### m1. <headline>  [tag]
<Same four parts, shorter - two to four lines is typical.>

## Inconsistencies and numerical errors found
| # | Location A | Location B | Discrepancy |
|---|------------|------------|-------------|

## Reporting-guideline gaps (<guideline>)
| Item | Required | Status in manuscript |
|------|----------|----------------------|

## Priority plan
| Priority | Concern | Kind of fix | Effort |
|----------|---------|-------------|--------|
<Ordered list of what to do first. Separate "must fix before submission" from "prepare an
answer for when reviewers ask".>

## What I could not assess
<Raw data, statistical code, missing files, areas outside what the manuscript shows.>
```

## 7. Reporting guidelines table

Use the current version from equator-network.org; check the item list rather than relying
on memory.

| Study type | Guideline |
|------------|-----------|
| Randomised trial | CONSORT (2025 update) + extensions (cluster, non-inferiority, pilot, harms, abstracts) |
| Trial protocol | SPIRIT |
| Cohort, case-control, cross-sectional | STROBE (+ RECORD for routinely collected data) |
| Systematic review / meta-analysis | PRISMA 2020 (+ PRISMA-NMA, -DTA, -ScR, -P); MOOSE for observational |
| Diagnostic accuracy | STARD |
| Prediction model (incl. machine learning) | TRIPOD+AI; risk of bias with PROBAST |
| AI intervention trials | CONSORT-AI, SPIRIT-AI; early clinical evaluation: DECIDE-AI |
| Case report | CARE |
| Case series (surgical) | PROCESS |
| Animal research | ARRIVE 2.0 |
| Quality improvement | SQUIRE 2.0 |
| Economic evaluation | CHEERS 2022 |
| Qualitative research | COREQ / SRQR |
| Mendelian randomisation | STROBE-MR |
| Genetic association | STREGA |
| Tumour-marker prognostic studies | REMARK |
| Observational studies in surgery | STROCSS |
| Clinical practice guidelines | AGREE II / RIGHT |
| Sex and gender reporting | SAGER |
