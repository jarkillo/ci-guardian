#!/usr/bin/env python3
"""
Script temporal para instalar el hook commit-msg en este repositorio.

Este script instalará el hook de validación de autoría para probar
que efectivamente bloquea commits con Co-Authored-By: Claude.
"""

import stat
from pathlib import Path

# Rutas
REPO_ROOT = Path(__file__).parent.parent
HOOKS_DIR = REPO_ROOT / ".git" / "hooks"
HOOK_SOURCE = REPO_ROOT / "src" / "ci_guardian" / "hooks" / "commit-msg.py"
HOOK_DEST = HOOKS_DIR / "commit-msg-ci-guardian"


def main() -> int:
    """Instala el hook commit-msg."""
    print("📦 Instalando hook commit-msg de CI Guardian...")

    # Verificar que estamos en un repo git
    if not HOOKS_DIR.exists():
        print("❌ Error: No se encuentra el directorio .git/hooks/")
        return 1

    # Verificar que el hook fuente existe
    if not HOOK_SOURCE.exists():
        print(f"❌ Error: No se encuentra el hook fuente en {HOOK_SOURCE}")
        return 1

    # Obtener el python del venv actual
    import sys

    python_executable = sys.executable

    # Crear el script del hook
    hook_content = f"""#!{python_executable}
# CI-GUARDIAN-HOOK
# This hook was installed by CI Guardian to prevent Claude co-authorship

import sys
from pathlib import Path

# Path to the hook implementation
hook_impl = Path(__file__).parent.parent.parent / "src" / "ci_guardian" / "hooks" / "commit-msg.py"

# Execute the hook
exec(open(hook_impl).read())
"""

    # Escribir el hook
    HOOK_DEST.write_text(hook_content, encoding="utf-8")

    # Dar permisos de ejecución (755)
    HOOK_DEST.chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

    print(f"✅ Hook instalado en: {HOOK_DEST}")
    print(f"✅ Permisos: {oct(HOOK_DEST.stat().st_mode)[-3:]}")
    print("\n🧪 Ahora intenta hacer un commit con Co-Authored-By: Claude")
    print("   Debería ser rechazado por el hook.\n")

    return 0


if __name__ == "__main__":
    exit(main())
