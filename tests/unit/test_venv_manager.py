"""
Tests para el gestor de entornos virtuales (LIB-2).

Este módulo prueba la funcionalidad de detección, validación y creación
de entornos virtuales de Python en diferentes plataformas.

Todos estos tests deben FALLAR inicialmente (FASE RED) porque el código
de producción aún no ha sido implementado.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Importaciones del módulo bajo prueba (fallará hasta implementar el código)
from ci_guardian.core.venv_manager import (
    crear_venv,
    detectar_venv,
    esta_en_venv,
    obtener_python_ejecutable,
    validar_venv,
)


class TestDetectarVenv:
    """Tests para la función detectar_venv()."""

    def test_debe_detectar_venv_en_linux(self, proyecto_con_venv_linux: Path) -> None:
        """Debe detectar venv/ con estructura bin/python en Linux."""
        # Arrange
        with patch("platform.system", return_value="Linux"):
            # Act
            resultado = detectar_venv(proyecto_con_venv_linux)

            # Assert
            assert resultado is not None, "Debe detectar el venv en Linux"
            assert resultado.name == "venv", "Debe retornar el directorio venv/"
            assert (resultado / "bin" / "python").exists(), "Debe tener bin/python"

    def test_debe_detectar_venv_en_windows(self, proyecto_con_venv_windows: Path) -> None:
        """Debe detectar venv/ con estructura Scripts/python.exe en Windows."""
        # Arrange
        with patch("platform.system", return_value="Windows"):
            # Act
            resultado = detectar_venv(proyecto_con_venv_windows)

            # Assert
            assert resultado is not None, "Debe detectar el venv en Windows"
            assert resultado.name == "venv", "Debe retornar el directorio venv/"
            assert (resultado / "Scripts" / "python.exe").exists(), "Debe tener Scripts/python.exe"

    def test_debe_detectar_dotvenv_en_linux(self, proyecto_con_dotvenv: Path) -> None:
        """Debe detectar .venv/ como alternativa a venv/."""
        # Arrange
        with patch("platform.system", return_value="Linux"):
            # Act
            resultado = detectar_venv(proyecto_con_dotvenv)

            # Assert
            assert resultado is not None, "Debe detectar .venv/"
            assert resultado.name == ".venv", "Debe retornar el directorio .venv/"

    def test_debe_priorizar_venv_sobre_dotvenv(self, tmp_path: Path) -> None:
        """Debe priorizar venv/ sobre .venv/ cuando ambos existen."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        # Crear venv/
        venv = proyecto / "venv"
        venv.mkdir()
        (venv / "bin").mkdir()
        (venv / "bin" / "python").touch()
        (venv / "bin" / "python").chmod(0o755)

        # Crear .venv/
        dotvenv = proyecto / ".venv"
        dotvenv.mkdir()
        (dotvenv / "bin").mkdir()
        (dotvenv / "bin" / "python").touch()
        (dotvenv / "bin" / "python").chmod(0o755)

        with patch("platform.system", return_value="Linux"):
            # Act
            resultado = detectar_venv(proyecto)

            # Assert
            assert (
                resultado is not None and resultado.name == "venv"
            ), "Debe priorizar venv/ sobre .venv/"

    def test_debe_buscar_env_y_ENV_como_alternativas(self, tmp_path: Path) -> None:
        """Debe buscar env/, .env/, ENV/ si no existe venv/."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        # Crear solo env/
        env = proyecto / "env"
        env.mkdir()
        (env / "bin").mkdir()
        (env / "bin" / "python").touch()
        (env / "bin" / "python").chmod(0o755)

        with patch("platform.system", return_value="Linux"):
            # Act
            resultado = detectar_venv(proyecto)

            # Assert
            assert resultado is not None, "Debe detectar env/"
            assert resultado.name == "env", "Debe retornar el directorio env/"

    def test_debe_retornar_none_si_no_existe_venv(self, directorio_no_git: Path) -> None:
        """Debe retornar None si no existe ningún venv en el proyecto."""
        # Arrange
        with patch("platform.system", return_value="Linux"):
            # Act
            resultado = detectar_venv(directorio_no_git)

            # Assert
            assert resultado is None, "Debe retornar None si no hay venv"

    def test_debe_retornar_none_si_directorio_existe_pero_no_es_venv(self, tmp_path: Path) -> None:
        """Debe retornar None si el directorio venv/ existe pero no es válido."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        # Crear directorio venv/ vacío (sin bin/ ni Scripts/)
        venv = proyecto / "venv"
        venv.mkdir()

        with patch("platform.system", return_value="Linux"):
            # Act
            resultado = detectar_venv(proyecto)

            # Assert
            assert resultado is None, "Debe retornar None si venv/ existe pero no es válido"

    def test_debe_resolver_symlinks_correctamente(self, tmp_path: Path) -> None:
        """Debe resolver symlinks y retornar el path absoluto real."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        # Crear venv real
        venv_real = tmp_path / "venv_real"
        venv_real.mkdir()
        (venv_real / "bin").mkdir()
        (venv_real / "bin" / "python").touch()
        (venv_real / "bin" / "python").chmod(0o755)

        # Crear symlink en el proyecto
        venv_link = proyecto / "venv"
        venv_link.symlink_to(venv_real)

        with patch("platform.system", return_value="Linux"):
            # Act
            resultado = detectar_venv(proyecto)

            # Assert
            assert resultado is not None, "Debe detectar el venv a través del symlink"
            assert (
                resultado.resolve() == venv_real.resolve()
            ), "Debe resolver el symlink al path real"

    def test_debe_detectar_python3_si_no_existe_python(self, tmp_path: Path) -> None:
        """Debe aceptar bin/python3 si no existe bin/python."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        venv = proyecto / "venv"
        venv.mkdir()
        (venv / "bin").mkdir()
        # Solo crear python3, no python
        (venv / "bin" / "python3").touch()
        (venv / "bin" / "python3").chmod(0o755)

        with patch("platform.system", return_value="Linux"):
            # Act
            resultado = detectar_venv(proyecto)

            # Assert
            assert resultado is not None, "Debe detectar venv con python3"
            assert (resultado / "bin" / "python3").exists(), "Debe tener bin/python3"

    @pytest.mark.skipif(platform.system() != "Darwin", reason="Test específico de macOS")
    def test_debe_funcionar_en_macos(self, tmp_path: Path) -> None:
        """Debe funcionar correctamente en macOS (misma lógica que Linux)."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        venv = proyecto / "venv"
        venv.mkdir()
        (venv / "bin").mkdir()
        (venv / "bin" / "python").touch()
        (venv / "bin" / "python").chmod(0o755)

        # Act (sin mock, usa el sistema real)
        resultado = detectar_venv(proyecto)

        # Assert
        assert resultado is not None, "Debe detectar venv en macOS"
        assert resultado.name == "venv"


class TestValidarVenv:
    """Tests para la función validar_venv()."""

    def test_debe_validar_venv_funcional_en_linux(self, venv_linux_mock: Path) -> None:
        """Debe validar un venv funcional en Linux."""
        # Arrange
        with patch("platform.system", return_value="Linux"):
            # Act
            resultado = validar_venv(venv_linux_mock)

            # Assert
            assert resultado is True, "Debe validar venv funcional en Linux"

    def test_debe_validar_venv_funcional_en_windows(self, venv_windows_mock: Path) -> None:
        """Debe validar un venv funcional en Windows."""
        # Arrange
        with patch("platform.system", return_value="Windows"):
            # Act
            resultado = validar_venv(venv_windows_mock)

            # Assert
            assert resultado is True, "Debe validar venv funcional en Windows"

    def test_debe_rechazar_venv_sin_ejecutable_python(self, venv_corrupto: Path) -> None:
        """Debe rechazar venv que no tiene ejecutable Python."""
        # Arrange
        with patch("platform.system", return_value="Linux"):
            # Act
            resultado = validar_venv(venv_corrupto)

            # Assert
            assert resultado is False, "Debe rechazar venv sin ejecutable Python"

    def test_debe_rechazar_directorio_vacio(self, tmp_path: Path) -> None:
        """Debe rechazar un directorio vacío que no es venv."""
        # Arrange
        venv_vacio = tmp_path / "venv"
        venv_vacio.mkdir()

        with patch("platform.system", return_value="Linux"):
            # Act
            resultado = validar_venv(venv_vacio)

            # Assert
            assert resultado is False, "Debe rechazar directorio vacío"

    def test_debe_rechazar_venv_sin_bin_o_scripts(self, tmp_path: Path) -> None:
        """Debe rechazar venv sin estructura bin/ o Scripts/."""
        # Arrange
        venv = tmp_path / "venv"
        venv.mkdir()
        # Crear python directamente sin bin/
        (venv / "python").touch()

        with patch("platform.system", return_value="Linux"):
            # Act
            resultado = validar_venv(venv)

            # Assert
            assert resultado is False, "Debe rechazar venv sin estructura bin/ o Scripts/"

    def test_debe_rechazar_ejecutable_python_sin_permisos_en_linux(
        self, venv_sin_permisos: Path
    ) -> None:
        """Debe rechazar venv con Python sin permisos de ejecución en Linux."""
        # Arrange
        with patch("platform.system", return_value="Linux"):
            # Act
            resultado = validar_venv(venv_sin_permisos)

            # Assert
            assert resultado is False, "Debe rechazar Python sin permisos de ejecución"

    def test_debe_validar_venv_con_python3_en_linux(self, tmp_path: Path) -> None:
        """Debe validar venv que solo tiene python3 en lugar de python."""
        # Arrange
        venv = tmp_path / "venv"
        venv.mkdir()
        (venv / "bin").mkdir()
        # Solo python3
        (venv / "bin" / "python3").touch()
        (venv / "bin" / "python3").chmod(0o755)

        with patch("platform.system", return_value="Linux"):
            # Act
            resultado = validar_venv(venv)

            # Assert
            assert resultado is True, "Debe validar venv con python3"

    def test_debe_rechazar_path_que_no_existe(self, tmp_path: Path) -> None:
        """Debe rechazar un path que no existe."""
        # Arrange
        venv_inexistente = tmp_path / "venv_inexistente"

        with patch("platform.system", return_value="Linux"):
            # Act
            resultado = validar_venv(venv_inexistente)

            # Assert
            assert resultado is False, "Debe rechazar path que no existe"

    def test_debe_rechazar_path_que_es_archivo(self, tmp_path: Path) -> None:
        """Debe rechazar un path que apunta a un archivo en lugar de directorio."""
        # Arrange
        archivo = tmp_path / "no_es_directorio.txt"
        archivo.touch()

        with patch("platform.system", return_value="Linux"):
            # Act
            resultado = validar_venv(archivo)

            # Assert
            assert resultado is False, "Debe rechazar archivo como venv"


class TestCrearVenv:
    """Tests para la función crear_venv()."""

    def test_debe_crear_venv_exitosamente_en_linux(self, tmp_path: Path) -> None:
        """Debe crear un nuevo venv funcional en Linux."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        mock_subprocess = MagicMock()
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch("platform.system", return_value="Linux"),
            patch("subprocess.run", mock_subprocess),
            patch("ci_guardian.core.venv_manager.validar_venv", return_value=True) as mock_validar,
        ):
            # Act
            resultado = crear_venv(proyecto)

            # Assert
            assert resultado == proyecto / "venv", "Debe retornar path al venv creado"
            mock_subprocess.assert_called_once()
            # Verificar que el comando es correcto
            args = mock_subprocess.call_args[0][0]
            assert args[0] == sys.executable, "Debe usar sys.executable"
            assert args[1] == "-m", "Debe usar -m para módulo"
            assert args[2] == "venv", "Debe llamar al módulo venv"
            # Verificar que se validó el venv creado
            mock_validar.assert_called_once()

    def test_debe_crear_venv_exitosamente_en_windows(self, tmp_path: Path) -> None:
        """Debe crear un nuevo venv funcional en Windows."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        mock_subprocess = MagicMock()
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch("platform.system", return_value="Windows"),
            patch("subprocess.run", mock_subprocess),
            patch("ci_guardian.core.venv_manager.validar_venv", return_value=True),
        ):
            # Act
            resultado = crear_venv(proyecto)

            # Assert
            assert resultado == proyecto / "venv", "Debe retornar path al venv creado"
            mock_subprocess.assert_called_once()

    def test_debe_crear_venv_con_nombre_personalizado(self, tmp_path: Path) -> None:
        """Debe crear venv con nombre personalizado."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()
        nombre_custom = ".venv_custom"

        mock_subprocess = MagicMock()
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch("platform.system", return_value="Linux"),
            patch("subprocess.run", mock_subprocess),
            patch("ci_guardian.core.venv_manager.validar_venv", return_value=True),
        ):
            # Act
            resultado = crear_venv(proyecto, nombre_venv=nombre_custom)

            # Assert
            assert resultado == proyecto / nombre_custom, "Debe crear venv con nombre personalizado"
            args = mock_subprocess.call_args[0][0]
            assert str(proyecto / nombre_custom) in " ".join(
                args
            ), "Debe usar el nombre personalizado"

    def test_debe_levantar_runtime_error_si_subprocess_falla(self, tmp_path: Path) -> None:
        """Debe levantar RuntimeError si subprocess.run falla."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        mock_subprocess = MagicMock()
        mock_subprocess.return_value = MagicMock(
            returncode=1, stdout="", stderr="Error al crear venv"
        )

        with (
            patch("platform.system", return_value="Linux"),
            patch("subprocess.run", mock_subprocess),
        ):
            # Act & Assert
            with pytest.raises(RuntimeError, match="Error al crear el entorno virtual"):
                crear_venv(proyecto)

    def test_debe_levantar_runtime_error_si_venv_creado_no_es_valido(self, tmp_path: Path) -> None:
        """Debe levantar RuntimeError si el venv creado no pasa validación."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        mock_subprocess = MagicMock()
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch("platform.system", return_value="Linux"),
            patch("subprocess.run", mock_subprocess),
            patch("ci_guardian.core.venv_manager.validar_venv", return_value=False),
        ):  # Validación falla
            # Act & Assert
            with pytest.raises(RuntimeError, match="El entorno virtual creado no es válido"):
                crear_venv(proyecto)

    def test_debe_usar_shell_false_por_seguridad(self, tmp_path: Path) -> None:
        """Debe usar shell=False en subprocess.run por seguridad."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        mock_subprocess = MagicMock()
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch("platform.system", return_value="Linux"),
            patch("subprocess.run", mock_subprocess),
            patch("ci_guardian.core.venv_manager.validar_venv", return_value=True),
        ):
            # Act
            crear_venv(proyecto)

            # Assert
            # Verificar que shell NO está en True
            call_kwargs = mock_subprocess.call_args[1]
            assert call_kwargs.get("shell") is not True, "NO debe usar shell=True por seguridad"

    def test_debe_tener_timeout_en_subprocess(self, tmp_path: Path) -> None:
        """Debe configurar un timeout en subprocess.run."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        mock_subprocess = MagicMock()
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch("platform.system", return_value="Linux"),
            patch("subprocess.run", mock_subprocess),
            patch("ci_guardian.core.venv_manager.validar_venv", return_value=True),
        ):
            # Act
            crear_venv(proyecto)

            # Assert
            call_kwargs = mock_subprocess.call_args[1]
            assert "timeout" in call_kwargs, "Debe configurar timeout en subprocess.run"
            assert call_kwargs["timeout"] > 0, "Timeout debe ser mayor a 0"

    def test_debe_capturar_output_de_subprocess(self, tmp_path: Path) -> None:
        """Debe capturar stdout y stderr de subprocess.run."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        mock_subprocess = MagicMock()
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch("platform.system", return_value="Linux"),
            patch("subprocess.run", mock_subprocess),
            patch("ci_guardian.core.venv_manager.validar_venv", return_value=True),
        ):
            # Act
            crear_venv(proyecto)

            # Assert
            call_kwargs = mock_subprocess.call_args[1]
            assert call_kwargs.get("capture_output") is True or (
                call_kwargs.get("stdout") is not None and call_kwargs.get("stderr") is not None
            ), "Debe capturar stdout y stderr"

    def test_debe_manejar_subprocess_timeout_exception(self, tmp_path: Path) -> None:
        """Debe manejar TimeoutExpired exception de subprocess."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        mock_subprocess = MagicMock()
        mock_subprocess.side_effect = subprocess.TimeoutExpired(cmd="venv", timeout=60)

        with (
            patch("platform.system", return_value="Linux"),
            patch("subprocess.run", mock_subprocess),
        ):
            # Act & Assert
            with pytest.raises(RuntimeError, match="Timeout al crear el entorno virtual"):
                crear_venv(proyecto)

    def test_debe_rechazar_nombre_venv_con_path_traversal(self, tmp_path: Path) -> None:
        """Debe rechazar nombres de venv con path traversal (..)."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        # Act & Assert
        with pytest.raises(ValueError, match="Nombre de venv no válido"):
            crear_venv(proyecto, nombre_venv="../malicious")

        with pytest.raises(ValueError, match="Nombre de venv no válido"):
            crear_venv(proyecto, nombre_venv="/etc/passwd")

    def test_debe_rechazar_nombre_venv_con_caracteres_peligrosos(self, tmp_path: Path) -> None:
        """Debe rechazar nombres de venv con caracteres peligrosos."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        # Act & Assert
        with pytest.raises(ValueError, match="Nombre de venv no válido"):
            crear_venv(proyecto, nombre_venv="venv; rm -rf /")

        with pytest.raises(ValueError, match="Nombre de venv no válido"):
            crear_venv(proyecto, nombre_venv="venv && malicious")

    def test_debe_rechazar_paths_absolutos_windows(self, tmp_path: Path) -> None:
        """Debe rechazar paths absolutos de Windows (C:\\, D:/, etc.)."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        # Act & Assert - Windows drive letters
        # En Linux, estos paths se detectan por ":" (caracteres peligrosos)
        # En Windows, se detectan por is_absolute()
        with pytest.raises(ValueError, match="(path absoluto|caracteres peligrosos)"):
            crear_venv(proyecto, nombre_venv="C:\\Windows\\System32\\venv")

        with pytest.raises(ValueError, match="(path absoluto|caracteres peligrosos)"):
            crear_venv(proyecto, nombre_venv="D:/tmp/venv")

    @pytest.mark.skipif(platform.system() != "Windows", reason="UNC paths only on Windows")
    def test_debe_rechazar_unc_paths_windows(self, tmp_path: Path) -> None:
        """Debe rechazar UNC paths de Windows (\\\\server\\share)."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        # Act & Assert - UNC paths
        # En Linux, \\server\share\venv es un nombre relativo válido (no es peligroso)
        # En Windows, es un path absoluto UNC y debe ser rechazado
        with pytest.raises(ValueError, match="path absoluto"):
            crear_venv(proyecto, nombre_venv="\\\\server\\share\\venv")

    def test_debe_rechazar_paths_absolutos_unix(self, tmp_path: Path) -> None:
        """Debe rechazar paths absolutos Unix (/path)."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        # Act & Assert
        with pytest.raises(ValueError, match="path absoluto"):
            crear_venv(proyecto, nombre_venv="/tmp/venv")  # noqa: S108 - Testing path validation

        with pytest.raises(ValueError, match="path absoluto"):
            crear_venv(
                proyecto, nombre_venv="/etc/malicious_venv"
            )  # noqa: S108 - Testing path validation

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific test")
    def test_debe_rechazar_nombres_reservados_windows(self, tmp_path: Path) -> None:
        """Debe rechazar nombres reservados de Windows (CON, PRN, AUX, etc.)."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        # Act & Assert
        nombres_reservados = ["CON", "PRN", "AUX", "NUL", "COM1", "LPT1"]
        for nombre in nombres_reservados:
            with pytest.raises(ValueError, match="nombre reservado"):
                crear_venv(proyecto, nombre_venv=nombre)


