"""Tests para el módulo validators/common.py de CI Guardian.

Este módulo implementa tests para utilidades comunes de validadores,
principalmente la validación centralizada de path traversal.
Los tests se escriben PRIMERO siguiendo TDD estricto (fase RED).
"""

from __future__ import annotations

from pathlib import Path

import pytest


class TestValidarPathSeguro:
    """Tests para la función validar_path_seguro()."""

    def test_debe_aceptar_path_normal_relativo(self) -> None:
        """Debe aceptar paths relativos normales sin '..'."""
        # Arrange & Act
        from ci_guardian.validators.common import validar_path_seguro

        path_resultado = validar_path_seguro("src/main.py")

        # Assert
        assert path_resultado == Path("src/main.py")

    def test_debe_aceptar_path_normal_absoluto(self, tmp_path: Path) -> None:
        """Debe aceptar paths absolutos sin '..'."""
        # Arrange
        path_absoluto = tmp_path / "proyecto" / "archivo.py"

        # Act
        from ci_guardian.validators.common import validar_path_seguro

        path_resultado = validar_path_seguro(str(path_absoluto))

        # Assert
        assert path_resultado == path_absoluto

    def test_debe_rechazar_path_con_doble_punto_simple(self) -> None:
        """Debe rechazar path con '..' simple."""
        # Arrange & Act & Assert
        from ci_guardian.validators.common import validar_path_seguro

        with pytest.raises(ValueError, match="Path traversal detectado"):
            validar_path_seguro("../etc/passwd")

    def test_debe_rechazar_path_con_doble_punto_multiple(self) -> None:
        """Debe rechazar path con múltiples '..'."""
        # Arrange & Act & Assert
        from ci_guardian.validators.common import validar_path_seguro

        with pytest.raises(ValueError, match="Path traversal detectado"):
            validar_path_seguro("../../etc/passwd")

    def test_debe_rechazar_path_con_doble_punto_intermedio(self) -> None:
        """Debe rechazar path con '..' en medio de la ruta."""
        # Arrange & Act & Assert
        from ci_guardian.validators.common import validar_path_seguro

        with pytest.raises(ValueError, match="Path traversal detectado"):
            validar_path_seguro("foo/../bar/baz.py")

    def test_debe_rechazar_path_con_doble_punto_al_final(self) -> None:
        """Debe rechazar path que termina con '..'."""
        # Arrange & Act & Assert
        from ci_guardian.validators.common import validar_path_seguro

        with pytest.raises(ValueError, match="Path traversal detectado"):
            validar_path_seguro("foo/bar/..")

    def test_debe_aceptar_path_object_en_lugar_de_string(self) -> None:
        """Debe aceptar objetos Path además de strings."""
        # Arrange
        path_obj = Path("src") / "archivo.py"

        # Act
        from ci_guardian.validators.common import validar_path_seguro

        path_resultado = validar_path_seguro(path_obj)

        # Assert
        assert path_resultado == path_obj

    def test_debe_rechazar_path_object_con_doble_punto(self) -> None:
        """Debe rechazar objetos Path que contengan '..'."""
        # Arrange
        path_obj = Path("..") / "etc" / "passwd"

        # Act & Assert
        from ci_guardian.validators.common import validar_path_seguro

        with pytest.raises(ValueError, match="Path traversal detectado"):
            validar_path_seguro(path_obj)

    def test_mensaje_error_debe_incluir_nombre_contexto_por_defecto(self) -> None:
        """El mensaje de error debe incluir 'path' por defecto."""
        # Arrange & Act & Assert
        from ci_guardian.validators.common import validar_path_seguro

        with pytest.raises(ValueError, match="path.*\\.\\."):
            validar_path_seguro("../malicious")

    def test_mensaje_error_debe_incluir_nombre_contexto_personalizado(
        self,
    ) -> None:
        """El mensaje de error debe incluir el contexto personalizado."""
        # Arrange & Act & Assert
        from ci_guardian.validators.common import validar_path_seguro

        with pytest.raises(ValueError, match="archivo.*\\.\\."):
            validar_path_seguro("../malicious", nombre_contexto="archivo")

    def test_debe_incluir_path_en_mensaje_de_error(self) -> None:
        """El mensaje de error debe mostrar el path problemático."""
        # Arrange
        path_malicioso = "../../etc/shadow"

        # Act & Assert
        from ci_guardian.validators.common import validar_path_seguro

        with pytest.raises(ValueError, match=path_malicioso):
            validar_path_seguro(path_malicioso)

    def test_debe_manejar_paths_vacios(self) -> None:
        """Debe manejar gracefully paths vacíos."""
        # Arrange & Act
        from ci_guardian.validators.common import validar_path_seguro

        path_resultado = validar_path_seguro("")

        # Assert - path vacío es técnicamente válido (current dir)
        assert path_resultado == Path("")

    def test_debe_manejar_punto_simple_como_directorio_actual(self) -> None:
        """Debe aceptar '.' como directorio actual."""
        # Arrange & Act
        from ci_guardian.validators.common import validar_path_seguro

        path_resultado = validar_path_seguro(".")

        # Assert
        assert path_resultado == Path(".")

    def test_debe_aceptar_archivos_con_doble_punto_en_nombre(self) -> None:
        """Debe aceptar archivos con '..' literales en el nombre (no path sep)."""
        # Arrange - algunos archivos pueden tener .. en su nombre
        # Ej: "version..backup.txt" (aunque inusual, es válido)

        # Act
        from ci_guardian.validators.common import validar_path_seguro

        # Este caso es edge - si el archivo se llama literalmente "test..py"
        # sin separadores de directorio, no es path traversal
        # Sin embargo, nuestra implementación simple detectará ".." en el string
        # Esto es CORRECTO desde una perspectiva de seguridad (better safe than sorry)

        # Por ahora, el test verifica que ".." se rechaza siempre
        with pytest.raises(ValueError, match="Path traversal detectado"):
            validar_path_seguro("test..py")

    def test_debe_retornar_path_object_siempre(self) -> None:
        """Debe retornar siempre un objeto Path, nunca string."""
        # Arrange & Act
        from ci_guardian.validators.common import validar_path_seguro

        resultado_desde_str = validar_path_seguro("src/main.py")
        resultado_desde_path = validar_path_seguro(Path("src/main.py"))

        # Assert
        assert isinstance(resultado_desde_str, Path)
        assert isinstance(resultado_desde_path, Path)


