#!/usr/bin/env python3
"""
Resume Classification Pipeline (LLM-based via Groq)

Features:
- Local resume classification
- Groq-hosted LLM for parsing (chat completions)
- Robust text extraction (PDF, DOCX)
- Clean Excel output (grouped by Profession)
"""

import os
import re
from pathlib import Path
from datetime import datetime

import pandas as pd

# =========================
# Groq SDK (LLM)
# =========================
try:
    from groq import Groq

    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# =========================
# Configuration
# =========================
BASE_DIR = Path(__file__).parent
ATTACHMENTS_DIR = BASE_DIR / "data" / "attachments"
OUTPUT_DIR = BASE_DIR / "results" / "excel"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EXCEL_PATH = OUTPUT_DIR / "classified_resumes.xlsx"

# =========================
# Safety checks
# =========================
def require_api_key():
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("❌ GROQ_API_KEY not set in environment variables")

    if not GROQ_AVAILABLE:
        raise RuntimeError("❌ groq SDK not installed")


# =========================
# Text Extraction
# =========================
def extract_text(file_path: Path) -> str:
    try:
        if file_path.suffix.lower() == ".pdf":
            from PyPDF2 import PdfReader
            reader = PdfReader(str(file_path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)

        elif file_path.suffix.lower() == ".docx":
            import docx
            doc = docx.Document(str(file_path))
            return "\n".join(p.text for p in doc.paragraphs)

        else:
            return ""

    except Exception as e:
        print(f"⚠️ Error extracting text from {file_path.name}: {e}")
        return ""


# =========================
# LLM call via Groq
# =========================
def gemini_generate(prompt: str) -> str:
    """
    Kept name for backwards compatibility.
    Now uses Groq chat completions under the hood.
    """
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set in environment variables")

        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=256,
        )

        choice = response.choices[0]
        content = getattr(choice.message, "content", None) or ""
        return content.strip()

    except Exception as e:
        print(f"❌ LLM error (Groq): {e}")
        return ""

# =========================
# Resume Parsing
# =========================
def parse_resume_with_gemini(text: str) -> dict:
    prompt = f"""
Extract the following details from the resume text.

Return the answer STRICTLY in this format:
Name: <full name>
Profession: <one of Software Engineer, Data Science, QA / Testing, HR, Unclassified>
Experience: <number of years or Fresher>

Resume Text:
{text[:6000]}
"""

    output = gemini_generate(prompt)

    name = profession = experience = ""

    for line in output.splitlines():
        if line.lower().startswith("name:"):
            name = line.split(":", 1)[1].strip()
        elif line.lower().startswith("profession:"):
            profession = line.split(":", 1)[1].strip()
        elif line.lower().startswith("experience:"):
            experience = line.split(":", 1)[1].strip()

    profession_lower = profession.lower()

    if "data" in profession_lower:
        profession = "Data Science"
    elif "software" in profession_lower or "developer" in profession_lower or "engineer" in profession_lower:
        profession = "Software Engineer"
    elif "qa" in profession_lower or "test" in profession_lower:
        profession = "QA / Testing"
    elif "hr" in profession_lower or "human" in profession_lower:
        profession = "HR"
    else:
        profession = "Unclassified"

    if not name or len(name) < 3:
        name = "Unknown"

    return {
        "Full Name": name,
        "Profession": profession,
        "Experience": experience
    }

# =========================
# Local Resume Classification
# =========================
def safe_sheet_name(name: str) -> str:
    # Excel forbidden characters: \ / ? * [ ]
    return re.sub(r"[\\/*?\[\]]", "_", name)[:31]


def classify_local_resumes_and_write_excel():
    records = []

    files = list(ATTACHMENTS_DIR.glob("*"))
    print(f"📂 Found {len(files)} local resume files")

    for file_path in files:
        print(f"🔍 Processing: {file_path.name}")

        text = extract_text(file_path)
        if not text.strip():
            print("   → No text found, skipping")
            continue

        parsed = parse_resume_with_gemini(text)

        records.append({
            "Full Name": parsed["Full Name"],
            "Email": "",
            "Mobile Number": "",
            "Domain": parsed["Profession"],
            "Skills": "",
            "Experience": parsed["Experience"],
            "Resume Link": str(file_path),
            "Date Received": datetime.now().strftime("%Y-%m-%d"),
            "Profession": parsed["Profession"]
        })

        print(f"   → Profession: {parsed['Profession']} | Name: {parsed['Full Name']}")

    if not records:
        print("❌ No valid resumes processed")
        return

    df = pd.DataFrame(records)

    # Keep Profession for grouping
    column_order = [
        "Full Name",
        "Email",
        "Mobile Number",
        "Domain",
        "Skills",
        "Experience",
        "Resume Link",
        "Date Received",
        "Profession"
    ]
    df = df[column_order]

    # Write Excel
    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
        for profession, group in df.groupby("Profession"):
            group.drop(columns=["Profession"]).to_excel(
                writer,
                sheet_name=safe_sheet_name(profession),

                index=False
            )

    print(f"\n✅ Excel successfully written to:\n{EXCEL_PATH}")
    print(f"📊 File size: {EXCEL_PATH.stat().st_size // 1024} KB")


# =========================
# MAIN (THIS WAS MISSING BEFORE)
# =========================
def main():
    require_api_key()

    if not ATTACHMENTS_DIR.exists():
        raise RuntimeError(f"❌ Attachments folder not found: {ATTACHMENTS_DIR}")

    classify_local_resumes_and_write_excel()


if __name__ == "__main__":
    main()
