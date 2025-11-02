"""
Validador de autoría de commits.

Este módulo previene que Claude Code se añada como co-autor en los commits.
"""

import re
from pathlib import Path

# Regex para detectar "Co-Authored-By: Claude" (case-insensitive)
# Debe estar al inicio de línea (^), seguido de "claude" con espacio, < o fin de línea
# Usamos \s* para espacios/tabs antes y después
CLAUDE_COAUTHOR_PATTERN = re.compile(
    r"^\s*co-authored-by:\s*claude(\s|<|$)", re.IGNORECASE | re.MULTILINE
)


def contiene_coauthor_claude(mensaje: str) -> bool:
    """
    Verifica si el mensaje contiene Co-Authored-By: Claude.

    Detecta:
    - Co-Authored-By: Claude <noreply@anthropic.com>
    - Co-Authored-By: Claude <claude@anthropic.com>
    - Co-authored-by: claude (case-insensitive)
    - Variaciones de email @anthropic.com
    - Solo al INICIO de línea (no en medio)
    - Con espacios/tabs extra

    NO detecta:
    - Claude mencionado en el cuerpo (no como co-author)
    - Nombres similares (Claudette, Claudia)
    - URLs con claude.ai

    Args:
        mensaje: Mensaje de commit completo

    Returns:
        True si contiene Co-Authored-By: Claude
    """
    return bool(CLAUDE_COAUTHOR_PATTERN.search(mensaje))


def leer_mensaje_commit(mensaje_path: Path) -> str:
    """
    Lee el mensaje de commit desde archivo.

    Debe:
    - Leer archivo con encoding UTF-8
    - Ignorar líneas que empiezan con # (comentarios de git)
    - Preservar líneas vacías
    - Manejar ñ, emojis, acentos

    Args:
        mensaje_path: Ruta al archivo COMMIT_EDITMSG

    Returns:
        Mensaje de commit sin comentarios

    Raises:
        FileNotFoundError: Si el archivo no existe
    """
    if not mensaje_path.exists():
        raise FileNotFoundError(f"Archivo de commit no encontrado: {mensaje_path}")

    with open(mensaje_path, encoding="utf-8") as f:
        lines = f.readlines()

    # Filtrar comentarios de git (líneas que empiezan con #)
    non_comment_lines = [line for line in lines if not line.strip().startswith("#")]

    return "".join(non_comment_lines)


def validar_autoria_commit(mensaje_path: Path) -> tuple[bool, str]:
    """
    Valida que el commit no tenga a Claude como co-autor.

    Args:
        mensaje_path: Ruta al archivo COMMIT_EDITMSG

    Returns:
        (True, "") si es válido
        (False, mensaje_error) si inválido
    """
    try:
        mensaje = leer_mensaje_commit(mensaje_path)
    except FileNotFoundError as e:
        return False, str(e)

    if contiene_coauthor_claude(mensaje):
        mensaje_error = (
            "Commit rechazado: Co-Authored-By: Claude detectado.\n"
            "CI Guardian no permite que Claude se añada como co-autor.\n"
            "Por favor, elimina la línea Co-Authored-By: Claude del mensaje de commit."
        )
        return False, mensaje_error

    return True, ""
