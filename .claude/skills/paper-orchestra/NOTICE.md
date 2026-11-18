# NOTICE

This skill is a derivative work of **PaperOrchestra** (https://github.com/google-research/paper-orchestra),
Copyright 2026 Google LLC, licensed under the Apache License 2.0 (see `LICENSE`).

Changes made: the Python/Gemini implementation was decomposed into a Claude Code skill. Agent system prompts
in `references/` are reproduced verbatim from `methods/prompts/`, `utils/prompt_utils.py`,
`utils/paper_banana_utils.py`, `autoraters/agent_review.py` and `autoraters/prompts/`; the surrounding
procedure, the helper scripts in `scripts/` (re-implemented with the Python standard library), and the
plotting style guide are new. `templates/` and `examples/` are copied from the original repository
(conference style files remain under their respective conference licenses).

Citation:
Song, Y., Song, Y., Pfister, T., & Yoon, J. (2026). PaperOrchestra: A Multi-Agent Framework for Automated
AI Research Paper Writing. arXiv:2604.05018.
