#!/usr/bin/env bash
# Compile a LaTeX paper: pdflatex -> bibtex -> pdflatex x2 (same sequence as PaperOrchestra's compile_latex).
# Usage: bash compile.sh <latex_dir> <basename-without-.tex>
# Tries latexmk, then pdflatex+bibtex, then tectonic. Prints the PDF page count when pdfinfo exists.
# Exit 0 = PDF produced, 2 = no TeX engine available, 1 = compilation failed (see <basename>.log).
set -u
dir="${1:?latex dir}"; name="${2:?basename}"
cd "$dir" || exit 1
rm -f "$name.pdf"

if command -v latexmk >/dev/null 2>&1; then
  latexmk -pdf -interaction=nonstopmode -halt-on-error "$name.tex" >/dev/null 2>&1
elif command -v pdflatex >/dev/null 2>&1; then
  pdflatex -interaction=nonstopmode "$name.tex" >/dev/null 2>&1
  command -v bibtex >/dev/null 2>&1 && bibtex "$name" >/dev/null 2>&1
  pdflatex -interaction=nonstopmode "$name.tex" >/dev/null 2>&1
  pdflatex -interaction=nonstopmode "$name.tex" >/dev/null 2>&1
elif command -v tectonic >/dev/null 2>&1; then
  tectonic --keep-logs "$name.tex" >/dev/null 2>&1
else
  echo "NO_TEX_ENGINE: install TeX Live (e.g. apt-get install -y texlive-latex-extra texlive-fonts-recommended texlive-bibtex-extra latexmk) or tectonic, or upload this folder to Overleaf." >&2
  exit 2
fi

if [ -f "$name.pdf" ]; then
  echo "PDF: $dir/$name.pdf"
  command -v pdfinfo >/dev/null 2>&1 && pdfinfo "$name.pdf" | grep -i '^Pages'
  [ -f "$name.log" ] && grep -E '^! |Overfull \\hbox|Citation .* undefined|Reference .* undefined' "$name.log" | sort | uniq -c | head -20
  exit 0
fi
echo "COMPILE_FAILED — first errors from $name.log:" >&2
[ -f "$name.log" ] && grep -n -A3 '^! ' "$name.log" | head -30 >&2
exit 1
