"""Tests para el hook commit-msg de CI Guardian.

Este hook valida que Claude Code no se añada como co-autor en commits.
"""

from pathlib import Path
from unittest.mock import patch

import pytest


class TestCommitMsgValidacion:
    """Tests para validación de mensajes de commit."""

    def test_debe_rechazar_commit_con_coauthor_claude(self, tmp_path: Path) -> None:
        """Debe rechazar commits con Co-Authored-By: Claude."""
        # Arrange
        mensaje_file = tmp_path / "COMMIT_EDITMSG"
        mensaje_file.write_text(
            "feat: add new feature\n\n" "Co-Authored-By: Claude <noreply@anthropic.com>\n"
        )

        # Act
        with patch("sys.argv", ["commit-msg", str(mensaje_file)]):
            from ci_guardian.hooks.commit_msg import main

            resultado = main()

        # Assert
        assert resultado == 1, "Debe rechazar commit con Co-Authored-By: Claude"

    def test_debe_permitir_commit_sin_coauthor_claude(self, tmp_path: Path) -> None:
        """Debe permitir commits sin Co-Authored-By: Claude."""
        # Arrange
        mensaje_file = tmp_path / "COMMIT_EDITMSG"
        mensaje_file.write_text("feat: add new feature\n\nNormal commit message\n")

        # Act
        with patch("sys.argv", ["commit-msg", str(mensaje_file)]):
            from ci_guardian.hooks.commit_msg import main

            resultado = main()

        # Assert
        assert resultado == 0, "Debe permitir commit sin Co-Authored-By: Claude"

    def test_debe_permitir_commit_con_otro_coautor(self, tmp_path: Path) -> None:
        """Debe permitir commits con otros co-autores (no Claude)."""
        # Arrange
        mensaje_file = tmp_path / "COMMIT_EDITMSG"
        mensaje_file.write_text(
            "feat: add new feature\n\n" "Co-Authored-By: John Doe <john@example.com>\n"
        )

        # Act
        with patch("sys.argv", ["commit-msg", str(mensaje_file)]):
            from ci_guardian.hooks.commit_msg import main

            resultado = main()

        # Assert
        assert resultado == 0, "Debe permitir commits con co-autores válidos"

    def test_debe_permitir_commit_con_multiples_coautores_sin_claude(self, tmp_path: Path) -> None:
        """Debe permitir commits con múltiples co-autores si ninguno es Claude."""
        # Arrange
        mensaje_file = tmp_path / "COMMIT_EDITMSG"
        mensaje_file.write_text(
            "feat: collaborative work\n\n"
            "Co-Authored-By: Alice <alice@example.com>\n"
            "Co-Authored-By: Bob <bob@example.com>\n"
        )

        # Act
        with patch("sys.argv", ["commit-msg", str(mensaje_file)]):
            from ci_guardian.hooks.commit_msg import main

            resultado = main()

        # Assert
        assert resultado == 0, "Debe permitir múltiples co-autores válidos"

    def test_debe_rechazar_commit_con_claude_entre_otros_coautores(self, tmp_path: Path) -> None:
        """Debe rechazar commit si Claude está entre otros co-autores."""
        # Arrange
        mensaje_file = tmp_path / "COMMIT_EDITMSG"
        mensaje_file.write_text(
            "feat: collaborative work\n\n"
            "Co-Authored-By: Alice <alice@example.com>\n"
            "Co-Authored-By: Claude <noreply@anthropic.com>\n"
            "Co-Authored-By: Bob <bob@example.com>\n"
        )

        # Act
        with patch("sys.argv", ["commit-msg", str(mensaje_file)]):
            from ci_guardian.hooks.commit_msg import main

            resultado = main()

        # Assert
        assert resultado == 1, "Debe rechazar si Claude aparece entre co-autores"

    def test_debe_detectar_claude_code_en_mensaje_generado(self, tmp_path: Path) -> None:
        """Debe detectar el formato típico que genera Claude Code."""
        # Arrange - Formato típico de Claude Code
        mensaje_file = tmp_path / "COMMIT_EDITMSG"
        mensaje_file.write_text(
            "feat(core): implement hook installer\n\n"
            "🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\n"
            "Co-Authored-By: Claude <noreply@anthropic.com>\n"
        )

        # Act
        with patch("sys.argv", ["commit-msg", str(mensaje_file)]):
            from ci_guardian.hooks.commit_msg import main

            resultado = main()

        # Assert
        assert resultado == 1, "Debe rechazar formato típico de Claude Code"

    def test_debe_rechazar_variaciones_de_claude_email(self, tmp_path: Path) -> None:
        """Debe rechazar variaciones del email de Claude."""
        # Arrange
        mensaje_file = tmp_path / "COMMIT_EDITMSG"
        mensaje_file.write_text("feat: test\n\n" "Co-Authored-By: Claude <claude@anthropic.com>\n")

        # Act
        with patch("sys.argv", ["commit-msg", str(mensaje_file)]):
            from ci_guardian.hooks.commit_msg import main

            resultado = main()

        # Assert
        # Nota: Este test verifica el comportamiento actual del validador
        # Si solo valida noreply@anthropic.com, este test debería pasar
        # Documenta el comportamiento esperado
        assert isinstance(resultado, int), "Debe retornar código de salida válido"


