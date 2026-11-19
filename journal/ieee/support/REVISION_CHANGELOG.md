# Smart Safety Tag manuscript revision

## Report audit

The supplied report is an **AI-writing report**: its 83% figure is an estimate of qualifying text detected as AI-written or AI-altered, not a source-similarity or plagiarism score. It corresponds to the manuscript that was in main.pdf before this revision. The report does not provide a list of matching sources. No revised Turnitin result was available during this work, so the revised score and the requested thresholds cannot be confirmed.

The report's highlights were most extensive in the abstract, system architecture, wearable design, verification, discussion, and conclusion. The introduction was also substantially highlighted; Related Work was highlighted in part. Figure captions and table material are protected by the requested editing rules and were left unchanged. There is no dataset-description section in this paper.

## Changes by section

Percentages estimate the share of **original prose sentences that no longer have an exact sentence match** in the corresponding revised section. The comparison normalizes whitespace and excludes figures, tables, captions, headings, and bibliography. Sentence splitting and merging make the counts approximate; they are not similarity or AI-detection scores. REVISION.diff contains the full source comparison.

| Section | Approximate sentences changed | Revision |
| --- | ---: | --- |
| Abstract | 100% | Reordered the prototype description, recorded checks, and evidence limits. |
| Introduction | 100% | Clarified the alert path, the different stages of software and hardware, and the paper's scope. |
| Related Work | 100% | Connected prior designs by communication path, sensing, and privacy while retaining their existing citations. |
| System Architecture | 97% | Reworked the SOS flow, service selection, location handling, guardian access, and record descriptions. |
| Wearable Design | 97% | Reframed the power path, board layout, interfaces, charging assumptions, and firmware behavior around the documented design. |
| Verification Method and Evidence | 98% | Clarified the distinction between saved checks, calculated estimates, and proposed physical tests. |
| Discussion and Limitations | 79% | Reorganized integration, delivery, privacy, and participant-related limitations. |
| Conclusion | 100% | Restated the current evidence and the work needed to evaluate the complete path. |

No new experimental results, measurements, references, technical numbers, or claims about completed hardware validation were added. Existing project-specific facts were retained and reorganized.

## Citation and source review

The existing citations were retained with the claims they support. The patent and the available research descriptions were checked against their published records or author-provided copies, including the Purnima, Wankhede, Barman, Roy, Sonia, Hariprasad, Just, Kurt Peker, and Givehchian studies. Android's permission documentation was also checked. This was not a complete independent review of every statement in every cited work.

Two passages need author attention before submission:

1. **Related Work, privacy paragraph:** the general statement that location and alert data can reveal routines has no dedicated citation. The adjacent Barman citation addresses inferences from encrypted Bluetooth traffic; confirm whether an additional source is needed for the broader statement.
2. **Wearable Design, capacitor-derating paragraph:** the general explanation of effective capacitance and the part-selection discussion have no direct manuscript citation. The project's smart-safety-tag-v1/docs/power-budget.md references manufacturer information; confirm the source and add an appropriate citation if required. Existing citations and bibliography entries were not changed under the requested rules.

Related Work descriptions and the wearable component and charging descriptions remain the main passages to inspect against any future matching-source report. Exact technical names and component identifiers necessarily remain. A narrow comparison against the full available PDFs of Barman, Wankhede, Givehchian, and Just found no identical 12-word sequences in the revised manuscript body. This is not a comprehensive similarity check and does not establish the result against other sources, shorter matches, or the institution's database.

IEEE Access's [submission guidelines](https://ieeeaccess.ieee.org/authors/submission-guidelines/) describe disclosure and citation requirements for AI-generated text. No AI-system citation was added to the manuscript, as requested; the authors should review the journal's requirements before submission.

## Build and integrity checks

- Rebuilt with pdfLaTeX, BibTeX, and two further pdfLaTeX runs using the documented, checksum-verified TinyTeX release. The revised PDF has 10 pages, the same as the baseline.
- The final build reports no overfull boxes, unresolved references, or citation warnings. The PDF layout was visually reviewed.
- The source comparison found the same 27 citation commands, 8 reference commands, 8 labels, inline math, document preamble, and all 5 figure and 3 table environments in the same order. The bibliography and figure assets are unchanged. Numeric tokens match within each corresponding paragraph; the numerical context was also reviewed.
- The compiled bibliography still contains 21 entries. latex_source.zip was updated to contain the revised main.tex.
- Mobile unit tests: 24 passed. Administrative TypeScript check: passed. Backend suite: 57 passed with two dependency deprecation warnings when run outside the sandbox. Two earlier sandboxed reruns timed out during an authentication test; neither represents a completed run.

## Author confirmations

- Affiliations and corresponding-author details are still marked as needing confirmation in the manuscript.
- The paper continues to describe the wearable emergency link, keyword inference, and physical hardware validation as incomplete. If the project has progressed beyond the saved records, provide the new evidence before changing those statements.
- Obtain the separate matching-source similarity report and a new AI-writing report to assess the revised manuscript against the institution's actual checks.
