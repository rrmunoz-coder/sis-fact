from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
FORBIDDEN_NAMES = {"config.ini", ".venv", ".venv.venv", "sis-fact-main"}
FORBIDDEN_SUFFIXES = {".zip", ".log", ".pyc"}
issues = []
for path in ROOT.rglob("*"):
    rel = path.relative_to(ROOT)
    if any(part in FORBIDDEN_NAMES for part in rel.parts):
        issues.append(str(rel))
        continue
    if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES:
        issues.append(str(rel))
if issues:
    print("HIGIENE_REVISAR")
    for item in sorted(set(issues)):
        print(item)
    sys.exit(1)
print("HIGIENE_OK")
