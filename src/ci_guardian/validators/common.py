"""Utilidades comunes para validadores de CI Guardian.

Este módulo proporciona funciones reutilizables para validación de seguridad,
principalmente la validación centralizada de path traversal.
"""

from __future__ import annotations

from pathlib import Path


def validar_path_seguro(path: Path | str, nombre_contexto: str = "path") -> Path:
    """Valida que un path sea seguro y no contenga path traversal.

    Verifica que el path no contenga ".." que podría permitir acceso a
    archivos fuera del directorio del proyecto (path traversal attack).

    Args:
        path: Path a validar (Path o str)
        nombre_contexto: Nombre para mensaje de error (ej: "archivo", "directorio", "repositorio")

    Returns:
        Path validado como objeto Path

    Raises:
        ValueError: Si se detecta path traversal (".." en la ruta)

    Examples:
        >>> validar_path_seguro("src/main.py")
        Path('src/main.py')

        >>> validar_path_seguro("../../etc/passwd")
        Traceback (most recent call last):
            ...
        ValueError: Path traversal detectado en path: ../../etc/passwd

        >>> validar_path_seguro("../malicious", "archivo")
        Traceback (most recent call last):
            ...
        ValueError: Path traversal detectado en archivo: ../malicious

    Security Note:
        Esta función implementa una validación básica pero efectiva contra
        path traversal. Rechaza cualquier path que contenga ".." para prevenir
        acceso a directorios padre, incluso si ".." está en medio de la ruta
        (ej: "foo/../bar").

        Futuras mejoras podrían incluir:
        - Validación de symlinks maliciosos
        - Validación de UNC paths en Windows
        - Resolución de paths y verificación de que estén dentro del repo
    """
    # Convertir a Path si es string
    path_obj = Path(path) if isinstance(path, str) else path

    # Convertir a string para validación
    path_str = str(path_obj)

    # Validar path traversal básico
    # IMPORTANTE: Cualquier ocurrencia de ".." es sospechosa y se rechaza
    # Esto incluye: "../foo", "foo/../bar", "foo/..", etc.
    if ".." in path_str:
        raise ValueError(
            f"Path traversal detectado en {nombre_contexto}: {path_str}. "
            f"ruta inválida fuera del proyecto"
        )

    return path_obj
