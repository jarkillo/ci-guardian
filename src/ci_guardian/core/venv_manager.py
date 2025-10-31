"""
Gestor de entornos virtuales de Python (LIB-2).

Este módulo proporciona funcionalidad para detectar, validar y crear
entornos virtuales de Python en diferentes plataformas (Linux/Windows/macOS).
"""

import logging
import os
import platform
import subprocess  # nosec B404 - subprocess is needed for venv creation with shell=False
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Nombres de venv a buscar, en orden de prioridad
VENV_NAMES = ["venv", ".venv", "env", ".env", "ENV"]

# Caracteres peligrosos para nombres de venv
CARACTERES_PELIGROSOS = {";", "&", "|", "$", "`", "\n", "\r"}


def obtener_python_ejecutable(ruta_venv: Path) -> Path:
    """
    Retorna el path al ejecutable Python del venv.

    Args:
        ruta_venv: Path al directorio del venv

    Returns:
        Path al ejecutable Python (bin/python en Linux/macOS, Scripts/python.exe en Windows)

    Raises:
        FileNotFoundError: Si el ejecutable no existe

    Example:
        >>> venv = Path("/home/user/proyecto/venv")
        >>> python_exe = obtener_python_ejecutable(venv)
        >>> print(python_exe)
        /home/user/proyecto/venv/bin/python
    """
    sistema = platform.system()

    if sistema == "Windows":
        python_path = ruta_venv / "Scripts" / "python.exe"
    else:
        # Linux, Darwin (macOS), y otros Unix-like
        python_path = ruta_venv / "bin" / "python"
        # Si no existe python, intentar python3
        if not python_path.exists():
            python_path = ruta_venv / "bin" / "python3"

    # Resolver el path
    python_path = python_path.resolve()

    # Verificar que existe
    if not python_path.exists():
        raise FileNotFoundError(f"Ejecutable Python no encontrado en {ruta_venv}")

    return python_path


def esta_en_venv() -> bool:
    """
    Detecta si el script actual se está ejecutando dentro de un venv.

    Verifica sys.prefix != sys.base_prefix y variable VIRTUAL_ENV.

    Returns:
        True si está en venv, False en caso contrario

    Example:
        >>> if esta_en_venv():
        ...     print("Ejecutando dentro de un venv")
    """
    # Check 1: sys.prefix != sys.base_prefix
    if sys.prefix != sys.base_prefix:
        return True

    # Check 2: Variable de entorno VIRTUAL_ENV
    return bool(os.environ.get("VIRTUAL_ENV"))


def validar_venv(ruta_venv: Path) -> bool:
    """
    Valida que el venv es funcional.

    Verifica estructura correcta, ejecutable Python, y permisos.

    Args:
        ruta_venv: Path al directorio del venv

    Returns:
        True si es válido, False si está corrupto o no es un venv

    Example:
        >>> venv = Path("/home/user/proyecto/venv")
        >>> if validar_venv(venv):
        ...     print("Venv válido")
    """
    try:
        # Verificar que la ruta existe y es un directorio
        if not ruta_venv.exists() or not ruta_venv.is_dir():
            return False

        # Obtener el ejecutable Python
        python_exe = obtener_python_ejecutable(ruta_venv)

        # Verificar que el ejecutable existe
        if not python_exe.exists():
            return False

        # En Linux/macOS, verificar permisos de ejecución
        # En Windows, siempre retorna True si el ejecutable existe
        return platform.system() == "Windows" or bool(python_exe.stat().st_mode & 0o111)

    except (FileNotFoundError, PermissionError, OSError):
        # Cualquier error indica que el venv no es válido
        return False


def detectar_venv(ruta_proyecto: Path) -> Path | None:
    """
    Detecta si existe un entorno virtual en el proyecto.

    Busca en orden de prioridad: venv/, .venv/, env/, .env/, ENV/

    Args:
        ruta_proyecto: Path al directorio del proyecto

    Returns:
        Path al directorio del venv si existe, None en caso contrario

    Example:
        >>> proyecto = Path("/home/user/mi_proyecto")
        >>> venv = detectar_venv(proyecto)
        >>> if venv:
        ...     print(f"Venv encontrado: {venv}")
    """
    try:
        # Buscar cada nombre de venv en orden de prioridad
        for nombre_venv in VENV_NAMES:
            ruta_venv = ruta_proyecto / nombre_venv

            # Verificar si el venv existe y es válido
            if validar_venv(ruta_venv):
                # Resolver symlinks y retornar path absoluto
                return ruta_venv.resolve()

        # No se encontró ningún venv válido
        return None

    except (PermissionError, OSError):
        # Si no tenemos permisos de lectura o hay otro error, retornar None
        return None


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

    Example:
        >>> proyecto = Path("/home/user/mi_proyecto")
        >>> venv = crear_venv(proyecto)
        >>> print(f"Venv creado: {venv}")
    """
    # Validar nombre_venv (seguridad)
    if ".." in nombre_venv:
        raise ValueError(f"Nombre de venv no válido: {nombre_venv}")

    if nombre_venv.startswith("/") or nombre_venv.startswith("\\"):
        raise ValueError(f"Nombre de venv no válido: {nombre_venv}")

    if any(c in nombre_venv for c in CARACTERES_PELIGROSOS):
        raise ValueError(f"Nombre de venv no válido: {nombre_venv}")

    # Path al venv a crear
    ruta_venv = ruta_proyecto / nombre_venv

    # Comando para crear venv
    comando = [sys.executable, "-m", "venv", str(ruta_venv)]

    try:
        # Ejecutar comando
        resultado = subprocess.run(  # nosec B603  # noqa: S603 - validated command, shell=False
            comando,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutos máximo
            shell=False,  # CRÍTICO para seguridad
            check=False,  # We check returncode manually
        )

        # Verificar código de salida
        if resultado.returncode != 0:
            raise RuntimeError(f"Error al crear el entorno virtual: {resultado.stderr}")

    except subprocess.TimeoutExpired as err:
        raise RuntimeError("Timeout al crear el entorno virtual (más de 5 minutos)") from err

    # Validar que el venv creado es funcional
    if not validar_venv(ruta_venv):
        raise RuntimeError("El entorno virtual creado no es válido")

    return ruta_venv
