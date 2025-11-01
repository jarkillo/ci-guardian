"""
Tests para el validador de autoría de commits (anti Claude co-author).

Este módulo contiene tests que validan que Claude Code no pueda añadirse
como co-autor en los commits del proyecto.
"""

import pytest


class TestDeteccionCoAuthorClaude:
    """Tests para detectar Co-Authored-By: Claude en mensajes de commit."""

    def test_debe_rechazar_coauthor_claude_formato_estandar(self):
        """Debe rechazar Co-Authored-By: Claude <noreply@anthropic.com>."""
        # Arrange
        mensaje = """feat: add new feature

Some description here.

Co-Authored-By: Claude <noreply@anthropic.com>
"""

        # Act
        from ci_guardian.validators.authorship import contiene_coauthor_claude

        resultado = contiene_coauthor_claude(mensaje)

        # Assert
        assert resultado is True, "Debe detectar Co-Authored-By: Claude con email noreply"

    def test_debe_rechazar_coauthor_claude_minusculas(self):
        """Debe rechazar Co-authored-by: Claude (minúsculas)."""
        # Arrange
        mensaje = """fix: bug fix

Co-authored-by: Claude <noreply@anthropic.com>
"""

        # Act
        from ci_guardian.validators.authorship import contiene_coauthor_claude

        resultado = contiene_coauthor_claude(mensaje)

        # Assert
        assert resultado is True, "Debe detectar variación en minúsculas"

    def test_debe_rechazar_coauthor_claude_mayusculas(self):
        """Debe rechazar CO-AUTHORED-BY: Claude (mayúsculas)."""
        # Arrange
        mensaje = """refactor: code cleanup

CO-AUTHORED-BY: Claude <noreply@anthropic.com>
"""

        # Act
        from ci_guardian.validators.authorship import contiene_coauthor_claude

        resultado = contiene_coauthor_claude(mensaje)

        # Assert
        assert resultado is True, "Debe detectar variación en mayúsculas"

    def test_debe_rechazar_coauthor_claude_nombre_minusculas(self):
        """Debe rechazar Co-Authored-By: claude (nombre en minúsculas)."""
        # Arrange
        mensaje = """docs: update README

Co-Authored-By: claude <noreply@anthropic.com>
"""

        # Act
        from ci_guardian.validators.authorship import contiene_coauthor_claude

        resultado = contiene_coauthor_claude(mensaje)

        # Assert
        assert resultado is True, "Debe detectar 'claude' en minúsculas"

    def test_debe_rechazar_coauthor_claude_email_alternativo(self):
        """Debe rechazar Co-Authored-By: Claude <claude@anthropic.com>."""
        # Arrange
        mensaje = """test: add tests

Co-Authored-By: Claude <claude@anthropic.com>
"""

        # Act
        from ci_guardian.validators.authorship import contiene_coauthor_claude

        resultado = contiene_coauthor_claude(mensaje)

        # Assert
        assert resultado is True, "Debe detectar email alternativo claude@anthropic.com"

    def test_debe_rechazar_coauthor_con_espacios_extra(self):
        """Debe rechazar Co-Authored-By con espacios extra."""
        # Arrange
        mensaje = """feat: feature

Co-Authored-By:  Claude  <noreply@anthropic.com>
"""

        # Act
        from ci_guardian.validators.authorship import contiene_coauthor_claude

        resultado = contiene_coauthor_claude(mensaje)

        # Assert
        assert resultado is True, "Debe detectar incluso con espacios extra"

    def test_debe_rechazar_cuando_claude_es_uno_de_varios_coautores(self):
        """Debe rechazar cuando Claude está entre múltiples co-autores."""
        # Arrange
        mensaje = """feat: collaborative feature

Co-Authored-By: John Doe <john@example.com>
Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Jane Smith <jane@example.com>
"""

        # Act
        from ci_guardian.validators.authorship import contiene_coauthor_claude

        resultado = contiene_coauthor_claude(mensaje)

        # Assert
        assert resultado is True, "Debe detectar Claude entre múltiples co-autores"

    def test_debe_aceptar_coauthor_humano(self):
        """Debe aceptar Co-Authored-By con autor humano."""
        # Arrange
        mensaje = """feat: pair programming

Co-Authored-By: John Doe <john@example.com>
"""

        # Act
        from ci_guardian.validators.authorship import contiene_coauthor_claude

        resultado = contiene_coauthor_claude(mensaje)

        # Assert
        assert resultado is False, "Debe aceptar co-autores humanos"

    def test_debe_aceptar_multiples_coautores_humanos(self):
        """Debe aceptar múltiples co-autores humanos sin Claude."""
        # Arrange
        mensaje = """feat: team work

Co-Authored-By: John Doe <john@example.com>
Co-Authored-By: Jane Smith <jane@example.com>
Co-Authored-By: Bob Wilson <bob@example.com>
"""

        # Act
        from ci_guardian.validators.authorship import contiene_coauthor_claude

        resultado = contiene_coauthor_claude(mensaje)

        # Assert
        assert resultado is False, "Debe aceptar múltiples humanos sin Claude"

    def test_debe_aceptar_mencion_claude_en_cuerpo_mensaje(self):
        """Debe aceptar mención de Claude en el cuerpo del mensaje (no como co-author)."""
        # Arrange
        mensaje = """feat: implement feature

This feature was developed with assistance from Claude Code.
Claude helped review the implementation.
"""

        # Act
        from ci_guardian.validators.authorship import contiene_coauthor_claude

        resultado = contiene_coauthor_claude(mensaje)

        # Assert
        assert resultado is False, "Debe permitir mencionar a Claude en el cuerpo"

    def test_debe_aceptar_mensaje_sin_coautores(self):
        """Debe aceptar mensaje sin ningún co-autor."""
        # Arrange
        mensaje = """fix: critical bug

Fixed the memory leak in the parser.
"""

        # Act
        from ci_guardian.validators.authorship import contiene_coauthor_claude

        resultado = contiene_coauthor_claude(mensaje)

        # Assert
        assert resultado is False, "Debe aceptar mensajes sin co-autores"

    def test_debe_rechazar_coauthor_claude_sin_email(self):
        """Debe rechazar Co-Authored-By: Claude sin email."""
        # Arrange
        mensaje = """feat: new feature

Co-Authored-By: Claude
"""

        # Act
        from ci_guardian.validators.authorship import contiene_coauthor_claude

        resultado = contiene_coauthor_claude(mensaje)

        # Assert
        assert resultado is True, "Debe detectar Claude incluso sin email"

    def test_debe_aceptar_coauthor_con_claude_en_nombre_pero_diferente(self):
        """Debe aceptar co-autor con Claude en el nombre pero diferente (ej: Claudette)."""
        # Arrange
        mensaje = """feat: feature

Co-Authored-By: Claudette Johnson <claudette@example.com>
"""

        # Act
        from ci_guardian.validators.authorship import contiene_coauthor_claude

        resultado = contiene_coauthor_claude(mensaje)

        # Assert
        assert (
            resultado is False
        ), "Debe aceptar nombres que contengan 'Claude' pero no sean exactamente 'Claude'"


