# Smart Safety Tag journal draft

`main.tex`, `references.bib`, `figures/`, and `template_compat.tex` are the manuscript source; `main.pdf` is the compiled draft. `latex_source.zip` is a portable source bundle with the publisher assets at its root. Use pdfLaTeX, BibTeX, then pdfLaTeX twice (or import the ZIP into Overleaf with pdfLaTeX). For this directory, put a TeX distribution on PATH and run `./build.sh`; build files go to `build/`.

The template assets and compatibility file come from the supplied IDP_Project IEEE Access manuscript. Its documentation reports that the assets came from a pinned mirror after the direct publisher archive returned HTTP 403; equivalence to the official archive has not been independently verified. `cite.sty` was obtained from CTAN. The toolchain used here was TinyTeX 2026.10, archive SHA-256 `4d519d6236ee6798e3ec0d8e2093d1fda01aeb267aa22c2a5586d76bcfce6566`; the compiler was kept in temporary storage and is not part of the source bundle.

The article is a design-and-implementation draft, not evidence of an integrated hardware trial. The four author names are provisional. Affiliations, corresponding author, author contributions, conflicts, funding and disclosure history require team confirmation. IEEE Access suitability and similarity screening remain for author review. The references are verified publication or manufacturer records, not a comprehensive systematic review.

Evidence checked on 29 October 2026 against repository commit `5598d3f`: `npm test` in `client/` (24 tests passed); `npm run typecheck` in `admin/` (passed); and `PYTHONDONTWRITEBYTECODE=1 timeout 45s .venv/bin/python -m pytest -q -p no:cacheprovider` in `server/` (57 tests passed, with two dependency deprecation warnings). Backend tests use in-memory repositories and mock notification providers; they do not test a live database or real alert delivery. An earlier isolated authentication run timed out before the full suite subsequently passed. Hardware status is taken from `smart-safety-tag-v1/docs/verification.md` and its referenced records, not a new physical test.

The expanded draft is ten pages with five vector figures, including CAD assembly views for both PCBs, and 21 cited references (including 10 research publications). It includes a modeled runtime table and an evidence table. Battery figures are calculated scenarios; the documented tag-to-phone integration and physical measurements remain pending.

A local 12-word-sequence comparison with the supplied QubitChat journal sections and patent document found no matches in the new manuscript source or disclosure HTML. This narrow comparison is not a plagiarism certification or a substitute for a publisher/institution similarity check.

The current draft omits the AI-use disclosure. Before submission, consult IEEE Access’s disclosure policy: https://ieeeaccess.ieee.org/authors/submission-guidelines/ . Author, affiliation, funding, and conflict details still require confirmation.

A 12-word overlap check on the rewritten manuscript found no matches against the supplied example documents and two accessible cited studies (the BLE traffic-analysis paper and the BLE wearable-security study). This is a narrow diagnostic and cannot certify a plagiarism-screening outcome.
