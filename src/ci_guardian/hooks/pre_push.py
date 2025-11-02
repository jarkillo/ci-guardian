"""Hook pre-push de CI Guardian.

Este hook ejecuta validaciones antes de permitir un push al repositorio:
- Ejecuta tests con pytest
- Ejecuta GitHub Actions localmente (si está configurado)

Este módulo fue originalmente documentado en v0.1.0 pero no implementado,
causando el bug crítico ModuleNotFoundError. Implementación en v0.2.0.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _ejecutar_pytest(repo_path: Path) -> tuple[bool, str]:
    """
    Ejecuta pytest en el repositorio.

    Args:
        repo_path: Ruta al repositorio

    Returns:
        Tupla (éxito: bool, mensaje: str)
    """
    try:
        resultado = subprocess.run(
            ["pytest", "-v"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutos timeout
            shell=False,  # CRÍTICO: nunca usar shell=True
        )

        if resultado.returncode == 0:
            return True, "✓ Tests pasaron exitosamente"
        return False, f"✗ Tests fallaron:\n{resultado.stdout}"

    except FileNotFoundError:
        return False, "✗ pytest no está instalado. Instala con: pip install pytest"
    except subprocess.TimeoutExpired:
        return False, "✗ Tests excedieron timeout de 5 minutos"
    except Exception as e:
        return False, f"✗ Error ejecutando tests: {e}"


def _ejecutar_github_actions(repo_path: Path) -> tuple[bool, str]:
    """
    Ejecuta GitHub Actions localmente usando act o fallback.

    Args:
        repo_path: Ruta al repositorio

    Returns:
        Tupla (éxito: bool, mensaje: str)
    """
    # Importar el runner de GitHub Actions
    try:
        from ci_guardian.runners.github_actions import ejecutar_workflow

        exito, mensaje = ejecutar_workflow(repo_path=repo_path)
        return exito, mensaje
    except Exception as e:
        return False, f"✗ Error ejecutando GitHub Actions: {e}"


def main() -> int:
    """
    Punto de entrada principal del hook pre-push.

    Returns:
        0 si todas las validaciones pasan, 1 si alguna falla

    Nota arquitectural (LIB-23):
        La orquestación de validadores está inline (no en core/hook_runner.py)
        porque solo 2 de 4 hooks necesitan orquestación actualmente.

        Según la Regla de Tres: "No abstraer hasta tener 3+ casos similares".
        Ver CLAUDE.md sección "Decisiones Arquitecturales Postponed" para
        triggers que justificarían crear hook_runner.py en el futuro.
    """
    # Detectar si se debe skip (variable de entorno)
    if os.environ.get("CI_GUARDIAN_SKIP_TESTS") == "1":
        print("⚠️  CI_GUARDIAN_SKIP_TESTS=1 detectado, saltando validaciones")
        return 0

    # Obtener directorio del repositorio
    repo_path = Path.cwd()

    # Cargar configuración desde módulo centralizado
    from ci_guardian.core.config import cargar_configuracion

    config = cargar_configuracion(repo_path)

    # Verificar si pre-push está habilitado
    pre_push_config = config.hooks.get("pre-push")
    if not pre_push_config or not pre_push_config.enabled:
        print("ℹ️  Hook pre-push deshabilitado en configuración")
        return 0

    print("🔍 Ejecutando validaciones pre-push...")

    # Obtener validadores configurados
    validadores = pre_push_config.validadores if pre_push_config.validadores else ["tests"]

    todas_exitosas = True

    # Ejecutar tests si está configurado
    if "tests" in validadores:
        print("\n1. Ejecutando tests...")
        exito, mensaje = _ejecutar_pytest(repo_path)
        print(f"   {mensaje}")
        if not exito:
            todas_exitosas = False

    # Ejecutar GitHub Actions si está configurado
    if "github-actions" in validadores and todas_exitosas:
        print("\n2. Ejecutando GitHub Actions localmente...")
        exito, mensaje = _ejecutar_github_actions(repo_path)
        print(f"   {mensaje}")
        if not exito:
            todas_exitosas = False

    if todas_exitosas:
        print("\n✅ Todas las validaciones pasaron. Push permitido.")
        return 0
    print("\n❌ Algunas validaciones fallaron. Push bloqueado.")
    print("   Tip: Fix los errores o usa CI_GUARDIAN_SKIP_TESTS=1 para skip temporal")
    return 1


if __name__ == "__main__":
    sys.exit(main())
