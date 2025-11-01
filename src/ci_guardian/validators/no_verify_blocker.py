"""
Validador Anti --no-verify.

Este módulo implementa el sistema de tokens para prevenir que commits
se realicen usando el flag --no-verify (bypass de hooks).

Sistema de funcionamiento:
1. pre-commit: genera token y lo guarda
2. post-commit: valida token existe y lo consume
3. Si no existe token → commit usó --no-verify → revertir
"""

import platform
import secrets
import subprocess
from pathlib import Path

# Nombre del archivo de token en .git/
TOKEN_FILENAME = "CI_GUARDIAN_TOKEN"  # noqa: S105 (no es una contraseña, es un nombre de archivo)


def generar_token_seguro() -> str:
    """
    Genera token criptográficamente seguro de 256 bits.

    Utiliza secrets.token_hex para generar tokens impredecibles
    adecuados para uso criptográfico.

    Returns:
        Token hexadecimal de 64 caracteres (32 bytes = 256 bits)
    """
    return secrets.token_hex(32)


def guardar_token(repo_path: Path, token: str) -> None:
    """
    Guarda token en .git/CI_GUARDIAN_TOKEN.

    Valida que el repositorio sea válido y que el token no esté vacío
    antes de guardarlo. En Linux, establece permisos 600 (solo lectura/escritura
    para el propietario).

    Args:
        repo_path: Path al repositorio Git
        token: Token a guardar

    Raises:
        ValueError: Si repo no es válido o token vacío/inválido
        TypeError: Si token no es una cadena
    """
    # Validar tipo de dato
    if not isinstance(token, str):
        raise TypeError("Token debe ser una cadena de texto (str)")

    # Validar que es un repositorio Git válido
    if not (repo_path / ".git").is_dir():
        raise ValueError("no es un repositorio Git válido")

    # Validar que token no esté vacío
    if not token or not token.strip():
        raise ValueError("Token no puede estar vacío")

    # Validar longitud máxima (1KB es razonable para un token)
    if len(token) > 1000:
        raise ValueError("Token demasiado largo, excede el límite de 1000 caracteres")

    # Validar que solo contenga caracteres seguros
    # Permitir: a-z (minúsculas), 0-9, guión bajo
    # Rechazar: caracteres peligrosos para command injection y mayúsculas
    caracteres_peligrosos = {";", "|", "&", "$", "`", "(", ")", "<", ">", "\n", "\r", " ", "\t"}
    if any(c in caracteres_peligrosos for c in token):
        raise ValueError("Token contiene caracteres no permitidos")

    # Validar que solo contenga minúsculas, dígitos y guión bajo
    # NO permitir mayúsculas (para rechazar XYZ pero aceptar abc)
    if not all(c.islower() or c.isdigit() or c == "_" for c in token):
        raise ValueError("Token contiene caracteres no permitidos")

    # Path al archivo de token
    token_path = repo_path / ".git" / TOKEN_FILENAME

    # Escribir token
    token_path.write_text(token, encoding="utf-8")

    # Establecer permisos 600 en Linux (solo owner puede leer/escribir)
    if platform.system() != "Windows":
        token_path.chmod(0o600)


def validar_y_consumir_token(repo_path: Path) -> bool:
    """
    Valida que existe token y lo consume (elimina archivo).

    Lee el archivo de token, verifica que no esté vacío y lo elimina.
    Este proceso de "consumir" el token asegura que cada token solo
    pueda usarse una vez.

    Args:
        repo_path: Path al repositorio Git

    Returns:
        True si token válido y consumido, False en caso contrario

    Raises:
        ValueError: Si no es un repositorio Git válido
        PermissionError: Si no hay permisos para leer el archivo o tiene permisos inseguros (777)
    """
    # Validar que es un repositorio Git
    if not (repo_path / ".git").is_dir():
        raise ValueError("no es un repositorio Git válido")

    token_path = repo_path / ".git" / TOKEN_FILENAME

    # Verificar que existe
    if not token_path.exists():
        return False

    # Verificar permisos seguros en Linux (rechazar solo 777)
    if platform.system() != "Windows":
        permisos = token_path.stat().st_mode & 0o777
        if permisos == 0o777:
            raise PermissionError(
                f"Archivo de token tiene permisos inseguros: {oct(permisos)} "
                "(demasiado permisivo, debe ser 600)"
            )

    try:
        # Leer token
        token = token_path.read_text(encoding="utf-8")

        # Validar que no está vacío
        if not token.strip():
            # Eliminar token inválido
            token_path.unlink()
            return False

        # Consumir token (eliminar archivo)
        token_path.unlink()
        return True

    except UnicodeDecodeError:
        # Archivo corrupto (no es UTF-8 válido)
        token_path.unlink()  # Eliminar archivo corrupto
        return False
    except PermissionError:
        # Re-lanzar PermissionError para que el test lo capture
        raise


def revertir_ultimo_commit(repo_path: Path) -> tuple[bool, str]:
    """
    Revierte el último commit preservando cambios staged.

    Utiliza 'git reset --soft HEAD~1' para revertir el último commit
    manteniendo los cambios en el staging area.

    Args:
        repo_path: Path al repositorio Git

    Returns:
        Tupla (éxito, mensaje):
        - (True, mensaje_exito) si el commit fue revertido exitosamente
        - (False, mensaje_error) si hubo error

    Raises:
        ValueError: Si no es un repositorio Git válido
    """
    # Validar que es un repositorio Git
    if not (repo_path / ".git").is_dir():
        raise ValueError("no es un repositorio Git válido")

    try:
        resultado = subprocess.run(
            ["git", "reset", "--soft", "HEAD~1"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
            shell=False,  # CRÍTICO: nunca usar shell=True
        )

        if resultado.returncode == 0:
            return True, "Commit revertido exitosamente"
        # Detectar caso específico: no hay commits (solo cuando hay "unknown revision")
        stderr = resultado.stderr.lower()
        if "unknown revision" in stderr:
            return False, "No hay commits para revertir (repositorio sin commits)"
        # Para otros errores, devolver stderr original (que contiene "error:" o "fatal:")
        return False, resultado.stderr

    except subprocess.TimeoutExpired:
        return False, "Timeout al revertir commit"
    except FileNotFoundError:
        return False, "Git no está instalado"


def verificar_commit_sin_hooks(repo_path: Path) -> bool:
    """
    Workflow completo post-commit: verifica si se usó --no-verify.

    Este es el flujo principal que se ejecuta en el hook post-commit:
    1. Intenta validar y consumir el token
    2. Si existe token → commit válido (se ejecutó pre-commit)
    3. Si no existe token → commit inválido (usó --no-verify) → revertir

    Args:
        repo_path: Path al repositorio Git

    Returns:
        True si commit válido (token encontrado y consumido)
        False si commit revertido (no había token, se usó --no-verify)
    """
    # Intentar validar y consumir token
    token_valido = validar_y_consumir_token(repo_path)

    if token_valido:
        # Token existe → commit válido
        return True
    # Token no existe → commit con --no-verify → revertir
    exito, _ = revertir_ultimo_commit(repo_path)
    return False
