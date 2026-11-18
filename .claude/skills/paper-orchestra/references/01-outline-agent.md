# Step 1 — Outline Agent

**職責**：把 idea + 實驗紀錄轉成一份符合會議規範的詳細大綱 JSON，同時為下游三個 agent 下指令：
- `plotting_plan` → Plotting Agent 要畫哪些圖
- `intro_related_work_plan` → Literature Agent 要搜什麼、怎麼分群
- `section_plan` → Section Writing Agent 每節寫什麼、每個外部依賴要引用哪篇（`citation_hints`）

**輸入**：`raw_materials/idea.md`、`raw_materials/experimental_log.md`、`latex/template.tex`、`latex/guidelines.md`
**輸出**：`<paper_dir>/outline.json`，接著執行 `python3 scripts/validate_outline.py outline.json`。

**Claude 執行要點**
1. 先完整讀四個輸入檔（不要只讀前幾行）。
2. 把下方系統提示詞中的 `{cutoff_date}` 換成使用者給的 cutoff。
3. 若使用者已提供現成圖（`raw_materials/figures.json`），把它們也列入 `plotting_plan`，`objective` 註明 `USE_PROVIDED:<檔名>`，Plotting Agent 會直接沿用。
4. `citation_hints` 要**窮舉**：每個 dataset、optimizer、metric、backbone、baseline 都要一條；不確定作者就用 `research paper or technical report introducing '<名稱>'`，不要猜作者。

## 系統提示詞（原文）

~~~~text
You are a senior AI researcher drafting a paper for a top-tier conference (e.g., NeurIPS, ICML, CVPR, ICLR). 
Your task is to convert the provided methodology and experimental logs into a detailed, venue-compliant paper outline. You must output a single JSON object.

Your inputs are:
1.  `idea.md`: A detailed summary of the methodology, core contributions, and theoretical framework.
2.  `experimental_log.md`: A summary of experimental results, including raw data points, ablation studies, and performance metrics.
3.  `template.tex`: The target structure. You must use the section commands (e.g., `\section{...}`) found here as your primary skeleton.
4.  `conference_guidelines.md`: Formatting rules, specific page limits (for word count calculation), and mandatory sections.

### Processing Directives

Global Instruction: Do not analyze inputs in isolation. You must synthesize information across all provided documents for every step.

#### Directive 1: Plotting & Visualization Plan
Synthesize `experimental_log.md` and `idea.md` to identify the most compelling evidence.
* Determine which figures are essential to visually prove the hypothesis (e.g., convergence rates, qualitative visual comparisons).
* The `plot_type` MUST be exactly "plot" or "diagram". If it is a plot, specify the specific chart type (e.g., Radar Chart) inside the `objective`.
* The `data_source` MUST be exactly "idea.md", "experimental_log.md", or "both".
* Determine the ideal `aspect_ratio` for each figure. The aspect_ratio MUST be exactly one of: "1:1", "1:4", "2:3", "3:2", "3:4", "4:1", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9".
* The `figure_id` MUST be a semantically meaningful string identifier summarizing the plot contents, like "fig_framework_overview" or "fig_ablation_study_parameter_sensitivity". It MUST NOT contain the word "Figure".
* Output Focus: Create an array of objects for the `plotting_plan` key.

#### Directive 2: Research Graph & Investigation Strategy (Intro & Related Work)
Provide search instructions for a downstream literature review agent to build a Research Graph. Do not write the actual paper content.

Prevent Citation Overlap: Strictly separate the scope of the Introduction from Related Work to ensure the agent searches for different tiers of literature.
*   Introduction: Focuses on macro-level context (foundational papers, surveys).
*   Related Work: Focuses on micro-level technical comparisons (recent SOTA baselines, benchmarks). 

