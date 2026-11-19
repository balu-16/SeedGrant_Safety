# Smart Safety Tag journal

The complete journal text is in **[main.tex](main.tex)**. Search for a section name from the table below to find it in that file.

| What you need | Where to find it |
| --- | --- |
| Compiled journal | [main.pdf](main.pdf) |
| Abstract, introduction and related work | [main.tex](main.tex): abstract, Introduction, Related Work |
| App, backend and emergency flow | [main.tex](main.tex): System Architecture |
| Wearable, power and PCB design | [main.tex](main.tex): Wearable Design |
| Tests, evidence and proposed evaluation | [main.tex](main.tex): Verification Method and Evidence |
| Limitations and conclusion | [main.tex](main.tex): Discussion and Limitations, Conclusion |
| All tables and captions | [main.tex](main.tex), near the relevant discussion |
| References | [references.bib](references.bib) |
| Figures | [images/](images/) |
| Template, build tools and revision history | [support/](support/) |
| Portable LaTeX source for sharing or Overleaf | [latex_source.zip](latex_source.zip) |

Comments marked `TODO(author)` in `main.tex` identify questions for the authors. The [latest revision notes](support/REVISION_2_CHANGELOG.md) collect them; the [earlier notes](support/REVISION_CHANGELOG.md) are also retained.

## Figures

| Journal figure | File |
| --- | --- |
| System overview | [architecture.pdf](images/architecture.pdf) |
| App-originated SOS flow | [sos_flow.pdf](images/sos_flow.pdf) |
| Wearable power path | [power_path.pdf](images/power_path.pdf) |
| Tag PCB assembly views | [tag_board.pdf](images/tag_board.pdf) |
| Charging-adapter views | [adapter_board.pdf](images/adapter_board.pdf) |

`architecture.png` is a preview of the architecture figure. The five PDF figures above are the ones included in the manuscript.

## Build the journal

Install a TeX distribution that provides `pdflatex` and `bibtex`, along with Python 3. From the repository root, run:

```sh
cd journal/ieee
./support/build.sh
```

The script runs pdfLaTeX, BibTeX and pdfLaTeX twice in a temporary directory. On success, it updates `main.pdf` and `latex_source.zip`; temporary build files are removed. The previous build files are preserved in [support/previous_build.zip](support/previous_build.zip).

For Overleaf, upload `latex_source.zip` and select pdfLaTeX. The archive places the IEEE template files at its root and figures in `images/` so it can compile independently. To refresh only the archive without rebuilding the PDF, run `python3 support/package_source.py` from `journal/ieee`.

The optional `support/make_figures.py` script regenerates the figures from project CAD exports and requires PyMuPDF. It overwrites the files in `images/`; normal journal builds do not run it.

## Draft and evidence notes

The manuscript is a design-and-implementation draft, not evidence of an integrated hardware trial. The four author names are provisional. Affiliations, corresponding author, author contributions, conflicts, funding and disclosure history require team confirmation. Consult the [IEEE Access submission guidelines](https://ieeeaccess.ieee.org/authors/submission-guidelines/) before submission.

The saved checks reported 24 passing mobile tests, 57 passing backend tests using in-memory repositories and mock providers, and a passing administrative type check. Hardware status comes from the [verification register](../../smart-safety-tag-v1/docs/verification.md); the wearable emergency link and physical measurements remain pending.

The supplied 83% report estimates AI writing for an earlier draft. It is not a text-similarity score, and no score for the current manuscript is available. Previous limited overlap checks and their limitations are documented in the revision notes.

The IEEE template assets and compatibility file came from the supplied IDP_Project IEEE Access manuscript. Its documentation reports that the assets came from a pinned mirror after the direct publisher archive returned HTTP 403; equivalence to the official archive has not been independently verified. `cite.sty` came from CTAN. The previous build used TinyTeX 2026.10, archive SHA-256 `4d519d6236ee6798e3ec0d8e2093d1fda01aeb267aa22c2a5586d76bcfce6566`.
