"""Tests para el hook post-commit de CI Guardian.

Este hook valida que el commit haya pasado por pre-commit (sistema de tokens)
y revierte commits hechos con --no-verify.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestPostCommitTokenValidation:
    """Tests para validación de token post-commit."""

    def test_debe_pasar_si_token_valido(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe permitir commit si token existe (flujo normal)."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        from ci_guardian.hooks.post_commit import main

        # Mock token válido (patchear donde se USA, no donde se DEFINE)
        with patch(
            "ci_guardian.hooks.post_commit.validar_y_consumir_token",
            return_value=True,
        ):
            # Act
            resultado = main()

        # Assert
        assert resultado == 0, "Debe retornar 0 si token es válido"

    def test_debe_revertir_commit_sin_token(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe revertir commit si token no existe (--no-verify usado)."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        from ci_guardian.hooks.post_commit import main

        # Mock token inválido (--no-verify usado)
        with patch(
            "ci_guardian.hooks.post_commit.validar_y_consumir_token",
            return_value=False,
        ):
            # Mock revertir_ultimo_commit exitoso
            with patch(
                "ci_guardian.hooks.post_commit.revertir_ultimo_commit",
                return_value=(True, "Commit revertido exitosamente"),
            ):
                # Act
                resultado = main()

        # Assert
        assert resultado == 1, "Debe retornar 1 si commit fue revertido"

    def test_debe_llamar_a_revertir_si_no_hay_token(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe llamar a revertir_ultimo_commit si no hay token."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        from ci_guardian.hooks.post_commit import main

        with patch(
            "ci_guardian.hooks.post_commit.validar_y_consumir_token",
            return_value=False,
        ):
            with patch(
                "ci_guardian.hooks.post_commit.revertir_ultimo_commit",
                return_value=(True, "Revertido"),
            ) as mock_revertir:
                # Act
                main()

        # Assert
        mock_revertir.assert_called_once_with(tmp_path)


class TestPostCommitRootCommit:
    """Tests para manejo de root commit (primer commit del repo)."""

    def test_debe_manejar_root_commit_sin_token(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe manejar root commit (primer commit) sin token."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        # Mock token inválido
        with patch(
            "ci_guardian.hooks.post_commit.validar_y_consumir_token",
            return_value=False,
        ):
            # Mock revertir_ultimo_commit que falla porque es root commit
            with patch(
                "ci_guardian.hooks.post_commit.revertir_ultimo_commit",
                return_value=(False, "No hay commits para revertir"),
            ):
                # Mock subprocess para git symbolic-ref (detectar branch)
                mock_symbolic = MagicMock()
                mock_symbolic.returncode = 0
                mock_symbolic.stdout = "refs/heads/master"

                # Mock subprocess para git update-ref (eliminar branch)
                mock_update = MagicMock()
                mock_update.returncode = 0

                with patch("subprocess.run", side_effect=[mock_symbolic, mock_update]):
                    # Act
                    from ci_guardian.hooks.post_commit import main

                    resultado = main()

        # Assert
        assert resultado == 1, "Debe retornar 1 después de revertir root commit"

    def test_debe_manejar_error_al_revertir_root_commit(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe manejar error al revertir root commit."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        with patch(
            "ci_guardian.hooks.post_commit.validar_y_consumir_token",
            return_value=False,
        ):
            with patch(
                "ci_guardian.hooks.post_commit.revertir_ultimo_commit",
                return_value=(False, "No hay commits para revertir"),
            ):
                # Mock git symbolic-ref que falla
                mock_symbolic = MagicMock()
                mock_symbolic.returncode = 1

                with patch("subprocess.run", return_value=mock_symbolic):
                    # Act
                    from ci_guardian.hooks.post_commit import main

                    resultado = main()

        # Assert
        assert resultado == 1, "Debe retornar 1 en caso de error"


class TestPostCommitErrorHandling:
    """Tests para manejo de errores del hook post-commit."""

    def test_debe_manejar_error_al_revertir_commit_normal(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe manejar error al revertir commit normal (no root)."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        with patch(
            "ci_guardian.hooks.post_commit.validar_y_consumir_token",
            return_value=False,
        ):
            # Mock revertir_ultimo_commit que falla por otro motivo
            with patch(
                "ci_guardian.hooks.post_commit.revertir_ultimo_commit",
                return_value=(False, "Error al ejecutar git reset"),
            ):
                # Act
                from ci_guardian.hooks.post_commit import main

                resultado = main()

        # Assert
        assert resultado == 1, "Debe retornar 1 si falla al revertir"

    def test_debe_manejar_value_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe manejar ValueError de validación."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        # Mock que lanza ValueError
        with patch(
            "ci_guardian.hooks.post_commit.validar_y_consumir_token",
            side_effect=ValueError("Error de validación"),
        ):
            # Act
            from ci_guardian.hooks.post_commit import main

            resultado = main()

        # Assert
        assert resultado == 1, "Debe retornar 1 en caso de ValueError"

    def test_debe_manejar_exception_generica(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe manejar excepciones genéricas."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        # Mock que lanza Exception
        with patch(
            "ci_guardian.hooks.post_commit.validar_y_consumir_token",
            side_effect=Exception("Error inesperado"),
        ):
            # Act
            from ci_guardian.hooks.post_commit import main

            resultado = main()

        # Assert
        assert resultado == 1, "Debe retornar 1 en caso de excepción"


class TestPostCommitMensajes:
    """Tests para mensajes de salida del hook post-commit."""

    def test_debe_mostrar_mensaje_de_bypass_detectado(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Debe mostrar mensaje claro cuando se detecta bypass."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        with patch(
            "ci_guardian.hooks.post_commit.validar_y_consumir_token",
            return_value=False,
        ):
            with patch(
                "ci_guardian.hooks.post_commit.revertir_ultimo_commit",
                return_value=(True, "Revertido"),
            ):
                # Act
                from ci_guardian.hooks.post_commit import main

                main()

        # Assert
        captured = capsys.readouterr()
        assert "🚨" in captured.err, "Debe mostrar emoji de alerta"
        assert "BYPASS DETECTADO" in captured.err.upper(), "Debe indicar bypass"
        assert "--no-verify" in captured.err, "Debe mencionar --no-verify"

    def test_debe_mostrar_instrucciones_para_rehacer_commit(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Debe mostrar instrucciones para rehacer commit sin --no-verify."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        with patch(
            "ci_guardian.hooks.post_commit.validar_y_consumir_token",
            return_value=False,
        ):
            with patch(
                "ci_guardian.hooks.post_commit.revertir_ultimo_commit",
                return_value=(True, "Revertido"),
            ):
                # Act
                from ci_guardian.hooks.post_commit import main

                main()

        # Assert
        captured = capsys.readouterr()
        assert "git commit" in captured.err, "Debe mostrar comando git commit"
        assert "💡" in captured.err, "Debe mostrar emoji de tip"

    def test_no_debe_mostrar_mensajes_si_token_valido(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """No debe mostrar mensajes de error si token es válido."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        with patch(
            "ci_guardian.hooks.post_commit.validar_y_consumir_token",
            return_value=True,
        ):
            # Act
            from ci_guardian.hooks.post_commit import main

            main()

        # Assert
        captured = capsys.readouterr()
        assert len(captured.err) == 0, "No debe mostrar mensajes de error en flujo normal"
        assert len(captured.out) == 0, "No debe mostrar mensajes en stdout en flujo normal"


