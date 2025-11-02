"""
Tests de integración end-to-end para CI Guardian.

Estos tests validan el flujo completo del sistema:
1. Instalación de hooks en repositorios Git reales
2. Ejecución de commits reales con validaciones
3. Flujo CLI completo (install, check, status, uninstall)
4. Integración con code quality, security, y authorship validators

IMPORTANTE: Estos son tests de INTEGRACIÓN, NO usan mocks.
Crean repositorios Git temporales reales y ejecutan comandos reales.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def repo_git_real(tmp_path: Path) -> Path:
    """
    Crea un repositorio Git REAL usando 'git init'.

    Args:
        tmp_path: Directorio temporal proporcionado por pytest

    Returns:
        Path al repositorio Git inicializado
    """
    repo = tmp_path / "test_repo"
    repo.mkdir()

    # Inicializar repositorio Git REAL
    subprocess.run(
        ["git", "init"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )

    # Configurar usuario Git (necesario para commits)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    return repo


@pytest.fixture
def archivo_python_valido(repo_git_real: Path) -> Path:
    """
    Crea un archivo Python válido en el repositorio.

    Args:
        repo_git_real: Repositorio Git real

    Returns:
        Path al archivo Python creado
    """
    archivo = repo_git_real / "test_module.py"
    archivo.write_text(
        '''"""Módulo de prueba."""


def funcion_valida() -> bool:
    """Función de ejemplo."""
    return True
''',
        encoding="utf-8",
    )
    return archivo


@pytest.fixture
def archivo_python_invalido(repo_git_real: Path) -> Path:
    """
    Crea un archivo Python con errores de formato (para Ruff/Black).

    Args:
        repo_git_real: Repositorio Git real

    Returns:
        Path al archivo Python con errores
    """
    archivo = repo_git_real / "test_invalid.py"
    archivo.write_text(
        """def funcion_sin_espacios():return True  # Error de formato
