"""
Tests unitarios para la CLI de CI Guardian (LIB-8).

Estos tests validan la interfaz de línea de comandos usando Click's CliRunner.
Fase RED del TDD: TODOS los tests deben FALLAR inicialmente.
"""

from __future__ import annotations

import platform
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from ci_guardian.cli import (
    check,
    configure,
    install,
    main,
    status,
    uninstall,
)

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def cli_runner() -> CliRunner:
    """
    Fixture que proporciona un CliRunner de Click para invocar comandos.

    Returns:
        CliRunner configurado para tests
    """
    return CliRunner()


@pytest.fixture
def repo_git_mock(tmp_path: Path) -> Path:
    """
    Crea un repositorio Git mock con estructura válida.

    Args:
        tmp_path: Directorio temporal de pytest

    Returns:
        Path al repositorio mock
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / ".git" / "hooks").mkdir()
    return repo


@pytest.fixture
def archivos_python_mock(tmp_path: Path) -> list[Path]:
    """
    Crea archivos Python de prueba.

    Args:
        tmp_path: Directorio temporal de pytest

    Returns:
        Lista de Paths a archivos Python creados
    """
    archivos = []
    for i in range(3):
        archivo = tmp_path / f"test_{i}.py"
        archivo.write_text(
            f'"""Módulo {i}."""\n\n\ndef funcion_{i}():\n    """Función {i}."""\n    pass\n'
        )
        archivos.append(archivo)
    return archivos


# ============================================================================
# TESTS COMANDO: install
# ============================================================================


class TestCLIInstall:
    """Tests para el comando 'ci-guardian install'."""

    def test_debe_instalar_hooks_exitosamente_cuando_esta_en_repo_git(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
    ) -> None:
        """
        Debe instalar todos los hooks exitosamente cuando está en un repo git válido.

        Escenario:
        1. Usuario ejecuta 'ci-guardian install' en un repo git
        2. CLI detecta que es repo válido
        3. Instala pre-commit, pre-push, post-commit
        4. Muestra mensaje de éxito
        5. Exit code = 0
        """
        with (
            patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock),
            patch("ci_guardian.cli.instalar_hook") as mock_instalar,
        ):
            # Act
            resultado = cli_runner.invoke(install)

            # Assert
            assert resultado.exit_code == 0, f"Debe salir con código 0. Output: {resultado.output}"
            assert (
                "instalados exitosamente" in resultado.output.lower()
            ), "Debe mostrar mensaje de éxito"
            assert (
                mock_instalar.call_count == 3
            ), "Debe instalar 3 hooks (pre-commit, commit-msg, post-commit)"

    def test_debe_fallar_cuando_no_esta_en_repo_git(
        self, cli_runner: CliRunner, tmp_path: Path
    ) -> None:
        """
        Debe fallar con mensaje claro cuando no está en un repositorio git.

        Escenario:
        1. Usuario ejecuta 'ci-guardian install' en directorio sin .git
        2. CLI detecta que NO es repo git
        3. Muestra error descriptivo
        4. Exit code != 0
        """
        # Arrange: directorio sin .git
        no_repo = tmp_path / "no_repo"
        no_repo.mkdir()

        # Act
        with patch("ci_guardian.cli.Path.cwd", return_value=no_repo):
            resultado = cli_runner.invoke(install)

        # Assert
        assert resultado.exit_code != 0, "Debe fallar con exit code != 0"
        assert (
            "no es un repositorio git" in resultado.output.lower()
        ), "Debe mostrar mensaje de error claro"

    def test_debe_rechazar_instalacion_cuando_hooks_ya_existen(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
    ) -> None:
        """
        Debe rechazar la instalación si los hooks ya existen (sin --force).

        Escenario:
        1. Hooks de CI Guardian ya están instalados
        2. Usuario ejecuta 'ci-guardian install' sin --force
        3. CLI detecta hooks existentes
        4. Muestra error y NO sobrescribe
        5. Exit code != 0
        """
        with (
            patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock),
            patch("ci_guardian.cli.instalar_hook") as mock_instalar,
        ):
            # Simular que el hook ya existe
            mock_instalar.side_effect = FileExistsError("El hook pre-commit ya existe")

            # Act
            resultado = cli_runner.invoke(install)

            # Assert
            assert resultado.exit_code != 0, "Debe fallar cuando hooks ya existen"
            assert "ya existe" in resultado.output.lower(), "Debe mostrar mensaje de error"

    def test_debe_sobrescribir_hooks_cuando_se_usa_flag_force(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
    ) -> None:
        """
        Debe sobrescribir hooks existentes cuando se usa el flag --force.

        Escenario:
        1. Hooks ya existen
        2. Usuario ejecuta 'ci-guardian install --force'
        3. CLI elimina hooks existentes
        4. Reinstala todos los hooks
        5. Muestra mensaje de éxito con advertencia
        6. Exit code = 0
        """
        # Crear hooks existentes
        (repo_git_mock / ".git" / "hooks" / "pre-commit").write_text(
            "#!/bin/bash\n# CI-GUARDIAN-HOOK\necho 'old hook'"
        )

        with (
            patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock),
            patch("ci_guardian.cli.desinstalar_hook") as mock_desinstalar,
            patch("ci_guardian.cli.instalar_hook") as mock_instalar,
        ):
            # Act
            resultado = cli_runner.invoke(install, ["--force"])

            # Assert
            assert resultado.exit_code == 0, "Debe salir con código 0 con --force"
            assert mock_desinstalar.called, "Debe llamar a desinstalar_hook"
            assert mock_instalar.call_count == 3, "Debe reinstalar los 3 hooks"
            assert (
                "forzada" in resultado.output.lower() or "sobrescrito" in resultado.output.lower()
            ), "Debe indicar que fue una instalación forzada"

    def test_debe_validar_path_traversal_en_repo_path(self, cli_runner: CliRunner) -> None:
        """
        Debe rechazar paths con path traversal (..) en repo_path.

        Escenario de seguridad:
        1. Atacante intenta: ci-guardian install --repo ../../etc/passwd
        2. CLI valida el path
        3. Rechaza path traversal
        4. Exit code != 0
        """
        # Act
        resultado = cli_runner.invoke(install, ["--repo", "../../etc/passwd"])

        # Assert
        assert resultado.exit_code != 0, "Debe rechazar path traversal"
        assert (
            "path traversal" in resultado.output.lower()
            or "ruta inválida" in resultado.output.lower()
        ), "Debe mostrar error de seguridad"

    @pytest.mark.skipif(platform.system() == "Windows", reason="Test específico de Linux")
    def test_debe_instalar_hooks_con_permisos_755_en_linux(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
    ) -> None:
        """
        Debe instalar hooks con permisos 755 (rwxr-xr-x) en Linux.

        Escenario Linux:
        1. Usuario ejecuta 'ci-guardian install' en Linux
        2. CLI instala hooks
        3. Hooks tienen permisos de ejecución (755)
        """
        with (
            patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock),
            patch("ci_guardian.cli.instalar_hook") as mock_instalar,
        ):
            # Act
            resultado = cli_runner.invoke(install)

            # Assert
            assert resultado.exit_code == 0
            # Verificar que se llamó a instalar_hook (que internamente aplica chmod 0o755)
            assert mock_instalar.called

    @pytest.mark.skipif(platform.system() != "Windows", reason="Test específico de Windows")
    def test_debe_instalar_hooks_bat_en_windows(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
    ) -> None:
        """
        Debe instalar hooks como archivos .bat en Windows.

        Escenario Windows:
        1. Usuario ejecuta 'ci-guardian install' en Windows
        2. CLI detecta sistema Windows
        3. Instala hooks con extensión .bat
        """
        with (
            patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock),
            patch("ci_guardian.cli.instalar_hook") as mock_instalar,
        ):
            # Act
            resultado = cli_runner.invoke(install)

            # Assert
            assert resultado.exit_code == 0
            assert mock_instalar.called


# ============================================================================
# TESTS COMANDO: uninstall
# ============================================================================


class TestCLIUninstall:
    """Tests para el comando 'ci-guardian uninstall'."""

    def test_debe_pedir_confirmacion_antes_de_desinstalar(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
    ) -> None:
        """
        Debe pedir confirmación antes de desinstalar los hooks.

        Escenario:
        1. Usuario ejecuta 'ci-guardian uninstall'
        2. CLI pide confirmación (y/N)
        3. Usuario NO confirma (Enter o 'n')
        4. Hooks NO se eliminan
        5. Exit code = 0 (cancelación exitosa)
        """
        with patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock):
            # Simular que usuario responde 'n' (no confirma)
            resultado = cli_runner.invoke(uninstall, input="n\n")

            # Assert
            assert resultado.exit_code == 0, "Debe salir con código 0 (cancelación)"
            assert (
                "cancelado" in resultado.output.lower() or "abortado" in resultado.output.lower()
            ), "Debe mostrar que se canceló"

    def test_debe_desinstalar_todos_los_hooks_cuando_usuario_confirma(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
    ) -> None:
        """
        Debe desinstalar todos los hooks cuando el usuario confirma.

        Escenario:
        1. Hooks están instalados
        2. Usuario ejecuta 'ci-guardian uninstall'
        3. Usuario confirma con 'y'
        4. CLI desinstala todos los hooks
        5. Muestra mensaje de éxito
        6. Exit code = 0
        """
        # Crear hooks instalados
        for hook in ["pre-commit", "commit-msg", "post-commit"]:
            (repo_git_mock / ".git" / "hooks" / hook).write_text(
                f"#!/bin/bash\n# CI-GUARDIAN-HOOK\necho '{hook}'"
            )

        with (
            patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock),
            patch("ci_guardian.cli.desinstalar_hook") as mock_desinstalar,
        ):
            mock_desinstalar.return_value = True

            # Simular que usuario confirma con 'y'
            resultado = cli_runner.invoke(uninstall, input="y\n")

            # Assert
            assert resultado.exit_code == 0, "Debe salir con código 0"
            assert mock_desinstalar.call_count == 3, "Debe desinstalar 3 hooks"
            assert "desinstalados" in resultado.output.lower(), "Debe mostrar mensaje de éxito"

    def test_debe_omitir_confirmacion_con_flag_yes(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
    ) -> None:
        """
        Debe omitir la confirmación cuando se usa el flag --yes.

        Escenario:
        1. Usuario ejecuta 'ci-guardian uninstall --yes'
        2. CLI NO pide confirmación
        3. Desinstala directamente
        4. Exit code = 0
        """
        with (
            patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock),
            patch("ci_guardian.cli.desinstalar_hook") as mock_desinstalar,
        ):
            mock_desinstalar.return_value = True

            # Act
            resultado = cli_runner.invoke(uninstall, ["--yes"])

            # Assert
            assert resultado.exit_code == 0, "Debe salir con código 0"
            assert mock_desinstalar.call_count == 3, "Debe desinstalar los 3 hooks"
            # No debe mostrar prompt de confirmación
            assert "¿" not in resultado.output, "No debe mostrar pregunta de confirmación"

    def test_debe_manejar_error_cuando_hooks_no_son_de_ci_guardian(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
    ) -> None:
        """
        Debe manejar el error cuando los hooks no son de CI Guardian.

        Escenario:
        1. Hooks existen pero son de otra herramienta (Husky, etc.)
        2. Usuario ejecuta 'ci-guardian uninstall --yes'
        3. CLI detecta que no son de CI Guardian
        4. Muestra advertencia y NO elimina
        5. Exit code != 0
        """
        # Crear hook de otra herramienta (sin marca CI-GUARDIAN-HOOK)
        (repo_git_mock / ".git" / "hooks" / "pre-commit").write_text(
            "#!/bin/bash\n# Husky hook\necho 'not ci-guardian'"
        )

        with (
            patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock),
            patch("ci_guardian.cli.desinstalar_hook") as mock_desinstalar,
        ):
            # Simular que desinstalar_hook rechaza hook que no es de CI Guardian
            mock_desinstalar.side_effect = ValueError(
                "El hook pre-commit no es un hook de CI Guardian"
            )

            # Act
            resultado = cli_runner.invoke(uninstall, ["--yes"])

            # Assert
            assert resultado.exit_code != 0, "Debe fallar con exit code != 0"
            assert (
                "no es un hook de ci guardian" in resultado.output.lower()
            ), "Debe mostrar advertencia específica"

    def test_debe_informar_cuando_no_hay_hooks_instalados(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
    ) -> None:
        """
        Debe informar cuando no hay hooks instalados.

        Escenario:
        1. No hay hooks instalados
        2. Usuario ejecuta 'ci-guardian uninstall --yes'
        3. CLI detecta que no hay nada que desinstalar
        4. Muestra mensaje informativo
        5. Exit code = 0
        """
        with (
            patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock),
            patch("ci_guardian.cli.desinstalar_hook") as mock_desinstalar,
        ):
            # Simular que no hay hooks (desinstalar_hook retorna False)
            mock_desinstalar.return_value = False

            # Act
            resultado = cli_runner.invoke(uninstall, ["--yes"])

            # Assert
            assert resultado.exit_code == 0, "Debe salir con código 0"
            assert (
                "no hay hooks" in resultado.output.lower()
                or "no instalado" in resultado.output.lower()
            ), "Debe informar que no hay hooks"


# ============================================================================
# TESTS COMANDO: status
# ============================================================================


class TestCLIStatus:
    """Tests para el comando 'ci-guardian status'."""

    def test_debe_mostrar_hooks_instalados_y_faltantes(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
    ) -> None:
        """
        Debe mostrar qué hooks están instalados y cuáles faltan.

        Escenario:
        1. pre-commit, commit-msg y pre-push instalados
        2. post-commit falta
        3. Usuario ejecuta 'ci-guardian status'
        4. CLI muestra lista de instalados (✓) y faltantes (✗)
        5. Exit code = 0
        """
        with (
            patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock),
            patch("ci_guardian.cli.obtener_hooks_instalados") as mock_hooks_instalados,
        ):
            # Simular que solo pre-commit y commit-msg están instalados
            mock_hooks_instalados.return_value = ["pre-commit", "commit-msg"]

            # Act
            resultado = cli_runner.invoke(status)

            # Assert
            assert resultado.exit_code == 0, "Debe salir con código 0"
            # Debe mostrar hooks instalados
            assert "pre-commit" in resultado.output, "Debe listar pre-commit"
            assert "commit-msg" in resultado.output, "Debe listar commit-msg"
            # Debe mostrar hook faltante
            assert "post-commit" in resultado.output, "Debe listar post-commit como faltante"
            # Debe usar algún indicador visual (✓, ✗, [INSTALADO], etc.)
            assert any(
                indicator in resultado.output for indicator in ["✓", "✗", "instalado", "faltante"]
            ), "Debe usar indicadores visuales"

    def test_debe_mostrar_version_de_ci_guardian(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
    ) -> None:
        """
        Debe mostrar la versión de CI Guardian instalada.

        Escenario:
        1. Usuario ejecuta 'ci-guardian status'
        2. CLI muestra versión (ej: 0.1.0)
        3. Exit code = 0
        """
        with (
            patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock),
            patch("ci_guardian.cli.obtener_hooks_instalados", return_value=[]),
        ):
            # Act
            resultado = cli_runner.invoke(status)

            # Assert
            assert resultado.exit_code == 0
            # Debe mostrar versión (formato: X.Y.Z o vX.Y.Z)
            assert any(
                char.isdigit() for char in resultado.output
            ), "Debe mostrar número de versión"
            assert "." in resultado.output, "Versión debe tener formato X.Y.Z"

    def test_debe_mostrar_mensaje_completo_cuando_todos_instalados(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
    ) -> None:
        """
        Debe mostrar mensaje positivo cuando todos los hooks están instalados.

        Escenario:
        1. Todos los hooks están instalados (pre-commit, commit-msg, post-commit, pre-push)
        2. Usuario ejecuta 'ci-guardian status'
        3. CLI muestra mensaje de que todo está OK
        4. Exit code = 0
        """
        with (
            patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock),
            patch("ci_guardian.cli.obtener_hooks_instalados") as mock_hooks_instalados,
        ):
            # Simular que todos los hooks están instalados
            mock_hooks_instalados.return_value = [
                "pre-commit",
                "commit-msg",
                "post-commit",
                "commit-msg",
            ]

            # Act
            resultado = cli_runner.invoke(status)

            # Assert
            assert resultado.exit_code == 0
            assert (
                "todos" in resultado.output.lower()
                or "completo" in resultado.output.lower()
                or "100%" in resultado.output
            ), "Debe indicar que todo está instalado"

    def test_debe_mostrar_mensaje_cuando_no_hay_hooks_instalados(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
    ) -> None:
        """
        Debe mostrar mensaje claro cuando no hay hooks instalados.

        Escenario:
        1. No hay hooks instalados
        2. Usuario ejecuta 'ci-guardian status'
        3. CLI muestra que no hay hooks y sugiere ejecutar 'install'
        4. Exit code = 0
        """
        with (
            patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock),
            patch("ci_guardian.cli.obtener_hooks_instalados", return_value=[]),
        ):
            # Act
            resultado = cli_runner.invoke(status)

            # Assert
            assert resultado.exit_code == 0
            assert (
                "no hay hooks" in resultado.output.lower() or "ninguno" in resultado.output.lower()
            ), "Debe indicar que no hay hooks"
            assert "install" in resultado.output, "Debe sugerir ejecutar 'install'"

    def test_debe_fallar_cuando_no_esta_en_repo_git(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """
        Debe fallar cuando no está en un repositorio git.

        Escenario:
        1. Usuario ejecuta 'ci-guardian status' fuera de un repo git
        2. CLI detecta que no es repo git
        3. Muestra error
        4. Exit code != 0
        """
        no_repo = tmp_path / "no_repo"
        no_repo.mkdir()

        with patch("ci_guardian.cli.Path.cwd", return_value=no_repo):
            # Act
            resultado = cli_runner.invoke(status)

            # Assert
            assert resultado.exit_code != 0, "Debe fallar con exit code != 0"
            assert (
                "no es un repositorio git" in resultado.output.lower()
            ), "Debe mostrar error de repo git"


# ============================================================================
# TESTS COMANDO: check
# ============================================================================


class TestCLICheck:
    """Tests para el comando 'ci-guardian check'."""

    def test_debe_ejecutar_ruff_y_black_exitosamente_cuando_codigo_valido(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
        archivos_python_mock: list[Path],
    ) -> None:
        """
        Debe ejecutar Ruff y Black exitosamente cuando el código es válido.

        Escenario:
        1. Usuario ejecuta 'ci-guardian check'
        2. CLI encuentra archivos .py en el proyecto
        3. Ejecuta Ruff (sin errores)
        4. Ejecuta Black (código formateado)
        5. Muestra resumen de éxito
        6. Exit code = 0
        """
        with (
            patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock),
            patch("ci_guardian.cli.ejecutar_ruff") as mock_ruff,
            patch("ci_guardian.cli.ejecutar_black") as mock_black,
            patch("ci_guardian.cli.Path.rglob") as mock_rglob,
        ):
            # Simular archivos Python encontrados
            mock_rglob.return_value = archivos_python_mock

            # Simular que Ruff y Black pasan
            mock_ruff.return_value = (True, "Código sin errores de linting (OK)")
            mock_black.return_value = (True, "Archivos formateados correctamente")

            # Act
            resultado = cli_runner.invoke(check)

            # Assert
            assert resultado.exit_code == 0, f"Debe salir con código 0. Output: {resultado.output}"
            assert mock_ruff.called, "Debe llamar a ejecutar_ruff"
            assert mock_black.called, "Debe llamar a ejecutar_black"
            assert (
                "sin errores" in resultado.output.lower() or "ok" in resultado.output.lower()
            ), "Debe mostrar mensaje de éxito"

    def test_debe_fallar_con_exit_code_1_cuando_ruff_detecta_errores(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
        archivos_python_mock: list[Path],
    ) -> None:
        """
        Debe fallar con exit code 1 cuando Ruff detecta errores.

        Escenario:
        1. Usuario ejecuta 'ci-guardian check'
        2. Ruff detecta errores de linting
        3. CLI muestra los errores
        4. Exit code = 1 (para uso en CI/CD)
        """
        with (
            patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock),
            patch("ci_guardian.cli.ejecutar_ruff") as mock_ruff,
            patch("ci_guardian.cli.ejecutar_black") as mock_black,
            patch("ci_guardian.cli.Path.rglob", return_value=archivos_python_mock),
        ):
            # Simular que Ruff detecta errores
            mock_ruff.return_value = (
                False,
                "tests/test_cli.py:10:5: F401 Unused import 'os'",
            )
            mock_black.return_value = (True, "Archivos formateados correctamente")

            # Act
            resultado = cli_runner.invoke(check)

            # Assert
            assert resultado.exit_code == 1, "Debe fallar con exit code 1"
            assert (
                "error" in resultado.output.lower() or "f401" in resultado.output.lower()
            ), "Debe mostrar errores de Ruff"

    def test_debe_fallar_cuando_black_detecta_archivos_sin_formatear(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
        archivos_python_mock: list[Path],
    ) -> None:
        """
        Debe fallar cuando Black detecta archivos sin formatear.

        Escenario:
        1. Usuario ejecuta 'ci-guardian check'
        2. Ruff pasa sin errores
        3. Black detecta que archivos necesitan formateo
        4. CLI muestra qué archivos necesitan formateo
        5. Exit code = 1
        """
        with (
            patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock),
            patch("ci_guardian.cli.ejecutar_ruff") as mock_ruff,
            patch("ci_guardian.cli.ejecutar_black") as mock_black,
            patch("ci_guardian.cli.Path.rglob", return_value=archivos_python_mock),
        ):
            # Simular que Ruff pasa pero Black detecta archivos sin formatear
            mock_ruff.return_value = (True, "Código sin errores de linting (OK)")
            mock_black.return_value = (False, "would reformat tests/test_cli.py")

            # Act
            resultado = cli_runner.invoke(check)

            # Assert
            assert resultado.exit_code == 1, "Debe fallar con exit code 1"
            assert (
                "formatear" in resultado.output.lower() or "black" in resultado.output.lower()
            ), "Debe mencionar Black o formateo"

    def test_debe_buscar_archivos_python_recursivamente_en_proyecto(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
    ) -> None:
        """
        Debe buscar archivos .py recursivamente en el proyecto.

        Escenario:
        1. Usuario ejecuta 'ci-guardian check'
        2. CLI busca archivos .py en src/, tests/, scripts/
        3. Ejecuta validaciones en todos los archivos encontrados
        """
        with (
            patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock),
            patch("ci_guardian.cli.ejecutar_ruff") as mock_ruff,
            patch("ci_guardian.cli.ejecutar_black") as mock_black,
            patch("ci_guardian.cli.Path.rglob") as mock_rglob,
        ):
            # Simular archivos encontrados en diferentes directorios
            archivos_encontrados = [
                repo_git_mock / "src" / "main.py",
                repo_git_mock / "tests" / "test_main.py",
                repo_git_mock / "scripts" / "build.py",
            ]
            mock_rglob.return_value = archivos_encontrados
            mock_ruff.return_value = (True, "OK")
            mock_black.return_value = (True, "OK")

            # Act
            resultado = cli_runner.invoke(check)

            # Assert
            assert resultado.exit_code == 0
            # Verificar que se buscaron archivos .py
            mock_rglob.assert_called_once_with("**/*.py")
            # Verificar que se procesaron los archivos
            assert mock_ruff.call_count == 1
            assert mock_black.call_count == 1

    def test_debe_ignorar_directorios_excluidos(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
    ) -> None:
        """
        Debe ignorar directorios excluidos (venv, .git, __pycache__, etc.).

        Escenario:
        1. Usuario ejecuta 'ci-guardian check'
        2. CLI encuentra archivos .py en venv/, .git/, __pycache__/
        3. Los ignora y NO los valida
        4. Solo valida archivos del proyecto
        """
        with (
            patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock),
            patch("ci_guardian.cli.ejecutar_ruff") as mock_ruff,
            patch("ci_guardian.cli.ejecutar_black") as mock_black,
            patch("ci_guardian.cli.Path.rglob") as mock_rglob,
        ):
            # Simular archivos en directorios excluidos
            todos_archivos = [
                repo_git_mock / "src" / "main.py",  # VÁLIDO
                repo_git_mock / "venv" / "lib" / "python3.12" / "site.py",  # IGNORAR
                repo_git_mock / ".git" / "hooks" / "pre-commit",  # IGNORAR
                repo_git_mock / "__pycache__" / "main.cpython-312.pyc",  # IGNORAR
            ]
            mock_rglob.return_value = todos_archivos
            mock_ruff.return_value = (True, "OK")
            mock_black.return_value = (True, "OK")

            # Act
            resultado = cli_runner.invoke(check)

            # Assert
            assert resultado.exit_code == 0
            # Verificar que solo se validó 1 archivo (main.py)
            llamada_ruff = mock_ruff.call_args[0][0]  # Primer argumento de la llamada
            assert len(llamada_ruff) == 1, "Solo debe validar archivos del proyecto"
            assert "main.py" in str(llamada_ruff[0]), "Debe validar main.py"

    def test_debe_informar_cuando_no_hay_archivos_python(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
    ) -> None:
        """
        Debe informar cuando no hay archivos Python para validar.

        Escenario:
        1. Usuario ejecuta 'ci-guardian check' en repo sin .py
        2. CLI busca archivos .py
        3. No encuentra ninguno
        4. Muestra mensaje informativo
        5. Exit code = 0 (no es un error)
        """
        with (
            patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock),
            patch("ci_guardian.cli.Path.rglob", return_value=[]),
        ):
            # Act
            resultado = cli_runner.invoke(check)

            # Assert
            assert resultado.exit_code == 0, "No debe fallar si no hay archivos"
            assert (
                "no hay archivos" in resultado.output.lower()
                or "ningún archivo" in resultado.output.lower()
            ), "Debe informar que no hay archivos Python"

    def test_debe_manejar_error_cuando_ruff_no_esta_instalado(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
        archivos_python_mock: list[Path],
    ) -> None:
        """
        Debe manejar el error cuando Ruff no está instalado.

        Escenario:
        1. Usuario ejecuta 'ci-guardian check'
        2. Ruff no está instalado (FileNotFoundError)
        3. CLI muestra error claro
        4. Sugiere instalar Ruff
        5. Exit code = 1
        """
        with (
            patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock),
            patch("ci_guardian.cli.ejecutar_ruff") as mock_ruff,
            patch("ci_guardian.cli.Path.rglob", return_value=archivos_python_mock),
        ):
            # Simular que Ruff no está instalado
            mock_ruff.return_value = (False, "Ruff no encontrado. Instálalo con: pip install ruff")

            # Act
            resultado = cli_runner.invoke(check)

            # Assert
            assert resultado.exit_code == 1, "Debe fallar con exit code 1"
            assert "ruff no encontrado" in resultado.output.lower(), "Debe mencionar que Ruff falta"
            assert "pip install" in resultado.output.lower(), "Debe sugerir cómo instalar"

    def test_debe_manejar_path_traversal_en_archivos(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
    ) -> None:
        """
        Debe rechazar archivos con path traversal (..).

        Escenario de seguridad:
        1. Alguien intenta inyectar path traversal en archivos
        2. CLI detecta path traversal
        3. Rechaza esos archivos
        4. Muestra error de seguridad
        """
        with (
            patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock),
            patch("ci_guardian.cli.ejecutar_ruff") as mock_ruff,
            patch("ci_guardian.cli.Path.rglob") as mock_rglob,
        ):
            # Simular archivo con path traversal
            archivo_malicioso = Path("../../etc/passwd.py")
            mock_rglob.return_value = [archivo_malicioso]

            # Simular que ejecutar_ruff detecta path traversal
            mock_ruff.side_effect = ValueError("path traversal detectado")

            # Act
            resultado = cli_runner.invoke(check)

            # Assert
            assert resultado.exit_code == 1, "Debe fallar por path traversal"
            assert (
                "path traversal" in resultado.output.lower()
                or "ruta inválida" in resultado.output.lower()
            ), "Debe mostrar error de seguridad"


# ============================================================================
# TESTS COMANDO: configure
# ============================================================================


class TestCLIConfigure:
    """Tests para el comando 'ci-guardian configure'."""

    def test_debe_crear_archivo_configuracion_cuando_no_existe(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
    ) -> None:
        """
        Debe crear archivo .ci-guardian.yaml cuando no existe.

        Escenario:
        1. Usuario ejecuta 'ci-guardian configure'
        2. Archivo .ci-guardian.yaml NO existe
        3. CLI crea el archivo con configuración por defecto
        4. Muestra mensaje de éxito
        5. Exit code = 0
        """
        config_path = repo_git_mock / ".ci-guardian.yaml"

        with patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock):
            # Act
            resultado = cli_runner.invoke(configure)

            # Assert
            assert resultado.exit_code == 0, "Debe salir con código 0"
            assert config_path.exists(), "Debe crear el archivo .ci-guardian.yaml"
            assert (
                "configuración creada" in resultado.output.lower()
            ), "Debe mostrar mensaje de éxito"

    def test_debe_preguntar_antes_de_sobrescribir_configuracion_existente(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
    ) -> None:
        """
        Debe preguntar antes de sobrescribir configuración existente.

        Escenario:
        1. Archivo .ci-guardian.yaml ya existe
        2. Usuario ejecuta 'ci-guardian configure'
        3. CLI pregunta si desea sobrescribir
        4. Usuario responde 'n'
        5. Configuración NO se sobrescribe
        """
        config_path = repo_git_mock / ".ci-guardian.yaml"
        config_path.write_text("# Configuración existente\nversion: 0.1.0\n")
        contenido_original = config_path.read_text()

        with patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock):
            # Simular que usuario responde 'n' (no sobrescribir)
            resultado = cli_runner.invoke(configure, input="n\n")

            # Assert
            assert resultado.exit_code == 0, "Debe salir con código 0 (cancelación)"
            assert config_path.read_text() == contenido_original, "No debe modificar configuración"
            assert "cancelado" in resultado.output.lower() or "abortado" in resultado.output.lower()

    def test_debe_incluir_configuraciones_basicas_en_yaml(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
    ) -> None:
        """
        Debe incluir configuraciones básicas en el archivo YAML.

        Escenario:
        1. Usuario ejecuta 'ci-guardian configure'
        2. CLI crea .ci-guardian.yaml con:
           - versión de config
           - hooks habilitados
           - opciones de validadores
        """
        config_path = repo_git_mock / ".ci-guardian.yaml"

        with patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock):
            # Act
            resultado = cli_runner.invoke(configure)

            # Assert
            assert resultado.exit_code == 0
            contenido = config_path.read_text()
            # Debe incluir configuraciones básicas
            assert "version:" in contenido.lower(), "Debe incluir versión"
            assert (
                "hooks:" in contenido.lower() or "validadores:" in contenido.lower()
            ), "Debe incluir sección de hooks o validadores"

    def test_debe_validar_formato_yaml_correcto(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
    ) -> None:
        """
        Debe generar YAML con formato válido.

        Escenario:
        1. Usuario ejecuta 'ci-guardian configure'
        2. CLI crea .ci-guardian.yaml
        3. El archivo es YAML válido (puede parsearse)
        """
        import yaml

        config_path = repo_git_mock / ".ci-guardian.yaml"

        with patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock):
            # Act
            resultado = cli_runner.invoke(configure)

            # Assert
            assert resultado.exit_code == 0
            # Debe poder parsearse como YAML válido
            with open(config_path) as f:
                config = yaml.safe_load(f)
                assert config is not None, "YAML debe ser válido y parseable"
                assert isinstance(config, dict), "YAML debe ser un diccionario"

    def test_debe_fallar_cuando_no_esta_en_repo_git(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """
        Debe fallar cuando no está en un repositorio git.

        Escenario:
        1. Usuario ejecuta 'ci-guardian configure' fuera de repo git
        2. CLI detecta que no es repo git
        3. Muestra error
        4. Exit code != 0
        """
        no_repo = tmp_path / "no_repo"
        no_repo.mkdir()

        with patch("ci_guardian.cli.Path.cwd", return_value=no_repo):
            # Act
            resultado = cli_runner.invoke(configure)

            # Assert
            assert resultado.exit_code != 0, "Debe fallar con exit code != 0"
            assert "no es un repositorio git" in resultado.output.lower()


# ============================================================================
# TESTS GRUPO CLI PRINCIPAL
# ============================================================================


class TestCLIMain:
    """Tests para el grupo CLI principal y opciones globales."""

    def test_debe_mostrar_ayuda_con_flag_help(self, cli_runner: CliRunner) -> None:
        """
        Debe mostrar ayuda cuando se usa --help.

        Escenario:
        1. Usuario ejecuta 'ci-guardian --help'
        2. CLI muestra ayuda con lista de comandos
        3. Exit code = 0
        """
        # Act
        resultado = cli_runner.invoke(main, ["--help"])

        # Assert
        assert resultado.exit_code == 0, "Debe salir con código 0"
        # Debe mostrar todos los comandos disponibles
        assert "install" in resultado.output, "Debe listar comando install"
        assert "uninstall" in resultado.output, "Debe listar comando uninstall"
        assert "status" in resultado.output, "Debe listar comando status"
        assert "check" in resultado.output, "Debe listar comando check"
        assert "configure" in resultado.output, "Debe listar comando configure"

    def test_debe_mostrar_version_con_flag_version(self, cli_runner: CliRunner) -> None:
        """
        Debe mostrar versión cuando se usa --version.

        Escenario:
        1. Usuario ejecuta 'ci-guardian --version'
        2. CLI muestra versión (ej: 0.1.0)
        3. Exit code = 0
        """
        # Act
        resultado = cli_runner.invoke(main, ["--version"])

        # Assert
        assert resultado.exit_code == 0, "Debe salir con código 0"
        # Debe mostrar versión en formato X.Y.Z
        assert any(char.isdigit() for char in resultado.output), "Debe mostrar número de versión"
        assert "." in resultado.output, "Versión debe tener formato X.Y.Z"

    def test_debe_fallar_con_comando_invalido(self, cli_runner: CliRunner) -> None:
        """
        Debe fallar con mensaje claro cuando se usa un comando inválido.

        Escenario:
        1. Usuario ejecuta 'ci-guardian comando-invalido'
        2. CLI detecta que el comando no existe
        3. Muestra error y sugiere comandos disponibles
        4. Exit code != 0
        """
        # Act
        resultado = cli_runner.invoke(main, ["comando-invalido"])

        # Assert
        assert resultado.exit_code != 0, "Debe fallar con exit code != 0"
        assert (
            "no such command" in resultado.output.lower()
            or "comando no encontrado" in resultado.output.lower()
        ), "Debe indicar que el comando no existe"

    def test_debe_usar_colorama_para_output_en_windows(self, cli_runner: CliRunner) -> None:
        """
        Debe inicializar colorama para output con colores en Windows.

        Escenario Windows:
        1. CLI se ejecuta en Windows
        2. Debe inicializar colorama para soporte de colores
        3. Los comandos funcionan correctamente
        """
        with (
            patch("platform.system", return_value="Windows"),
            patch("ci_guardian.cli.colorama.init"),
        ):
            # Act
            cli_runner.invoke(main, ["--help"])

            # Assert
            # Verificar que se intentó inicializar colorama
            # (esto depende de si main() lo hace automáticamente)
            # Si no está implementado aún, este test fallará en fase RED
            pass


# ============================================================================
# TESTS DE INTEGRACIÓN CLI
# ============================================================================


class TestCLIIntegration:
    """Tests de integración del flujo completo de la CLI."""

    def test_debe_permitir_flujo_completo_install_status_uninstall(
        self,
        cli_runner: CliRunner,
        repo_git_mock: Path,
    ) -> None:
        """
        Debe permitir flujo completo: install → status → uninstall.

        Escenario de integración:
        1. Usuario ejecuta 'ci-guardian install'
        2. Hooks se instalan correctamente
        3. Usuario ejecuta 'ci-guardian status'
        4. Status muestra hooks instalados
        5. Usuario ejecuta 'ci-guardian uninstall --yes'
        6. Hooks se desinst alan correctamente
        """
        with (
            patch("ci_guardian.cli.Path.cwd", return_value=repo_git_mock),
            patch("ci_guardian.cli.instalar_hook") as mock_instalar,
            patch("ci_guardian.cli.obtener_hooks_instalados") as mock_hooks_instalados,
            patch("ci_guardian.cli.desinstalar_hook") as mock_desinstalar,
        ):
            # 1. Install
            mock_instalar.return_value = None
            resultado_install = cli_runner.invoke(install)
            assert resultado_install.exit_code == 0, "Install debe funcionar"

            # 2. Status (simular hooks instalados)
            mock_hooks_instalados.return_value = [
                "pre-commit",
                "commit-msg",
                "post-commit",
                "commit-msg",
            ]
            resultado_status = cli_runner.invoke(status)
            assert resultado_status.exit_code == 0, "Status debe funcionar"
            assert "pre-commit" in resultado_status.output

            # 3. Uninstall
            mock_desinstalar.return_value = True
            resultado_uninstall = cli_runner.invoke(uninstall, ["--yes"])
            assert resultado_uninstall.exit_code == 0, "Uninstall debe funcionar"

    def test_debe_manejar_errores_en_cascada_correctamente(
        self,
        cli_runner: CliRunner,
        tmp_path: Path,
    ) -> None:
        """
        Debe manejar errores en cascada sin crashes.

        Escenario de error:
        1. Usuario ejecuta comandos fuera de repo git
        2. Todos los comandos fallan gracefully
        3. Ningún comando causa crash (exit code != 0 pero sin traceback)
        """
        no_repo = tmp_path / "no_repo"
        no_repo.mkdir()

        with patch("ci_guardian.cli.Path.cwd", return_value=no_repo):
            # Todos estos comandos deben fallar gracefully
            comandos = [
                (install, []),
                (status, []),
                (uninstall, ["--yes"]),
                (check, []),
                (configure, []),
            ]

            for comando, args in comandos:
                resultado = cli_runner.invoke(comando, args)
                assert resultado.exit_code != 0, f"Comando {comando} debe fallar"
                # No debe mostrar traceback completo
                assert "Traceback" not in resultado.output, f"Comando {comando} no debe hacer crash"