class TestLecturaMensajeCommit:
    """Tests para leer mensajes de commit desde archivos."""

    def test_debe_leer_mensaje_simple_desde_archivo(self, tmp_path):
        """Debe leer correctamente un mensaje simple desde archivo."""
        # Arrange
        mensaje_path = tmp_path / "COMMIT_EDITMSG"
        contenido = "feat: simple commit message\n"
        mensaje_path.write_text(contenido, encoding="utf-8")

        # Act
        from ci_guardian.validators.authorship import leer_mensaje_commit

        resultado = leer_mensaje_commit(mensaje_path)

        # Assert
        assert resultado == contenido, "Debe leer el mensaje exactamente como está"

    def test_debe_leer_mensaje_multilinea(self, tmp_path):
        """Debe leer mensajes multilínea correctamente."""
        # Arrange
        mensaje_path = tmp_path / "COMMIT_EDITMSG"
        contenido = """feat: add new feature

This is a longer description
that spans multiple lines.

Co-Authored-By: John Doe <john@example.com>
"""
        mensaje_path.write_text(contenido, encoding="utf-8")

        # Act
        from ci_guardian.validators.authorship import leer_mensaje_commit

        resultado = leer_mensaje_commit(mensaje_path)

        # Assert
        assert resultado == contenido, "Debe preservar formato multilínea"

    def test_debe_ignorar_comentarios_git(self, tmp_path):
        """Debe ignorar líneas que empiezan con # (comentarios de git)."""
        # Arrange
        mensaje_path = tmp_path / "COMMIT_EDITMSG"
        contenido = """feat: commit message

# Please enter the commit message for your changes.
# Lines starting with '#' will be ignored.

Co-Authored-By: John Doe <john@example.com>

# Changes to be committed:
#   modified: file.py
"""
        mensaje_path.write_text(contenido, encoding="utf-8")

        # Act
        from ci_guardian.validators.authorship import leer_mensaje_commit

        resultado = leer_mensaje_commit(mensaje_path)

        # Assert
        assert "# Please enter" not in resultado, "No debe incluir comentarios de git"
        assert "# Lines starting" not in resultado, "No debe incluir comentarios"
        assert "# Changes to be committed" not in resultado, "No debe incluir comentarios"
        assert "feat: commit message" in resultado, "Debe incluir el mensaje real"
        assert "Co-Authored-By: John Doe" in resultado, "Debe incluir co-autores"

    def test_debe_manejar_mensaje_vacio(self, tmp_path):
        """Debe manejar correctamente mensajes vacíos."""
        # Arrange
        mensaje_path = tmp_path / "COMMIT_EDITMSG"
        mensaje_path.write_text("", encoding="utf-8")

        # Act
        from ci_guardian.validators.authorship import leer_mensaje_commit

        resultado = leer_mensaje_commit(mensaje_path)

        # Assert
        assert resultado == "", "Debe retornar string vacío para mensaje vacío"

    def test_debe_manejar_solo_comentarios(self, tmp_path):
        """Debe manejar archivo que solo contiene comentarios."""
        # Arrange
        mensaje_path = tmp_path / "COMMIT_EDITMSG"
        contenido = """# This is a comment
# Another comment
# More comments
"""
        mensaje_path.write_text(contenido, encoding="utf-8")

        # Act
        from ci_guardian.validators.authorship import leer_mensaje_commit

        resultado = leer_mensaje_commit(mensaje_path)

        # Assert
        assert resultado.strip() == "", "Debe retornar vacío si solo hay comentarios"

    def test_debe_lanzar_error_si_archivo_no_existe(self, tmp_path):
        """Debe lanzar FileNotFoundError si el archivo no existe."""
        # Arrange
        mensaje_path = tmp_path / "NO_EXISTE.txt"

        # Act & Assert
        from ci_guardian.validators.authorship import leer_mensaje_commit

        with pytest.raises(FileNotFoundError, match="Archivo de commit no encontrado"):
            leer_mensaje_commit(mensaje_path)

    def test_debe_manejar_archivo_con_encoding_utf8(self, tmp_path):
        """Debe manejar correctamente archivos con caracteres UTF-8."""
        # Arrange
        mensaje_path = tmp_path / "COMMIT_EDITMSG"
        contenido = "feat: añadir función con ñ y acentos\n\nDescripción con émojis 🚀\n"
        mensaje_path.write_text(contenido, encoding="utf-8")

        # Act
        from ci_guardian.validators.authorship import leer_mensaje_commit

        resultado = leer_mensaje_commit(mensaje_path)

        # Assert
        assert "ñ" in resultado, "Debe manejar caracteres españoles"
        assert "🚀" in resultado, "Debe manejar emojis"


