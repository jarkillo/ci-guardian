"""Tests para el hook pre-push de CI Guardian.

Este módulo implementa tests para el hook que causó el bug crítico v0.1.0.
Los tests se escriben PRIMERO siguiendo TDD estricto.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestPrePushHookExecution:
    """Tests para la ejecución del hook pre-push."""

    def test_debe_ejecutar_pytest_exitosamente_cuando_tests_pasan(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe ejecutar pytest y permitir push si tests pasan."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        # Mock subprocess.run para simular pytest exitoso
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "===== 10 passed in 1.23s ====="
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            # Mock venv validator (pre_push lo llama ahora)
            with patch(
                "ci_guardian.hooks.pre_push.esta_venv_activo", return_value=(True, "✓ Venv activo")
            ):
                # Act
                from ci_guardian.hooks.pre_push import main

                resultado = main()

                # Assert
                assert resultado == 0, "Debe retornar 0 cuando tests pasan"
                mock_run.assert_called_once()
                # Verificar que se llamó a pytest
                args = mock_run.call_args[0][0]
                assert "pytest" in args

    def test_debe_fallar_cuando_pytest_falla(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe rechazar push si pytest falla."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        # Mock subprocess.run para simular pytest fallando
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "===== 5 failed, 5 passed in 2.34s ====="
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            # Mock venv validator
            with patch(
                "ci_guardian.hooks.pre_push.esta_venv_activo", return_value=(True, "✓ Venv activo")
            ):
                # Act
                from ci_guardian.hooks.pre_push import main

                resultado = main()

                # Assert
                assert resultado == 1, "Debe retornar 1 cuando tests fallan"

    # NOTE: test_debe_permitir_skip_con_variable_entorno ELIMINADO en v0.3.1
    # CI_GUARDIAN_SKIP_TESTS fue removido porque contradecía el objetivo de seguridad.
    # Para deshabilitar validadores temporalmente, usar .ci-guardian.yaml con config protegida.

    def test_debe_ejecutar_github_actions_localmente_si_configurado(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe ejecutar GitHub Actions localmente usando act."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        # Crear config que habilita GitHub Actions
        config_file = tmp_path / ".ci-guardian.yaml"
        config_file.write_text(
            """
hooks:
  pre-push:
    enabled: true
    validadores:
      - tests
      - github-actions
"""
        )

        # Mock subprocess.run para pytest
        mock_pytest_result = MagicMock()
        mock_pytest_result.returncode = 0
        mock_pytest_result.stdout = "===== 10 passed ====="
        mock_pytest_result.stderr = ""

        # Mock ejecutar_workflow para GitHub Actions
        with patch("subprocess.run", return_value=mock_pytest_result):
            with patch(
                "ci_guardian.hooks.pre_push._ejecutar_github_actions",
                return_value=(True, "✓ GitHub Actions pasaron"),
            ):
                # Mock venv validator
                with patch(
                    "ci_guardian.hooks.pre_push.esta_venv_activo",
                    return_value=(True, "✓ Venv activo"),
                ):
                    # Act
                    from ci_guardian.hooks.pre_push import main

                    resultado = main()

                    # Assert
                    assert resultado == 0, "Debe retornar 0 cuando todo pasa"


class TestPrePushConfiguration:
    """Tests para la configuración del hook pre-push."""

    def test_debe_cargar_configuracion_desde_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe cargar configuración desde .ci-guardian.yaml."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        config_file = tmp_path / ".ci-guardian.yaml"
        config_file.write_text(
            """
hooks:
  pre-push:
    enabled: true
    validadores:
      - tests
