"""Tests para el hook pre-commit de CI Guardian.

Este hook ejecuta validaciones (Ruff, Black, Bandit) antes de cada commit
y genera un token anti --no-verify.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestPreCommitObtenerArchivos:
    """Tests para la función obtener_archivos_python_staged."""

    def test_debe_obtener_archivos_python_staged(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe obtener archivos Python desde git diff --cached."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        # Crear archivos de prueba
        (tmp_path / "main.py").write_text("print('main')")
        (tmp_path / "utils.py").write_text("print('utils')")

        # Mock subprocess.run para simular git diff --cached
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "main.py\nutils.py\n"

        with patch("subprocess.run", return_value=mock_result):
            from ci_guardian.hooks.pre_commit import obtener_archivos_python_staged

            archivos = obtener_archivos_python_staged(tmp_path)

        # Assert
        assert len(archivos) == 2
        assert any("main.py" in str(f) for f in archivos)
        assert any("utils.py" in str(f) for f in archivos)

    def test_debe_retornar_vacio_si_no_hay_archivos_staged(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe retornar lista vacía si no hay archivos staged."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        # Mock subprocess sin archivos
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""

        with patch("subprocess.run", return_value=mock_result):
            from ci_guardian.hooks.pre_commit import obtener_archivos_python_staged

            archivos = obtener_archivos_python_staged(tmp_path)

        # Assert
        assert archivos == []

    def test_debe_filtrar_solo_archivos_python(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe filtrar solo archivos .py."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        # Crear archivos de diferentes tipos
        (tmp_path / "main.py").write_text("python")
        (tmp_path / "README.md").write_text("readme")

        # Mock subprocess que retorna ambos
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "main.py\nREADME.md\n"

        with patch("subprocess.run", return_value=mock_result):
            from ci_guardian.hooks.pre_commit import obtener_archivos_python_staged

            archivos = obtener_archivos_python_staged(tmp_path)

        # Assert
        assert len(archivos) == 1
        assert archivos[0].suffix == ".py"

    def test_debe_manejar_git_diff_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe manejar error al ejecutar git diff."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        # Mock subprocess que falla
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "fatal: not a git repository"

        with patch("subprocess.run", return_value=mock_result):
            from ci_guardian.hooks.pre_commit import obtener_archivos_python_staged

            archivos = obtener_archivos_python_staged(tmp_path)

        # Assert
        assert archivos == [], "Debe retornar lista vacía en caso de error"

    def test_debe_manejar_timeout(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Debe manejar timeout al ejecutar git diff."""
        # Arrange
        import subprocess

        monkeypatch.chdir(tmp_path)

        # Mock subprocess que hace timeout (subprocess.TimeoutExpired, no TimeoutError)
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("git", 30)):
            from ci_guardian.hooks.pre_commit import obtener_archivos_python_staged

            archivos = obtener_archivos_python_staged(tmp_path)

        # Assert
        assert archivos == [], "Debe retornar lista vacía en caso de timeout"