class TestPostCommitIntegracion:
    """Tests de integración del hook post-commit."""

    def test_workflow_completo_commit_normal(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test de workflow completo para commit normal (con token)."""
        # Arrange - Simular commit normal que pasó por pre-commit
        monkeypatch.chdir(tmp_path)

        with patch(
            "ci_guardian.hooks.post_commit.validar_y_consumir_token",
            return_value=True,
        ) as mock_validar:
            # Act
            from ci_guardian.hooks.post_commit import main

            resultado = main()

        # Assert
        assert resultado == 0
        mock_validar.assert_called_once_with(tmp_path)

    def test_workflow_completo_commit_con_no_verify(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test de workflow completo para commit con --no-verify."""
        # Arrange - Simular commit con --no-verify (sin token)
        monkeypatch.chdir(tmp_path)

        with patch(
            "ci_guardian.hooks.post_commit.validar_y_consumir_token",
            return_value=False,
        ) as mock_validar:
            with patch(
                "ci_guardian.hooks.post_commit.revertir_ultimo_commit",
                return_value=(True, "Commit revertido"),
            ) as mock_revertir:
                # Act
                from ci_guardian.hooks.post_commit import main

                resultado = main()

        # Assert
        assert resultado == 1
        mock_validar.assert_called_once_with(tmp_path)
        mock_revertir.assert_called_once_with(tmp_path)

    def test_debe_usar_path_cwd_como_repo_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe usar Path.cwd() como repo_path."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        with patch(
            "ci_guardian.hooks.post_commit.validar_y_consumir_token",
            return_value=True,
        ) as mock_validar:
            # Act
            from ci_guardian.hooks.post_commit import main

            main()

        # Assert
        # Verificar que se llamó con tmp_path (que es el cwd)
        call_args = mock_validar.call_args[0][0]
        assert call_args == tmp_path, "Debe pasar Path.cwd() como repo_path"