class TestObtenerPythonEjecutable:
    """Tests para la función obtener_python_ejecutable()."""

    def test_debe_retornar_bin_python_en_linux(self, venv_linux_mock: Path) -> None:
        """Debe retornar bin/python en Linux/macOS."""
        # Arrange
        with patch("platform.system", return_value="Linux"):
            # Act
            resultado = obtener_python_ejecutable(venv_linux_mock)

            # Assert
            assert (
                resultado == venv_linux_mock / "bin" / "python"
            ), "Debe retornar bin/python en Linux"
            assert resultado.exists(), "El ejecutable debe existir"

    def test_debe_retornar_scripts_python_exe_en_windows(self, venv_windows_mock: Path) -> None:
        """Debe retornar Scripts/python.exe en Windows."""
        # Arrange
        with patch("platform.system", return_value="Windows"):
            # Act
            resultado = obtener_python_ejecutable(venv_windows_mock)

            # Assert
            assert (
                resultado == venv_windows_mock / "Scripts" / "python.exe"
            ), "Debe retornar Scripts/python.exe en Windows"
            assert resultado.exists(), "El ejecutable debe existir"

    def test_debe_resolver_path_correctamente(self, venv_linux_mock: Path) -> None:
        """Debe resolver el path con .resolve()."""
        # Arrange
        with patch("platform.system", return_value="Linux"):
            # Act
            resultado = obtener_python_ejecutable(venv_linux_mock)

            # Assert
            assert resultado.is_absolute(), "Debe retornar path absoluto"
            assert resultado == resultado.resolve(), "Debe estar resuelto"

    def test_debe_levantar_filenotfound_si_no_existe_ejecutable(self, venv_corrupto: Path) -> None:
        """Debe levantar FileNotFoundError si no existe el ejecutable."""
        # Arrange
        with patch("platform.system", return_value="Linux"):
            # Act & Assert
            with pytest.raises(FileNotFoundError, match="Ejecutable Python no encontrado"):
                obtener_python_ejecutable(venv_corrupto)

    def test_debe_levantar_filenotfound_si_venv_no_existe(self, tmp_path: Path) -> None:
        """Debe levantar FileNotFoundError si el venv no existe."""
        # Arrange
        venv_inexistente = tmp_path / "venv_inexistente"

        with patch("platform.system", return_value="Linux"):
            # Act & Assert
            with pytest.raises(FileNotFoundError, match="Ejecutable Python no encontrado"):
                obtener_python_ejecutable(venv_inexistente)

    @pytest.mark.skipif(platform.system() != "Darwin", reason="Test específico de macOS")
    def test_debe_funcionar_en_macos(self, tmp_path: Path) -> None:
        """Debe funcionar correctamente en macOS (misma lógica que Linux)."""
        # Arrange
        venv = tmp_path / "venv"
        venv.mkdir()
        (venv / "bin").mkdir()
        (venv / "bin" / "python").touch()
        (venv / "bin" / "python").chmod(0o755)

        # Act (sin mock, usa el sistema real)
        resultado = obtener_python_ejecutable(venv)

        # Assert
        assert resultado == venv / "bin" / "python"


