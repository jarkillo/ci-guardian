"""
Ejecutor local de GitHub Actions workflows (LIB-7).

Este módulo permite ejecutar workflows de GitHub Actions localmente para prevenir
consumo de minutos de CI/CD y detectar errores antes del push.

Usa 'act' (https://github.com/nektos/act) cuando está disponible, con fallback
a ejecución directa de herramientas (pytest, ruff, black) cuando no lo está.
"""

import subprocess
from pathlib import Path


def esta_act_instalado() -> bool:
    """
    Detecta si act está instalado.

    Returns:
        True si act está disponible en PATH, False en caso contrario
    """
    try:
        subprocess.run(
            ["act", "--version"],
            capture_output=True,
            timeout=5,
            shell=False,
        )
        return True
    except (FileNotFoundError, PermissionError):
        return False


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
    # Validar evento (whitelist)
    EVENTOS_PERMITIDOS = {"push", "pull_request", "workflow_dispatch", "schedule"}
    if evento not in EVENTOS_PERMITIDOS:
        raise ValueError(f"evento inválido: {evento}")

    # Validar path traversal
    if ".." in str(workflow_file):
        raise ValueError("path traversal detectado en workflow_file")

    # Validar existencia
    if not workflow_file.exists():
        raise ValueError(f"Workflow no existe: {workflow_file}")

    # Ejecutar act
    try:
        resultado = subprocess.run(
            ["act", evento, "-W", str(workflow_file)],
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )

        if resultado.returncode == 0:
            return (True, resultado.stdout)
        return (False, resultado.stderr)

    except FileNotFoundError as err:
        raise FileNotFoundError("act no está instalado") from err


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
    resultados = []
    todo_ok = True

    # Ejecutar pytest
    try:
        res = subprocess.run(
            ["pytest"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60,
            shell=False,
        )
        if res.returncode == 0:
            resultados.append("✅ pytest: PASS")
        else:
            resultados.append("❌ pytest: FAIL")
            todo_ok = False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        resultados.append("⚠️  pytest: SKIP (no instalado)")

    # Ejecutar ruff
    try:
        res = subprocess.run(
            ["ruff", "check", "."],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60,
            shell=False,
        )
        if res.returncode == 0:
            resultados.append("✅ ruff: PASS")
        else:
            resultados.append("❌ ruff: FAIL")
            todo_ok = False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        resultados.append("⚠️  ruff: SKIP (no instalado)")

    # Ejecutar black
    try:
        res = subprocess.run(
            ["black", "--check", "."],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60,
            shell=False,
        )
        if res.returncode == 0:
            resultados.append("✅ black: PASS")
        else:
            resultados.append("❌ black: FAIL")
            todo_ok = False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        resultados.append("⚠️  black: SKIP (no instalado)")

    return (todo_ok, "\n".join(resultados))


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
    # Defaults
    if repo_path is None:
        repo_path = Path.cwd()

    # Auto-detectar workflow
    if workflow_file is None:
        ci_yml = repo_path / ".github" / "workflows" / "ci.yml"
        test_yml = repo_path / ".github" / "workflows" / "test.yml"

        if ci_yml.exists():
            workflow_file = ci_yml
        elif test_yml.exists():
            workflow_file = test_yml

    # Decidir modo
    if esta_act_instalado() and workflow_file is not None and workflow_file.exists():
        # Usar act
        exito, output = ejecutar_workflow_con_act(workflow_file, evento)
        return (exito, f"🎬 Ejecutando con act...\n{output}")
    # Usar fallback
    exito, output = ejecutar_workflow_fallback(repo_path)
    return (exito, f"⚠️  act no disponible, usando modo fallback...\n{output}")
