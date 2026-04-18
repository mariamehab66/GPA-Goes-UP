"""
smoke_test.py — T027: Run both sample PDFs through the parsing pipeline.
Usage: python smoke_test.py
Run from the backend/ directory.
"""
import sys
import os

# Make src importable without installing the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.parsing.pipeline import TranscriptParser

SAMPLES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "data", "sample_academic_record"
)

def run_sample(path: str):
    name = os.path.basename(path)
    print(f"\n{'='*60}")
    print(f"FILE: {name}")
    print('='*60)

    with open(path, "rb") as f:
        pdf_bytes = f.read()

    try:
        result = TranscriptParser().parse(pdf_bytes)
    except Exception as e:
        print(f"  PIPELINE ERROR: {type(e).__name__}: {e}")
        return

    s = result.student
    print(f"  Student: CGPA={s.cgpa}, Earned={s.earned_hours}h, Level={s.level}, "
          f"Program={s.program!r}, AdmissionYear={s.admission_year}, "
          f"LastSemGPA={s.last_semester_gpa}")
    print(f"  Enrollments: {len(result.enrollments)}")
    for e in result.enrollments[:5]:
        print(f"    {e.course_code}  {e.semester} {e.year}  grade={e.course_grade}  gpa={e.course_gpa}")
    if len(result.enrollments) > 5:
        print(f"    ... +{len(result.enrollments)-5} more")
    print(f"  is_partial: {result.is_partial}")
    print(f"  Warnings: {len(result.warnings)}")
    for w in result.warnings[:5]:
        print(f"    [{w.level}] {w.location}: {w.message} (raw={w.raw_value!r})")
    if result.is_partial or result.warnings:
        print(f"\n  STATUS: PARTIAL/WARNINGS")
    else:
        print(f"\n  STATUS: CLEAN OK")

if __name__ == "__main__":
    samples = [
        os.path.join(SAMPLES_DIR, "academic_record1.pdf"),
        os.path.join(SAMPLES_DIR, "academic_record2.pdf"),
    ]
    for path in samples:
        if os.path.exists(path):
            run_sample(path)
        else:
            print(f"SKIP (not found): {path}")
    print("\nDone.")
