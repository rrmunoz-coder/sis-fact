from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = [
    "README.md", "VERSION.md", "requirements.txt", "config.ini.example",
    "run_dev.cmd", "service_entry.py", "wsgi.py",
    "sisfact/__init__.py", "sisfact/config.py", "sisfact/db.py",
    "sisfact/security.py", "sisfact/auth/routes.py", "sisfact/auth/service.py",
    "sisfact/users/routes.py", "sisfact/context/routes.py", "sisfact/context/service.py",
    "sisfact/integrations/routes.py",
    "sql/10_SECURITY_BASE.sql", "sql/11_VALIDAR_SECURITY.sql",
    "sql/20_CONTEXT_BASE.sql", "sql/21_VALIDAR_CONTEXT.sql",
    "sql/30_INTEGRATION_BASE.sql", "sql/31_VALIDAR_INTEGRATION.sql",
    "sql/40_OPERATIONAL_BASE.sql", "sql/41_VALIDAR_OPERATIONAL.sql",
    "sql/90_VALIDAR_BILLING_ONE.sql",
    "sql/migration_v0_2_0_to_v0_2_1/00_PRECHECK.sql",
    "sql/migration_v0_2_0_to_v0_2_1/10_APPLY.sql",
    "sql/migration_v0_2_0_to_v0_2_1/20_VALIDATE.sql",
    "docs/ARQUITECTURA_V0_2.md", "docs/MODELO_FUNCIONAL_V0_2_1.md",
    "docs/FUENTES_E_INTEGRACIONES_V0_2.md",
]
missing = [item for item in REQUIRED if not (ROOT / item).exists()]
if missing:
    print("RELEASE_REVISAR")
    for item in missing:
        print(f"FALTA {item}")
    sys.exit(1)
print(f"RELEASE_OK archivos_requeridos={len(REQUIRED)}")