class TestValidadorAutoría:
    """Tests para el validador principal de autoría."""

    def test_debe_retornar_valido_para_mensaje_sin_claude(self, tmp_path):
        """Debe retornar (True, '') para mensaje sin Claude como co-autor."""
        # Arrange
        mensaje_path = tmp_path / "COMMIT_EDITMSG"
        mensaje_path.write_text(
            """feat: implement feature

Co-Authored-By: John Doe <john@example.com>
""",
            encoding="utf-8",
        )

        # Act
        from ci_guardian.validators.authorship import validar_autoria_commit

        valido, mensaje_error = validar_autoria_commit(mensaje_path)

        # Assert
        assert valido is True, "Debe ser válido sin Claude"
        assert mensaje_error == "", "No debe haber mensaje de error"

    def test_debe_retornar_invalido_para_mensaje_con_claude(self, tmp_path):
        """Debe retornar (False, mensaje) para mensaje con Claude como co-autor."""
        # Arrange
        mensaje_path = tmp_path / "COMMIT_EDITMSG"
        mensaje_path.write_text(
            """feat: implement feature

Co-Authored-By: Claude <noreply@anthropic.com>
""",
            encoding="utf-8",
        )

        # Act
        from ci_guardian.validators.authorship import validar_autoria_commit

        valido, mensaje_error = validar_autoria_commit(mensaje_path)

        # Assert
        assert valido is False, "Debe ser inválido con Claude"
        assert "Claude" in mensaje_error, "El mensaje debe mencionar a Claude"
        assert "rechazado" in mensaje_error.lower(), "El mensaje debe indicar rechazo"

    def test_debe_retornar_valido_para_mensaje_vacio(self, tmp_path):
        """Debe permitir mensaje vacío (git lo rechazará por otros motivos)."""
        # Arrange
        mensaje_path = tmp_path / "COMMIT_EDITMSG"
        mensaje_path.write_text("", encoding="utf-8")

        # Act
        from ci_guardian.validators.authorship import validar_autoria_commit

        valido, mensaje_error = validar_autoria_commit(mensaje_path)

        # Assert
        assert valido is True, "Debe permitir mensaje vacío (git lo manejará)"
        assert mensaje_error == "", "No debe haber error para mensaje vacío"

    def test_debe_retornar_invalido_con_mensaje_descriptivo(self, tmp_path):
        """Debe retornar mensaje de error descriptivo cuando detecta Claude."""
        # Arrange
        mensaje_path = tmp_path / "COMMIT_EDITMSG"
        mensaje_path.write_text(
            """feat: feature

Co-Authored-By: Claude <claude@anthropic.com>
""",
            encoding="utf-8",
        )

        # Act
        from ci_guardian.validators.authorship import validar_autoria_commit

        valido, mensaje_error = validar_autoria_commit(mensaje_path)

        # Assert
        assert valido is False, "Debe ser inválido"
        assert len(mensaje_error) > 0, "Debe haber un mensaje de error"
        assert any(
            palabra in mensaje_error.lower() for palabra in ["claude", "co-author"]
        ), "El mensaje debe ser específico sobre Claude como co-autor"

    def test_debe_manejar_multiples_coautores_con_claude(self, tmp_path):
        """Debe rechazar cuando Claude está entre varios co-autores."""
        # Arrange
        mensaje_path = tmp_path / "COMMIT_EDITMSG"
        mensaje_path.write_text(
            """feat: team feature

Co-Authored-By: John Doe <john@example.com>
Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Jane Smith <jane@example.com>
""",
            encoding="utf-8",
        )

        # Act
        from ci_guardian.validators.authorship import validar_autoria_commit

        valido, mensaje_error = validar_autoria_commit(mensaje_path)

        # Assert
        assert valido is False, "Debe rechazar aunque haya otros co-autores válidos"
        assert mensaje_error != "", "Debe haber mensaje de error"

    def test_debe_ignorar_comentarios_al_validar(self, tmp_path):
        """Debe ignorar comentarios de git al validar autoría."""
        # Arrange
        mensaje_path = tmp_path / "COMMIT_EDITMSG"
        mensaje_path.write_text(
            """feat: feature

# Co-Authored-By: Claude <noreply@anthropic.com>
# This is a commented out co-author

Co-Authored-By: John Doe <john@example.com>
""",
            encoding="utf-8",
        )

        # Act
        from ci_guardian.validators.authorship import validar_autoria_commit

        valido, mensaje_error = validar_autoria_commit(mensaje_path)

        # Assert
        assert valido is True, "No debe detectar Claude en comentarios"
        assert mensaje_error == "", "No debe haber error"

    def test_debe_ser_case_insensitive_para_deteccion_claude(self, tmp_path):
        """Debe detectar Claude independientemente de mayúsculas/minúsculas."""
        # Arrange
        mensaje_path = tmp_path / "COMMIT_EDITMSG"
        mensaje_path.write_text(
            """feat: feature

co-authored-by: CLAUDE <NOREPLY@ANTHROPIC.COM>
""",
            encoding="utf-8",
        )

        # Act
        from ci_guardian.validators.authorship import validar_autoria_commit

        valido, mensaje_error = validar_autoria_commit(mensaje_path)

        # Assert
        assert valido is False, "Debe detectar Claude en cualquier case"

    def test_debe_rechazar_claude_al_inicio_de_linea_solamente(self, tmp_path):
        """Debe rechazar solo Co-Authored-By al inicio de línea, no en medio."""
        # Arrange
        mensaje_path = tmp_path / "COMMIT_EDITMSG"
        mensaje_path.write_text(
            """feat: feature

We discussed this with Claude but decided against
adding Co-Authored-By: Claude <noreply@anthropic.com> to commits.
""",
            encoding="utf-8",
        )

        # Act
        from ci_guardian.validators.authorship import validar_autoria_commit

        valido, mensaje_error = validar_autoria_commit(mensaje_path)

        # Assert
        assert valido is True, "No debe detectar Co-Authored-By en medio de texto"


