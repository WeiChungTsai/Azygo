# 選用：自動評估（autoraters）

原 repo `autoraters/` 用於研究評估，不在寫作管線內。需要比較兩版稿件、或評估文獻回顧品質時使用。所有評估都建議交給**獨立 subagent** 執行。

| 評估 | 原版做法 | Claude 版 |
|---|---|---|
| Side-by-side 整體品質 | 兩篇對調順序各評一次再彙總，消除位置偏差 | 兩個 subagent 各評一種順序；兩次 winner 一致才算勝，否則 tie |
| Side-by-side 文獻回顧 | 同上，只看 Intro + Related Work | 同上 |
| 文獻回顧絕對品質 | 0–100 多軸，嚴格防灌分，需提供該領域平均引用數 | 同上；`{avg_citation_count}` 由使用者提供或以同會議論文估計 |
| Citation F1 | 先把真實論文的參考文獻分 P0（必引）/ P1，再算生成稿引用的 precision/recall | 需要一篇「參考答案」論文；P0/P1 分類用下方提示詞 |

## SxS 整體品質（原文）
~~~~text
You are an expert AI researcher and reviewer for top-tier machine learning conferences (e.g., CVPR, NeurIPS, ICLR).
Your task is to perform a Side-by-Side (SxS) holistic comparison of two academic papers.
The two papers describe the same or highly similar research ideas. Your evaluation should formulate a holistic judgment that accounts for both scientific execution and writing quality/presentation.

The ordering of the papers is arbitrary and does not indicate quality. Evaluate each paper independently before comparing them.
Do not base your decision solely on length or verbosity.

CRITICAL EVALUATION CRITERIA:
1. Scientific Depth and Soundness
   - Which paper provides more rigorous technical justifications, theoretical foundations, and comprehensive experimental setups?
2. Technical Execution
   - Within the bounds of the described idea, which paper executes the implementation and methodology more innovatively or effectively?
3. Organization and Logical Flow
   - Which paper presents ideas in a clearer and more coherent order from Abstract through Conclusion?
   - Are sections and paragraphs structured logically with smooth transitions?
4. Clarity and Precision of Writing
   - Which paper explains its ideas more clearly and concisely?
   - Does the writing avoid unnecessary verbosity, ambiguity, or repetitive phrasing?
5. Presentation of Evidence and Formatting
   - Which paper integrates figures, tables, and experimental results more effectively into the narrative?
   - Are visuals clearly referenced and explained in the text?
   - Which paper has fewer visual formatting mistakes (e.g., overflowed tables, misplaced figures, overlapping text)?
6. Professional Academic Style
   - Which paper maintains a more polished and professional academic tone?
   - Does it use precise domain terminology and consistent terminology throughout the paper?

OUTPUT FORMAT:
Return a valid JSON object with the following schema:
```json
{
  "paper_1_holistic_analysis": "analysis of paper_1 writing, presentation, and scientific execution",
  "paper_2_holistic_analysis": "analysis of paper_2 writing, presentation, and scientific execution",
  "comparison_justification": "comparison reasoning",
  "winner": "winner of your choice"
}
```
The "winner" field must be exactly one of: "paper_1", "paper_2", or "tie".
~~~~

## SxS 文獻回顧（原文）
~~~~text
You are an expert AI researcher and reviewer for top-tier machine learning conferences (e.g., CVPR, NeurIPS, ICLR).
Your task is to perform a Side-by-Side (SxS) comparison of the literature review sections (Introduction and Related Work) between two academic papers.

The ordering of the papers is arbitrary and does not indicate quality. Evaluate each paper independently before comparing them.
Do not base your decision solely on length or verbosity.

CRITICAL EVALUATION CRITERIA:
1. Problem Framing and Motivation
   - Which paper introduces the research problem more clearly?
   - Does the introduction explain the importance of the problem and the gap in existing work?
2. Coverage of Prior Work
   - Which paper provides a more complete and relevant overview of prior research?
3. Organization and Synthesis
   - Which paper organizes related work more effectively (e.g., grouping by themes or approaches)?
   - Does it synthesize prior work rather than simply listing papers?
4. Positioning of the Contribution
   - Which paper more clearly explains how its approach differs from existing methods?
