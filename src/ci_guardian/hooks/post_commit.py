"""
Post-commit hook de CI Guardian.

Este hook se ejecuta DESPUÉS de cada commit y valida que el commit
haya pasado por el pre-commit hook (sistema de tokens anti --no-verify).

Flujo:
1. Intentar consumir token de .git/CI_GUARDIAN_TOKEN
2. Si el token existe → commit válido (pasó por pre-commit) → exit 0
3. Si NO existe token → commit usó --no-verify → revertir commit → exit 1

El sistema de tokens previene que los usuarios bypasseen las validaciones
usando 'git commit --no-verify'.
"""

import sys
from pathlib import Path

from ci_guardian.validators.no_verify_blocker import (
    revertir_ultimo_commit,
    validar_y_consumir_token,
)


def main() -> int:
    """
    Ejecuta validación post-commit.

    Verifica que el commit haya pasado por pre-commit usando el sistema de tokens.
    Si no hay token (commit con --no-verify), revierte el commit.

    Returns:
        0 si token válido (commit normal), 1 si commit revertido (bypass detectado)
    """
    try:
        repo_path = Path.cwd()

        # Intentar validar y consumir token
        token_valido = validar_y_consumir_token(repo_path)

        if token_valido:
            # Token existe y fue consumido → commit válido
            # Este es el flujo normal (commit pasó por pre-commit)
            return 0

        # Token NO existe → commit usó --no-verify
        print("", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        print("🚨 COMMIT RECHAZADO: Bypass detectado", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        print("", file=sys.stderr)
        print("❌ Este commit fue realizado con el flag --no-verify", file=sys.stderr)
        print("", file=sys.stderr)
        print(
            "El flag --no-verify bypasea las validaciones de calidad y seguridad,", file=sys.stderr
        )
        print("lo cual va en contra de las políticas de desarrollo del proyecto.", file=sys.stderr)
        print("", file=sys.stderr)
        print("🔄 Revirtiendo commit automáticamente...", file=sys.stderr)

        # Revertir commit
        exito, mensaje = revertir_ultimo_commit(repo_path)

        if not exito and "No hay commits para revertir" in mensaje:
            # Caso especial: root commit (primer commit del repo)
            # En este caso, eliminar el branch actual y recrearlo
            import subprocess

            resultado_branch = subprocess.run(
                ["git", "symbolic-ref", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                shell=False,
            )

            if resultado_branch.returncode == 0:
                branch_ref = resultado_branch.stdout.strip()
                # Eliminar el branch actual (ej: refs/heads/master)
                subprocess.run(
                    ["git", "update-ref", "-d", branch_ref],
                    cwd=repo_path,
                    capture_output=True,
                    shell=False,
                )
                print("   ✅ Root commit revertido exitosamente", file=sys.stderr)
                print("", file=sys.stderr)
                print("💡 Tus cambios se mantienen en el staging area.", file=sys.stderr)
                print("   Vuelve a hacer commit SIN el flag --no-verify:", file=sys.stderr)
                print("   $ git commit -m 'tu mensaje'", file=sys.stderr)
                print("", file=sys.stderr)
                print("=" * 70, file=sys.stderr)
            else:
                print("   ❌ Error al revertir root commit", file=sys.stderr)
                print("", file=sys.stderr)
                print("⚠️  Por favor, elimina el branch manualmente:", file=sys.stderr)
                print("   $ git update-ref -d HEAD", file=sys.stderr)
                print("", file=sys.stderr)
                print("=" * 70, file=sys.stderr)
        elif exito:
            print(f"   ✅ {mensaje}", file=sys.stderr)
            print("", file=sys.stderr)
            print("💡 Tus cambios se mantienen en el staging area.", file=sys.stderr)
            print("   Vuelve a hacer commit SIN el flag --no-verify:", file=sys.stderr)
            print("   $ git commit -m 'tu mensaje'", file=sys.stderr)
            print("", file=sys.stderr)
            print("=" * 70, file=sys.stderr)
        else:
            print(f"   ❌ Error al revertir: {mensaje}", file=sys.stderr)
            print("", file=sys.stderr)
            print("⚠️  Por favor, revierte el commit manualmente:", file=sys.stderr)
            print("   $ git reset --soft HEAD~1", file=sys.stderr)
            print("", file=sys.stderr)
            print("=" * 70, file=sys.stderr)

        # Retornar 1 para indicar que el commit fue rechazado
        return 1

    except ValueError as e:
        print(f"❌ Error de validación: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Error inesperado en post-commit: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
