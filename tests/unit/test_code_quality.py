# tests/unit/test_code_quality.py
"""
Tests para validadores de calidad de código (Ruff y Black).

Siguiendo TDD: Estos tests están diseñados para FALLAR primero (RED),
luego se implementará el código mínimo para que pasen (GREEN).
"""

import platform
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestEjecutorRuff:
    """Tests para el ejecutor de Ruff (linter)."""

    @pytest.fixture
    def archivos_python_validos(self, tmp_path):
        """Crea archivos Python válidos para testing."""
        archivos = []
        for i in range(3):
            archivo = tmp_path / f"test_{i}.py"
            archivo.write_text(
                f'"""Módulo de prueba {i}."""\n\n\ndef funcion_{i}():\n    pass\n', encoding="utf-8"
            )
            archivos.append(archivo)
        return archivos

    @pytest.fixture
    def mock_subprocess_ruff_exitoso(self):
        """Mock de subprocess.run simulando Ruff sin errores."""
        return MagicMock(
            returncode=0,
            stdout="[]",  # JSON vacío = sin errores
            stderr="",
        )

    @pytest.fixture
    def mock_subprocess_ruff_con_errores(self):
        """Mock de subprocess.run simulando Ruff con errores de linting."""
        return MagicMock(
            returncode=1,
            stdout='[{"code": "F401", "message": "unused import", "location": {"row": 1}}]',
            stderr="",
        )

    def test_debe_ejecutar_ruff_exitosamente_cuando_archivos_validos(
        self, archivos_python_validos, mock_subprocess_ruff_exitoso
    ):
        """Debe ejecutar Ruff con archivos válidos y retornar True."""
        from ci_guardian.validators.code_quality import ejecutar_ruff

        # Arrange
        with patch("subprocess.run", return_value=mock_subprocess_ruff_exitoso) as mock_run:
            # Act
            exitoso, mensaje = ejecutar_ruff(archivos_python_validos)

            # Assert
            assert exitoso is True, "Ruff debe retornar True cuando no hay errores"
            assert (
                "sin errores" in mensaje.lower() or "ok" in mensaje.lower()
            ), "El mensaje debe indicar que no hay errores"
            mock_run.assert_called_once()

            # Verificar que se llamó con argumentos seguros
            args_llamada = mock_run.call_args[0][0]
            assert args_llamada[0] == "ruff", "Debe ejecutar el comando 'ruff'"
            assert "check" in args_llamada, "Debe usar subcomando 'check'"
            assert any(
                "--output-format=json" in arg or "--format=json" in arg for arg in args_llamada
            ), "Debe usar formato JSON"

            # Verificar que NO se usa shell=True
            assert (
                mock_run.call_args.kwargs.get("shell", False) is False
            ), "NUNCA debe usar shell=True (vulnerabilidad de command injection)"

    def test_debe_retornar_false_cuando_ruff_detecta_errores(
        self, archivos_python_validos, mock_subprocess_ruff_con_errores
    ):
        """Debe retornar False cuando Ruff detecta errores de linting."""
        from ci_guardian.validators.code_quality import ejecutar_ruff

        # Arrange
        with patch("subprocess.run", return_value=mock_subprocess_ruff_con_errores) as mock_run:
            # Act
            exitoso, mensaje = ejecutar_ruff(archivos_python_validos)

            # Assert
            assert exitoso is False, "Ruff debe retornar False cuando hay errores"
            assert len(mensaje) > 0, "Debe incluir mensaje de error"
            assert mock_run.called, "Debe haber ejecutado Ruff"

    def test_debe_filtrar_solo_archivos_python(self, tmp_path):
        """Debe filtrar y procesar solo archivos .py."""
        from ci_guardian.validators.code_quality import ejecutar_ruff

        # Arrange
        archivo_py = tmp_path / "valido.py"
        archivo_py.write_text("# código python", encoding="utf-8")

        archivo_txt = tmp_path / "no_python.txt"
        archivo_txt.write_text("no es python", encoding="utf-8")

        archivo_js = tmp_path / "script.js"
        archivo_js.write_text("console.log('no python')", encoding="utf-8")

        archivos_mixtos = [archivo_py, archivo_txt, archivo_js]

        with patch(
            "subprocess.run", return_value=MagicMock(returncode=0, stdout="[]", stderr="")
        ) as mock_run:
            # Act
            ejecutar_ruff(archivos_mixtos)

            # Assert
            args_llamada = mock_run.call_args[0][0]
            archivos_procesados = [arg for arg in args_llamada if arg.endswith(".py")]
            assert len(archivos_procesados) == 1, "Debe procesar solo archivos .py"
            assert str(archivo_py) in archivos_procesados[0], "Debe incluir el archivo .py válido"

    def test_debe_validar_que_archivos_existan(self, tmp_path):
        """Debe validar que los archivos existan antes de ejecutar Ruff."""
        from ci_guardian.validators.code_quality import ejecutar_ruff

        # Arrange
        archivo_existente = tmp_path / "existe.py"
        archivo_existente.write_text("# código", encoding="utf-8")

        archivo_inexistente = tmp_path / "no_existe.py"
        # No crear el archivo

        archivos = [archivo_existente, archivo_inexistente]

        with patch(
            "subprocess.run", return_value=MagicMock(returncode=0, stdout="[]", stderr="")
        ) as mock_run:
            # Act
            ejecutar_ruff(archivos)

            # Assert
            args_llamada = mock_run.call_args[0][0]
            archivos_procesados = [arg for arg in args_llamada if arg.endswith(".py")]

            # Solo debe procesar archivos que existen
            assert str(archivo_existente) in str(
                archivos_procesados
            ), "Debe incluir archivos existentes"
            assert str(archivo_inexistente) not in str(
                archivos_procesados
            ), "NO debe incluir archivos que no existen"

    def test_debe_manejar_lista_vacia_de_archivos(self):
        """Debe manejar correctamente una lista vacía de archivos."""
        from ci_guardian.validators.code_quality import ejecutar_ruff

        # Act
        exitoso, mensaje = ejecutar_ruff([])

        # Assert
        assert exitoso is True, "Debe retornar True cuando no hay archivos (nada que validar)"
        assert (
            "sin archivos" in mensaje.lower() or "vacío" in mensaje.lower()
        ), "Debe indicar que no hay archivos para validar"

    def test_debe_usar_timeout_de_60_segundos(self, archivos_python_validos):
        """Debe configurar timeout de 60 segundos para evitar bloqueos."""
        from ci_guardian.validators.code_quality import ejecutar_ruff

        # Arrange
        with patch(
            "subprocess.run", return_value=MagicMock(returncode=0, stdout="[]", stderr="")
        ) as mock_run:
            # Act
            ejecutar_ruff(archivos_python_validos)

            # Assert
            assert "timeout" in mock_run.call_args.kwargs, "Debe configurar timeout"
            timeout_usado = mock_run.call_args.kwargs["timeout"]
            assert timeout_usado >= 30, "Timeout debe ser al menos 30 segundos"
            assert timeout_usado <= 120, "Timeout no debe exceder 120 segundos"

    def test_debe_capturar_stdout_y_stderr(self, archivos_python_validos):
        """Debe capturar stdout y stderr para procesar resultados."""
        from ci_guardian.validators.code_quality import ejecutar_ruff

        # Arrange
        with patch(
            "subprocess.run", return_value=MagicMock(returncode=0, stdout="[]", stderr="")
        ) as mock_run:
            # Act
            ejecutar_ruff(archivos_python_validos)

            # Assert
            assert mock_run.call_args.kwargs.get("capture_output") is True or (
                mock_run.call_args.kwargs.get("stdout") == subprocess.PIPE
                and mock_run.call_args.kwargs.get("stderr") == subprocess.PIPE
            ), "Debe capturar stdout y stderr"
            assert (
                mock_run.call_args.kwargs.get("text") is True
            ), "Debe procesar output como texto (no bytes)"

    def test_debe_soportar_modo_fix_para_autocorreccion(self, archivos_python_validos):
        """Debe soportar modo --fix para auto-corregir errores."""
        from ci_guardian.validators.code_quality import ejecutar_ruff

        # Arrange
        with patch(
            "subprocess.run", return_value=MagicMock(returncode=0, stdout="[]", stderr="")
        ) as mock_run:
            # Act
            ejecutar_ruff(archivos_python_validos, fix=True)

            # Assert
            args_llamada = mock_run.call_args[0][0]
            assert "--fix" in args_llamada, "Debe incluir --fix cuando fix=True"

    def test_no_debe_usar_fix_por_defecto(self, archivos_python_validos):
        """Por defecto NO debe usar --fix (solo validar)."""
        from ci_guardian.validators.code_quality import ejecutar_ruff

        # Arrange
        with patch(
            "subprocess.run", return_value=MagicMock(returncode=0, stdout="[]", stderr="")
        ) as mock_run:
            # Act
            ejecutar_ruff(archivos_python_validos)

            # Assert
            args_llamada = mock_run.call_args[0][0]
            assert "--fix" not in args_llamada, "NO debe incluir --fix por defecto"

    def test_debe_manejar_timeout_exception(self, archivos_python_validos):
        """Debe manejar TimeoutExpired cuando Ruff tarda demasiado."""
        from ci_guardian.validators.code_quality import ejecutar_ruff

        # Arrange
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("ruff", 60)):
            # Act
            exitoso, mensaje = ejecutar_ruff(archivos_python_validos)

            # Assert
            assert exitoso is False, "Debe retornar False cuando hay timeout"
            assert (
                "timeout" in mensaje.lower() or "tiempo" in mensaje.lower()
            ), "Debe indicar que hubo timeout"

    def test_debe_rechazar_path_traversal(self, tmp_path):
        """Debe rechazar rutas con path traversal (seguridad)."""
        from ci_guardian.validators.code_quality import ejecutar_ruff

        # Arrange
        archivo_malicioso = tmp_path / ".." / ".." / "etc" / "passwd"

        # Act & Assert
        with pytest.raises(ValueError, match="path traversal|ruta inválida|fuera del proyecto"):
            ejecutar_ruff([archivo_malicioso])

    def test_debe_rechazar_rutas_absolutas_fuera_proyecto(self, tmp_path):
        """Debe rechazar rutas absolutas fuera del directorio del proyecto."""
        from ci_guardian.validators.code_quality import ejecutar_ruff

        # Arrange
        archivo_fuera = Path("/tmp/malicious.py")  # noqa: S108

        # Act & Assert - Debe validar que las rutas sean relativas o dentro del proyecto
        # La implementación decidirá cómo manejar esto (raise o filtrar)
        # Por ahora esperamos que rechace o filtre este tipo de archivos
        with patch(
            "subprocess.run", return_value=MagicMock(returncode=0, stdout="[]", stderr="")
        ) as mock_run:
            # Si no lanza excepción, al menos debe filtrar el archivo
            ejecutar_ruff([archivo_fuera])

            # Si se ejecutó, no debe incluir rutas absolutas fuera del proyecto
            if mock_run.called:
                args_llamada = mock_run.call_args[0][0]
                archivos_procesados = [arg for arg in args_llamada if ".py" in arg]
                # No debe haber procesado archivos en /tmp
                assert not any(
                    "/tmp/" in str(arg) for arg in archivos_procesados  # noqa: S108
                ), "No debe procesar archivos fuera del proyecto"