x=1+2+3+4+5  # Sin espacios
""",
        encoding="utf-8",
    )
    return archivo


@pytest.fixture
def archivo_python_con_vulnerabilidad(repo_git_real: Path) -> Path:
    """
    Crea un archivo Python con vulnerabilidad de seguridad.

    Args:
        repo_git_real: Repositorio Git real

    Returns:
        Path al archivo con vulnerabilidad
    """
    archivo = repo_git_real / "vulnerable.py"
    archivo.write_text(
        '''"""Código vulnerable."""

import os


def ejecutar_comando(cmd: str) -> None:
    """Función vulnerable a command injection."""
    os.system(cmd)  # Bandit: B605 HIGH
''',
        encoding="utf-8",
    )
    return archivo


# =============================================================================
# TESTS: Workflow completo de instalación
# =============================================================================


@pytest.mark.integration
def test_debe_instalar_hooks_exitosamente_en_repo_limpio(repo_git_real: Path) -> None:
    """
    Workflow completo: ci-guardian install en repo limpio.

    Verifica:
    - CLI install funciona
    - Los 3 hooks se instalan correctamente
    - Hooks tienen permisos correctos
    - Hooks contienen marca CI-GUARDIAN-HOOK
    """
    # Act: Ejecutar ci-guardian install
    resultado = subprocess.run(
        ["ci-guardian", "install", "--repo", str(repo_git_real)],
        capture_output=True,
        text=True,
    )

    # Assert: Comando exitoso
    assert resultado.returncode == 0, f"Stderr: {resultado.stderr}"
    assert "3 hooks instalados exitosamente" in resultado.stdout

    # Assert: Hooks existen
    hooks_dir = repo_git_real / ".git" / "hooks"
    assert (hooks_dir / "pre-commit").exists(), "Hook pre-commit debe existir"
    assert (hooks_dir / "pre-push").exists(), "Hook pre-push debe existir"
    assert (hooks_dir / "post-commit").exists(), "Hook post-commit debe existir"

    # Assert: Hooks tienen marca CI-GUARDIAN-HOOK
    pre_commit_content = (hooks_dir / "pre-commit").read_text(encoding="utf-8")
    assert "CI-GUARDIAN-HOOK" in pre_commit_content, "Hook debe tener marca CI-GUARDIAN-HOOK"

    # Assert: Permisos correctos en Linux (solo si no es Windows)
    import platform

    if platform.system() != "Windows":
        import stat

        permisos = (hooks_dir / "pre-commit").stat().st_mode
        assert permisos & stat.S_IXUSR, "Hook debe tener permisos de ejecución"


@pytest.mark.integration
def test_debe_rechazar_instalacion_si_hooks_ya_existen(repo_git_real: Path) -> None:
    """
    Workflow: Intentar instalar cuando ya hay hooks instalados.

    Verifica:
    - Primera instalación exitosa
    - Segunda instalación falla sin --force
    - Mensaje de error claro
    """
    # Arrange: Instalar hooks la primera vez
    resultado1 = subprocess.run(
        ["ci-guardian", "install", "--repo", str(repo_git_real)],
        capture_output=True,
        text=True,
    )
    assert resultado1.returncode == 0, "Primera instalación debe ser exitosa"

    # Act: Intentar instalar de nuevo SIN --force
    resultado2 = subprocess.run(
        ["ci-guardian", "install", "--repo", str(repo_git_real)],
        capture_output=True,
        text=True,
    )

    # Assert: Debe fallar
    assert resultado2.returncode != 0, "Segunda instalación debe fallar"
    assert "ya existe" in resultado2.stderr, "Mensaje debe indicar que el hook ya existe"


@pytest.mark.integration
def test_debe_permitir_reinstalacion_con_force(repo_git_real: Path) -> None:
    """
    Workflow: Reinstalar hooks usando --force.

    Verifica:
    - Primera instalación exitosa
    - Segunda instalación con --force exitosa
    - Hooks sobrescritos correctamente
    """
    # Arrange: Instalar hooks la primera vez
    resultado1 = subprocess.run(
        ["ci-guardian", "install", "--repo", str(repo_git_real)],
        capture_output=True,
        text=True,
    )
    assert resultado1.returncode == 0, "Primera instalación debe ser exitosa"

    # Act: Instalar de nuevo CON --force
    resultado2 = subprocess.run(
        ["ci-guardian", "install", "--repo", str(repo_git_real), "--force"],
        capture_output=True,
        text=True,
    )

    # Assert: Debe ser exitosa
    assert resultado2.returncode == 0, f"Stderr: {resultado2.stderr}"
    assert "instalación forzada" in resultado2.stdout
    assert "3 hooks instalados exitosamente" in resultado2.stdout


@pytest.mark.integration
def test_debe_hacer_commit_exitosamente_con_codigo_valido(
    repo_git_real: Path, archivo_python_valido: Path
) -> None:
    """
    Workflow completo: Commit exitoso con código válido.

    Verifica:
    - Instalar hooks
    - Añadir archivo válido al stage
    - Commit se ejecuta exitosamente (hooks pasan)
    """
    # Arrange: Instalar hooks
    subprocess.run(
        ["ci-guardian", "install", "--repo", str(repo_git_real)],
        check=True,
        capture_output=True,
    )

    # Añadir archivo al stage
    subprocess.run(
        ["git", "add", archivo_python_valido.name],
        cwd=repo_git_real,
        check=True,
        capture_output=True,
    )

    # Act: Hacer commit
    resultado = subprocess.run(
        ["git", "commit", "-m", "Test commit con código válido"],
        cwd=repo_git_real,
        capture_output=True,
        text=True,
    )

    # Assert: Commit exitoso
    assert resultado.returncode == 0, f"Stderr: {resultado.stderr}"

    # Verificar que el commit se creó
    log_result = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=repo_git_real,
        capture_output=True,
        text=True,
    )
    assert "Test commit con código válido" in log_result.stdout


# =============================================================================
# TESTS: Workflow de code quality
# =============================================================================


@pytest.mark.integration
@pytest.mark.slow
def test_debe_rechazar_commit_con_errores_de_formato(
    repo_git_real: Path, archivo_python_invalido: Path
) -> None:
    """
    Workflow: Commit rechazado por errores de formato (Ruff/Black).

    Verifica:
    - Instalar hooks
    - Añadir archivo con errores de formato
    - Commit rechazado por pre-commit hook
    - Mensaje de error indica problema de formato
    """
    # Arrange: Instalar hooks
    subprocess.run(
        ["ci-guardian", "install", "--repo", str(repo_git_real)],
        check=True,
        capture_output=True,
    )

    # Añadir archivo inválido al stage
    subprocess.run(
        ["git", "add", archivo_python_invalido.name],
        cwd=repo_git_real,
        check=True,
        capture_output=True,
    )

    # Act: Intentar hacer commit
    resultado = subprocess.run(
        ["git", "commit", "-m", "Test commit con errores de formato"],
        cwd=repo_git_real,
        capture_output=True,
        text=True,
    )

    # Assert: Commit rechazado
    assert resultado.returncode != 0, "Commit debe ser rechazado por errores de formato"

    # Assert: Mensaje de error indica validación de calidad
    output_completo = resultado.stdout + resultado.stderr
    assert (
        "CI Guardian" in output_completo or "ruff" in output_completo.lower()
    ), "Debe indicar error de validación"


@pytest.mark.integration
def test_debe_ejecutar_check_exitosamente_con_codigo_valido(
    repo_git_real: Path, archivo_python_valido: Path
) -> None:
    """
    Workflow: ci-guardian check con código válido.

    Verifica:
    - CLI check encuentra archivos Python
    - Ruff pasa
    - Black pasa
    - Comando exitoso
    """
    # Act: Ejecutar ci-guardian check
    resultado = subprocess.run(
        ["ci-guardian", "check", "--repo", str(repo_git_real)],
        capture_output=True,
        text=True,
    )

    # Assert: Comando exitoso
    assert resultado.returncode == 0, f"Stderr: {resultado.stderr}"
    assert "Validando" in resultado.stdout, "Debe indicar que está validando archivos"
    assert "Ruff" in resultado.stdout, "Debe ejecutar Ruff"
    assert "Black" in resultado.stdout, "Debe ejecutar Black"
    assert "sin errores" in resultado.stdout, "Debe indicar éxito"


@pytest.mark.integration
@pytest.mark.slow
def test_debe_rechazar_check_con_codigo_invalido(
    repo_git_real: Path, archivo_python_invalido: Path
) -> None:
    """
    Workflow: ci-guardian check con código inválido.

    Verifica:
    - CLI check detecta errores
    - Comando falla
    - Mensaje indica errores encontrados
    """
    # Act: Ejecutar ci-guardian check
    resultado = subprocess.run(
        ["ci-guardian", "check", "--repo", str(repo_git_real)],
        capture_output=True,
        text=True,
    )

    # Assert: Comando falla
    assert resultado.returncode != 0, "Check debe fallar con código inválido"

    # Assert: Mensaje indica errores
    output_completo = resultado.stdout + resultado.stderr
    assert "error" in output_completo.lower() or "✗" in output_completo


# =============================================================================
# TESTS: Workflow de seguridad
# =============================================================================


@pytest.mark.integration
@pytest.mark.slow
def test_debe_detectar_vulnerabilidades_en_codigo(
    repo_git_real: Path, archivo_python_con_vulnerabilidad: Path
) -> None:
    """
    Workflow: Detectar vulnerabilidades con Bandit.

    Verifica:
    - Instalar hooks
    - Añadir archivo vulnerable
    - Commit rechazado por vulnerabilidad
    """
    # Arrange: Instalar hooks
    subprocess.run(
        ["ci-guardian", "install", "--repo", str(repo_git_real)],
        check=True,
        capture_output=True,
    )

    # Añadir archivo vulnerable al stage
    subprocess.run(
        ["git", "add", archivo_python_con_vulnerabilidad.name],
        cwd=repo_git_real,
        check=True,
        capture_output=True,
    )

    # Act: Intentar hacer commit
    resultado = subprocess.run(
        ["git", "commit", "-m", "Test commit con vulnerabilidad"],
        cwd=repo_git_real,
        capture_output=True,
        text=True,
    )

    # Assert: Commit rechazado
    assert resultado.returncode != 0, "Commit debe ser rechazado por vulnerabilidad"

    # Assert: Mensaje indica problema de seguridad
    output_completo = resultado.stdout + resultado.stderr
    assert (
        "security" in output_completo.lower() or "bandit" in output_completo.lower()
    ), "Debe indicar problema de seguridad"


# =============================================================================
# TESTS: Workflow anti --no-verify
# =============================================================================


@pytest.mark.integration
def test_debe_rechazar_commit_con_no_verify(
    repo_git_real: Path, archivo_python_valido: Path
) -> None:
    """
    Workflow: Intentar commit con --no-verify (bypass de hooks).

    Verifica:
    - Instalar hooks con anti --no-verify
    - Añadir archivo válido
    - Commit con --no-verify rechazado
    - Sistema de tokens funciona
    """
    # Arrange: Instalar hooks
    subprocess.run(
        ["ci-guardian", "install", "--repo", str(repo_git_real)],
        check=True,
        capture_output=True,
    )

    # Añadir archivo al stage
    subprocess.run(
        ["git", "add", archivo_python_valido.name],
        cwd=repo_git_real,
        check=True,
        capture_output=True,
    )

    # Act: Intentar commit con --no-verify
    resultado = subprocess.run(
        ["git", "commit", "-m", "Bypass attempt", "--no-verify"],
        cwd=repo_git_real,
        capture_output=True,
        text=True,
    )

    # Assert: Commit debe fallar
    # NOTA: Como --no-verify salta pre-commit, el post-commit debe detectar
    # la ausencia de token y revertir el commit
    if resultado.returncode == 0:
        # Si el commit pasó, verificar que post-commit lo revirtió
        log_result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=repo_git_real,
            capture_output=True,
            text=True,
        )
        # No debe haber commits (post-commit debe haber hecho reset)
        assert (
            "Bypass attempt" not in log_result.stdout
        ), "Post-commit debe revertir commits con --no-verify"
    else:
        # Si el commit falló directamente, está bien
        assert resultado.returncode != 0


# =============================================================================
# TESTS: Workflow CLI status
# =============================================================================


@pytest.mark.integration
def test_debe_mostrar_status_sin_hooks_instalados(repo_git_real: Path) -> None:
    """
    Workflow: ci-guardian status en repo sin hooks.

    Verifica:
    - CLI status funciona
    - Mensaje indica que no hay hooks
    - Lista los hooks faltantes
    """
    # Act: Ejecutar ci-guardian status
    resultado = subprocess.run(
        ["ci-guardian", "status", "--repo", str(repo_git_real)],
        capture_output=True,
        text=True,
    )

    # Assert: Comando exitoso
    assert resultado.returncode == 0, f"Stderr: {resultado.stderr}"
    assert "No hay hooks instalados" in resultado.stdout
    assert "faltante" in resultado.stdout or "✗" in resultado.stdout


@pytest.mark.integration
def test_debe_mostrar_status_con_todos_los_hooks_instalados(repo_git_real: Path) -> None:
    """
    Workflow: ci-guardian status con hooks completos.

    Verifica:
    - Instalar hooks
    - CLI status muestra todos instalados
    - Mensaje indica 100%
    """
    # Arrange: Instalar hooks
    subprocess.run(
        ["ci-guardian", "install", "--repo", str(repo_git_real)],
        check=True,
        capture_output=True,
    )

    # Act: Ejecutar ci-guardian status
    resultado = subprocess.run(
        ["ci-guardian", "status", "--repo", str(repo_git_real)],
        capture_output=True,
        text=True,
    )

    # Assert: Comando exitoso
    assert resultado.returncode == 0, f"Stderr: {resultado.stderr}"
    assert "100%" in resultado.stdout or "Todos los hooks" in resultado.stdout
    assert "✓" in resultado.stdout


@pytest.mark.integration
def test_debe_mostrar_status_parcial_con_hooks_incompletos(repo_git_real: Path) -> None:
    """
    Workflow: ci-guardian status con hooks parcialmente instalados.

    Verifica:
    - Instalar solo algunos hooks manualmente
    - CLI status detecta estado parcial
    - Muestra porcentaje correcto
    """
    # Arrange: Instalar hooks
    subprocess.run(
        ["ci-guardian", "install", "--repo", str(repo_git_real)],
        check=True,
        capture_output=True,
    )

    # Eliminar uno de los hooks manualmente
    hooks_dir = repo_git_real / ".git" / "hooks"
    (hooks_dir / "pre-push").unlink()

    # Act: Ejecutar ci-guardian status
    resultado = subprocess.run(
        ["ci-guardian", "status", "--repo", str(repo_git_real)],
        capture_output=True,
        text=True,
    )

    # Assert: Comando exitoso
    assert resultado.returncode == 0, f"Stderr: {resultado.stderr}"
    assert "2/3" in resultado.stdout or "66%" in resultado.stdout
    assert "pre-push" in resultado.stdout and "faltante" in resultado.stdout


# =============================================================================
# TESTS: Workflow CLI uninstall
# =============================================================================


@pytest.mark.integration
def test_debe_desinstalar_hooks_exitosamente(repo_git_real: Path) -> None:
    """
    Workflow: ci-guardian uninstall con confirmación.

    Verifica:
    - Instalar hooks
    - Uninstall con --yes elimina todos los hooks
    - Hooks desaparecen del filesystem
    """
    # Arrange: Instalar hooks
    subprocess.run(
        ["ci-guardian", "install", "--repo", str(repo_git_real)],
        check=True,
        capture_output=True,
    )

    # Act: Desinstalar con --yes (sin confirmación interactiva)
    resultado = subprocess.run(
        ["ci-guardian", "uninstall", "--repo", str(repo_git_real), "--yes"],
        capture_output=True,
        text=True,
    )

    # Assert: Comando exitoso
    assert resultado.returncode == 0, f"Stderr: {resultado.stderr}"
    assert "3 hooks desinstalados" in resultado.stdout

    # Assert: Hooks no existen
    hooks_dir = repo_git_real / ".git" / "hooks"
    assert not (hooks_dir / "pre-commit").exists(), "Hook pre-commit debe ser eliminado"
    assert not (hooks_dir / "pre-push").exists(), "Hook pre-push debe ser eliminado"
    assert not (hooks_dir / "post-commit").exists(), "Hook post-commit debe ser eliminado"


@pytest.mark.integration
def test_debe_manejar_uninstall_sin_hooks_instalados(repo_git_real: Path) -> None:
    """
    Workflow: ci-guardian uninstall en repo sin hooks.

    Verifica:
    - Uninstall en repo limpio
    - Mensaje indica que no hay hooks
    - Comando exitoso
    """
    # Act: Desinstalar sin tener hooks instalados
    resultado = subprocess.run(
        ["ci-guardian", "uninstall", "--repo", str(repo_git_real), "--yes"],
        capture_output=True,
        text=True,
    )

    # Assert: Comando exitoso
    assert resultado.returncode == 0, f"Stderr: {resultado.stderr}"
    assert "No hay hooks" in resultado.stdout or "0 hooks" in resultado.stdout


# =============================================================================
# TESTS: Workflow CLI configure
# =============================================================================


@pytest.mark.integration
def test_debe_crear_archivo_configuracion(repo_git_real: Path) -> None:
    """
    Workflow: ci-guardian configure crea .ci-guardian.yaml.

    Verifica:
    - CLI configure crea archivo
    - Archivo contiene configuración válida
    - Formato YAML correcto
    """
    # Act: Ejecutar ci-guardian configure
    resultado = subprocess.run(
        ["ci-guardian", "configure", "--repo", str(repo_git_real)],
        capture_output=True,
        text=True,
    )

    # Assert: Comando exitoso
    assert resultado.returncode == 0, f"Stderr: {resultado.stderr}"
    assert "Configuración creada" in resultado.stdout

    # Assert: Archivo existe
    config_path = repo_git_real / ".ci-guardian.yaml"
    assert config_path.exists(), "Archivo de configuración debe existir"

    # Assert: Contenido YAML válido
    import yaml

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert "version" in config, "Configuración debe incluir versión"
    assert "hooks" in config, "Configuración debe incluir sección hooks"
    assert "validadores" in config, "Configuración debe incluir sección validadores"


# =============================================================================
# TESTS: Workflow completo end-to-end
# =============================================================================


@pytest.mark.integration
@pytest.mark.slow
def test_workflow_completo_desarrollo_normal(repo_git_real: Path) -> None:
    """
    Workflow end-to-end completo simulando desarrollo normal.

    Pasos:
    1. ci-guardian install
    2. ci-guardian configure
    3. ci-guardian status (verificar instalación)
    4. Crear archivo Python válido
    5. git add + git commit (debe pasar)
    6. ci-guardian check (debe pasar)
    7. Crear archivo Python inválido
    8. git add + git commit (debe fallar)
    9. Corregir archivo
    10. git add + git commit (debe pasar)
    11. ci-guardian status (verificar hooks activos)
    12. ci-guardian uninstall (limpiar)
    """
    # 1. Instalar hooks
    resultado = subprocess.run(
        ["ci-guardian", "install", "--repo", str(repo_git_real)],
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 0, "Instalación debe ser exitosa"

    # 2. Configurar
    resultado = subprocess.run(
        ["ci-guardian", "configure", "--repo", str(repo_git_real)],
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 0, "Configuración debe ser exitosa"

    # 3. Verificar status
    resultado = subprocess.run(
        ["ci-guardian", "status", "--repo", str(repo_git_real)],
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 0, "Status debe ser exitoso"
    assert "100%" in resultado.stdout, "Todos los hooks deben estar instalados"

    # 4. Crear archivo válido
    archivo_valido = repo_git_real / "main.py"
    archivo_valido.write_text(
        '''"""Módulo principal."""


def main() -> int:
    """Función principal."""
    return 0


if __name__ == "__main__":
    main()
''',
        encoding="utf-8",
    )

    # 5. Commit archivo válido
    subprocess.run(["git", "add", "main.py"], cwd=repo_git_real, check=True, capture_output=True)
    resultado = subprocess.run(
        ["git", "commit", "-m", "feat: add main module"],
        cwd=repo_git_real,
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 0, "Commit con código válido debe pasar"

    # 6. Ejecutar check
    resultado = subprocess.run(
        ["ci-guardian", "check", "--repo", str(repo_git_real)],
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 0, "Check debe pasar con código válido"

    # 7. Crear archivo inválido
    archivo_invalido = repo_git_real / "bad_code.py"
    archivo_invalido.write_text("x=1+2+3", encoding="utf-8")  # Sin espacios, sin newline

    # 8. Intentar commit de archivo inválido (debe fallar)
    subprocess.run(
        ["git", "add", "bad_code.py"], cwd=repo_git_real, check=True, capture_output=True
    )
    resultado = subprocess.run(
        ["git", "commit", "-m", "feat: add bad code"],
        cwd=repo_git_real,
        capture_output=True,
        text=True,
    )
    assert resultado.returncode != 0, "Commit con código inválido debe fallar"

    # 9. Corregir archivo
    archivo_invalido.write_text(
        '''"""Módulo corregido."""

x = 1 + 2 + 3
''',
        encoding="utf-8",
    )

    # 10. Commit de archivo corregido (debe pasar)
    subprocess.run(
        ["git", "add", "bad_code.py"], cwd=repo_git_real, check=True, capture_output=True
    )
    resultado = subprocess.run(
        ["git", "commit", "-m", "fix: correct code formatting"],
        cwd=repo_git_real,
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 0, "Commit con código corregido debe pasar"

    # 11. Verificar status final
    resultado = subprocess.run(
        ["ci-guardian", "status", "--repo", str(repo_git_real)],
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 0, "Status debe seguir siendo exitoso"

    # 12. Desinstalar
    resultado = subprocess.run(
        ["ci-guardian", "uninstall", "--repo", str(repo_git_real), "--yes"],
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 0, "Desinstalación debe ser exitosa"


@pytest.mark.integration
@pytest.mark.slow
def test_workflow_proteccion_contra_bypass_con_no_verify(repo_git_real: Path) -> None:
    """
    Workflow end-to-end: Protección contra bypass con --no-verify.

    Pasos:
    1. Instalar hooks
    2. Crear archivo válido
    3. Intentar commit con --no-verify
    4. Verificar que post-commit detecta y revierte
    5. Hacer commit normal (debe funcionar)
    """
    # 1. Instalar hooks
    subprocess.run(
        ["ci-guardian", "install", "--repo", str(repo_git_real)],
        check=True,
        capture_output=True,
    )

    # 2. Crear archivo válido
    archivo = repo_git_real / "test.py"
    archivo.write_text('"""Test."""\n\n\ndef test() -> bool:\n    """Test."""\n    return True\n')

    subprocess.run(["git", "add", "test.py"], cwd=repo_git_real, check=True, capture_output=True)

    # 3. Intentar commit con --no-verify
    resultado_bypass = subprocess.run(
        ["git", "commit", "-m", "Bypass attempt", "--no-verify"],
        cwd=repo_git_real,
        capture_output=True,
        text=True,
    )

    # 4. Verificar que no hay commit persistente
    # (post-commit debe haber revertido)
    resultado_log = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=repo_git_real,
        capture_output=True,
        text=True,
    )

    # Si post-commit funcionó, el commit "Bypass attempt" no debe existir
    if resultado_bypass.returncode == 0:
        assert (
            "Bypass attempt" not in resultado_log.stdout
        ), "Post-commit debe revertir commits hechos con --no-verify"

    # 5. Hacer commit normal (sin --no-verify)
    subprocess.run(["git", "add", "test.py"], cwd=repo_git_real, check=True, capture_output=True)
    resultado_normal = subprocess.run(
        ["git", "commit", "-m", "Normal commit"],
        cwd=repo_git_real,
        capture_output=True,
        text=True,
    )

    assert resultado_normal.returncode == 0, "Commit normal debe funcionar"

    # Verificar que el commit normal SÍ existe
    resultado_log2 = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=repo_git_real,
        capture_output=True,
        text=True,
    )
    assert "Normal commit" in resultado_log2.stdout, "Commit normal debe persistir"
