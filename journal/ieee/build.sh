#!/bin/sh
set -eu
cd "$(dirname "$0")"
command -v pdflatex >/dev/null
command -v bibtex >/dev/null
mkdir -p build
assets="$PWD/template/assets"
export TEXINPUTS="$assets//:${TEXINPUTS:-}" TFMFONTS="$assets//:${TFMFONTS:-}" T1FONTS="$assets//:${T1FONTS:-}" TEXFONTMAPS="$assets//:${TEXFONTMAPS:-}" BSTINPUTS="$assets//:${BSTINPUTS:-}" BIBINPUTS="$PWD:${BIBINPUTS:-}"
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
(cd build && bibtex main)
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
cp build/main.pdf main.pdf
