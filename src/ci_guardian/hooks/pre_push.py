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

import yaml


def cargar_configuracion(repo_path: Path) -> dict:
    """
    Carga configuración desde .ci-guardian.yaml o retorna defaults.

    Args:
        repo_path: Ruta al repositorio Git

    Returns:
        Diccionario con configuración del hook pre-push
    """
    config_path = repo_path / ".ci-guardian.yaml"

    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config if config else _config_por_defecto()
        except Exception:
            # Si falla la lectura, usar defaults
            return _config_por_defecto()
    else:
        return _config_por_defecto()


def _config_por_defecto() -> dict:
    """
    Retorna configuración por defecto para pre-push.

    Returns:
        Diccionario con configuración default
    """
    return {
        "hooks": {
            "pre-push": {
                "enabled": True,
                "validadores": ["tests"],
            }
        }
    }


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

        exito, mensaje = ejecutar_workflow(repo_path)
        return exito, mensaje
    except Exception as e:
        return False, f"✗ Error ejecutando GitHub Actions: {e}"


def main() -> int:
    """
    Punto de entrada principal del hook pre-push.

    Returns:
        0 si todas las validaciones pasan, 1 si alguna falla
    """
    # Detectar si se debe skip (variable de entorno)
    if os.environ.get("CI_GUARDIAN_SKIP_TESTS") == "1":
        print("⚠️  CI_GUARDIAN_SKIP_TESTS=1 detectado, saltando validaciones")
        return 0

    # Obtener directorio del repositorio
    repo_path = Path.cwd()

    # Cargar configuración
    config = cargar_configuracion(repo_path)

    # Verificar si pre-push está habilitado
    if not config.get("hooks", {}).get("pre-push", {}).get("enabled", True):
        print("ℹ️  Hook pre-push deshabilitado en configuración")
        return 0

    print("🔍 Ejecutando validaciones pre-push...")

    # Obtener validadores configurados
    validadores = config.get("hooks", {}).get("pre-push", {}).get("validadores", ["tests"])

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
