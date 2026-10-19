
import json
import os
import re
from pathlib import Path
from urllib.parse import quote

# This script is inside:
# beu-pyq-pdfs/scripts/generate_index.py
#
# Repository structure:
# beu-pyq-pdfs/
#   beu-pyq-pdfs/
#     scripts/generate_index.py
#     pdfs/
#     papers.json

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "pdfs"
OUTPUT_FILE = ROOT / "papers.json"

REPOSITORY = os.environ.get(
    "GITHUB_REPOSITORY",
    "Beuconnect/beu-pyq-pdfs"
).strip()

BRANCH = os.environ.get("GITHUB_REF_NAME", "main").strip() or "main"

# Supported filename examples:
# 105707__E-Commerce and Erp__2021.pdf
# 101408__Structural Analysis__2023.pdf
FILENAME_PATTERN = re.compile(
    r"^([A-Za-z0-9-]+)__(.+)__((?:19|20)\d{2})\.pdf$",
    re.IGNORECASE,
)


def main():
    if not PDF_DIR.is_dir():
        raise FileNotFoundError(
            f"PDF folder not found: {PDF_DIR}"
        )

    papers = []
    invalid_files = []

    for pdf in sorted(PDF_DIR.rglob("*")):
        if not pdf.is_file() or pdf.suffix.lower() != ".pdf":
            continue

        match = FILENAME_PATTERN.fullmatch(pdf.name)

        if not match:
            invalid_files.append(
                pdf.relative_to(ROOT).as_posix()
            )
            continue

        code, subject, year = match.groups()

        subject = " ".join(
            subject.replace("_", " ").split()
        ).strip()

        if not subject:
            invalid_files.append(pdf.name)
            continue

        # Include the nested folder in the GitHub URL.
        # ROOT.parent is the repository root for the confirmed
        # repository structure described above.
        relative_path = pdf.relative_to(ROOT.parent).as_posix()

        encoded_path = quote(relative_path, safe="/")
        encoded_branch = quote(BRANCH, safe="")

        pdf_url = (
            "https://raw.githubusercontent.com/"
            f"{REPOSITORY}/{encoded_branch}/{encoded_path}"
        )

        papers.append({
            "id": f"{code}-{year}",
            "code": code,
            "subject": subject,
            "year": int(year),
            "pdfUrl": pdf_url,
        })

    if invalid_files:
        raise ValueError(
            "Invalid PDF filenames. Expected "
            "CODE__SUBJECT__YEAR.pdf:\n- "
            + "\n- ".join(invalid_files)
        )

    ids = [paper["id"] for paper in papers]

    if len(ids) != len(set(ids)):
        raise ValueError(
            "Duplicate paper IDs found. "
            "Each code/year combination must be unique."
        )

    papers.sort(
        key=lambda paper: (
            -paper["year"],
            paper["subject"].casefold(),
            paper["code"].casefold(),
        )
    )

    data = {
        "version": 1,
        "papers": papers,
    }

    OUTPUT_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Repository: {REPOSITORY}")
    print(f"Branch: {BRANCH}")
    print(f"PDF directory: {PDF_DIR}")
    print(f"Generated {OUTPUT_FILE} with {len(papers)} papers.")

    for paper in papers:
        print(
            f'{paper["code"]} | {paper["subject"]} | '
            f'{paper["year"]} | {paper["pdfUrl"]}'
        )


if __name__ == "__main__":
    main()
