"""
Ejecutor local de GitHub Actions workflows (LIB-7).

Este módulo permite ejecutar workflows de GitHub Actions localmente para prevenir
consumo de minutos de CI/CD y detectar errores antes del push.

Usa 'act' (https://github.com/nektos/act) cuando está disponible, con fallback
a ejecución directa de herramientas (pytest, ruff, black) cuando no lo está.
"""

from pathlib import Path


def esta_act_instalado() -> bool:
    """
    Detecta si act está instalado.

    Returns:
        True si act está disponible en PATH, False en caso contrario
    """
    raise NotImplementedError("Función no implementada - Fase RED de TDD")


def ejecutar_workflow_con_act(
    workflow_file: Path,
    evento: str = "push",
    timeout: int = 300,
) -> tuple[bool, str]:
    """
    Ejecuta workflow de GitHub Actions usando act.

    Args:
        workflow_file: Path al archivo de workflow (.github/workflows/ci.yml)
        evento: Evento de GitHub Actions (push, pull_request, etc.)
        timeout: Timeout en segundos (default: 300 = 5 minutos)

    Returns:
        Tupla (exito, output):
        - exito: True si el workflow pasó exitosamente
        - output: Output del workflow

    Raises:
        ValueError: Si workflow_file no existe o el path es inválido
        FileNotFoundError: Si act no está instalado
    """
    raise NotImplementedError("Función no implementada - Fase RED de TDD")


def ejecutar_workflow_fallback(repo_path: Path) -> tuple[bool, str]:
    """
    Ejecuta validaciones básicas cuando act no está disponible.

    Ejecuta comandos básicos que típicamente están en workflows:
    - pytest (tests)
    - ruff check (linting)
    - black --check (formatting)

    Args:
        repo_path: Path al repositorio

    Returns:
        Tupla (exito, output):
        - exito: True si todas las validaciones pasan
        - output: Resumen de resultados
    """
    raise NotImplementedError("Función no implementada - Fase RED de TDD")


def ejecutar_workflow(
    workflow_file: Path | None = None,
    repo_path: Path | None = None,
    evento: str = "push",
) -> tuple[bool, str]:
    """
    Ejecuta workflow localmente. Auto-detecta si usar act o fallback.

    Args:
        workflow_file: Path al workflow (None = auto-detect .github/workflows/ci.yml)
        repo_path: Path al repositorio (None = Path.cwd())
        evento: Evento de GH Actions

    Returns:
        Tupla (exito, output)
    """
    raise NotImplementedError("Función no implementada - Fase RED de TDD")