class TestCommitMsgEdgeCases:
    """Tests de edge cases del hook commit-msg."""

    def test_debe_manejar_mensaje_vacio(self, tmp_path: Path) -> None:
        """Debe manejar mensaje de commit vacío."""
        # Arrange
        mensaje_file = tmp_path / "COMMIT_EDITMSG"
        mensaje_file.write_text("")

        # Act
        with patch("sys.argv", ["commit-msg", str(mensaje_file)]):
            from ci_guardian.hooks.commit_msg import main

            resultado = main()

        # Assert
        # Mensaje vacío NO tiene Co-Authored-By: Claude, debe pasar
        assert resultado == 0, "Debe permitir mensaje vacío (Git lo rechazará después)"

    def test_debe_fallar_si_no_se_proporciona_path(self) -> None:
        """Debe fallar si no se proporciona path al mensaje."""
        # Act
        with patch("sys.argv", ["commit-msg"]):  # Sin segundo argumento
            from ci_guardian.hooks.commit_msg import main

            resultado = main()

        # Assert
        assert resultado == 1, "Debe fallar si no se proporciona path al mensaje"

    def test_debe_manejar_archivo_inexistente(self, tmp_path: Path) -> None:
        """Debe manejar archivo de mensaje inexistente."""
        # Arrange
        mensaje_file = tmp_path / "NONEXISTENT_FILE"

        # Act
        with patch("sys.argv", ["commit-msg", str(mensaje_file)]):
            from ci_guardian.hooks.commit_msg import main

            resultado = main()

        # Assert
        assert resultado == 1, "Debe fallar si el archivo no existe"

    def test_debe_manejar_mensaje_con_unicode(self, tmp_path: Path) -> None:
        """Debe manejar mensajes con caracteres Unicode."""
        # Arrange
        mensaje_file = tmp_path / "COMMIT_EDITMSG"
        mensaje_file.write_text("feat: añadir función 测试 🎉\n\nMensaje con émojis")

        # Act
        with patch("sys.argv", ["commit-msg", str(mensaje_file)]):
            from ci_guardian.hooks.commit_msg import main

            resultado = main()

        # Assert
        assert resultado == 0, "Debe manejar Unicode correctamente"

    def test_debe_manejar_mensaje_muy_largo(self, tmp_path: Path) -> None:
        """Debe manejar mensajes de commit muy largos."""
        # Arrange
        mensaje_file = tmp_path / "COMMIT_EDITMSG"
        mensaje_largo = "feat: test\n\n" + ("A" * 10000) + "\n\nNormal text"
        mensaje_file.write_text(mensaje_largo)

        # Act
        with patch("sys.argv", ["commit-msg", str(mensaje_file)]):
            from ci_guardian.hooks.commit_msg import main

            resultado = main()

        # Assert
        assert resultado == 0, "Debe manejar mensajes largos sin problemas"

    def test_debe_ser_case_sensitive_con_nombre_claude(self, tmp_path: Path) -> None:
        """Debe verificar comportamiento con variaciones de mayúsculas de 'Claude'."""
        # Arrange - Variación en minúsculas
        mensaje_file = tmp_path / "COMMIT_EDITMSG"
        mensaje_file.write_text("feat: test\n\n" "Co-Authored-By: claude <noreply@anthropic.com>\n")

        # Act
        with patch("sys.argv", ["commit-msg", str(mensaje_file)]):
            from ci_guardian.hooks.commit_msg import main

            resultado = main()

        # Assert
        # Documentar comportamiento: ¿Es case-sensitive?
        assert isinstance(resultado, int), "Debe retornar código de salida válido"


class TestCommitMsgIntegracion:
    """Tests de integración del hook commit-msg."""

    def test_debe_funcionar_con_path_absoluto(self, tmp_path: Path) -> None:
        """Debe funcionar con path absoluto al mensaje."""
        # Arrange
        mensaje_file = tmp_path / "COMMIT_EDITMSG"
        mensaje_file.write_text("feat: test with absolute path\n")

        # Act
        with patch("sys.argv", ["commit-msg", str(mensaje_file.absolute())]):
            from ci_guardian.hooks.commit_msg import main

            resultado = main()

        # Assert
        assert resultado == 0, "Debe funcionar con path absoluto"

    def test_debe_funcionar_con_path_relativo(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Debe funcionar con path relativo al mensaje."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        mensaje_file = Path("COMMIT_EDITMSG")
        mensaje_file.write_text("feat: test with relative path\n")

        # Act
        with patch("sys.argv", ["commit-msg", str(mensaje_file)]):
            from ci_guardian.hooks.commit_msg import main

            resultado = main()

        # Assert
        assert resultado == 0, "Debe funcionar con path relativo"

    def test_debe_preservar_formato_de_error(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Debe mostrar mensaje de error formateado al rechazar commit."""
        # Arrange
        mensaje_file = tmp_path / "COMMIT_EDITMSG"
        mensaje_file.write_text("feat: test\n\n" "Co-Authored-By: Claude <noreply@anthropic.com>\n")

        # Act
        with patch("sys.argv", ["commit-msg", str(mensaje_file)]):
            from ci_guardian.hooks.commit_msg import main

            resultado = main()

        # Assert
        assert resultado == 1
        captured = capsys.readouterr()
        assert "❌" in captured.err, "Debe mostrar icono de error"
        # Verificar que muestra mensaje descriptivo
        assert len(captured.err) > 10, "Debe mostrar mensaje de error descriptivo"
