"""
Validador de entornos virtuales activos.

Este módulo proporciona funciones para detectar si hay un entorno virtual
Python activo en el entorno actual.
"""

import os
import sys


def esta_venv_activo() -> tuple[bool, str]:
    """
    Verifica si hay un entorno virtual activo en el entorno actual.

    Métodos de detección (en orden de prioridad):
    1. Variable de entorno VIRTUAL_ENV (más explícito)
    2. Comparación sys.prefix != sys.base_prefix (Python 3.3+)

    Returns:
        Tupla (activo, mensaje):
        - activo: True si hay venv activo, False en caso contrario
        - mensaje: Descripción del estado o instrucciones para activar venv

    Example:
        >>> activo, msg = esta_venv_activo()
        >>> if not activo:
        ...     print(msg)
        ❌ ERROR: No hay entorno virtual activo
        ...
    """
    # Método 1: Variable de entorno VIRTUAL_ENV (prioridad)
    venv_path = os.getenv("VIRTUAL_ENV")
    if venv_path:  # String no vacío
        return True, f"✅ Venv activo: {venv_path}"

    # Método 2: Comparación sys.prefix != sys.base_prefix
    if sys.prefix != sys.base_prefix:
        return True, f"✅ Venv activo: {sys.prefix}"

    # No hay venv activo: proporcionar instrucciones claras
    mensaje = """❌ ERROR: No hay entorno virtual activo

Debes activar el venv antes de hacer commits:

  Linux/Mac:   source venv/bin/activate
  Windows:     venv\\Scripts\\activate

Alternativamente, usa: ci-guardian commit
"""
    return False, mensaje