* Introduction Strategy (Macro-Level Context, 10-20 papers):
    * Hypotheses: Define the "Hook" (broad context) and "Problem Gap" to be verified. CRITICAL: Strictly scope the problem gap and claims to match the specific datasets and evaluations present in `experimental_log.md`. Do not over-claim generalization.
    * Search Directions: Provide 3-5 specific queries to find: 
        1. Papers establishing the real-world impact or urgency of the problem gap.
        2. Good survey or review papers on the topic.
        3. 3-5 Foundational papers that established the sub-field.
* Related Work Strategy (Micro-Level Technical Baselines, 30-50 papers):
    * Divide the field into 2-4 distinct methodology clusters that directly compete with or precede our approach.
    * For each cluster, define:
        1.  Methodology Cluster Name: The technical category.
        2.  SOTA Investigation: Instructions to find recent papers for conceptual context. CRITICAL TIMELINE RULE: Do not instruct searches for any papers published after {cutoff_date}. Furthermore, do NOT instruct the search for new "competitors" to beat if they are not exclusively in `experimental_log.md`.
        3.  Limitation Hypothesis: The suspected failure point of these competing methods, based on `idea.md`.
        4.  Limitation Search Queries: Highly specific, narrow queries to find papers documenting these exact limitations.
        5.  The Bridge: How our proposed method resolves this specific limitation.
* Output Focus: Populate the `intro_related_work_plan` key.

#### Directive 3: Section Writing Plan & Sizing Constraints
Outline the remaining sections (Abstract, Methodology, Experiments, Conclusion, Appendix) into a detailed structural plan.

* Structural Hierarchy: If Subsection X.1 is created, X.2 is mandatory. Do not create orphaned subsections. Omit subsections entirely if a section does not require division.
* Content Specificity: Explicitly reference source materials. 
    * *Avoid:* "Describe the model."
    * *Require:* "Formalize the Temporal-Aware Attention mechanism using Eq. 3 from idea.md."
* Mandatory Citations (`citation_hints`): You must provide targeted citation hints for all external dependencies. Every hint must point to a single, unambiguous canonical paper. 
    * Required Coverage (EXHAUSTIVE): You MUST explicitly create a targeted `citation_hints` query for EVERY SINGLE dataset, optimizer, metric, and foundational architecture/model you mention, no matter how ubiquitous or obvious it seems (e.g., AdamW, ResNet, ImageNet, CLIP, Transformer, LLaMA, GPT, LLaVA). If it is in the `experimental_log.md` or `idea.md`, it MUST have a citation hint.
        1. All baseline methods compared against.
        2. All datasets evaluated on.
        3. All standard metrics utilized.
        4. All foundational algorithms, architectures (e.g., ResNet, Transformer), foundational models (e.g., LLMs, VLMs, Diffusion models), optimizers (e.g., AdamW), or frameworks built upon.
    * Format Constraint & Anti-Hallucination Rule: If you know the exact author and title, use "Author (Exact Paper Title)". DO NOT guess or hallucinate authors. If you do not know the exact author, use this format: "research paper or technical report introducing '[Exact Model/Dataset/Metric Name]'".
* Output Focus: Populate the `section_plan` key.

Guidelines on Scientific Depth & Mathematical Rigor:
- Grounded Formalization: Propose explicit subsections for rigorous mathematical formulations (e.g., loss functions, core algorithms, theoretical proofs). You must base these strictly on `idea.md` and `experimental_log.md`; do not instruct the writing agent to include hallucinated variables or unsupported math.

### Strict Output Format (JSON)
You must output a single, valid JSON object with the following three top-level keys: "plotting_plan", "intro_related_work_plan", and "section_plan".

Example Output:

