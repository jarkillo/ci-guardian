"""
Instalador de Git hooks para CI Guardian.

Este módulo proporciona funcionalidad para instalar, validar y gestionar
hooks de Git de forma segura y multiplataforma.
"""

from __future__ import annotations

import platform
from pathlib import Path

# Whitelist de hooks permitidos
HOOKS_PERMITIDOS: set[str] = {"pre-commit", "pre-push", "post-commit", "pre-rebase"}


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
    4. Valida que el directorio .git/hooks/ existe
    5. Verifica que el hook no exista previamente
    6. Escribe el hook con la extensión correcta según el SO
    7. En Linux/macOS, aplica permisos de ejecución (755)

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
    # 1. Validar repositorio Git
    if not es_repositorio_git(repo_path):
        raise ValueError(f"El directorio {repo_path} no es un repositorio Git válido")

    # 2. Validar nombre del hook (whitelist)
    validar_nombre_hook(hook_name)

    # 3. Validar contenido no vacío
    if not contenido or contenido.strip() == "":
        raise ValueError("El contenido del hook no puede estar vacío")

    # 4. Validar que el directorio de hooks existe
    hooks_dir = repo_path / ".git" / "hooks"
    if not hooks_dir.is_dir():
        raise ValueError("Directorio de hooks no encontrado")

    # 5. Determinar extensión según plataforma
    extension = obtener_extension_hook()
    hook_path = hooks_dir / f"{hook_name}{extension}"

    # 6. Verificar que el hook no exista
    if hook_path.exists():
        raise FileExistsError(f"El hook {hook_name} ya existe")

    # 7. Validar path del hook (prevención de path traversal)
    validar_path_hook(repo_path, hook_path)

    # 8. Escribir el hook
    hook_path.write_text(contenido, encoding="utf-8")

    # 9. Aplicar permisos de ejecución en Linux/macOS
    if platform.system() != "Windows":
        hook_path.chmod(0o755)
