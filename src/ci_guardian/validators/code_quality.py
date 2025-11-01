"""
Validadores de calidad de código (Ruff y Black).

Este módulo proporciona funciones para ejecutar Ruff (linter) y Black (formatter)
sobre archivos Python de forma segura, previniendo vulnerabilidades de command injection
y path traversal.
"""

import subprocess
from pathlib import Path


def _filtrar_archivos_python(archivos: list[Path]) -> list[Path]:
    """
    Filtra solo archivos .py que existan y no tengan path traversal.

    Args:
        archivos: Lista de archivos a filtrar

    Returns:
        Lista de archivos Python válidos

    Raises:
        ValueError: Si se detecta path traversal (..)
    """
    archivos_validos = []
    for archivo in archivos:
        # Rechazar path traversal (seguridad crítica)
        if ".." in str(archivo):
            raise ValueError(
                f"path traversal detectado en '{archivo}': ruta inválida fuera del proyecto"
            )

        # Solo archivos .py
        if archivo.suffix != ".py":
            continue

        # Solo si existe
        if not archivo.exists():
            continue

        archivos_validos.append(archivo)

    return archivos_validos


def ejecutar_ruff(archivos: list[Path], fix: bool = False) -> tuple[bool, str]:
    """
    Ejecuta Ruff sobre archivos Python.

    Filtra archivos válidos, ejecuta Ruff con subprocess.run (sin shell=True),
    y retorna el resultado del análisis.

    Args:
        archivos: Lista de archivos Python a analizar
        fix: Si True, auto-corrige los errores con --fix

    Returns:
        Tupla (éxito, mensaje):
        - (True, mensaje) si no hay errores de linting
        - (False, mensaje_error) si hay errores

    Examples:
        >>> exitoso, msg = ejecutar_ruff([Path("main.py")])
        >>> if not exitoso:
        ...     print(f"Errores: {msg}")
    """
    # Manejar lista vacía
    if not archivos:
        return True, "Sin archivos para validar"

    # Filtrar archivos válidos
    try:
        archivos_validos = _filtrar_archivos_python(archivos)
    except ValueError as e:
        # Path traversal detectado
        raise ValueError(f"Error de validación: {e}") from e

    # Si después del filtrado no hay archivos válidos
    if not archivos_validos:
        return True, "Sin archivos Python válidos para validar"

    # Construir comando Ruff
    comando = ["ruff", "check", "--output-format=json"]

    if fix:
        comando.append("--fix")

    # Añadir archivos como strings
    comando.extend([str(archivo) for archivo in archivos_validos])

    try:
        # Ejecutar Ruff de forma segura (sin shell=True)
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            timeout=60,
            shell=False,  # CRÍTICO: prevenir command injection
        )

        # returncode == 0 significa sin errores
        if resultado.returncode == 0:
            return True, "Código sin errores de linting (OK)"

        # returncode != 0 significa errores detectados
        mensaje_error = resultado.stderr if resultado.stderr else "Errores de linting detectados"
        return False, mensaje_error

    except subprocess.TimeoutExpired:
        return False, "Timeout: Ruff tardó más de 60 segundos"
    except FileNotFoundError:
        return False, "Ruff no encontrado. Instálalo con: pip install ruff"


def ejecutar_black(archivos: list[Path], check: bool = True) -> tuple[bool, str]:
    """
    Ejecuta Black sobre archivos Python.

    Filtra archivos válidos y ejecuta Black en modo check (validación) o formateo.

    Args:
        archivos: Lista de archivos Python a formatear
        check: Si True, solo valida (--check), si False formatea los archivos

    Returns:
        Tupla (éxito, mensaje):
        - (True, mensaje) si archivos están formateados correctamente
        - (False, mensaje) si necesitan formateo o hay errores

    Examples:
        >>> exitoso, msg = ejecutar_black([Path("main.py")], check=True)
        >>> if not exitoso:
        ...     print("Archivos necesitan formateo")
    """
    # Manejar lista vacía
    if not archivos:
        return True, "Sin archivos para validar"

    # Filtrar archivos válidos
    try:
        archivos_validos = _filtrar_archivos_python(archivos)
    except ValueError as e:
        # Path traversal detectado
        raise ValueError(f"Error de validación: {e}") from e

    # Si no hay archivos válidos después del filtrado
    if not archivos_validos:
        return True, "Sin archivos Python válidos para validar"

    # Construir comando Black
    comando = ["black"]

    if check:
        comando.append("--check")

    # Añadir archivos
    comando.extend([str(archivo) for archivo in archivos_validos])

    try:
        # Ejecutar Black de forma segura
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            timeout=60,
            shell=False,  # CRÍTICO: prevenir command injection
        )

        # returncode == 0: archivos formateados correctamente
        if resultado.returncode == 0:
            return True, "Archivos formateados correctamente"

        # returncode == 1: archivos necesitan formateo
        if resultado.returncode == 1:
            mensaje = resultado.stdout if resultado.stdout else "Archivos necesitan formateo"
            return False, mensaje

        # returncode > 1: error en Black
        return False, f"Error en Black: {resultado.stderr or 'Error desconocido'}"

    except subprocess.TimeoutExpired:
        return False, "Timeout: Black tardó más de 60 segundos"
    except FileNotFoundError:
        return False, "Black no encontrado. Instálalo con: pip install black"


def validar_calidad_codigo(archivos: list[Path], fix: bool = False) -> bool:
    """
    Ejecuta Ruff y Black en secuencia para validar calidad de código.

    Ejecuta primero Ruff (linting), luego Black (formatting).
    Retorna True solo si ambos pasan.

    Args:
        archivos: Lista de archivos Python a validar
        fix: Si True, auto-corrige errores en Ruff

    Returns:
        True si ambos (Ruff y Black) pasan, False en caso contrario

    Examples:
        >>> if validar_calidad_codigo([Path("main.py")]):
        ...     print("Calidad de código OK")
        ... else:
        ...     print("Se detectaron problemas")
    """
    # Manejar lista vacía
    if not archivos:
        return True

    # Ejecutar Ruff primero
    ruff_exitoso, ruff_mensaje = ejecutar_ruff(archivos, fix=fix)

    # Ejecutar Black después
    black_exitoso, black_mensaje = ejecutar_black(archivos, check=True)

    # Retornar True solo si ambos pasaron
    return ruff_exitoso and black_exitoso