class TestEjecutorBlack:
    """Tests para el ejecutor de Black (formatter)."""

    @pytest.fixture
    def archivos_python_formateados(self, tmp_path):
        """Crea archivos Python correctamente formateados."""
        archivos = []
        for i in range(2):
            archivo = tmp_path / f"formateado_{i}.py"
            archivo.write_text(
                f'"""Módulo {i}."""\n\n\ndef funcion():\n    pass\n', encoding="utf-8"
            )
            archivos.append(archivo)
        return archivos

    @pytest.fixture
    def mock_subprocess_black_ok(self):
        """Mock de subprocess.run simulando Black sin cambios necesarios."""
        return MagicMock(returncode=0, stdout="All done! ✨ 🍰 ✨", stderr="")

    @pytest.fixture
    def mock_subprocess_black_necesita_formato(self):
        """Mock de subprocess.run simulando Black detectando archivos sin formatear."""
        return MagicMock(returncode=1, stdout="would reformat 2 files", stderr="")

    def test_debe_ejecutar_black_en_modo_check_por_defecto(
        self, archivos_python_formateados, mock_subprocess_black_ok
    ):
        """Debe ejecutar Black en modo --check por defecto (sin modificar archivos)."""
        from ci_guardian.validators.code_quality import ejecutar_black

        # Arrange
        with patch("subprocess.run", return_value=mock_subprocess_black_ok) as mock_run:
            # Act
            exitoso, mensaje = ejecutar_black(archivos_python_formateados)

            # Assert
            assert exitoso is True, "Black debe retornar True cuando archivos están formateados"
            args_llamada = mock_run.call_args[0][0]
            assert "--check" in args_llamada, "Debe incluir --check por defecto"
            assert (
                mock_run.call_args.kwargs.get("shell", False) is False
            ), "NUNCA debe usar shell=True"

    def test_debe_retornar_false_cuando_archivos_necesitan_formato(
        self, archivos_python_formateados, mock_subprocess_black_necesita_formato
    ):
        """Debe retornar False cuando archivos necesitan formateo."""
        from ci_guardian.validators.code_quality import ejecutar_black

        # Arrange
        with patch("subprocess.run", return_value=mock_subprocess_black_necesita_formato):
            # Act
            exitoso, mensaje = ejecutar_black(archivos_python_formateados)

            # Assert
            assert exitoso is False, "Debe retornar False cuando archivos necesitan formato"
            assert len(mensaje) > 0, "Debe incluir mensaje indicando qué archivos necesitan formato"

    def test_debe_ejecutar_black_sin_check_cuando_check_false(
        self, archivos_python_formateados, mock_subprocess_black_ok
    ):
        """Debe ejecutar Black en modo formateo cuando check=False."""
        from ci_guardian.validators.code_quality import ejecutar_black

        # Arrange
        with patch("subprocess.run", return_value=mock_subprocess_black_ok) as mock_run:
            # Act
            exitoso, mensaje = ejecutar_black(archivos_python_formateados, check=False)

            # Assert
            args_llamada = mock_run.call_args[0][0]
            assert "--check" not in args_llamada, "NO debe incluir --check cuando check=False"
            assert exitoso is True, "Debe retornar True si formateo es exitoso"

    def test_debe_filtrar_solo_archivos_python(self, tmp_path):
        """Debe filtrar y procesar solo archivos .py."""
        from ci_guardian.validators.code_quality import ejecutar_black

        # Arrange
        archivo_py = tmp_path / "script.py"
        archivo_py.write_text("def func(): pass", encoding="utf-8")

        archivo_md = tmp_path / "readme.md"
        archivo_md.write_text("# README", encoding="utf-8")

        archivos_mixtos = [archivo_py, archivo_md]

        with patch(
            "subprocess.run", return_value=MagicMock(returncode=0, stdout="", stderr="")
        ) as mock_run:
            # Act
            ejecutar_black(archivos_mixtos)

            # Assert
            args_llamada = mock_run.call_args[0][0]
            archivos_procesados = [arg for arg in args_llamada if ".py" in str(arg)]
            assert len(archivos_procesados) >= 1, "Debe procesar al menos el archivo .py"
            assert not any(
                ".md" in str(arg) for arg in args_llamada
            ), "NO debe procesar archivos que no son .py"

    def test_debe_validar_que_archivos_existan(self, tmp_path):
        """Debe validar que archivos existan antes de ejecutar Black."""
        from ci_guardian.validators.code_quality import ejecutar_black

        # Arrange
        archivo_existe = tmp_path / "existe.py"
        archivo_existe.write_text("pass", encoding="utf-8")

        archivo_no_existe = tmp_path / "fantasma.py"

        archivos = [archivo_existe, archivo_no_existe]

        with patch(
            "subprocess.run", return_value=MagicMock(returncode=0, stdout="", stderr="")
        ) as mock_run:
            # Act
            ejecutar_black(archivos)

            # Assert
            args_llamada = mock_run.call_args[0][0]
            assert str(archivo_existe) in str(args_llamada), "Debe incluir archivos existentes"
            # No debe procesar archivos inexistentes

    def test_debe_manejar_lista_vacia(self):
        """Debe manejar lista vacía de archivos."""
        from ci_guardian.validators.code_quality import ejecutar_black

        # Act
        exitoso, mensaje = ejecutar_black([])

        # Assert
        assert exitoso is True, "Debe retornar True cuando no hay archivos"
        assert (
            "sin archivos" in mensaje.lower() or "vacío" in mensaje.lower()
        ), "Debe indicar que no hay archivos"

    def test_debe_usar_timeout(self, archivos_python_formateados):
        """Debe configurar timeout para evitar bloqueos."""
        from ci_guardian.validators.code_quality import ejecutar_black

        # Arrange
        with patch(
            "subprocess.run", return_value=MagicMock(returncode=0, stdout="", stderr="")
        ) as mock_run:
            # Act
            ejecutar_black(archivos_python_formateados)

            # Assert
            assert "timeout" in mock_run.call_args.kwargs, "Debe configurar timeout"
            timeout_usado = mock_run.call_args.kwargs["timeout"]
            assert timeout_usado >= 30, "Timeout mínimo de 30 segundos"

    def test_debe_capturar_output(self, archivos_python_formateados):
        """Debe capturar stdout y stderr."""
        from ci_guardian.validators.code_quality import ejecutar_black

        # Arrange
        with patch(
            "subprocess.run", return_value=MagicMock(returncode=0, stdout="", stderr="")
        ) as mock_run:
            # Act
            ejecutar_black(archivos_python_formateados)

            # Assert
            assert mock_run.call_args.kwargs.get("capture_output") is True or (
                mock_run.call_args.kwargs.get("stdout") == subprocess.PIPE
            ), "Debe capturar output"
            assert mock_run.call_args.kwargs.get("text") is True, "Debe usar modo texto"

    def test_debe_manejar_timeout_exception(self, archivos_python_formateados):
        """Debe manejar TimeoutExpired correctamente."""
        from ci_guardian.validators.code_quality import ejecutar_black

        # Arrange
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("black", 60)):
            # Act
            exitoso, mensaje = ejecutar_black(archivos_python_formateados)

            # Assert
            assert exitoso is False, "Debe retornar False en timeout"
            assert (
                "timeout" in mensaje.lower() or "tiempo" in mensaje.lower()
            ), "Debe indicar timeout en mensaje"

    def test_debe_rechazar_path_traversal(self, tmp_path):
        """Debe rechazar path traversal."""
        from ci_guardian.validators.code_quality import ejecutar_black

        # Arrange
        archivo_malicioso = tmp_path / ".." / ".." / "etc" / "hosts"

        # Act & Assert
        with pytest.raises(ValueError, match="path traversal|ruta inválida|fuera del proyecto"):
            ejecutar_black([archivo_malicioso])