class TestSeguridadValidacion:
    """Tests de seguridad para el validador de autoría."""

    def test_no_debe_ejecutar_comandos_del_mensaje(self, tmp_path):
        """Debe tratar el mensaje como texto, no como comandos ejecutables."""
        # Arrange
        mensaje_path = tmp_path / "COMMIT_EDITMSG"
        mensaje_malicioso = """feat: feature

Co-Authored-By: John Doe <john@example.com>
$(rm -rf /)
`rm -rf /`
; rm -rf /
"""
        mensaje_path.write_text(mensaje_malicioso, encoding="utf-8")

        # Act
        from ci_guardian.validators.authorship import validar_autoria_commit

        valido, mensaje_error = validar_autoria_commit(mensaje_path)

        # Assert
        # Si llegamos aquí sin que se ejecute nada malicioso, el test pasa
        assert valido is True, "Debe tratar todo como texto, no ejecutar comandos"
        assert mensaje_error == "", "No debe haber error"

    def test_debe_manejar_regex_sin_redos_vulnerability(self, tmp_path):
        """Debe usar regex seguro sin vulnerabilidad ReDoS."""
        # Arrange
        mensaje_path = tmp_path / "COMMIT_EDITMSG"
        # Mensaje diseñado para explotar regex mal escritas (backtracking)
        mensaje_redos = "feat: feature\n\n" + "Co-Authored-By: " + "A" * 10000 + "\n"
        mensaje_path.write_text(mensaje_redos, encoding="utf-8")

        # Act
        import time

        from ci_guardian.validators.authorship import validar_autoria_commit

        inicio = time.time()
        valido, mensaje_error = validar_autoria_commit(mensaje_path)
        duracion = time.time() - inicio

        # Assert
        assert duracion < 1.0, f"No debe tardar más de 1 segundo (tardó {duracion}s)"
        assert valido is True, "Debe manejar input extremo sin crash"

    def test_debe_manejar_caracteres_unicode_maliciosos(self, tmp_path):
        """Debe manejar caracteres Unicode que podrían causar problemas."""
        # Arrange
        mensaje_path = tmp_path / "COMMIT_EDITMSG"
        mensaje_unicode = """feat: feature

Co-Authored-By: Jоhn Dоe <john@example.com>
"""
        # Nota: La 'o' en 'John' y 'Doe' es Unicode Cyrillic 'о' (U+043E), no ASCII 'o'
        mensaje_path.write_text(mensaje_unicode, encoding="utf-8")

        # Act
        from ci_guardian.validators.authorship import validar_autoria_commit

        valido, mensaje_error = validar_autoria_commit(mensaje_path)

        # Assert
        # No debe crashear con caracteres Unicode lookalikes
        assert isinstance(valido, bool), "Debe retornar bool incluso con Unicode"
        assert isinstance(mensaje_error, str), "Debe retornar string incluso con Unicode"

    def test_debe_validar_longitud_mensaje_extrema(self, tmp_path):
        """Debe manejar mensajes extremadamente largos sin problemas."""
        # Arrange
        mensaje_path = tmp_path / "COMMIT_EDITMSG"
        mensaje_largo = (
            "feat: feature\n\n"
            + ("A" * 100000)
            + "\n\nCo-Authored-By: John Doe <john@example.com>\n"
        )
        mensaje_path.write_text(mensaje_largo, encoding="utf-8")

        # Act
        from ci_guardian.validators.authorship import validar_autoria_commit

        valido, mensaje_error = validar_autoria_commit(mensaje_path)

        # Assert
        assert valido is True, "Debe manejar mensajes muy largos"
        assert isinstance(mensaje_error, str), "Debe retornar string"