class TestPreCommitMain:
    """Tests para la función main del hook pre-commit."""

    def test_debe_pasar_todas_las_validaciones(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe pasar si todas las validaciones son exitosas."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        from ci_guardian.hooks.pre_commit import main

        # Mock archivos staged
        with patch(
            "ci_guardian.hooks.pre_commit.obtener_archivos_python_staged",
            return_value=[Path("main.py")],
        ):
            # Mock validadores exitosos
            with patch(
                "ci_guardian.hooks.pre_commit.ejecutar_ruff", return_value=(True, "✓ Ruff OK")
            ):
                with patch(
                    "ci_guardian.hooks.pre_commit.ejecutar_black", return_value=(True, "✓ Black OK")
                ):
                    with patch(
                        "ci_guardian.hooks.pre_commit.ejecutar_bandit", return_value=(True, {})
                    ):
                        with patch(
                            "ci_guardian.hooks.pre_commit.generar_token_seguro",
                            return_value="token123",
                        ):
                            with patch("ci_guardian.hooks.pre_commit.guardar_token"):
                                # Act
                                resultado = main()

        # Assert
        assert resultado == 0, "Debe retornar 0 si todas las validaciones pasan"

    def test_debe_fallar_si_ruff_falla(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe rechazar commit si Ruff encuentra errores."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        from ci_guardian.hooks.pre_commit import main

        with patch(
            "ci_guardian.hooks.pre_commit.obtener_archivos_python_staged",
            return_value=[Path("main.py")],
        ):
            # Mock Ruff que falla
            with patch(
                "ci_guardian.hooks.pre_commit.ejecutar_ruff",
                return_value=(False, "❌ E501 line too long"),
            ):
                # Act
                resultado = main()

        # Assert
        assert resultado == 1, "Debe retornar 1 si Ruff falla"

    def test_debe_fallar_si_black_falla(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe rechazar commit si Black encuentra errores de formato."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        from ci_guardian.hooks.pre_commit import main

        with patch(
            "ci_guardian.hooks.pre_commit.obtener_archivos_python_staged",
            return_value=[Path("main.py")],
        ):
            with patch("ci_guardian.hooks.pre_commit.ejecutar_ruff", return_value=(True, "✓")):
                # Mock Black que falla
                with patch(
                    "ci_guardian.hooks.pre_commit.ejecutar_black",
                    return_value=(False, "❌ would reformat"),
                ):
                    # Act
                    resultado = main()

        # Assert
        assert resultado == 1, "Debe retornar 1 si Black falla"

    def test_debe_fallar_si_bandit_encuentra_vulnerabilidades_high(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe rechazar commit si Bandit encuentra vulnerabilidades HIGH."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        from ci_guardian.hooks.pre_commit import main

        bandit_results = {
            "metrics": {"_totals": {"HIGH": 2}},
            "results": [
                {
                    "issue_severity": "HIGH",
                    "filename": "main.py",
                    "line_number": 10,
                    "issue_text": "SQL injection vulnerability",
                }
            ],
        }

        with patch(
            "ci_guardian.hooks.pre_commit.obtener_archivos_python_staged",
            return_value=[Path("main.py")],
        ):
            with patch("ci_guardian.hooks.pre_commit.ejecutar_ruff", return_value=(True, "✓")):
                with patch("ci_guardian.hooks.pre_commit.ejecutar_black", return_value=(True, "✓")):
                    # Mock Bandit con vulnerabilidades HIGH
                    with patch(
                        "ci_guardian.hooks.pre_commit.ejecutar_bandit",
                        return_value=(False, bandit_results),
                    ):
                        # Act
                        resultado = main()

        # Assert
        assert resultado == 1, "Debe retornar 1 si Bandit encuentra vulnerabilidades HIGH"

    def test_debe_permitir_commit_sin_archivos_python(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe permitir commit si no hay archivos Python staged."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        from ci_guardian.hooks.pre_commit import main

        with patch(
            "ci_guardian.hooks.pre_commit.obtener_archivos_python_staged",
            return_value=[],
        ):
            with patch(
                "ci_guardian.hooks.pre_commit.generar_token_seguro", return_value="token123"
            ):
                with patch("ci_guardian.hooks.pre_commit.guardar_token"):
                    # Act
                    resultado = main()

        # Assert
        assert resultado == 0, "Debe permitir commit sin archivos Python"

    def test_debe_generar_token_si_no_hay_archivos_python(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe generar token incluso si no hay archivos Python staged."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        from ci_guardian.hooks.pre_commit import main

        with patch(
            "ci_guardian.hooks.pre_commit.obtener_archivos_python_staged",
            return_value=[],
        ):
            with patch(
                "ci_guardian.hooks.pre_commit.generar_token_seguro", return_value="token"
            ) as mock_generar:
                with patch("ci_guardian.hooks.pre_commit.guardar_token") as mock_guardar:
                    # Act
                    main()

        # Assert
        mock_generar.assert_called_once()
        mock_guardar.assert_called_once()

    def test_debe_generar_token_solo_si_todas_las_validaciones_pasan(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe generar token SOLO si todas las validaciones pasan."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        from ci_guardian.hooks.pre_commit import main

        with patch(
            "ci_guardian.hooks.pre_commit.obtener_archivos_python_staged",
            return_value=[Path("main.py")],
        ):
            # Ruff falla
            with patch("ci_guardian.hooks.pre_commit.ejecutar_ruff", return_value=(False, "error")):
                with patch("ci_guardian.hooks.pre_commit.generar_token_seguro") as mock_generar:
                    # Act
                    main()

        # Assert
        mock_generar.assert_not_called(), "NO debe generar token si Ruff falla"

    def test_debe_omitir_bandit_si_no_esta_instalado(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe omitir Bandit si no está instalado."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        from ci_guardian.hooks.pre_commit import main

        bandit_error = {"error": "bandit no está instalado"}

        with patch(
            "ci_guardian.hooks.pre_commit.obtener_archivos_python_staged",
            return_value=[Path("main.py")],
        ):
            with patch("ci_guardian.hooks.pre_commit.ejecutar_ruff", return_value=(True, "✓")):
                with patch("ci_guardian.hooks.pre_commit.ejecutar_black", return_value=(True, "✓")):
                    with patch(
                        "ci_guardian.hooks.pre_commit.ejecutar_bandit",
                        return_value=(False, bandit_error),
                    ):
                        with patch(
                            "ci_guardian.hooks.pre_commit.generar_token_seguro",
                            return_value="token",
                        ):
                            with patch("ci_guardian.hooks.pre_commit.guardar_token"):
                                # Act
                                resultado = main()

        # Assert
        assert resultado == 0, "Debe pasar si Bandit no está instalado (warning only)"


class TestPreCommitErrorHandling:
    """Tests para manejo de errores del hook pre-commit."""

    def test_debe_manejar_value_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe manejar ValueError de validación."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        from ci_guardian.hooks.pre_commit import main

        # Mock que lanza ValueError
        with patch(
            "ci_guardian.hooks.pre_commit.obtener_archivos_python_staged",
            side_effect=ValueError("Error de validación"),
        ):
            # Act
            resultado = main()

        # Assert
        assert resultado == 1, "Debe retornar 1 en caso de ValueError"

    def test_debe_manejar_exception_generica(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe manejar excepciones genéricas."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        from ci_guardian.hooks.pre_commit import main

        # Mock que lanza Exception
        with patch(
            "ci_guardian.hooks.pre_commit.obtener_archivos_python_staged",
            side_effect=Exception("Error inesperado"),
        ):
            # Act
            resultado = main()

        # Assert
        assert resultado == 1, "Debe retornar 1 en caso de excepción"


class TestPreCommitIntegracion:
    """Tests de integración del hook pre-commit."""

    def test_workflow_completo_exitoso(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test de workflow completo exitoso."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        from ci_guardian.hooks.pre_commit import main

        # Simular workflow completo
        with patch(
            "ci_guardian.hooks.pre_commit.obtener_archivos_python_staged",
            return_value=[Path("main.py")],
        ) as mock_archivos:
            with patch(
                "ci_guardian.hooks.pre_commit.ejecutar_ruff", return_value=(True, "✓")
            ) as mock_ruff:
                with patch(
                    "ci_guardian.hooks.pre_commit.ejecutar_black", return_value=(True, "✓")
                ) as mock_black:
                    with patch(
                        "ci_guardian.hooks.pre_commit.ejecutar_bandit", return_value=(True, {})
                    ) as mock_bandit:
                        with patch(
                            "ci_guardian.hooks.pre_commit.generar_token_seguro", return_value="tok"
                        ) as mock_gen:
                            with patch("ci_guardian.hooks.pre_commit.guardar_token") as mock_save:
                                # Act
                                resultado = main()

        # Assert
        assert resultado == 0
        # Verificar que se llamaron todas las funciones
        mock_archivos.assert_called_once()
        mock_ruff.assert_called_once()
        mock_black.assert_called_once()
        mock_bandit.assert_called_once()
        mock_gen.assert_called_once()
        mock_save.assert_called_once()

    def test_debe_usar_path_cwd_como_repo_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe usar Path.cwd() como repo_path."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        from ci_guardian.hooks.pre_commit import main

        with patch(
            "ci_guardian.hooks.pre_commit.obtener_archivos_python_staged",
            return_value=[],
        ) as mock_archivos:
            with patch("ci_guardian.hooks.pre_commit.generar_token_seguro", return_value="token"):
                with patch("ci_guardian.hooks.pre_commit.guardar_token") as mock_guardar:
                    # Act
                    main()

        # Assert
        # Verificar que se llamó con tmp_path (que es el cwd)
        call_args = mock_archivos.call_args[0][0]
        assert call_args == tmp_path, "Debe pasar Path.cwd() como repo_path"

        call_args_guardar = mock_guardar.call_args[0][0]
        assert call_args_guardar == tmp_path, "Debe pasar Path.cwd() a guardar_token"