"""
        )

        # Act
        from ci_guardian.core.config import cargar_configuracion

        config = cargar_configuracion(tmp_path)

        # Assert
        assert config is not None, "Debe cargar configuración"
        assert "pre-push" in config.hooks
        assert config.hooks["pre-push"].enabled is True

    def test_debe_usar_configuracion_por_defecto_si_no_existe_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe usar configuración por defecto si no existe .ci-guardian.yaml."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        # No crear archivo de configuración

        # Act
        from ci_guardian.core.config import cargar_configuracion

        config = cargar_configuracion(tmp_path)

        # Assert
        assert config is not None, "Debe retornar configuración por defecto"
        assert "pre-push" in config.hooks


class TestPrePushSecurity:
    """Tests de seguridad para el hook pre-push."""

    def test_no_debe_usar_shell_true_con_comandos(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe usar subprocess de forma segura (shell=False)."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        # Mock subprocess.run
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            # Mock venv validator
            with patch(
                "ci_guardian.hooks.pre_push.esta_venv_activo", return_value=(True, "✓ Venv activo")
            ):
                # Act
                from ci_guardian.hooks.pre_push import main

                main()

                # Assert - verificar que NO se usa shell=True
                for call in mock_run.call_args_list:
                    kwargs = call[1]
                    assert (
                        kwargs.get("shell", False) is False
                    ), "NUNCA debe usar shell=True (previene command injection)"

    def test_debe_manejar_timeout_en_ejecucion(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe manejar timeout en ejecución de pytest."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("pytest", 60)):
            # Mock venv validator
            with patch(
                "ci_guardian.hooks.pre_push.esta_venv_activo", return_value=(True, "✓ Venv activo")
            ):
                # Act
                from ci_guardian.hooks.pre_push import main

                resultado = main()

                # Assert
                assert resultado == 1, "Debe fallar si hay timeout"


class TestPrePushCrossPlatform:
    """Tests de compatibilidad multiplataforma."""

    @pytest.mark.skipif(
        __import__("platform").system() != "Windows",
        reason="Test específico de Windows",
    )
    def test_debe_funcionar_en_windows(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe funcionar correctamente en Windows."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "===== 10 passed ====="
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            # Mock venv validator
            with patch(
                "ci_guardian.hooks.pre_push.esta_venv_activo", return_value=(True, "✓ Venv activo")
            ):
                # Act
                from ci_guardian.hooks.pre_push import main

                resultado = main()

                # Assert
                assert resultado == 0, "Debe funcionar en Windows"

    @pytest.mark.skipif(
        __import__("platform").system() != "Linux",
        reason="Test específico de Linux",
    )
    def test_debe_funcionar_en_linux(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Debe funcionar correctamente en Linux."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "===== 10 passed ====="
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            # Mock venv validator
            with patch(
                "ci_guardian.hooks.pre_push.esta_venv_activo", return_value=(True, "✓ Venv activo")
            ):
                # Act
                from ci_guardian.hooks.pre_push import main

                resultado = main()

                # Assert
                assert resultado == 0, "Debe funcionar en Linux"


class TestPrePushErrorHandling:
    """Tests de manejo de errores."""

    def test_debe_manejar_pytest_no_instalado(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe manejar el caso donde pytest no está instalado."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        with patch("subprocess.run", side_effect=FileNotFoundError("pytest not found")):
            # Mock venv validator
            with patch(
                "ci_guardian.hooks.pre_push.esta_venv_activo", return_value=(True, "✓ Venv activo")
            ):
                # Act
                from ci_guardian.hooks.pre_push import main

                resultado = main()

                # Assert
                assert resultado == 1, "Debe fallar si pytest no está instalado"

    def test_debe_proporcionar_mensaje_claro_al_fallar(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        """Debe proporcionar mensaje claro cuando las validaciones fallan."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "FAILED tests/test_example.py::test_func"
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            # Mock venv validator
            with patch(
                "ci_guardian.hooks.pre_push.esta_venv_activo", return_value=(True, "✓ Venv activo")
            ):
                # Act
                from ci_guardian.hooks.pre_push import main

                resultado = main()

                # Assert
                captured = capsys.readouterr()
                assert resultado == 1, "Debe fallar"
                assert (
                    "tests" in captured.out.lower() or "failed" in captured.out.lower()
                ), "Debe mostrar mensaje claro sobre tests fallidos"