5. Writing Quality and Readability
   - Which literature review is clearer, more concise, and easier to follow?

OUTPUT FORMAT:
Return a valid JSON object with the following schema:
```json
{
  "paper_1_analysis": "analysis of paper 1",
  "paper_2_analysis": "analysis of paper 2",
  "comparison_justification": "comparison reasoning",
  "winner": "winner of your choice"
}
```
The "winner" field must be exactly one of: "paper_1", "paper_2", or "tie".
~~~~

## 文獻回顧品質（原文）
~~~~text
You are an expert, skeptical academic reviewer agent. Your task is to rigorously evaluate the quality of the literature review in a draft research paper PDF.

You must be conservative with scoring. High scores are rare and must be explicitly justified with concrete evidence from the text. Assume most drafts are not publication-ready.

CONTEXTUAL BASELINE
The user has provided the average citation count for accepted papers in this specific field/venue.
Reference Average Citation Count: {avg_citation_count}
Use this number as the baseline for "typical" coverage volume.

SCOPE
- Evaluate ONLY the literature-review function of:
  - Introduction
  - Related Work / Background / Literature Review (or equivalent)
- Ignore methods, experiments, and results except to verify whether the literature review correctly sets up the paper’s scope and claims.

PROCESS (FOLLOW STRICTLY)
1. Identify the paper title.
2. Locate the Introduction and Related Work sections (or closest equivalents).
3. Identify:
   - The paper’s stated research problem
   - Claimed contributions
   - Implied relevant subfields
4. Estimate citation statistics from the literature review:
   - Approximate number of unique cited works
   - Citation density relative to section length
   - Breadth across relevant sub-areas
   - Volume relative to the Reference Average ({avg_citation_count}).
5. For each scoring axis, evaluate ONLY what is explicitly written.
   - Do NOT infer author intent.
   - Do NOT reward missing but “expected” knowledge.
6. Apply anti-inflation rules and penalties.
7. Produce output strictly in the JSON schema defined below.
   - NO extra text before or after the JSON.
   - All fields must be filled.
   - Use null if information is genuinely unavailable.

ANTI-INFLATION RULES (MANDATORY)
- Default expectation: overall score between 45–70.
- Scores >85 require strong evidence across ALL axes.
- Scores >90 are extremely rare and require near-survey-level mastery.
- If any axis <50, overall score should rarely exceed 75.
- If the review is mostly descriptive (paper-by-paper summaries), Critical Analysis must be ≤60.
- If novelty is asserted without explicit comparison to close prior work, Positioning must be ≤60.
- Sparse or inconsistent citations cap Citation Rigor at ≤60.
- High citation count does NOT automatically imply high quality; relevance and synthesis must justify it.

SCORING SCALE (ANCHORS — DO NOT INVENT NEW ONES)
0–20  = Unacceptable
21–40 = Weak
41–55 = Adequate but flawed
56–70 = Solid
71–85 = Strong
86–92 = Excellent
93–100 = Exceptional (extremely rare)

AXES (0–100 EACH)

Axis 1: Coverage & Completeness
Evaluate:
- Breadth across major relevant threads
- Inclusion of foundational and recent work
- Absence of obvious omissions
- Citation volume relative to the Reference Average ({avg_citation_count})

Citation count anchors (Relative to Reference Average of {avg_citation_count}):
- Count is < 50% of Reference: Usually narrow or incomplete (cap ≤55 unless field is very small).
- Count is 50%–80% of Reference: Minimal acceptable coverage.
- Count is 80%–120% of Reference: Solid breadth if well integrated.
- Count is > 120% of Reference: Strong evidence of comprehensive coverage IF relevance is maintained.

Axis 2: Relevance & Focus
Evaluate:
- Alignment of citations with the research problem
- Minimal tangents or citation padding
- Clear scoping and prioritization of literature

Axis 3: Critical Analysis & Synthesis
Evaluate:
- Thematic grouping and comparison of approaches
- Discussion of tradeoffs, limitations, and open gaps
- Evidence of synthesis rather than sequential summaries
Hard cap: ≤60 if the review is mostly descriptive.

Axis 4: Positioning & Novelty Justification
Evaluate:
- Clear, literature-grounded research gap
- Explicit differentiation from closest related work
- Motivation for why the gap matters
Hard cap: ≤60 if novelty claims are vague or unsupported.

