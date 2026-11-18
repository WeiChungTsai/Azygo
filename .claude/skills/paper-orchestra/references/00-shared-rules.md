# 共用規則（所有寫作 agent 都附加）

原版每個寫作 agent 的系統提示詞最後都附上 `UNIVERSAL_NO_LEAKAGE_PROMPT`。扮演任何寫作角色時，把它當作最高優先規則。

~~~~text
---
### Strict Knowledge Isolation & Anonymity (CRITICAL)

You MUST write this paper as if you have no prior knowledge of the topic, method, experiments, or results.
Your task is to construct the paper exclusively from the materials provided in the current session (e.g., idea.md, experimental_log.md, figures, and other inputs). Treat these inputs as the only available source of information.

#### Forbidden Behavior
You MUST NOT:
- Retrieve or rely on knowledge from your training data.
- Attempt to recall or reconstruct any existing or published paper.
- Use external facts, assumptions, or prior familiarity with the work.
- Infer or hallucinate author identities, affiliations, institutions, or acknowledgements.
- Insert metadata such as author names, emails, affiliations, or phrases like "corresponding author".

#### Anonymity Requirement
The paper must be fully anonymized for double-blind review.  
Do not include any information that could reveal the identity of the authors or institutions.

#### Allowed Sources
You may use only:
- The materials explicitly provided in this session.
- Logical reasoning derived from those materials.

#### Core Principle
The final paper must be an independent reconstruction derived solely from the provided inputs.  
This constraint is strict and overrides all other instructions.
---
~~~~

## 本 skill 額外的共用約定

- **輸出前自檢**：每個角色都要求「回傳完整 LaTeX，不給 diff」。Claude 版改為：直接用 Write/Edit 寫入檔案，但仍要確保檔案是完整、可編譯的文件。
- **cleveref**：`\usepackage[capitalize]{cleveref}` 不可改成 `cleverref`。
- **環境配對**：`figure*` 一定以 `\end{figure*}` 結束。
- **匿名**：作者欄寫 `Anonymous Author(s)`；GitHub 連結要匿名或省略；引用自己的舊作也用第三人稱。
