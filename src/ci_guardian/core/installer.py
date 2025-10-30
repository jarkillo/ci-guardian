"""
Instalador de Git hooks para CI Guardian.

Este módulo proporciona funcionalidad para instalar, validar y gestionar
hooks de Git de forma segura y multiplataforma.
"""

from __future__ import annotations

import logging
import platform
from pathlib import Path

# Logger para el módulo
logger = logging.getLogger(__name__)

# Whitelist de hooks permitidos
HOOKS_PERMITIDOS: set[str] = {"pre-commit", "pre-push", "post-commit", "pre-rebase"}

# Tamaño máximo permitido para un hook (100KB)
MAX_HOOK_SIZE: int = 1024 * 100


def es_repositorio_git(repo_path: Path) -> bool:
    """
    Verifica si un directorio es un repositorio Git válido.

    Un repositorio es válido si:
    - El directorio existe
    - Contiene un subdirectorio .git/
    - .git es un directorio, no un archivo

    Args:
        repo_path: Ruta al directorio a verificar

    Returns:
        True si es un repositorio Git válido, False en caso contrario
    """
    if not repo_path.exists():
        return False

    git_dir = repo_path / ".git"
    return git_dir.exists() and git_dir.is_dir()


def validar_nombre_hook(hook_name: str) -> bool:
    """
    Valida que el nombre del hook esté en la whitelist.

    Args:
        hook_name: Nombre del hook a validar

    Returns:
        True si el hook está en la whitelist

    Raises:
        ValueError: Si el nombre del hook no está en la whitelist
    """
    if hook_name not in HOOKS_PERMITIDOS:
        raise ValueError(f"Hook no permitido: {hook_name}")
    return True


def validar_shebang(contenido: str, sistema: str | None = None) -> None:
    """
    Valida que el hook tenga un shebang válido.

    En sistemas Unix (Linux/macOS), verifica que el contenido del hook comience
    con un shebang (#!) y que el intérprete usado esté en la whitelist.
    En Windows, permite scripts .bat que comienzan con @echo off.

    Args:
        contenido: Contenido del hook a validar
        sistema: Sistema operativo (Linux, Windows, Darwin). Si es None, detecta automáticamente.

    Raises:
        ValueError: Si el hook no tiene shebang o usa un intérprete no permitido
    """
    if sistema is None:
        sistema = platform.system()

    # Whitelist de shebangs permitidos (Unix)
    SHEBANGS_PERMITIDOS = {
        "#!/bin/bash",
        "#!/bin/sh",
        "#!/usr/bin/env python",
        "#!/usr/bin/env python3",
    }

    # Obtener la primera línea
    primera_linea = contenido.split("\n")[0].rstrip()

    # En Windows, permitir scripts .bat que comienzan con @echo off
    if sistema == "Windows":
        if primera_linea.startswith("@echo off") or primera_linea.startswith("#!"):
            # Permitir tanto @echo off como shebangs Unix en Windows
            return
        else:
            raise ValueError("El hook debe comenzar con un shebang (#!) o '@echo off' (Windows)")

    # En sistemas Unix, requerir shebang
    if not primera_linea.startswith("#!"):
        raise ValueError("El hook debe comenzar con un shebang (#!)")

    # Validar que el shebang esté en la whitelist
    if primera_linea not in SHEBANGS_PERMITIDOS:
        raise ValueError(f"Shebang no permitido: {primera_linea}")


def validar_path_hook(repo_path: Path, hook_path: Path) -> bool:
    """
    Valida que el path del hook esté dentro de .git/hooks/ (prevención de path traversal).

    Args:
        repo_path: Ruta al repositorio Git
        hook_path: Ruta al archivo del hook

    Returns:
        True si el path es válido

    Raises:
        ValueError: Si se detecta un intento de path traversal
    """
    # Resolver paths absolutos para prevenir ataques con ../
    repo_resuelto = repo_path.resolve()
    hooks_dir = (repo_resuelto / ".git" / "hooks").resolve()
    hook_resuelto = hook_path.resolve()

    # Verificar que el hook esté dentro del directorio de hooks
    try:
        # relative_to lanza ValueError si hook_path no está dentro de hooks_dir
        hook_resuelto.relative_to(hooks_dir)
        return True
    except ValueError:
        logger.warning(
            "Path traversal detectado: intento de escribir fuera de .git/hooks/. "
            f"Repo: {repo_path}, Hook solicitado: {hook_path}"
        )
        raise ValueError("Path traversal detectado") from None


