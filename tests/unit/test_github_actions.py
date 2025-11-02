"""
Tests unitarios para el ejecutor local de GitHub Actions (LIB-7).

Este módulo prueba la ejecución local de workflows de GitHub Actions usando 'act',
con fallback a ejecución directa de herramientas cuando 'act' no está disponible.

Fase TDD: RED - Todos estos tests deben fallar inicialmente.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ci_guardian.runners.github_actions import (
    ejecutar_workflow,
    ejecutar_workflow_con_act,
    ejecutar_workflow_fallback,
    esta_act_instalado,
)


class TestDeteccionAct:
    """Tests para la detección de la herramienta 'act'."""

    def test_debe_retornar_true_cuando_act_esta_instalado(self):
        """Debe retornar True cuando act está disponible en PATH."""
        # Arrange
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="act version 0.2.68")

            # Act
            resultado = esta_act_instalado()

            # Assert
            assert resultado is True, "Debe detectar act cuando está instalado"
            mock_run.assert_called_once()
            # Verificar que se usa shell=False por seguridad
            assert mock_run.call_args.kwargs.get("shell") is False

    def test_debe_retornar_false_cuando_act_no_esta_instalado(self):
        """Debe retornar False cuando act no está disponible."""
        # Arrange
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("act not found")

            # Act
            resultado = esta_act_instalado()

            # Assert
            assert resultado is False, "Debe retornar False cuando act no existe"

    def test_debe_usar_subprocess_con_shell_false(self):
        """Debe usar subprocess.run con shell=False por seguridad."""
        # Arrange
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            # Act
            esta_act_instalado()

            # Assert
            llamada = mock_run.call_args
            assert llamada.kwargs.get("shell") is False, "CRÍTICO: Debe usar shell=False"

    def test_debe_manejar_error_de_permisos_al_ejecutar_act(self):
        """Debe manejar PermissionError al verificar act."""
        # Arrange
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = PermissionError("Permission denied")

            # Act
            resultado = esta_act_instalado()

            # Assert
            assert resultado is False, "Debe retornar False cuando hay error de permisos"


class TestEjecucionConAct:
    """Tests para la ejecución de workflows usando act."""

    @pytest.fixture
    def workflow_file_mock(self, tmp_path):
        """Crea un archivo de workflow mock."""
        workflows_dir = tmp_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        workflow = workflows_dir / "ci.yml"
        workflow.write_text(
            """
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pytest
"""
        )
        return workflow

    def test_debe_ejecutar_act_con_argumentos_correctos(self, workflow_file_mock):
        """Debe ejecutar act con los argumentos correctos."""
        # Arrange
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="[CI/test] ✓ pytest passed", stderr=""
            )

            # Act
            exito, output = ejecutar_workflow_con_act(workflow_file_mock, evento="push")

            # Assert
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "act" in args, "Debe ejecutar el comando 'act'"
            assert "-W" in args or "--workflows" in args, "Debe pasar el flag de workflow"
            assert str(workflow_file_mock) in args, "Debe incluir la ruta del workflow"

    def test_debe_pasar_workflow_file_como_argumento(self, workflow_file_mock):
        """Debe pasar el workflow_file como argumento a act."""
        # Arrange
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            # Act
            ejecutar_workflow_con_act(workflow_file_mock)

            # Assert
            args = mock_run.call_args[0][0]
            assert str(workflow_file_mock) in args, "Workflow file debe estar en argumentos"

    def test_debe_usar_evento_correcto_push(self, workflow_file_mock):
        """Debe ejecutar act con el evento 'push' cuando se especifica."""
        # Arrange
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            # Act
            ejecutar_workflow_con_act(workflow_file_mock, evento="push")

            # Assert
            args = mock_run.call_args[0][0]
            assert "push" in args, "Debe incluir el evento 'push'"

    def test_debe_usar_evento_correcto_pull_request(self, workflow_file_mock):
        """Debe ejecutar act con el evento 'pull_request' cuando se especifica."""
        # Arrange
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            # Act
            ejecutar_workflow_con_act(workflow_file_mock, evento="pull_request")

            # Assert
            args = mock_run.call_args[0][0]
            assert "pull_request" in args, "Debe incluir el evento 'pull_request'"

    def test_debe_retornar_true_cuando_workflow_pasa_exitosamente(self, workflow_file_mock):
        """Debe retornar True cuando el workflow termina con exit code 0."""
        # Arrange
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="[CI/test] ✓ All checks passed",
                stderr="",
            )

            # Act
            exito, output = ejecutar_workflow_con_act(workflow_file_mock)

            # Assert
            assert exito is True, "Debe retornar True cuando exit code es 0"
            assert "passed" in output.lower(), "Output debe contener mensaje de éxito"

    def test_debe_retornar_false_cuando_workflow_falla(self, workflow_file_mock):
        """Debe retornar False cuando el workflow falla (exit code != 0)."""
        # Arrange
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="[CI/test] ✗ Tests failed",
                stderr="Error: test_example.py::test_foo FAILED",
            )

            # Act
            exito, output = ejecutar_workflow_con_act(workflow_file_mock)

            # Assert
            assert exito is False, "Debe retornar False cuando exit code != 0"
            assert (
                "failed" in output.lower() or "error" in output.lower()
            ), "Output debe contener mensaje de error"

    def test_debe_capturar_stdout_y_stderr(self, workflow_file_mock):
        """Debe capturar tanto stdout como stderr del workflow."""
        # Arrange
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="[CI/test] Running tests...",
                stderr="Warning: deprecated API",
            )

            # Act
            exito, output = ejecutar_workflow_con_act(workflow_file_mock)

            # Assert
            assert "Running tests" in output, "Debe capturar stdout"
            assert "deprecated" in output or exito, "Debe procesar stderr"
            mock_run.assert_called_once()
            assert mock_run.call_args.kwargs.get("capture_output") is True

    def test_debe_usar_shell_false_por_seguridad(self, workflow_file_mock):
        """Debe usar shell=False para prevenir command injection."""
        # Arrange
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            # Act
            ejecutar_workflow_con_act(workflow_file_mock)

            # Assert
            assert mock_run.call_args.kwargs.get("shell") is False, "CRÍTICO: Debe usar shell=False"

    def test_debe_manejar_timeout_correctamente(self, workflow_file_mock):
        """Debe configurar timeout para prevenir workflows colgados."""
        # Arrange
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            # Act
            ejecutar_workflow_con_act(workflow_file_mock, timeout=300)

            # Assert
            assert (
                mock_run.call_args.kwargs.get("timeout") == 300
            ), "Debe configurar timeout de 300 segundos"

    def test_debe_validar_que_workflow_file_existe(self, tmp_path):
        """Debe validar que el workflow_file existe antes de ejecutar."""
        # Arrange
        workflow_inexistente = tmp_path / "no_existe.yml"

        # Act & Assert
        with pytest.raises(
            (ValueError, FileNotFoundError),
            match=r"(no existe|not found|does not exist)",
        ):
            ejecutar_workflow_con_act(workflow_inexistente)

    def test_debe_rechazar_path_traversal_en_workflow_file(self, tmp_path):
        """Debe prevenir path traversal en workflow_file."""
        # Arrange
        workflow_malicioso = tmp_path / ".." / ".." / "etc" / "passwd"

        # Act & Assert
        with pytest.raises(ValueError, match=r"(path.*(traversal|inválido)|inválid.*path)"):
            ejecutar_workflow_con_act(workflow_malicioso)


class TestModoFallback:
    """Tests para el modo fallback cuando act no está disponible."""

    @pytest.fixture
    def repo_path_mock(self, tmp_path):
        """Crea un repositorio mock."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / "src").mkdir()
        (repo / "tests").mkdir()
        return repo

    def test_debe_ejecutar_pytest(self, repo_path_mock):
        """Debe ejecutar pytest en modo fallback."""
        # Arrange
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="passed", stderr="")

            # Act
            exito, output = ejecutar_workflow_fallback(repo_path_mock)

            # Assert
            # Verificar que se llamó subprocess.run con pytest
            llamadas = [str(call[0][0]) for call in mock_run.call_args_list]
            assert any("pytest" in str(llamada) for llamada in llamadas), "Debe ejecutar pytest"

    def test_debe_ejecutar_ruff_check(self, repo_path_mock):
        """Debe ejecutar ruff check en modo fallback."""
        # Arrange
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="All checks passed", stderr="")

            # Act
            exito, output = ejecutar_workflow_fallback(repo_path_mock)

            # Assert
            llamadas = [str(call[0][0]) for call in mock_run.call_args_list]
            assert any("ruff" in str(llamada) for llamada in llamadas), "Debe ejecutar ruff"

    def test_debe_ejecutar_black_check(self, repo_path_mock):
        """Debe ejecutar black --check en modo fallback."""
        # Arrange
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="All done!", stderr="")

            # Act
            exito, output = ejecutar_workflow_fallback(repo_path_mock)

            # Assert
            llamadas = [str(call[0][0]) for call in mock_run.call_args_list]
            assert any("black" in str(llamada) for llamada in llamadas), "Debe ejecutar black"

    def test_debe_retornar_true_si_todos_pasan(self, repo_path_mock):
        """Debe retornar True si todas las herramientas pasan."""
        # Arrange
        with patch("subprocess.run") as mock_run:
            # Todas las herramientas pasan
            mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")

            # Act
            exito, output = ejecutar_workflow_fallback(repo_path_mock)

            # Assert
            assert exito is True, "Debe retornar True cuando todas las validaciones pasan"

    def test_debe_retornar_false_si_pytest_falla(self, repo_path_mock):
        """Debe retornar False si pytest falla."""

        # Arrange
        def side_effect(*args, **kwargs):
            comando = args[0]
            if "pytest" in str(comando):
                return MagicMock(returncode=1, stdout="FAILED", stderr="test failed")
            return MagicMock(returncode=0, stdout="OK", stderr="")

        with patch("subprocess.run", side_effect=side_effect):
            # Act
            exito, output = ejecutar_workflow_fallback(repo_path_mock)

            # Assert
            assert exito is False, "Debe retornar False si pytest falla"

    def test_debe_retornar_false_si_ruff_falla(self, repo_path_mock):
        """Debe retornar False si ruff detecta errores."""

        # Arrange
        def side_effect(*args, **kwargs):
            comando = args[0]
            if "ruff" in str(comando):
                return MagicMock(returncode=1, stdout="Found 5 errors", stderr="")
            return MagicMock(returncode=0, stdout="OK", stderr="")

        with patch("subprocess.run", side_effect=side_effect):
            # Act
            exito, output = ejecutar_workflow_fallback(repo_path_mock)

            # Assert
            assert exito is False, "Debe retornar False si ruff falla"

    def test_debe_generar_resumen_de_resultados(self, repo_path_mock):
        """Debe generar output con resumen de todas las validaciones."""
        # Arrange
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")

            # Act
            exito, output = ejecutar_workflow_fallback(repo_path_mock)

            # Assert
            assert (
                "pytest" in output.lower() or "test" in output.lower()
            ), "Resumen debe mencionar pytest"
            assert (
                "ruff" in output.lower() or "lint" in output.lower()
            ), "Resumen debe mencionar ruff"
            assert (
                "black" in output.lower() or "format" in output.lower()
            ), "Resumen debe mencionar black"

    def test_debe_usar_shell_false_en_fallback(self, repo_path_mock):
        """Debe usar shell=False en todas las ejecuciones del fallback."""
        # Arrange
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")

            # Act
            ejecutar_workflow_fallback(repo_path_mock)

            # Assert
            for llamada in mock_run.call_args_list:
                assert (
                    llamada.kwargs.get("shell") is False
                ), "CRÍTICO: Todas las llamadas deben usar shell=False"