Axis 5: Organization & Writing Quality
Evaluate:
- Logical structure, flow, and signposting
- Clarity and precision of academic language
- Appropriate subsectioning and definitions

Axis 6: Citation Practices, Density & Scholarly Rigor
Evaluate:
- Whether key claims are supported by citations
- Credibility and consistency of sources
- Citation density relative to section length
- Balance between foundational and recent work
Hard caps:
- Citation count significantly below Reference Average ({avg_citation_count}) for a broad problem: ≤55
- High citation count with weak integration: ≤65

PENALTIES (APPLY AFTER AXIS SCORING)
Apply zero or more penalties:
- Overclaiming novelty without close comparison: −5 to −15
- Missing key recent work (if detectable): −5 to −15
- Mostly descriptive review with weak synthesis: −5 to −10
- Weak or generic gap statements: −5 to −10
- Citation dumping or consistency issues: −5 to −10

OPTIONAL POSITIVE ADJUSTMENT (RARE)
You MAY apply a small positive adjustment (+3 to +7 total points) ONLY IF:
- Citation count is substantially higher (>150%) than the Reference Average ({avg_citation_count})
- Citations are relevant and distributed across subtopics
- Review remains synthesized and focused
- Critical Analysis score >60 AND Relevance score >65
Do NOT apply this adjustment otherwise.

OVERALL SCORE
- Use weighted judgment:
  - Coverage: 20%
  - Relevance: 15%
  - Critical Analysis: 25%
  - Positioning: 25%
  - Organization: 10%
  - Citation Rigor: 5%
- Then apply penalties and any justified positive adjustment.
- Sanity-check against anti-inflation rules.

OUTPUT FORMAT (STRICT JSON ONLY)

Return exactly the following JSON structure and nothing else:

```json
{
  "paper_title": string | null,
  "citation_statistics": {{
    "estimated_unique_citations": number,
    "citation_density_assessment": "low" | "appropriate" | "high",
    "breadth_across_subareas": "narrow" | "moderate" | "broad",
    "comparison_to_baseline": string,
    "notes": string
  }},
  "axis_scores": {{
    "coverage_and_completeness": {{
      "score": number,
      "justification": string
    }},
    "relevance_and_focus": {{
      "score": number,
      "justification": string
    }},
    "critical_analysis_and_synthesis": {{
      "score": number,
      "justification": string
    }},
    "positioning_and_novelty": {{
      "score": number,
      "justification": string
    }},
    "organization_and_writing": {{
      "score": number,
      "justification": string
    }},
    "citation_practices_and_rigor": {{
      "score": number,
      "justification": string
    }}
  }},
  "penalties": [
    {{
      "reason": string,
      "points_deducted": number
    }}
  ],
  "summary": {{
    "strengths": [string],
    "weaknesses": [string],
    "top_improvements": [string]
  }},
  "overall_score": number
}
```

JUSTIFICATION CONSTRAINTS
- Each justification: 2–5 sentences, evidence-based.
- Do NOT quote more than 25 total words from the paper.
- If evidence is missing, explicitly state: “Not evidenced in the text.”
~~~~

## Citation F1 — 參考文獻優先級分類（原文）
~~~~text
You are an expert academic reviewer. Read the following paper text and analyze its references.
Your goal is to categorize the provided references into two priorities:
- P0 (Must-Have): Core citations strictly necessary for the paper. These MUST include:
    * Baselines directly compared against in experiments
    * Datasets the paper utilizes or evaluates on
    * Core methods the paper is directly building upon or modifying
    * Metrics or standard numbers heavily relied upon and cited from another paper
- P1 (Good-To-Have): Supplemental citations. These include:
    * Standard background references covering broad history
    * General related work that is not directly competing or built-upon
    * Minor implementations or utility tools mentioned in passing

PAPER TEXT:
{paper_text}

REFERENCES LIST:
{references_str}

Please return ONLY a JSON dictionary where the keys are the exact reference numbers (e.g., "1", "2") and the values are either "P0" or "P1".
Example output:

```json
{
    "1": "P0",
    "2": "P1",
    "3": "P0"
}
```
~~~~
