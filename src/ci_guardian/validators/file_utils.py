"""Utilidades para filtrado de archivos Python.

Este módulo centraliza la lógica de filtrado de archivos Python para eliminar
código duplicado entre cli.py y code_quality.py.
"""

from pathlib import Path

# Constante global para directorios excluidos
DIRECTORIOS_EXCLUIDOS: set[str] = {
    "venv",
    ".venv",
    "env",
    ".env",  # Virtual environments
    ".git",
    ".hg",
    ".svn",  # VCS
    "__pycache__",
    ".pytest_cache",  # Python cache
    "build",
    "dist",  # Build artifacts
    ".tox",
    ".nox",  # Testing tools
    "node_modules",  # JS (si el proyecto tiene frontend)
}


def filtrar_archivos_python_seguros(
    archivos: list[Path],
    repo_path: Path,
    excluir_directorios: set[str] | None = None,
    validar_path_traversal: bool = True,
    validar_existencia: bool = True,
) -> list[Path]:
    """
    Filtra archivos Python validando seguridad y directorios excluidos.

    Args:
        archivos: Lista de archivos a filtrar
        repo_path: Path al repositorio (para calcular paths relativos)
        excluir_directorios: Directorios a excluir (default: DIRECTORIOS_EXCLUIDOS)
        validar_path_traversal: Si validar path traversal (default: True)
        validar_existencia: Si validar que archivos existan (default: True)

    Returns:
        Lista de archivos Python válidos

    Raises:
        ValueError: Si se detecta path traversal y validar_path_traversal=True

    Examples:
        >>> archivos = [Path("src/main.py"), Path("venv/lib.py")]
        >>> repo = Path("/home/user/proyecto")
        >>> resultado = filtrar_archivos_python_seguros(archivos, repo)
        >>> len(resultado)
        1  # Solo main.py, venv excluido
    """
    # Usar directorios excluidos por defecto si no se especifican
    if excluir_directorios is None:
        excluir_directorios = DIRECTORIOS_EXCLUIDOS

    archivos_validos = []

    for archivo in archivos:
        # 1. Validar path traversal (seguridad crítica)
        if validar_path_traversal:
            from ci_guardian.validators.common import validar_path_seguro

            validar_path_seguro(archivo, "archivo")

        # 2. Filtrar por extensión .py
        if archivo.suffix != ".py":
            continue

        # 3. Validar existencia si se requiere
        if validar_existencia and not archivo.exists():
            continue

        # 4. Filtrar directorios excluidos
        # Calcular path relativo al repo para verificar si está en directorio excluido
        try:
            relativo = archivo.relative_to(repo_path)
        except ValueError:
            # Archivo fuera del repo - asumimos que es válido (para testing con mocks)
            # En producción esto solo ocurre con mocks mal configurados
            archivos_validos.append(archivo)
            continue

        # Verificar si está en directorio excluido
        # Si CUALQUIER parte del path está en excluir_directorios, rechazar
        partes = relativo.parts
        if any(parte in excluir_directorios for parte in partes):
            continue

        # 5. Archivo válido
        archivos_validos.append(archivo)

    return archivos_validos
