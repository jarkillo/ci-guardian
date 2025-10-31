"""
Gestor de entornos virtuales de Python (LIB-2).

Este módulo proporciona funcionalidad para detectar, validar y crear
entornos virtuales de Python en diferentes plataformas (Linux/Windows/macOS).

NOTA: Este es un stub inicial para la FASE RED de TDD.
Las funciones están definidas pero NO implementadas - solo levantan NotImplementedError.
"""

from pathlib import Path


def detectar_venv(ruta_proyecto: Path) -> Path | None:
    """
    Detecta si existe un entorno virtual en el proyecto.

    Busca en orden de prioridad: venv/, .venv/, env/, .env/, ENV/

    Args:
        ruta_proyecto: Path al directorio del proyecto

    Returns:
        Path al directorio del venv si existe, None en caso contrario
    """
    raise NotImplementedError("detectar_venv() no implementado (FASE RED)")


def validar_venv(ruta_venv: Path) -> bool:
    """
    Valida que el venv es funcional.

    Verifica estructura correcta, ejecutable Python, y permisos.

    Args:
        ruta_venv: Path al directorio del venv

    Returns:
        True si es válido, False si está corrupto o no es un venv
    """
    raise NotImplementedError("validar_venv() no implementado (FASE RED)")


def crear_venv(ruta_proyecto: Path, nombre_venv: str = "venv") -> Path:
    """
    Crea un nuevo entorno virtual.

    Args:
        ruta_proyecto: Path al directorio del proyecto
        nombre_venv: Nombre del directorio del venv (por defecto "venv")

    Returns:
        Path al venv creado

    Raises:
        RuntimeError: Si la creación falla o el venv no es válido
        ValueError: Si nombre_venv contiene caracteres peligrosos
    """
    raise NotImplementedError("crear_venv() no implementado (FASE RED)")


def obtener_python_ejecutable(ruta_venv: Path) -> Path:
    """
    Retorna el path al ejecutable Python del venv.

    Args:
        ruta_venv: Path al directorio del venv

    Returns:
        Path al ejecutable Python (bin/python en Linux/macOS, Scripts/python.exe en Windows)

    Raises:
        FileNotFoundError: Si el ejecutable no existe
    """
    raise NotImplementedError("obtener_python_ejecutable() no implementado (FASE RED)")


def esta_en_venv() -> bool:
    """
    Detecta si el script actual se está ejecutando dentro de un venv.

    Verifica sys.prefix != sys.base_prefix y variable VIRTUAL_ENV.

    Returns:
        True si está en venv, False en caso contrario
    """
    raise NotImplementedError("esta_en_venv() no implementado (FASE RED)")