def obtener_extension_hook(sistema: str | None = None) -> str:
    """
    Obtiene la extensión correcta para un hook según el sistema operativo.

    Args:
        sistema: Sistema operativo (Linux, Windows, Darwin). Si es None, detecta automáticamente.

    Returns:
        Extensión del hook: ".bat" para Windows, "" para Linux/macOS
    """
    if sistema is None:
        sistema = platform.system()

    return ".bat" if sistema == "Windows" else ""


def instalar_hook(repo_path: Path, hook_name: str, contenido: str) -> None:
    """
    Instala un hook de Git en el repositorio.

    El proceso:
    1. Valida que sea un repositorio Git válido
    2. Valida que el nombre del hook esté en la whitelist
    3. Valida que el contenido no esté vacío
    4. Valida que el shebang sea válido y esté en la whitelist
    5. Valida que el tamaño del contenido no exceda el límite (100KB)
    6. Valida que el directorio .git/hooks/ existe
    7. Verifica que el hook no exista previamente
    8. Valida el path del hook (prevención de path traversal)
    9. Escribe el hook con la extensión correcta según el SO
    10. En Linux/macOS, aplica permisos de ejecución (755)

    Args:
        repo_path: Ruta al repositorio Git
        hook_name: Nombre del hook (pre-commit, pre-push, etc.)
        contenido: Contenido del hook

    Raises:
        ValueError: Si el nombre del hook no está en la whitelist
        ValueError: Si no es un repositorio Git válido
        ValueError: Si el directorio de hooks no existe
        ValueError: Si el contenido está vacío
        ValueError: Si el shebang no es válido o no está permitido
        ValueError: Si el contenido excede el tamaño máximo permitido
        ValueError: Si se detecta path traversal
        FileExistsError: Si el hook ya existe
    """
    # 1. Validar repositorio Git
    if not es_repositorio_git(repo_path):
        raise ValueError(f"El directorio {repo_path} no es un repositorio Git válido")

    # 2. Validar nombre del hook (whitelist) y loggear path traversal si se detecta
    # Detectar path traversal en el nombre antes de validar whitelist
    if ".." in hook_name or "/" in hook_name or "\\" in hook_name:
        logger.warning(
            "Path traversal detectado: intento de escribir fuera de .git/hooks/. "
            f"Repo: {repo_path}, Hook solicitado: {hook_name}"
        )

    validar_nombre_hook(hook_name)

    # 3. Validar contenido no vacío
    if not contenido or contenido.strip() == "":
        raise ValueError("El contenido del hook no puede estar vacío")

    # 4. Validar shebang (detecta automáticamente el sistema operativo)
    validar_shebang(contenido)

    # 5. Validar tamaño del contenido
    tamano_bytes = len(contenido.encode("utf-8"))
    if tamano_bytes > MAX_HOOK_SIZE:
        raise ValueError(
            f"El hook es demasiado grande: {tamano_bytes} bytes. "
            f"Máximo permitido: {MAX_HOOK_SIZE} bytes"
        )

    # 6. Validar que el directorio de hooks existe
    hooks_dir = repo_path / ".git" / "hooks"
    if not hooks_dir.is_dir():
        raise ValueError("Directorio de hooks no encontrado")

    # 7. Determinar extensión según plataforma
    extension = obtener_extension_hook()
    hook_path = hooks_dir / f"{hook_name}{extension}"

    # 8. Verificar que el hook no exista
    if hook_path.exists():
        raise FileExistsError(f"El hook {hook_name} ya existe")

    # 9. Validar path del hook (prevención de path traversal)
    validar_path_hook(repo_path, hook_path)

    # 10. Escribir el hook
    hook_path.write_text(contenido, encoding="utf-8")

    # 11. Aplicar permisos de ejecución en Linux/macOS
    if platform.system() != "Windows":
        hook_path.chmod(0o755)
