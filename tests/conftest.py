"""
Configuración de pytest y fixtures compartidas para todos los tests.

Este módulo contiene fixtures reutilizables que están disponibles
automáticamente para todos los tests del proyecto.
"""

from pathlib import Path

import pytest


@pytest.fixture
def repo_git_mock(tmp_path: Path) -> Path:
    """
    Crea un repositorio Git mock con estructura básica.

    Args:
        tmp_path: Directorio temporal proporcionado por pytest

    Returns:
        Path al directorio del repositorio mock con .git/hooks/ creado
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / ".git" / "hooks").mkdir()
    return repo


@pytest.fixture
def repo_sin_hooks(tmp_path: Path) -> Path:
    """
    Crea un repositorio Git mock sin el directorio hooks/.

    Args:
        tmp_path: Directorio temporal proporcionado por pytest

    Returns:
        Path al directorio del repositorio mock solo con .git/
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    return repo


@pytest.fixture
def directorio_no_git(tmp_path: Path) -> Path:
    """
    Crea un directorio normal que NO es un repositorio Git.

    Args:
        tmp_path: Directorio temporal proporcionado por pytest

    Returns:
        Path al directorio normal sin .git/
    """
    dir_path = tmp_path / "no_repo"
    dir_path.mkdir()
    return dir_path


@pytest.fixture
def hook_contenido_bash() -> str:
    """
    Retorna contenido de ejemplo para un hook bash.

    Returns:
        String con un script bash válido con shebang
    """
    return """#!/bin/bash
# Hook de prueba
echo "Ejecutando hook de prueba"
exit 0
"""


@pytest.fixture
def hook_contenido_python() -> str:
    """
    Retorna contenido de ejemplo para un hook Python.

    Returns:
        String con un script Python válido con shebang
    """
    return """#!/usr/bin/env python3
# Hook de prueba en Python
import sys

def main():
    print("Ejecutando hook de prueba")
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""


@pytest.fixture
def hook_contenido_bat() -> str:
    """
    Retorna contenido de ejemplo para un hook batch de Windows.

    Returns:
        String con un script batch válido
    """
    return """@echo off
REM Hook de prueba para Windows
echo Ejecutando hook de prueba
exit /b 0
"""


@pytest.fixture
def venv_linux_mock(tmp_path: Path) -> Path:
    """
    Crea un entorno virtual mock para Linux/macOS.

    Args:
        tmp_path: Directorio temporal proporcionado por pytest

    Returns:
        Path al directorio del venv mock con estructura bin/python
    """
    venv = tmp_path / "venv"
    venv.mkdir()
    bin_dir = venv / "bin"
    bin_dir.mkdir()
    python_exe = bin_dir / "python"
    python_exe.touch()
    python_exe.chmod(0o755)
    # También crear python3 como symlink común
    python3_exe = bin_dir / "python3"
    python3_exe.touch()
    python3_exe.chmod(0o755)
    return venv


@pytest.fixture
def venv_windows_mock(tmp_path: Path) -> Path:
    """
    Crea un entorno virtual mock para Windows.

    Args:
        tmp_path: Directorio temporal proporcionado por pytest

    Returns:
        Path al directorio del venv mock con estructura Scripts/python.exe
    """
    venv = tmp_path / "venv"
    venv.mkdir()
    scripts_dir = venv / "Scripts"
    scripts_dir.mkdir()
    python_exe = scripts_dir / "python.exe"
    python_exe.touch()
    return venv


@pytest.fixture
def proyecto_con_venv_linux(tmp_path: Path) -> Path:
    """
    Crea un proyecto mock con venv funcional de Linux.

    Args:
        tmp_path: Directorio temporal proporcionado por pytest

    Returns:
        Path al directorio del proyecto con venv/ configurado
    """
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()
    venv = proyecto / "venv"
    venv.mkdir()
    bin_dir = venv / "bin"
    bin_dir.mkdir()
    python_exe = bin_dir / "python"
    python_exe.touch()
    python_exe.chmod(0o755)
    return proyecto


@pytest.fixture
def proyecto_con_venv_windows(tmp_path: Path) -> Path:
    """
    Crea un proyecto mock con venv funcional de Windows.

    Args:
        tmp_path: Directorio temporal proporcionado por pytest

    Returns:
        Path al directorio del proyecto con venv/ configurado
    """
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()
    venv = proyecto / "venv"
    venv.mkdir()
    scripts_dir = venv / "Scripts"
    scripts_dir.mkdir()
    python_exe = scripts_dir / "python.exe"
    python_exe.touch()
    return proyecto


@pytest.fixture
def proyecto_con_dotvenv(tmp_path: Path) -> Path:
    """
    Crea un proyecto mock con .venv/ en lugar de venv/.

    Args:
        tmp_path: Directorio temporal proporcionado por pytest

    Returns:
        Path al directorio del proyecto con .venv/ configurado
    """
    proyecto = tmp_path / "proyecto"
    proyecto.mkdir()
    venv = proyecto / ".venv"
    venv.mkdir()
    bin_dir = venv / "bin"
    bin_dir.mkdir()
    python_exe = bin_dir / "python"
    python_exe.touch()
    python_exe.chmod(0o755)
    return proyecto


@pytest.fixture
def venv_corrupto(tmp_path: Path) -> Path:
    """
    Crea un directorio venv corrupto (sin ejecutable Python).

    Args:
        tmp_path: Directorio temporal proporcionado por pytest

    Returns:
        Path al directorio del venv corrupto
    """
    venv = tmp_path / "venv"
    venv.mkdir()
    bin_dir = venv / "bin"
    bin_dir.mkdir()
    # No se crea el ejecutable Python
    return venv


@pytest.fixture
def venv_sin_permisos(tmp_path: Path) -> Path:
    """
    Crea un venv con ejecutable Python sin permisos de ejecución.

    Args:
        tmp_path: Directorio temporal proporcionado por pytest

    Returns:
        Path al directorio del venv sin permisos
    """
    venv = tmp_path / "venv"
    venv.mkdir()
    bin_dir = venv / "bin"
    bin_dir.mkdir()
    python_exe = bin_dir / "python"
    python_exe.touch()
    python_exe.chmod(0o644)  # Sin permisos de ejecución
    return venv
