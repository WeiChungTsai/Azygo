# Service 4 - Three-reviewer panel

Goal: show the author what the decision letter is likely to look like - three independent
reports from reviewers with different expertise, and the editor's reading of them.

This differs from the critical appraisal (Service 3): that is one exhaustive audit written
for the author; this is a realistic simulation of how the paper will be received, including
disagreement between reviewers and each reviewer's blind spots and hobby-horses. If both
services run, the panel must not be a re-sorted copy of the appraisal - each reviewer reads
the manuscript afresh.

## Casting the panel

Pick three reviewers the handling editor would plausibly invite for *this* paper. Default
cast, adapted to the manuscript:

| Reviewer | Default profile | Reads for |
|----------|-----------------|-----------|
| **Reviewer 1 - Clinical content expert** | Senior clinician-investigator in the paper's specialty | Clinical relevance, patient selection, whether outcomes matter at the bedside, standard of care, fit with existing guidelines and trials, missing key literature, would this change practice |
| **Reviewer 2 - Methodologist / biostatistician** | Epidemiologist or statistician | Design validity, bias, sample size, analysis choices, multiplicity, missing data, reporting-guideline adherence, whether numbers add up, whether conclusions follow |
| **Reviewer 3 - Basic / translational scientist** | Bench scientist in the relevant mechanism | Biological plausibility, mechanism, experimental controls, replication, model validity, image / data integrity, reagent reporting, the translational leap |

Adapt the cast to the paper, and say who you chose and why:

- Purely clinical paper with no bench work: Reviewer 3 becomes a second content expert from
  an adjacent discipline (e.g. a radiologist for an imaging-heavy cardiology paper, a
  pharmacologist for a drug study) or a generalist reader representing the journal's
  audience.
- Purely basic paper: Reviewer 1 becomes a clinician judging disease relevance; Reviewer 2
  becomes an expert in the key technique (omics / imaging / animal models) plus statistics.
- Systematic review: Reviewer 2 is an evidence-synthesis methodologist.
- AI / prediction model: Reviewer 2 is a clinical-prediction or machine-learning
  methodologist.
- Case report: three is still fine - content expert, a related-specialty clinician, and a
  reviewer who judges novelty and educational value.

Give each a one-line professional description (field, seniority, what they care about) - no
names of real people. Let temperament vary realistically: one may be more favourable. Do
not make all three harsh by default; severity should follow from what each expert sees.

## Independence

Real reviewers do not see each other's reports, and that is why their overlap is
informative: a point raised independently by two reviewers is one the editor will insist on.

- If subagents are available, run each reviewer as a separate subagent. Give each: the
  extracted manuscript and figure renders, the manuscript profile, the target journal (if
  known), its own persona, and the report format below. Do **not** give them the Service 3
  appraisal or each other's output.
- If subagents are not available, write the three reports sequentially, and for each one
  re-read the manuscript from that reviewer's viewpoint before writing. Do not consult the
  earlier reports while drafting; reconcile only in the editor's synthesis.

Each reviewer stays within their competence, as real ones do: the clinician may say "I
defer to a statistical reviewer on the modelling, but ..." - and may also be wrong about
statistics in a way the methodologist then corrects. Leave such disagreements in.

## Reviewer report format

Reports are written in English, in the register of a real review addressed to the editor
and authors, so the author can practise responding to them. Add a short summary in the
user's language after each report if the user does not write in English.

```markdown
## Reviewer <n> - <role> (<one-line profile>)

**Recommendation:** Accept / Minor revision / Major revision / Reject
(or Reject and resubmit, if the journal uses it)

**Summary of the submission**
<3-5 sentences restating what was done and found, in the reviewer's own words. Shows the
paper was understood; exposes it when the paper's message is unclear.>

**Overall assessment**
<One paragraph: importance, originality, soundness, and the main reason for the
recommendation.>

**Major comments**
1. <Specific, located, with what the authors must do. Number every point - authors must
   respond point by point.>
2. ...

**Minor comments**
1. ...

**Scores** (1 = poor, 5 = excellent)
Originality _ | Scientific rigour _ | Clinical / scientific importance _ |
Clarity of presentation _ | Appropriateness for the journal _

**Confidential comments to the editor**
<2-4 candid sentences: what the reviewer really thinks, concerns about integrity, overlap
with prior publications, conflicts, or whether the paper suits the journal. This is the
part authors never see - which is exactly why it is useful to them here.>
```

Each reviewer typically raises 3-6 major and 3-8 minor comments. Hold comments to the same
standard as in `critical-appraisal.md`: anchored to a location, with a concrete request.
"The discussion should be improved" is not a comment.

## Editor's synthesis

After the three reports, write as the handling editor (commentary in the user's language):

```markdown
## Editor's synthesis

**Likely decision:** <decision> - <one-line reason>
<If a target journal is known, calibrate to its selectivity; say how the decision would
probably differ at a less selective journal.>

**Consensus points** (raised by two or more reviewers - treat as mandatory)
| Issue | R1 | R2 | R3 |
|-------|----|----|----|

**Points of disagreement**
<Where reviewers conflict, what each said, which view the editor is likely to side with
and why, and how the authors should handle it in the response.>

**Decisive issues**
<The 2-4 points on which acceptance actually turns.>

**Revision roadmap**
| Priority | Action | Addresses | New data needed? | Effort |
|----------|--------|-----------|------------------|--------|

**If the authors cannot do X**
<For each request that needs new data the authors may not have: the best defensible
alternative response.>
```

Offer, as a follow-up, to draft a point-by-point **response-to-reviewers** template with the
reviewers' comments already laid out and space for replies and manuscript changes - this is
the natural next step once the author has revised.
