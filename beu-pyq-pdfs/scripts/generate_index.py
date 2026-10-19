import json
import os
import re
from pathlib import Path
from urllib.parse import quote

# Folder containing this script's parent directory
ROOT = Path(_file_).resolve().parents[1]
PDF_DIR = ROOT / "pdfs"
OUTPUT_FILE = ROOT / "papers.json"

REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")

# Filename format:
# CODESUBJECT NAMEYEAR.pdf
FILENAME_PATTERN = re.compile(
    r"^([A-Za-z0-9-]+)(.+)((?:19|20)\d{2})\.pdf$",
    re.IGNORECASE,
)


def main():
    if not REPOSITORY:
        raise RuntimeError(
            "GITHUB_REPOSITORY is missing. "
            "Run this script through GitHub Actions."
        )

    if not PDF_DIR.is_dir():
        raise FileNotFoundError(
            f"PDF folder not found: {PDF_DIR}"
        )

    papers = []
    invalid_files = []

    for pdf in sorted(PDF_DIR.rglob("*")):
        if not pdf.is_file() or pdf.suffix.lower() != ".pdf":
            continue

        relative_path = pdf.relative_to(ROOT).as_posix()
        match = FILENAME_PATTERN.fullmatch(pdf.name)

        if not match:
            invalid_files.append(pdf.name)
            continue

        code, subject, year = match.groups()
        subject = " ".join(
            subject.replace("_", " ").split()
        )

        if not subject:
            invalid_files.append(pdf.name)
            continue

        encoded_path = quote(relative_path, safe="/")
        encoded_branch = quote(BRANCH, safe="/")

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

    # Reject invalid filenames to prevent incomplete indexes.
    if invalid_files:
        raise ValueError(
            "Invalid PDF filenames. Use "
            "CODESUBJECT NAMEYEAR.pdf:\n- "
            + "\n- ".join(invalid_files)
        )

    # Each code/year combination must be unique.
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

    print(
        f"Generated {OUTPUT_FILE} "
        f"with {len(papers)} papers."
    )


if name == "main":
    main()