class TestEstaEnVenv:
    """Tests para la función esta_en_venv()."""

    def test_debe_detectar_ejecucion_dentro_de_venv_con_sys_prefix(self) -> None:
        """Debe detectar cuando sys.prefix != sys.base_prefix."""
        # Arrange
        with patch("sys.prefix", "/home/user/proyecto/venv"), patch("sys.base_prefix", "/usr"):
            # Act
            resultado = esta_en_venv()

            # Assert
            assert resultado is True, "Debe detectar venv cuando prefix es diferente"

    def test_debe_detectar_ejecucion_fuera_de_venv_con_sys_prefix(self) -> None:
        """Debe detectar cuando sys.prefix == sys.base_prefix."""
        # Arrange
        with (
            patch("sys.prefix", "/usr"),
            patch("sys.base_prefix", "/usr"),
            patch.dict(os.environ, {}, clear=True),
        ):
            # Act
            resultado = esta_en_venv()

            # Assert
            assert resultado is False, "Debe detectar que NO está en venv cuando prefix es igual"

    def test_debe_detectar_venv_con_variable_entorno_virtual_env(self) -> None:
        """Debe detectar venv usando variable de entorno VIRTUAL_ENV."""
        # Arrange
        with (
            patch("sys.prefix", "/usr"),
            patch("sys.base_prefix", "/usr"),
            patch.dict(os.environ, {"VIRTUAL_ENV": "/home/user/proyecto/venv"}),
        ):
            # Act
            resultado = esta_en_venv()

            # Assert
            assert resultado is True, "Debe detectar venv con variable VIRTUAL_ENV"

    def test_debe_funcionar_sin_virtual_env_si_prefix_diferente(self) -> None:
        """Debe funcionar sin VIRTUAL_ENV si sys.prefix es diferente."""
        # Arrange
        with (
            patch("sys.prefix", "/home/user/proyecto/venv"),
            patch("sys.base_prefix", "/usr"),
            patch.dict(os.environ, {}, clear=True),
        ):
            # Asegurar que VIRTUAL_ENV no existe
            if "VIRTUAL_ENV" in os.environ:
                del os.environ["VIRTUAL_ENV"]

            # Act
            resultado = esta_en_venv()

            # Assert
            assert resultado is True, "Debe detectar venv solo con sys.prefix diferente"

    def test_debe_retornar_false_sin_indicadores_de_venv(self) -> None:
        """Debe retornar False si no hay indicadores de venv."""
        # Arrange
        with (
            patch("sys.prefix", "/usr"),
            patch("sys.base_prefix", "/usr"),
            patch.dict(os.environ, {}, clear=True),
        ):
            # Asegurar que VIRTUAL_ENV no existe
            if "VIRTUAL_ENV" in os.environ:
                del os.environ["VIRTUAL_ENV"]

            # Act
            resultado = esta_en_venv()

            # Assert
            assert resultado is False, "Debe retornar False sin indicadores de venv"

    def test_debe_manejar_conda_environments(self) -> None:
        """Debe detectar conda environments como venvs."""
        # Arrange
        with (
            patch("sys.prefix", "/home/user/miniconda3/envs/myenv"),
            patch("sys.base_prefix", "/home/user/miniconda3"),
        ):
            # Act
            resultado = esta_en_venv()

            # Assert
            assert resultado is True, "Debe detectar conda environments"


