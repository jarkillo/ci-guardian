"""
Instalador de Git hooks para CI Guardian.

Este módulo proporciona funcionalidad para instalar, validar y gestionar
hooks de Git de forma segura y multiplataforma.

NOTA: Este archivo contiene STUBS (firmas sin implementación) para la FASE RED del TDD.
"""

from pathlib import Path

# Whitelist de hooks permitidos
HOOKS_PERMITIDOS: set[str] = {"pre-commit", "pre-push", "post-commit", "pre-rebase"}


def es_repositorio_git(repo_path: Path) -> bool:
    """
    Verifica si un directorio es un repositorio Git válido.

    Args:
        repo_path: Ruta al directorio a verificar

    Returns:
        True si es un repositorio Git válido, False en caso contrario
    """
    # STUB: No implementado aún
    raise NotImplementedError("Función no implementada (FASE RED del TDD)")


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
    # STUB: No implementado aún
    raise NotImplementedError("Función no implementada (FASE RED del TDD)")


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
    # STUB: No implementado aún
    raise NotImplementedError("Función no implementada (FASE RED del TDD)")


def instalar_hook(repo_path: Path, hook_name: str, contenido: str) -> None:
    """
    Instala un hook de Git en el repositorio.

    Args:
        repo_path: Ruta al repositorio Git
        hook_name: Nombre del hook (pre-commit, pre-push, etc.)
        contenido: Contenido del hook

    Raises:
        ValueError: Si el nombre del hook no está en la whitelist
        ValueError: Si no es un repositorio Git válido
        ValueError: Si el directorio de hooks no existe
        ValueError: Si el contenido está vacío
        FileExistsError: Si el hook ya existe
    """
    # STUB: No implementado aún
    raise NotImplementedError("Función no implementada (FASE RED del TDD)")