class TestEdgeCasesEspeciales:
    """Tests para edge cases específicos y casos límite."""

    def test_debe_rechazar_claude_con_variaciones_espacios(self, tmp_path):
        """Debe rechazar Claude con múltiples espacios y tabs."""
        # Arrange
        mensaje_path = tmp_path / "COMMIT_EDITMSG"
        mensaje_path.write_text(
            "feat: feature\n\nCo-Authored-By:\t\tClaude\t<noreply@anthropic.com>\n",
            encoding="utf-8",
        )

        # Act
        from ci_guardian.validators.authorship import validar_autoria_commit

        valido, mensaje_error = validar_autoria_commit(mensaje_path)

        # Assert
        assert valido is False, "Debe detectar Claude incluso con tabs"

    def test_debe_aceptar_mensaje_solo_titulo(self, tmp_path):
        """Debe aceptar mensaje con solo título sin cuerpo."""
        # Arrange
        mensaje_path = tmp_path / "COMMIT_EDITMSG"
        mensaje_path.write_text("feat: simple commit", encoding="utf-8")

        # Act
        from ci_guardian.validators.authorship import validar_autoria_commit

        valido, mensaje_error = validar_autoria_commit(mensaje_path)

        # Assert
        assert valido is True, "Debe aceptar mensaje simple sin co-autores"
        assert mensaje_error == "", "No debe haber error"

    def test_debe_rechazar_variaciones_email_anthropic(self, tmp_path):
        """Debe rechazar variaciones del dominio @anthropic.com."""
        # Arrange
        casos = [
            "Co-Authored-By: Claude <claude@anthropic.com>",
            "Co-Authored-By: Claude <noreply@anthropic.com>",
            "Co-Authored-By: Claude <bot@anthropic.com>",
        ]

        for caso in casos:
            mensaje_path = tmp_path / f"COMMIT_{casos.index(caso)}.txt"
            mensaje_path.write_text(f"feat: feature\n\n{caso}\n", encoding="utf-8")

            # Act
            from ci_guardian.validators.authorship import validar_autoria_commit

            valido, mensaje_error = validar_autoria_commit(mensaje_path)

            # Assert
            assert valido is False, f"Debe rechazar: {caso}"
            assert mensaje_error != "", f"Debe haber error para: {caso}"

    def test_debe_aceptar_url_con_claude_en_cuerpo(self, tmp_path):
        """Debe aceptar URLs o menciones de Claude.ai en el cuerpo."""
        # Arrange
        mensaje_path = tmp_path / "COMMIT_EDITMSG"
        mensaje_path.write_text(
            """feat: add feature

Developed with assistance from https://claude.ai
See more at https://www.anthropic.com/claude

Co-Authored-By: John Doe <john@example.com>
""",
            encoding="utf-8",
        )

        # Act
        from ci_guardian.validators.authorship import validar_autoria_commit

        valido, mensaje_error = validar_autoria_commit(mensaje_path)

        # Assert
        assert valido is True, "Debe permitir mencionar claude.ai en URLs"
        assert mensaje_error == "", "No debe haber error"

    def test_debe_manejar_archivo_con_solo_lineas_vacias(self, tmp_path):
        """Debe manejar archivo con solo líneas vacías."""
        # Arrange
        mensaje_path = tmp_path / "COMMIT_EDITMSG"
        mensaje_path.write_text("\n\n\n\n", encoding="utf-8")

        # Act
        from ci_guardian.validators.authorship import validar_autoria_commit

        valido, mensaje_error = validar_autoria_commit(mensaje_path)

        # Assert
        assert valido is True, "Debe permitir archivo con solo líneas vacías"
        assert mensaje_error == "", "No debe haber error"

    def test_debe_rechazar_claude_sin_espacios_alrededor(self, tmp_path):
        """Debe rechazar Claude incluso sin espacios alrededor del nombre."""
        # Arrange
        mensaje_path = tmp_path / "COMMIT_EDITMSG"
        mensaje_path.write_text(
            "feat: feature\n\nCo-Authored-By:Claude<noreply@anthropic.com>\n", encoding="utf-8"
        )

        # Act
        from ci_guardian.validators.authorship import validar_autoria_commit

        valido, mensaje_error = validar_autoria_commit(mensaje_path)

        # Assert
        assert valido is False, "Debe detectar Claude sin espacios"
