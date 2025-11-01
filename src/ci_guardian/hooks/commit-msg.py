#!/usr/bin/env python3
"""
Hook commit-msg de CI Guardian.

Este hook valida el mensaje de commit antes de que se complete el commit.
Previene que Claude Code se añada como co-autor.
"""

import sys
from pathlib import Path

# Añadir src/ al path para poder importar ci_guardian
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from ci_guardian.validators.authorship import validar_autoria_commit  # noqa: E402


def main() -> int:
    """
    Punto de entrada del hook commit-msg.

    Args (desde git):
        sys.argv[1]: Ruta al archivo COMMIT_EDITMSG

    Returns:
        0 si el commit es válido
        1 si el commit debe ser rechazado
    """
    if len(sys.argv) < 2:
        print("Error: El hook commit-msg requiere la ruta al mensaje de commit")
        return 1

    mensaje_path = Path(sys.argv[1])

    valido, mensaje_error = validar_autoria_commit(mensaje_path)

    if not valido:
        print(f"\n❌ {mensaje_error}\n", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