class TestValidarPathSeguroCompatibilidad:
    """Tests de compatibilidad con código existente."""

    def test_compatibilidad_con_cli_validar_path_traversal(self) -> None:
        """Debe ser compatible con uso actual en cli.py."""
        # Arrange - simular uso actual en cli.py:_validar_path_traversal

        # Act & Assert - debe rechazar lo mismo que la función original
        from ci_guardian.validators.common import validar_path_seguro

        # Caso que cli.py rechaza: paths con ".."
        with pytest.raises(ValueError):
            validar_path_seguro("../malicious", "repositorio")

        # Caso que cli.py acepta: paths sin ".."
        path_valido = validar_path_seguro("./mi-proyecto")
        assert path_valido == Path("./mi-proyecto")

    def test_compatibilidad_con_code_quality_validacion_archivos(
        self,
    ) -> None:
        """Debe ser compatible con validación en code_quality.py."""
        # Arrange - simular uso actual en code_quality.py:28-32
        archivos = [
            Path("src/main.py"),
            Path("tests/test_foo.py"),
            Path("README.md"),
        ]

        # Act
        from ci_guardian.validators.common import validar_path_seguro

        # Validar todos los archivos
        archivos_seguros = [validar_path_seguro(str(f), "archivo") for f in archivos]

        # Assert
        assert len(archivos_seguros) == 3
        assert all(isinstance(p, Path) for p in archivos_seguros)

    def test_compatibilidad_con_code_quality_rechazar_traversal(self) -> None:
        """Debe rechazar path traversal igual que code_quality.py."""
        # Arrange - archivo malicioso con path traversal
        archivo_malicioso = Path("../../../etc/passwd")

        # Act & Assert
        from ci_guardian.validators.common import validar_path_seguro

        with pytest.raises(ValueError, match="(?i)path traversal detectado.*ruta inválida"):
            validar_path_seguro(str(archivo_malicioso), "archivo")

    def test_compatibilidad_con_security_validacion_directorio(self) -> None:
        """Debe ser compatible con validación en security.py."""
        # Arrange - simular uso actual en security.py:37-38

        # Act & Assert - debe rechazar lo mismo
        from ci_guardian.validators.common import validar_path_seguro

        # Directorio malicioso
        with pytest.raises(ValueError, match="Path traversal detectado"):
            validar_path_seguro("../malicious", "directorio")

        # Directorio válido
        directorio_valido = validar_path_seguro("src")
        assert directorio_valido == Path("src")


class TestValidarPathSeguroEdgeCases:
    """Tests de casos edge y situaciones especiales."""

    def test_debe_manejar_paths_windows_con_backslash(self) -> None:
        """Debe manejar paths de Windows con backslashes."""
        # Arrange
        path_windows = "src\\main.py"

        # Act
        from ci_guardian.validators.common import validar_path_seguro

        path_resultado = validar_path_seguro(path_windows)

        # Assert - debe aceptar backslashes normales
        assert path_resultado == Path(path_windows)

    def test_debe_rechazar_path_windows_con_doble_punto(self) -> None:
        """Debe rechazar paths de Windows con path traversal."""
        # Arrange
        path_windows_malicioso = "..\\windows\\system32"

        # Act & Assert
        from ci_guardian.validators.common import validar_path_seguro

        with pytest.raises(ValueError, match="Path traversal detectado"):
            validar_path_seguro(path_windows_malicioso)

    def test_debe_manejar_paths_muy_largos(self) -> None:
        """Debe manejar paths muy largos sin problemas de performance."""
        # Arrange - path muy largo pero sin ".."
        path_largo = "/".join([f"dir{i}" for i in range(100)]) + "/archivo.py"

        # Act
        from ci_guardian.validators.common import validar_path_seguro

        path_resultado = validar_path_seguro(path_largo)

        # Assert
        assert path_resultado == Path(path_largo)

    def test_debe_manejar_paths_con_espacios(self) -> None:
        """Debe manejar paths con espacios en nombres."""
        # Arrange
        path_con_espacios = "Mi Proyecto/archivo con espacios.py"

        # Act
        from ci_guardian.validators.common import validar_path_seguro

        path_resultado = validar_path_seguro(path_con_espacios)

        # Assert
        assert path_resultado == Path(path_con_espacios)

    def test_debe_manejar_paths_con_caracteres_unicode(self) -> None:
        """Debe manejar paths con caracteres Unicode."""
        # Arrange
        path_unicode = "código/archivo_español.py"

        # Act
        from ci_guardian.validators.common import validar_path_seguro

        path_resultado = validar_path_seguro(path_unicode)

        # Assert
        assert path_resultado == Path(path_unicode)