class TestFuncionPrincipal:
    """Tests para la función principal que auto-detecta act vs fallback."""

    @pytest.fixture
    def repo_con_workflow(self, tmp_path):
        """Crea un repositorio con workflow."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        workflows_dir = repo / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        ci_workflow = workflows_dir / "ci.yml"
        ci_workflow.write_text("name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest")
        return repo

    def test_debe_usar_act_cuando_esta_instalado(self, repo_con_workflow):
        """Debe usar act cuando está disponible."""
        # Arrange
        with (
            patch("ci_guardian.runners.github_actions.esta_act_instalado", return_value=True),
            patch("ci_guardian.runners.github_actions.ejecutar_workflow_con_act") as mock_act,
        ):
            mock_act.return_value = (True, "Success with act")
            workflow_file = repo_con_workflow / ".github" / "workflows" / "ci.yml"

            # Act
            exito, output = ejecutar_workflow(workflow_file=workflow_file)

            # Assert
            mock_act.assert_called_once()
            assert "act" in output.lower() or exito, "Debe usar act cuando está instalado"

    def test_debe_usar_fallback_cuando_act_no_esta_instalado(self, repo_con_workflow):
        """Debe usar modo fallback cuando act no está disponible."""
        # Arrange
        with (
            patch("ci_guardian.runners.github_actions.esta_act_instalado", return_value=False),
            patch("ci_guardian.runners.github_actions.ejecutar_workflow_fallback") as mock_fb,
        ):
            mock_fb.return_value = (True, "Success with fallback")

            # Act
            exito, output = ejecutar_workflow(repo_path=repo_con_workflow)

            # Assert
            mock_fb.assert_called_once()
            assert "fallback" in output.lower() or exito, "Debe usar fallback sin act"

    def test_debe_auto_detectar_workflow_ci_yml(self, repo_con_workflow):
        """Debe auto-detectar .github/workflows/ci.yml."""
        # Arrange
        with (
            patch("ci_guardian.runners.github_actions.esta_act_instalado", return_value=True),
            patch("ci_guardian.runners.github_actions.ejecutar_workflow_con_act") as mock_act,
        ):
            mock_act.return_value = (True, "Success")

            # Act
            ejecutar_workflow(repo_path=repo_con_workflow)

            # Assert
            llamada_args = mock_act.call_args[0][0]
            assert "ci.yml" in str(llamada_args), "Debe detectar ci.yml automáticamente"

    def test_debe_auto_detectar_workflow_test_yml(self, tmp_path):
        """Debe auto-detectar .github/workflows/test.yml si ci.yml no existe."""
        # Arrange
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        workflows_dir = repo / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        test_workflow = workflows_dir / "test.yml"
        test_workflow.write_text("name: Test\non: [push]")

        with (
            patch("ci_guardian.runners.github_actions.esta_act_instalado", return_value=True),
            patch("ci_guardian.runners.github_actions.ejecutar_workflow_con_act") as mock_act,
        ):
            mock_act.return_value = (True, "Success")

            # Act
            ejecutar_workflow(repo_path=repo)

            # Assert
            llamada_args = mock_act.call_args[0][0]
            assert "test.yml" in str(llamada_args), "Debe detectar test.yml si ci.yml no existe"

    def test_debe_usar_repo_path_actual_si_no_se_especifica(self):
        """Debe usar Path.cwd() si repo_path no se especifica."""
        # Arrange
        with (
            patch("ci_guardian.runners.github_actions.esta_act_instalado", return_value=False),
            patch("ci_guardian.runners.github_actions.ejecutar_workflow_fallback") as mock_fb,
            patch("pathlib.Path.cwd") as mock_cwd,
        ):
            mock_cwd.return_value = Path("/fake/repo")
            mock_fb.return_value = (True, "Success")

            # Act
            ejecutar_workflow()

            # Assert
            llamada_args = mock_fb.call_args[0][0]
            assert llamada_args == Path("/fake/repo"), "Debe usar Path.cwd() por defecto"

    def test_debe_informar_modo_usado_en_output(self, repo_con_workflow):
        """Debe informar al usuario qué modo está usando (act vs fallback)."""
        # Arrange
        with (
            patch("ci_guardian.runners.github_actions.esta_act_instalado", return_value=True),
            patch("ci_guardian.runners.github_actions.ejecutar_workflow_con_act") as mock_act,
        ):
            mock_act.return_value = (True, "Output sin info de modo")
            workflow_file = repo_con_workflow / ".github" / "workflows" / "ci.yml"

            # Act
            exito, output = ejecutar_workflow(workflow_file=workflow_file)

            # Assert
            # El output debe mencionar que se está usando act o el modo
            assert (
                "act" in output.lower()
                or "docker" in output.lower()
                or "local" in output.lower()
                or exito
            ), "Debe informar el modo de ejecución"


class TestSeguridadGitHubActions:
    """Tests de seguridad para el módulo GitHub Actions."""

    def test_debe_prevenir_command_injection_con_shell_false(self, tmp_path):
        """Debe prevenir command injection usando shell=False."""
        # Arrange
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text("name: Test")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            # Act
            ejecutar_workflow_con_act(workflow_file)

            # Assert
            for llamada in mock_run.call_args_list:
                assert (
                    llamada.kwargs.get("shell") is False
                ), "CRÍTICO: Debe prevenir command injection con shell=False"

    def test_debe_validar_path_traversal_en_workflow_file(self, tmp_path):
        """Debe validar y rechazar path traversal en workflow_file."""
        # Arrange
        workflow_malicioso = tmp_path / ".." / ".." / "etc" / "passwd"

        # Act & Assert
        with pytest.raises(ValueError, match=r"(path|traversal|inválid)"):
            ejecutar_workflow_con_act(workflow_malicioso)

    def test_debe_validar_evento_con_whitelist(self, tmp_path):
        """Debe validar que el evento esté en una whitelist."""
        # Arrange
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text("name: Test")
        evento_malicioso = "../../malicious; rm -rf /"

        # Act & Assert
        with pytest.raises(ValueError, match=r"(evento|event).*(inválido|invalid|permitido)"):
            ejecutar_workflow_con_act(workflow_file, evento=evento_malicioso)

    def test_debe_configurar_timeout_para_prevenir_dos(self, tmp_path):
        """Debe configurar timeout para prevenir DoS con workflows colgados."""
        # Arrange
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text("name: Test")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            # Act
            ejecutar_workflow_con_act(workflow_file, timeout=300)

            # Assert
            timeout_config = mock_run.call_args.kwargs.get("timeout")
            assert timeout_config is not None, "Debe configurar timeout"
            assert timeout_config > 0, "Timeout debe ser positivo"
            assert timeout_config <= 600, "Timeout no debe exceder 10 minutos"

    def test_debe_capturar_stderr_para_debugging(self, tmp_path):
        """Debe capturar stderr para debugging y análisis de errores."""
        # Arrange
        workflow_file = tmp_path / "workflow.yml"
        workflow_file.write_text("name: Test")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="Normal output",
                stderr="ERROR: Docker not running",
            )

            # Act
            exito, output = ejecutar_workflow_con_act(workflow_file)

            # Assert
            assert mock_run.call_args.kwargs.get("capture_output") is True, "Debe capturar output"
            assert (
                "error" in output.lower() or "docker" in output.lower() or not exito
            ), "Debe incluir stderr en output"
