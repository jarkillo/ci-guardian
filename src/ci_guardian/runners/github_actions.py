"""
Ejecutor local de GitHub Actions workflows (LIB-7).

Este módulo permite ejecutar workflows de GitHub Actions localmente para prevenir
consumo de minutos de CI/CD y detectar errores antes del push.

Usa 'act' (https://github.com/nektos/act) cuando está disponible, con fallback
a ejecución directa de herramientas (pytest, ruff, black) cuando no lo está.

ADVERTENCIA DE SEGURIDAD:
act ejecuta workflows en contenedores Docker locales. NUNCA ejecutes workflows
de repositorios no confiables, ya que pueden ejecutar código arbitrario.
"""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


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
        logger.warning(f"Intento de usar evento no permitido: {evento}")
        raise ValueError(f"evento inválido: {evento}")

    # Validar path traversal de forma robusta
    try:
        workflow_file = workflow_file.resolve(strict=True)
    except (OSError, RuntimeError) as e:
        logger.error(f"Error resolviendo path de workflow: {e}")
        raise ValueError(f"Ruta de workflow inválida: {e}") from e

    # Validar que esté en .github/workflows/
    if ".github/workflows" not in str(workflow_file):
        logger.error(f"Workflow fuera de .github/workflows/: {workflow_file.name}")
        raise ValueError("El workflow debe estar en un directorio .github/workflows/ válido")

    # Validar extensión
    if workflow_file.suffix not in [".yml", ".yaml"]:
        raise ValueError("El workflow debe ser un archivo YAML (.yml o .yaml)")

    # Validar tamaño del archivo (máximo 1MB)
    MAX_WORKFLOW_SIZE = 1024 * 1024  # 1MB
    tamaño = workflow_file.stat().st_size
    if tamaño > MAX_WORKFLOW_SIZE:
        raise ValueError(
            f"Archivo workflow demasiado grande: {tamaño} bytes "
            f"(máximo: {MAX_WORKFLOW_SIZE} bytes)"
        )
    if tamaño == 0:
        raise ValueError("Archivo workflow vacío")

    logger.info(
        f"Ejecutando workflow con act: {workflow_file.name}, "
        f"evento={evento}, timeout={timeout}s"
    )

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
            logger.info(f"Workflow exitoso: {workflow_file.name}")
            return (True, resultado.stdout)

        logger.warning(
            f"Workflow falló: {workflow_file.name}, " f"returncode={resultado.returncode}"
        )
        return (False, resultado.stderr)

    except FileNotFoundError as err:
        logger.error("act no está instalado en el sistema")
        raise FileNotFoundError("act no está instalado") from err

    except subprocess.TimeoutExpired:
        logger.error(f"Workflow timeout después de {timeout}s: {workflow_file.name}")
        return (
            False,
            f"⏱️ Timeout: El workflow excedió el límite de {timeout} segundos. "
            f"Considera optimizar el workflow o aumentar el timeout.",
        )


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

    Raises:
        ValueError: Si repo_path no es válido
    """
    # Validar que repo_path sea Path
    if not isinstance(repo_path, Path):
        raise TypeError(f"repo_path debe ser Path, recibido: {type(repo_path)}")

    # Resolver y validar existencia
    try:
        repo_path = repo_path.resolve(strict=True)
    except (OSError, RuntimeError) as e:
        raise ValueError(f"Ruta de repositorio inválida: {e}") from e

    # Validar que sea repositorio git
    if not (repo_path / ".git").is_dir():
        raise ValueError("El directorio no es un repositorio Git válido")

    logger.info(f"Ejecutando workflow fallback en: {repo_path.name}")

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
