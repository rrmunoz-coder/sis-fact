from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent

# Elementos legítimos de una instalación local/servidor. Deben estar fuera de Git,
# pero su presencia física no es un problema de higiene del runtime.
LOCAL_RUNTIME_DIRS = {".venv", "logs", "__pycache__", ".pytest_cache", ".git"}
LOCAL_RUNTIME_FILES = {"config.ini", "service/nssm.exe"}

# Residuos que sí indican una instalación mezclada o una entrega incorrecta.
FORBIDDEN_NAMES = {".venv.venv", "sis-fact-main", "inicia.bat"}
FORBIDDEN_SUFFIXES = {".zip"}

issues = []
for path in ROOT.rglob("*"):
    rel = path.relative_to(ROOT)
    rel_text = str(rel).replace("\\", "/")

    if rel_text in LOCAL_RUNTIME_FILES:
        continue
    if any(part in LOCAL_RUNTIME_DIRS for part in rel.parts):
        continue
    if any(part in FORBIDDEN_NAMES for part in rel.parts):
        issues.append(rel_text)
        continue
    if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES:
        issues.append(rel_text)

if issues:
    print("HIGIENE_REVISAR")
    for item in sorted(set(issues)):
        print(item)
    sys.exit(1)

print("HIGIENE_OK")
