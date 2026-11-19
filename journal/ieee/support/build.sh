#!/bin/sh
set -eu

journal_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
assets="$journal_dir/support"
cd "$journal_dir"

for command in pdflatex bibtex python3; do
    if ! command -v "$command" >/dev/null 2>&1; then
        printf 'Required command not found: %s\n' "$command" >&2
        exit 1
    fi
done

work_dir=$(mktemp -d "${TMPDIR:-/tmp}/smart-safety-journal.XXXXXXXX")
trap 'rm -rf -- "$work_dir"' EXIT

export TEXINPUTS="$assets//:${TEXINPUTS:-}"
export TFMFONTS="$assets//:${TFMFONTS:-}"
export T1FONTS="$assets//:${T1FONTS:-}"
export TEXFONTMAPS="$assets//:${TEXFONTMAPS:-}"
export BSTINPUTS="$assets//:${BSTINPUTS:-}"
export BIBINPUTS="$journal_dir:${BIBINPUTS:-}"

pdflatex -interaction=nonstopmode -halt-on-error -output-directory="$work_dir" main.tex
(cd "$work_dir" && bibtex main)
pdflatex -interaction=nonstopmode -halt-on-error -output-directory="$work_dir" main.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory="$work_dir" main.tex
python3 "$assets/package_source.py" "$work_dir/latex_source.zip"

cp "$work_dir/main.pdf" "$journal_dir/main.pdf"
cp "$work_dir/latex_source.zip" "$journal_dir/latex_source.zip"
printf '\nUpdated main.pdf and latex_source.zip\n'