class TestValidadorCalidadCodigoCombinado:
    """Tests para el validador combinado (Ruff + Black)."""

    @pytest.fixture
    def archivos_python_validos(self, tmp_path):
        """Archivos Python válidos para testing."""
        archivos = []
        for i in range(2):
            archivo = tmp_path / f"modulo_{i}.py"
            archivo.write_text(f'"""Módulo {i}."""\n\n\ndef func():\n    pass\n', encoding="utf-8")
            archivos.append(archivo)
        return archivos

    def test_debe_ejecutar_ruff_y_black_en_secuencia(self, archivos_python_validos):
        """Debe ejecutar primero Ruff, luego Black."""
        from ci_guardian.validators.code_quality import validar_calidad_codigo

        # Arrange
        llamadas = []

        def mock_run(cmd, **kwargs):
            llamadas.append(cmd[0])
            return MagicMock(returncode=0, stdout="[]" if cmd[0] == "ruff" else "", stderr="")

        with patch("subprocess.run", side_effect=mock_run):
            # Act
            validar_calidad_codigo(archivos_python_validos)

            # Assert
            assert len(llamadas) >= 2, "Debe ejecutar al menos 2 comandos"
            assert llamadas[0] == "ruff", "Primero debe ejecutar Ruff"
            assert llamadas[1] == "black", "Segundo debe ejecutar Black"

    def test_debe_retornar_true_cuando_ambos_pasan(self, archivos_python_validos):
        """Debe retornar True solo cuando Ruff y Black pasan."""
        from ci_guardian.validators.code_quality import validar_calidad_codigo

        # Arrange
        def mock_run(cmd, **kwargs):
            return MagicMock(returncode=0, stdout="[]" if cmd[0] == "ruff" else "", stderr="")

        with patch("subprocess.run", side_effect=mock_run):
            # Act
            resultado = validar_calidad_codigo(archivos_python_validos)

            # Assert
            assert resultado is True, "Debe retornar True cuando ambos pasan"

    def test_debe_retornar_false_cuando_ruff_falla(self, archivos_python_validos):
        """Debe retornar False si Ruff detecta errores."""
        from ci_guardian.validators.code_quality import validar_calidad_codigo

        # Arrange
        def mock_run(cmd, **kwargs):
            if cmd[0] == "ruff":
                return MagicMock(returncode=1, stdout='[{"code":"E501"}]', stderr="")
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=mock_run):
            # Act
            resultado = validar_calidad_codigo(archivos_python_validos)

            # Assert
            assert resultado is False, "Debe retornar False cuando Ruff falla"

    def test_debe_retornar_false_cuando_black_falla(self, archivos_python_validos):
        """Debe retornar False si Black detecta archivos sin formatear."""
        from ci_guardian.validators.code_quality import validar_calidad_codigo

        # Arrange
        def mock_run(cmd, **kwargs):
            if cmd[0] == "black":
                return MagicMock(returncode=1, stdout="would reformat", stderr="")
            return MagicMock(returncode=0, stdout="[]", stderr="")

        with patch("subprocess.run", side_effect=mock_run):
            # Act
            resultado = validar_calidad_codigo(archivos_python_validos)

            # Assert
            assert resultado is False, "Debe retornar False cuando Black falla"

    def test_debe_retornar_false_cuando_ambos_fallan(self, archivos_python_validos):
        """Debe retornar False cuando ambos fallan."""
        from ci_guardian.validators.code_quality import validar_calidad_codigo

        # Arrange
        def mock_run(cmd, **kwargs):
            return MagicMock(returncode=1, stdout="error", stderr="")

        with patch("subprocess.run", side_effect=mock_run):
            # Act
            resultado = validar_calidad_codigo(archivos_python_validos)

            # Assert
            assert resultado is False, "Debe retornar False cuando ambos fallan"

    def test_debe_soportar_modo_fix(self, archivos_python_validos):
        """Debe soportar modo fix para auto-corregir errores."""
        from ci_guardian.validators.code_quality import validar_calidad_codigo

        # Arrange
        with patch(
            "subprocess.run", return_value=MagicMock(returncode=0, stdout="[]", stderr="")
        ) as mock_run:
            # Act
            validar_calidad_codigo(archivos_python_validos, fix=True)

            # Assert
            # Verificar que al menos una llamada incluyó --fix
            [call[0][0] for call in mock_run.call_args_list]
            args_todas_llamadas = [arg for call in mock_run.call_args_list for arg in call[0][0]]
            assert "--fix" in args_todas_llamadas, "Debe pasar --fix a Ruff cuando fix=True"

    def test_debe_reportar_cual_herramienta_fallo(self, archivos_python_validos):
        """Debe indicar qué herramienta falló en el resultado."""
        from ci_guardian.validators.code_quality import validar_calidad_codigo

        # Arrange - Ruff falla
        def mock_run_ruff_fail(cmd, **kwargs):
            if cmd[0] == "ruff":
                return MagicMock(returncode=1, stdout='[{"code":"E501"}]', stderr="")
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=mock_run_ruff_fail):
            # Act
            resultado = validar_calidad_codigo(archivos_python_validos)

            # Assert
            assert resultado is False, "Debe retornar False"
            # La implementación puede loggear o retornar mensaje indicando qué falló

    def test_debe_manejar_lista_vacia(self):
        """Debe manejar lista vacía de archivos."""
        from ci_guardian.validators.code_quality import validar_calidad_codigo

        # Act
        resultado = validar_calidad_codigo([])

        # Assert
        assert resultado is True, "Debe retornar True cuando no hay archivos (nada que validar)"


