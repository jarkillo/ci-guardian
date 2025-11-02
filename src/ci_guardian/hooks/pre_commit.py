"""
Pre-commit hook de CI Guardian.

Este hook se ejecuta antes de cada commit y realiza las siguientes validaciones:
1. Obtiene archivos Python en stage (git diff --cached)
2. Ejecuta Ruff (linter)
3. Ejecuta Black (formatter)
4. Ejecuta Bandit (security scanner)
5. Si todas las validaciones pasan, genera token anti --no-verify

Si alguna validación falla, el commit se rechaza (exit 1).
El token generado será consumido por post-commit para detectar bypass con --no-verify.
"""

import subprocess
import sys
from pathlib import Path

from ci_guardian.validators.code_quality import ejecutar_black, ejecutar_ruff
from ci_guardian.validators.no_verify_blocker import generar_token_seguro, guardar_token
from ci_guardian.validators.security import ejecutar_bandit


def obtener_archivos_python_staged(repo_path: Path) -> list[Path]:
    """
    Obtiene la lista de archivos Python en el staging area.

    Usa 'git diff --cached --name-only --diff-filter=ACM' para obtener solo
    archivos añadidos, modificados o copiados que están staged.

    Args:
        repo_path: Path al repositorio Git

    Returns:
        Lista de Path a archivos Python staged
    """
    try:
        resultado = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
            shell=False,
        )

        if resultado.returncode != 0:
            print(
                f"⚠️  Advertencia: No se pudo obtener archivos staged: {resultado.stderr}",
                file=sys.stderr,
            )
            return []

        # Filtrar solo archivos .py
        archivos_staged = []
        for linea in resultado.stdout.strip().split("\n"):
            if not linea:
                continue

            archivo_path = repo_path / linea
            if archivo_path.suffix == ".py" and archivo_path.exists():
                archivos_staged.append(archivo_path)

        return archivos_staged

    except subprocess.TimeoutExpired:
        print("⚠️  Advertencia: Timeout al obtener archivos staged", file=sys.stderr)
        return []
    except FileNotFoundError:
        print("❌ Error: Git no está instalado", file=sys.stderr)
        sys.exit(1)


def main() -> int:
    """
    Ejecuta validaciones pre-commit.

    Flujo:
    1. Obtener archivos Python en stage
    2. Ejecutar Ruff
    3. Ejecutar Black
    4. Ejecutar Bandit
    5. Si todas pasan → generar token
    6. Si alguna falla → exit 1 (rechazar commit)

    Returns:
        0 si todas las validaciones pasan, 1 si alguna falla
    """
    try:
        repo_path = Path.cwd()

        print("🔍 CI Guardian pre-commit hook ejecutándose...")
        print("")

        # 1. Obtener archivos Python en stage
        archivos_staged = obtener_archivos_python_staged(repo_path)

        if not archivos_staged:
            print("ℹ️  No hay archivos Python en stage, omitiendo validaciones")
            # Aún así generar token (commit sin Python es válido)
            token = generar_token_seguro()
            guardar_token(repo_path, token)
            print("✅ Pre-commit validations passed")
            return 0

        print(f"📝 Validando {len(archivos_staged)} archivo(s) Python...")
        print("")

        # 2. Ejecutar Ruff
        print("1️⃣  Ejecutando Ruff (linter)...")
        ruff_ok, ruff_msg = ejecutar_ruff(archivos_staged, fix=False)

        if not ruff_ok:
            print(f"❌ Ruff falló: {ruff_msg}", file=sys.stderr)
            print("", file=sys.stderr)
            print("💡 Tip: Ejecuta 'ruff check --fix .' para auto-corregir", file=sys.stderr)
            return 1

        print(f"   ✅ {ruff_msg}")
        print("")

        # 3. Ejecutar Black
        print("2️⃣  Ejecutando Black (formatter)...")
        black_ok, black_msg = ejecutar_black(archivos_staged, check=True)

        if not black_ok:
            print(f"❌ Black falló: {black_msg}", file=sys.stderr)
            print("", file=sys.stderr)
            print("💡 Tip: Ejecuta 'black .' para formatear automáticamente", file=sys.stderr)
            return 1

        print(f"   ✅ {black_msg}")
        print("")

        # 4. Ejecutar Bandit (solo si hay archivos Python)
        print("3️⃣  Ejecutando Bandit (security scanner)...")
        bandit_ok, bandit_results = ejecutar_bandit(repo_path, formato="json")

        if not bandit_ok:
            # Verificar si el error es por Bandit no instalado
            if "error" in bandit_results and "no está instalado" in bandit_results["error"]:
                print("   ⚠️  Bandit no instalado, omitiendo auditoría de seguridad")
            else:
                # Vulnerabilidades HIGH encontradas
                metrics = bandit_results.get("metrics", {}).get("_totals", {})
                high_count = metrics.get("HIGH", 0)

                print(f"❌ Bandit detectó {high_count} vulnerabilidad(es) HIGH", file=sys.stderr)
                print("", file=sys.stderr)

                # Mostrar detalles de vulnerabilidades
                results = bandit_results.get("results", [])
                for issue in results[:5]:  # Limitar a 5 para no saturar output
                    if issue.get("issue_severity") == "HIGH":
                        filename = issue.get("filename", "unknown")
                        line_number = issue.get("line_number", 0)
                        issue_text = issue.get("issue_text", "No description")
                        print(f"   📍 {filename}:{line_number}", file=sys.stderr)
                        print(f"      {issue_text}", file=sys.stderr)

                print("", file=sys.stderr)
                print(
                    "💡 Tip: Revisa y corrige las vulnerabilidades antes de commitear",
                    file=sys.stderr,
                )
                return 1

        print("   ✅ Sin vulnerabilidades HIGH detectadas")
        print("")

        # 5. SOLO si todas las validaciones pasaron, generar token
        # IMPORTANTE: El token se genera AL FINAL para prevenir tokens huérfanos
        # (si el commit se aborta después, el token no queda en disco)
        token = generar_token_seguro()
        guardar_token(repo_path, token)

        print("✅ Todas las validaciones pasaron exitosamente")
        print("🎉 Commit permitido")
        return 0

    except ValueError as e:
        print(f"❌ Error de validación: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Error inesperado en pre-commit: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
