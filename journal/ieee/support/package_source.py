"""Create the portable IEEE manuscript archive used by the journal build."""

from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

JOURNAL = Path(__file__).resolve().parent.parent
SUPPORT = JOURNAL / "support"
IMAGES = JOURNAL / "images"
TEMPLATE_EXTENSIONS = {".bst", ".cls", ".fd", ".map", ".pfb", ".sty", ".tfm"}
TEMPLATE_IMAGES = {"bullet.png", "logo.png", "notaglinelogo.png"}
REQUIRED_ASSETS = {
    "IEEEtran.bst",
    "IEEEtran.cls",
    "cite.sty",
    "ieeeaccess.cls",
    "spotcolor.sty",
    "bullet.png",
    "logo.png",
    "notaglinelogo.png",
}


def package(output: Path) -> None:
    assets = sorted(
        path
        for path in SUPPORT.iterdir()
        if path.is_file()
        and (path.suffix.lower() in TEMPLATE_EXTENSIONS or path.name in TEMPLATE_IMAGES)
    )
    missing = REQUIRED_ASSETS - {path.name for path in assets}
    if missing:
        raise FileNotFoundError(f"Missing IEEE template assets: {', '.join(sorted(missing))}")

    figures = sorted(path for path in IMAGES.iterdir() if path.is_file())
    if not figures:
        raise FileNotFoundError(f"No journal images found in {IMAGES}")

    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for filename in ("main.tex", "references.bib"):
            archive.write(JOURNAL / filename, filename)
        archive.write(SUPPORT / "template_compat.tex", "template_compat.tex")
        for path in assets:
            archive.write(path, path.name)
        for path in figures:
            archive.write(path, f"images/{path.name}")
        archive.writestr(
            "README.txt",
            "Compile main.tex with pdfLaTeX, BibTeX and pdfLaTeX twice. "
            "IEEE template assets are at the archive root; figures are in images/.\n",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        default=JOURNAL / "latex_source.zip",
        help="output ZIP path (default: journal/ieee/latex_source.zip)",
    )
    args = parser.parse_args()
    package(args.output)


if __name__ == "__main__":
    main()