class TestSeguridadCodeQuality:
    """Tests de seguridad para validadores de calidad."""

    def test_nunca_debe_usar_shell_true_en_ruff(self, tmp_path):
        """CRÍTICO: Nunca debe usar shell=True con Ruff (command injection)."""
        from ci_guardian.validators.code_quality import ejecutar_ruff

        # Arrange
        archivo = tmp_path / "test.py"
        archivo.write_text("pass", encoding="utf-8")

        with patch(
            "subprocess.run", return_value=MagicMock(returncode=0, stdout="[]", stderr="")
        ) as mock_run:
            # Act
            ejecutar_ruff([archivo])

            # Assert
            assert (
                mock_run.call_args.kwargs.get("shell") is False
                or "shell" not in mock_run.call_args.kwargs
            ), "NUNCA debe usar shell=True - vulnerabilidad crítica de command injection"

    def test_nunca_debe_usar_shell_true_en_black(self, tmp_path):
        """CRÍTICO: Nunca debe usar shell=True con Black."""
        from ci_guardian.validators.code_quality import ejecutar_black

        # Arrange
        archivo = tmp_path / "test.py"
        archivo.write_text("pass", encoding="utf-8")

        with patch(
            "subprocess.run", return_value=MagicMock(returncode=0, stdout="", stderr="")
        ) as mock_run:
            # Act
            ejecutar_black([archivo])

            # Assert
            assert (
                mock_run.call_args.kwargs.get("shell") is False
                or "shell" not in mock_run.call_args.kwargs
            ), "NUNCA debe usar shell=True - vulnerabilidad crítica"

    def test_debe_validar_extension_python_ruff(self, tmp_path):
        """Debe validar que solo se procesen archivos .py (seguridad)."""
        from ci_guardian.validators.code_quality import ejecutar_ruff

        # Arrange
        archivo_malicioso = tmp_path / "malicious.sh"
        archivo_malicioso.write_text("#!/bin/bash\nrm -rf /", encoding="utf-8")

        with patch(
            "subprocess.run", return_value=MagicMock(returncode=0, stdout="[]", stderr="")
        ) as mock_run:
            # Act
            ejecutar_ruff([archivo_malicioso])

            # Assert
            # Debe filtrar archivos que no son .py
            if mock_run.called:
                args = mock_run.call_args[0][0]
                assert not any(
                    ".sh" in str(arg) for arg in args
                ), "NO debe procesar archivos que no son .py"

    def test_debe_validar_extension_python_black(self, tmp_path):
        """Debe validar que solo se procesen archivos .py."""
        from ci_guardian.validators.code_quality import ejecutar_black

        # Arrange
        archivo_malicioso = tmp_path / "exploit.exe"
        archivo_malicioso.write_text("binary data", encoding="utf-8")

        with patch(
            "subprocess.run", return_value=MagicMock(returncode=0, stdout="", stderr="")
        ) as mock_run:
            # Act
            ejecutar_black([archivo_malicioso])

            # Assert
            if mock_run.called:
                args = mock_run.call_args[0][0]
                assert not any(
                    ".exe" in str(arg) for arg in args
                ), "NO debe procesar archivos que no son .py"

    def test_debe_sanitizar_paths_relativos_peligrosos(self, tmp_path):
        """Debe rechazar paths con .. (path traversal)."""
        from ci_guardian.validators.code_quality import ejecutar_ruff

        # Arrange
        archivo_traversal = Path("../../etc/passwd.py")

        # Act & Assert
        with pytest.raises(ValueError, match="path traversal|ruta inválida|fuera del proyecto"):
            ejecutar_ruff([archivo_traversal])

    def test_debe_rechazar_comandos_inyectados_en_nombres_archivo(self, tmp_path):
        """Debe manejar nombres de archivo maliciosos sin ejecutar comandos."""
        from ci_guardian.validators.code_quality import ejecutar_ruff

        # Arrange
        archivo_malicioso = tmp_path / "test; rm -rf /.py"
        # Incluso si el archivo existe, no debe ejecutar el comando inyectado
        try:
            archivo_malicioso.touch()
        except OSError:
            pytest.skip("Sistema de archivos no permite este nombre")

        with patch(
            "subprocess.run", return_value=MagicMock(returncode=0, stdout="[]", stderr="")
        ) as mock_run:
            # Act
            ejecutar_ruff([archivo_malicioso])

            # Assert
            # El path debe ser pasado como argumento de lista, NO concatenado en string
            assert (
                mock_run.call_args.kwargs.get("shell") is False
            ), "Debe usar shell=False para prevenir ejecución de comandos inyectados"

            # Los argumentos deben ser lista, no string concatenado
            args = mock_run.call_args[0][0]
            assert isinstance(args, list), "Argumentos deben ser lista, no string"