class TestEdgeCases:
    """Tests para casos límite y de seguridad."""

    def test_debe_manejar_venv_en_ruta_con_espacios(self, tmp_path: Path) -> None:
        """Debe manejar correctamente venvs en rutas con espacios."""
        # Arrange
        proyecto = tmp_path / "proyecto con espacios"
        proyecto.mkdir()

        venv = proyecto / "venv"
        venv.mkdir()
        (venv / "bin").mkdir()
        (venv / "bin" / "python").touch()
        (venv / "bin" / "python").chmod(0o755)

        with patch("platform.system", return_value="Linux"):
            # Act
            resultado = detectar_venv(proyecto)

            # Assert
            assert resultado is not None, "Debe manejar rutas con espacios"
            assert "espacios" in str(resultado.parent), "Debe mantener la ruta correcta"

    def test_debe_manejar_venv_en_ruta_con_unicode(self, tmp_path: Path) -> None:
        """Debe manejar correctamente venvs en rutas con caracteres Unicode."""
        # Arrange
        proyecto = tmp_path / "proyecto_ñoño_测试"
        proyecto.mkdir()

        venv = proyecto / "venv"
        venv.mkdir()
        (venv / "bin").mkdir()
        (venv / "bin" / "python").touch()
        (venv / "bin" / "python").chmod(0o755)

        with patch("platform.system", return_value="Linux"):
            # Act
            resultado = detectar_venv(proyecto)

            # Assert
            assert resultado is not None, "Debe manejar rutas con Unicode"

    def test_debe_validar_permisos_de_lectura_en_directorio(self, tmp_path: Path) -> None:
        """Debe manejar directorios sin permisos de lectura."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        venv = proyecto / "venv"
        venv.mkdir()
        (venv / "bin").mkdir()
        (venv / "bin" / "python").touch()
        (venv / "bin" / "python").chmod(0o755)

        # Quitar permisos de lectura al proyecto
        proyecto.chmod(0o000)

        try:
            with patch("platform.system", return_value="Linux"):
                # Act
                resultado = detectar_venv(proyecto)

                # Assert
                assert resultado is None, "Debe manejar directorios sin permisos de lectura"
        finally:
            # Restaurar permisos para cleanup
            proyecto.chmod(0o755)

    def test_debe_rechazar_crear_venv_en_directorio_sin_permisos_escritura(
        self, tmp_path: Path
    ) -> None:
        """Debe fallar al crear venv en directorio sin permisos de escritura."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()
        proyecto.chmod(0o444)  # Solo lectura

        try:
            # Act & Assert
            with pytest.raises(
                (RuntimeError, PermissionError, OSError),
                match="(Error al crear|Permission denied)",
            ):
                crear_venv(proyecto)
        finally:
            # Restaurar permisos para cleanup
            proyecto.chmod(0o755)

    def test_debe_manejar_multiples_versiones_python_en_venv(self, tmp_path: Path) -> None:
        """Debe detectar venv con múltiples versiones de Python."""
        # Arrange
        venv = tmp_path / "venv"
        venv.mkdir()
        (venv / "bin").mkdir()
        (venv / "bin" / "python").touch()
        (venv / "bin" / "python3").touch()
        (venv / "bin" / "python3.12").touch()
        (venv / "bin" / "python").chmod(0o755)
        (venv / "bin" / "python3").chmod(0o755)
        (venv / "bin" / "python3.12").chmod(0o755)

        with patch("platform.system", return_value="Linux"):
            # Act
            resultado = validar_venv(venv)

            # Assert
            assert resultado is True, "Debe validar venv con múltiples versiones Python"

    def test_debe_resolver_paths_relativos_correctamente(self, tmp_path: Path) -> None:
        """Debe resolver correctamente paths relativos."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        venv = proyecto / "venv"
        venv.mkdir()
        (venv / "bin").mkdir()
        (venv / "bin" / "python").touch()
        (venv / "bin" / "python").chmod(0o755)

        # Usar path relativo
        import os

        cwd_original = os.getcwd()
        try:
            os.chdir(tmp_path)
            proyecto_relativo = Path("proyecto")

            with patch("platform.system", return_value="Linux"):
                # Act
                resultado = detectar_venv(proyecto_relativo)

                # Assert
                assert resultado is not None, "Debe manejar paths relativos"
                assert resultado.is_absolute(), "Debe retornar path absoluto"
        finally:
            os.chdir(cwd_original)

    def test_debe_detectar_pyenv_virtualenv(self, tmp_path: Path) -> None:
        """Debe detectar virtualenvs creados con pyenv."""
        # Arrange
        # pyenv-virtualenv usa la misma estructura que venv
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        venv = proyecto / ".python-version"  # Indicador de pyenv
        venv.touch()

        venv_dir = proyecto / "venv"
        venv_dir.mkdir()
        (venv_dir / "bin").mkdir()
        (venv_dir / "bin" / "python").touch()
        (venv_dir / "bin" / "python").chmod(0o755)

        with patch("platform.system", return_value="Linux"):
            # Act
            resultado = detectar_venv(proyecto)

            # Assert
            assert resultado is not None, "Debe detectar pyenv-virtualenv"

    def test_debe_manejar_venv_en_wsl(self, tmp_path: Path) -> None:
        """Debe funcionar correctamente en WSL (Windows Subsystem for Linux)."""
        # Arrange
        proyecto = tmp_path / "proyecto"
        proyecto.mkdir()

        venv = proyecto / "venv"
        venv.mkdir()
        (venv / "bin").mkdir()
        (venv / "bin" / "python").touch()
        (venv / "bin" / "python").chmod(0o755)

        # WSL reporta Linux como sistema
        with patch("platform.system", return_value="Linux"):
            # Act
            resultado = detectar_venv(proyecto)

            # Assert
            assert resultado is not None, "Debe funcionar en WSL"
            assert resultado.name == "venv"
