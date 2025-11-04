"""
Tests para el validador de entornos virtuales.

Estos tests verifican la detección de venv activos mediante:
1. Variable de entorno VIRTUAL_ENV
2. Comparación sys.prefix != sys.base_prefix
"""

from unittest.mock import patch

from ci_guardian.core.venv_validator import esta_venv_activo


class TestVenvValidator:
    """Tests para el validador de entornos virtuales."""

    def test_debe_detectar_venv_activo_via_variable_entorno(self):
        """Debe detectar venv activo mediante variable VIRTUAL_ENV."""
        # Arrange
        venv_path = "/home/user/proyecto/venv"

        # Act
        with patch("os.getenv", return_value=venv_path):
            activo, mensaje = esta_venv_activo()

        # Assert
        assert activo is True, "Debe detectar venv activo vía VIRTUAL_ENV"
        assert "✅" in mensaje, "Mensaje debe indicar éxito"
        assert venv_path in mensaje, "Mensaje debe incluir path del venv"

    def test_debe_detectar_venv_activo_via_sys_prefix(self):
        """Debe detectar venv activo mediante sys.prefix != sys.base_prefix."""
        # Arrange
        venv_prefix = "/home/user/proyecto/venv"
        base_prefix = "/usr"

        # Act
        with (
            patch("os.getenv", return_value=None),
            patch("sys.prefix", venv_prefix),
            patch("sys.base_prefix", base_prefix),
        ):
            activo, mensaje = esta_venv_activo()

        # Assert
        assert activo is True, "Debe detectar venv activo vía sys.prefix"
        assert "✅" in mensaje, "Mensaje debe indicar éxito"
        assert venv_prefix in mensaje, "Mensaje debe incluir path del venv"

    def test_debe_rechazar_cuando_no_hay_venv_activo(self):
        """Debe indicar que no hay venv activo cuando sys.prefix == sys.base_prefix."""
        # Arrange
        base_prefix = "/usr"

        # Act
        with (
            patch("os.getenv", return_value=None),
            patch("sys.prefix", base_prefix),
            patch("sys.base_prefix", base_prefix),
        ):
            activo, mensaje = esta_venv_activo()

        # Assert
        assert activo is False, "No debe detectar venv cuando prefix == base_prefix"
        assert "❌" in mensaje, "Mensaje debe indicar error"
        assert "entorno virtual" in mensaje.lower(), "Debe mencionar entorno virtual"

    def test_mensaje_error_debe_incluir_instrucciones_linux(self):
        """Mensaje de error debe incluir comando para activar venv en Linux."""
        # Arrange
        base_prefix = "/usr"

        # Act
        with (
            patch("os.getenv", return_value=None),
            patch("sys.prefix", base_prefix),
            patch("sys.base_prefix", base_prefix),
        ):
            activo, mensaje = esta_venv_activo()

        # Assert
        assert activo is False
        assert (
            "source venv/bin/activate" in mensaje
        ), "Debe incluir comando de activación para Linux/Mac"

    def test_mensaje_error_debe_incluir_instrucciones_windows(self):
        """Mensaje de error debe incluir comando para activar venv en Windows."""
        # Arrange
        base_prefix = "C:\\Python312"

        # Act
        with (
            patch("os.getenv", return_value=None),
            patch("sys.prefix", base_prefix),
            patch("sys.base_prefix", base_prefix),
        ):
            activo, mensaje = esta_venv_activo()

        # Assert
        assert activo is False
        assert (
            "venv\\Scripts\\activate" in mensaje or "venv/Scripts/activate" in mensaje
        ), "Debe incluir comando de activación para Windows"

    def test_mensaje_error_debe_incluir_alternativa_ci_guardian(self):
        """Mensaje de error debe sugerir usar ci-guardian commit como alternativa."""
        # Arrange
        base_prefix = "/usr"

        # Act
        with (
            patch("os.getenv", return_value=None),
            patch("sys.prefix", base_prefix),
            patch("sys.base_prefix", base_prefix),
        ):
            activo, mensaje = esta_venv_activo()

        # Assert
        assert activo is False
        assert (
            "ci-guardian commit" in mensaje
        ), "Debe sugerir usar ci-guardian commit como alternativa"

    def test_debe_priorizar_variable_entorno_sobre_sys_prefix(self):
        """VIRTUAL_ENV debe tener prioridad sobre sys.prefix (más explícito)."""
        # Arrange
        venv_path = "/home/user/proyecto/venv"
        base_prefix = "/usr"

        # Act
        with (
            patch("os.getenv", return_value=venv_path),
            patch("sys.prefix", base_prefix),
            patch("sys.base_prefix", base_prefix),
        ):  # sys.prefix == base_prefix (sin venv)
            activo, mensaje = esta_venv_activo()

        # Assert
        assert activo is True, "VIRTUAL_ENV debe tener prioridad"
        assert venv_path in mensaje, "Debe usar path de VIRTUAL_ENV"

    def test_debe_manejar_variable_entorno_vacia(self):
        """Debe tratar variable VIRTUAL_ENV vacía como no activo."""
        # Arrange
        base_prefix = "/usr"

        # Act
        with (
            patch("os.getenv", return_value=""),
            patch("sys.prefix", base_prefix),
            patch("sys.base_prefix", base_prefix),
        ):
            activo, mensaje = esta_venv_activo()

        # Assert
        assert activo is False, "String vacío no debe considerarse venv activo"
        assert "❌" in mensaje

    def test_debe_manejar_paths_con_espacios(self):
        """Debe manejar correctamente paths con espacios en el nombre."""
        # Arrange
        venv_path = "/home/user/my project/venv"

        # Act
        with patch("os.getenv", return_value=venv_path):
            activo, mensaje = esta_venv_activo()

        # Assert
        assert activo is True
        assert venv_path in mensaje, "Debe preservar paths con espacios"
