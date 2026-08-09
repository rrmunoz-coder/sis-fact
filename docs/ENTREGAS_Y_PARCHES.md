# Modelo de entregas y parches SIS-FACT

## Regla principal

SIS-FACT mantiene una sola versión vigente en GitHub:

```text
main
```

No se deben mantener carpetas paralelas como versión principal.

## Qué no se versiona

```text
sis-fact-main/
sis-fact-main.zip
.venv/
.venv.venv/
inicia.bat
patch_*/
config.ini
logs/
```

## Cómo se entrega un cambio

Todo cambio debe entrar como commit sobre `main` y tocar, cuando corresponda:

```text
código
sql
documentación
CHANGELOG.md
```

## Estructura limpia esperada en servidor

```text
K:\@@@@@sis-fact
├── .venv/
├── docs/
├── prompts/
├── releases/
├── sisfact/
├── sql/
├── tests/
├── config.ini
├── config.ini.example
├── requirements.txt
├── run_dev.cmd
└── wsgi.py
```

La carpeta `sis-fact-main` solo puede existir temporalmente al descomprimir un ZIP, pero luego debe integrarse/renombrarse a la carpeta activa o eliminarse.

## Parche correcto

Un parche correcto es:

```text
commit GitHub + instrucciones de actualización
```

No es:

```text
zip suelto + carpeta duplicada + script alternativo no versionado
```

## Dinámica tipo ATLAS

1. Código único en carpeta estable.
2. Configuración real fuera del repo (`config.ini`).
3. Oracle local guarda autorización y roles.
4. LDAP valida password corporativa.
5. Servicio Windows apunta siempre a la misma carpeta.
6. Las migraciones SQL son explícitas y numeradas.
7. El manual se actualiza junto con el cambio.
