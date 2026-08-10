from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = [
    "README.md", "VERSION.md", "requirements.txt", "config.ini.example",
    "run_dev.cmd", "service_entry.py", "wsgi.py",
    "sisfact/__init__.py", "sisfact/config.py", "sisfact/db.py",
    "sisfact/security.py", "sisfact/auth/routes.py", "sisfact/auth/service.py",
    "sql/10_SECURITY_BASE.sql", "sql/11_VALIDAR_SECURITY.sql",
    "sql/20_CONTEXT_BASE.sql", "sql/21_VALIDAR_CONTEXT.sql",
    "sql/30_INTEGRATION_BASE.sql", "sql/31_VALIDAR_INTEGRATION.sql",
    "sql/90_VALIDAR_BILLING_ONE.sql",
]
missing = [item for item in REQUIRED if not (ROOT / item).exists()]
if missing:
    print("RELEASE_REVISAR")
    for item in missing:
        print(f"FALTA {item}")
    sys.exit(1)
print(f"RELEASE_OK archivos_requeridos={len(REQUIRED)}")