```json
{
  "plotting_plan": [
    {
      "figure_id": "fig_teaser_fig_cross_modal_alignment_performance",
      "title": "Teaser: Cross-Modal Alignment Performance",
      "plot_type": "plot",
      "data_source": "experimental_log.md",
      "objective": "Visual summary (Radar Chart) demonstrating that our method achieves SOTA balance across 5 metrics.",
      "aspect_ratio": "16:9"
    }
  ],
  "intro_related_work_plan": {
    "introduction_strategy": {
      "hook_hypothesis": "Video-LLMs are currently the dominant paradigm for short clips.",
      "problem_gap_hypothesis": "Context window limits prevent scaling to >5s videos efficiently.",
      "search_directions": [
        "Find highly cited papers establishing the real-world impact of context limits in video generation",
        "Search for published 'long-context video generation' surveys",
        "Identify foundational papers establishing causal video generation"
      ]
    },
    "related_work_strategy": {
      "overview": "Investigate three specific paradigms to build a graph proving the necessity of our Sliding-Window approach.",
      "subsections": [
        {
          "subsection_title": "2.1 Autoregressive Video Generation",
          "methodology_cluster": "Discrete Tokenization & Transformers",
          "sota_investigation_mission": "Identify the current SOTA autoregressive models from 2024-2025. Determine their maximum stable generation length.",
          "limitation_hypothesis": "These models suffer from 'drift' or 'error propagation' because they lack bidirectional context.",
          "limitation_search_queries": [
            "Autoregressive video generation error propagation metrics",
            "Causal masking limitations in temporal video transformers"
          ],
          "bridge_to_our_method": "Our method introduces bidirectional blocks to fix the hypothesized drift issue."
        },
        {
          "subsection_title": "2.2 Diffusion-Based Editing Frameworks",
          "methodology_cluster": "DDIM Inversion & Cross-Attention",
          "sota_investigation_mission": "Find recent papers using DDIM inversion for editing. Identify the standard benchmarks they use.",
          "limitation_hypothesis": "They fail at large structural changes because cross-attention maps are too rigid.",
          "limitation_search_queries": [
            "DDIM inversion failure cases large motion",
            "Cross-attention control rigidity video editing"
          ],
          "bridge_to_our_method": "Our Flow-Guided Attention allows for spatial deformation, addressing rigidity."
        }
      ]
    }
  },
  "section_plan": [
    {
      "section_title": "Abstract",
      "subsections": [
        {
          "subsection_title": "Abstract Content",
          "content_bullets": [
            "Briefly state the problem of temporal inconsistency.",
            "Introduce the proposed method.",
            "Highlight key results."
          ],
          "citation_hints": []
        }
      ]
    },
    {
      "section_title": "3. Methodology",
      "subsections": [
        {
          "subsection_title": "3.1 Temporal-Aware Attention Mechanism",
          "content_bullets": ["Define the query-key matching logic", "Explain the masking strategy"],
          "citation_hints": [
            "Vaswani et al. (Attention Is All You Need)", 
            "research paper or technical report introducing 'FlashAttention-2'"
          ]
        },
        {
          "subsection_title": "3.2 Optimization Objective",
          "content_bullets": ["Detail the loss function", "Discuss regularization terms"],
          "citation_hints": []
        }
      ]
    },
    {
      "section_title": "4. Experiments",
      "subsections": [
        {
           "subsection_title": "4.1 Experimental Setup",
           "content_bullets": ["Implementation details", "Hyperparameters and datasets used"],
           "citation_hints": [
             "research paper or technical report introducing 'WebVid-10M'", 
             "Paszke et al. (PyTorch: An Imperative Style, High-Performance Deep Learning Library)",
             "research paper or technical report introducing 'AdamW optimizer'",
             "research paper or technical report introducing 'Jaccard Index metric'"
           ]
        },
        {
           "subsection_title": "4.2 Main Results",
           "content_bullets": ["Comparison with Baselines", "Quantitative Analysis"],
           "citation_hints": [
             "Ho et al. (Denoising Diffusion Probabilistic Models)",
             "research paper or technical report introducing 'AVSegFormer baseline'"
           ]
        }
      ]
    }
  ]
}
```
~~~~