class TestEdgeCasesCodeQuality:
    """Tests de casos límite y edge cases."""

    def test_debe_manejar_archivo_vacio(self, tmp_path):
        """Debe manejar archivos Python vacíos."""
        from ci_guardian.validators.code_quality import ejecutar_ruff

        # Arrange
        archivo_vacio = tmp_path / "vacio.py"
        archivo_vacio.write_text("", encoding="utf-8")

        with patch(
            "subprocess.run", return_value=MagicMock(returncode=0, stdout="[]", stderr="")
        ) as mock_run:
            # Act
            exitoso, mensaje = ejecutar_ruff([archivo_vacio])

            # Assert
            # Debe procesar sin errores
            assert mock_run.called or exitoso is True, "Debe manejar archivos vacíos sin errores"

    def test_debe_manejar_archivos_sin_permisos_lectura(self, tmp_path):
        """Debe manejar archivos sin permisos de lectura."""
        from ci_guardian.validators.code_quality import ejecutar_ruff

        # Arrange
        archivo_sin_permisos = tmp_path / "sin_permisos.py"
        archivo_sin_permisos.write_text("pass", encoding="utf-8")

        if platform.system() != "Windows":
            archivo_sin_permisos.chmod(0o000)  # Sin permisos

        with patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="[]", stderr="")):
            # Act - La herramienta externa manejará el error
            exitoso, mensaje = ejecutar_ruff([archivo_sin_permisos])

            # Assert - Debe intentar ejecutar o filtrar archivos no legibles
            # La implementación puede variar, pero no debe crashear
            assert isinstance(
                exitoso, bool
            ), "Debe retornar booleano incluso con errores de permisos"

    def test_debe_manejar_file_not_found_error(self, tmp_path):
        """Debe manejar FileNotFoundError cuando Ruff no está instalado."""
        from ci_guardian.validators.code_quality import ejecutar_ruff

        # Arrange
        archivo = tmp_path / "test.py"
        archivo.write_text("pass", encoding="utf-8")

        with patch("subprocess.run", side_effect=FileNotFoundError("ruff not found")):
            # Act
            exitoso, mensaje = ejecutar_ruff([archivo])

            # Assert
            assert exitoso is False, "Debe retornar False cuando la herramienta no existe"
            assert "ruff" in mensaje.lower() and (
                "encontrado" in mensaje.lower() or "instalado" in mensaje.lower()
            ), "Debe indicar que Ruff no está instalado"

    def test_debe_manejar_file_not_found_black(self, tmp_path):
        """Debe manejar FileNotFoundError cuando Black no está instalado."""
        from ci_guardian.validators.code_quality import ejecutar_black

        # Arrange
        archivo = tmp_path / "test.py"
        archivo.write_text("pass", encoding="utf-8")

        with patch("subprocess.run", side_effect=FileNotFoundError("black not found")):
            # Act
            exitoso, mensaje = ejecutar_black([archivo])

            # Assert
            assert exitoso is False, "Debe retornar False cuando Black no existe"
            assert "black" in mensaje.lower() and (
                "encontrado" in mensaje.lower() or "instalado" in mensaje.lower()
            ), "Debe indicar que Black no está instalado"

    def test_debe_manejar_rutas_con_espacios(self, tmp_path):
        """Debe manejar correctamente rutas con espacios."""
        from ci_guardian.validators.code_quality import ejecutar_ruff

        # Arrange
        directorio_con_espacios = tmp_path / "mi carpeta con espacios"
        directorio_con_espacios.mkdir()
        archivo = directorio_con_espacios / "archivo con espacios.py"
        archivo.write_text("def func(): pass", encoding="utf-8")

        with patch(
            "subprocess.run", return_value=MagicMock(returncode=0, stdout="[]", stderr="")
        ) as mock_run:
            # Act
            ejecutar_ruff([archivo])

            # Assert
            assert mock_run.called, "Debe ejecutar incluso con espacios en rutas"
            # Verificar que los argumentos son lista (maneja espacios automáticamente)
            args = mock_run.call_args[0][0]
            assert isinstance(args, list), "Debe pasar argumentos como lista para manejar espacios"

    @pytest.mark.skipif(platform.system() == "Windows", reason="Test específico de Linux/Mac")
    def test_debe_manejar_symlinks(self, tmp_path):
        """Debe manejar symlinks correctamente."""
        from ci_guardian.validators.code_quality import ejecutar_ruff

        # Arrange
        archivo_real = tmp_path / "real.py"
        archivo_real.write_text("pass", encoding="utf-8")

        symlink = tmp_path / "link.py"
        symlink.symlink_to(archivo_real)

        with patch(
            "subprocess.run", return_value=MagicMock(returncode=0, stdout="[]", stderr="")
        ) as mock_run:
            # Act
            exitoso, mensaje = ejecutar_ruff([symlink])

            # Assert
            assert mock_run.called or exitoso is True, "Debe manejar symlinks correctamente"
