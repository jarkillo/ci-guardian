"""
Tests unitarios para el instalador de hooks de Git.

Este módulo prueba la funcionalidad del instalador de hooks, incluyendo:
- Detección de repositorios Git válidos
- Instalación de hooks con permisos correctos
- Validación de nombres de hooks (whitelist)
- Prevención de path traversal
- Compatibilidad multiplataforma (Linux/Windows)
"""

import platform
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ci_guardian.core.installer import (
    HOOKS_PERMITIDOS,
    es_repositorio_git,
    instalar_hook,
    validar_nombre_hook,
    validar_path_hook,
)


class TestDeteccionRepositorioGit:
    """Tests para la detección de repositorios Git válidos."""

    def test_debe_detectar_repositorio_git_valido(self, tmp_path: Path) -> None:
        """Debe detectar si un directorio es un repositorio Git válido."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()

        # Act
        es_valido = es_repositorio_git(repo_path)

        # Assert
        assert es_valido, "Debe reconocer un repositorio Git válido con directorio .git/"

    def test_debe_rechazar_directorio_sin_git(self, tmp_path: Path) -> None:
        """Debe rechazar directorios sin .git/ como repositorios inválidos."""
        # Arrange
        dir_path = tmp_path / "no_repo"
        dir_path.mkdir()

        # Act
        es_valido = es_repositorio_git(dir_path)

        # Assert
        assert not es_valido, "No debe reconocer directorios sin .git/ como repositorios Git"

    def test_debe_rechazar_directorio_inexistente(self, tmp_path: Path) -> None:
        """Debe rechazar directorios que no existen."""
        # Arrange
        dir_path = tmp_path / "no_existe"

        # Act
        es_valido = es_repositorio_git(dir_path)

        # Assert
        assert not es_valido, "No debe reconocer directorios inexistentes como repositorios Git"

    def test_debe_rechazar_git_como_archivo(self, tmp_path: Path) -> None:
        """Debe rechazar si .git es un archivo en lugar de un directorio."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").write_text("gitdir: ../../../malicious")

        # Act
        es_valido = es_repositorio_git(repo_path)

        # Assert
        assert not es_valido, ".git debe ser un directorio, no un archivo"


class TestValidacionNombreHook:
    """Tests para la validación de nombres de hooks mediante whitelist."""

    def test_debe_permitir_hooks_en_whitelist(self) -> None:
        """Debe permitir todos los hooks en la whitelist."""
        # Arrange
        hooks_validos = ["pre-commit", "pre-push", "post-commit", "pre-rebase"]

        # Act & Assert
        for hook_name in hooks_validos:
            assert (
                validar_nombre_hook(hook_name) is True
            ), f"El hook {hook_name} debe estar en la whitelist"

    def test_debe_rechazar_hook_no_en_whitelist(self) -> None:
        """Debe rechazar nombres de hooks no incluidos en la whitelist."""
        # Arrange
        hooks_invalidos = [
            "malicious-hook",
            "backdoor",
            "custom-hook",
            "../../../etc/passwd",
        ]

        # Act & Assert
        for hook_name in hooks_invalidos:
            with pytest.raises(ValueError, match=f"Hook no permitido: {hook_name}"):
                validar_nombre_hook(hook_name)

    def test_debe_rechazar_hook_vacio(self) -> None:
        """Debe rechazar nombres de hooks vacíos."""
        # Arrange
        hook_name = ""

        # Act & Assert
        with pytest.raises(ValueError, match="Hook no permitido:"):
            validar_nombre_hook(hook_name)

    def test_debe_verificar_whitelist_contiene_hooks_esperados(self) -> None:
        """Debe verificar que HOOKS_PERMITIDOS contiene los hooks esperados."""
        # Arrange
        hooks_esperados = {"pre-commit", "pre-push", "post-commit", "pre-rebase"}

        # Assert
        assert (
            HOOKS_PERMITIDOS == hooks_esperados
        ), "HOOKS_PERMITIDOS debe contener exactamente los hooks esperados"


class TestValidacionPathTraversal:
    """Tests para prevención de path traversal."""

    def test_debe_aceptar_path_hook_valido(self, tmp_path: Path) -> None:
        """Debe aceptar paths de hooks válidos dentro de .git/hooks/."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"

        # Act
        es_valido = validar_path_hook(repo_path, hook_path)

        # Assert
        assert es_valido, "Debe aceptar paths de hooks dentro de .git/hooks/"

    def test_debe_rechazar_path_traversal_con_dotdot(self, tmp_path: Path) -> None:
        """Debe rechazar intentos de path traversal usando ../."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        hook_path = repo_path / ".git" / "hooks" / ".." / ".." / "malicious"

        # Act & Assert
        with pytest.raises(ValueError, match="Path traversal detectado"):
            validar_path_hook(repo_path, hook_path.resolve())

    def test_debe_rechazar_path_fuera_de_hooks(self, tmp_path: Path) -> None:
        """Debe rechazar paths fuera del directorio .git/hooks/."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        hook_path = tmp_path / "etc" / "passwd"

        # Act & Assert
        with pytest.raises(ValueError, match="Path traversal detectado"):
            validar_path_hook(repo_path, hook_path)


class TestInstalacionHooksLinux:
    """Tests para la instalación de hooks en sistemas Linux."""

    @pytest.mark.skipif(platform.system() == "Windows", reason="Test específico de Linux/Unix")
    def test_debe_instalar_hook_con_permisos_755_en_linux_real(self, tmp_path: Path) -> None:
        """Debe instalar hook con permisos 755 (rwxr-xr-x) en Linux real."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        contenido_hook = "#!/bin/bash\necho 'test hook'"

        # Act
        instalar_hook(repo_path, "pre-commit", contenido_hook)

        # Assert
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists(), "El hook debe existir después de la instalación"

        permisos = oct(hook_path.stat().st_mode)[-3:]
        assert permisos == "755", f"Los permisos deben ser 755, pero son {permisos}"

    def test_debe_instalar_hook_sin_extension_en_linux(self, tmp_path: Path) -> None:
        """Debe instalar hooks sin extensión .bat en Linux."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        contenido_hook = "#!/bin/bash\necho 'test'"

        # Act
        with patch("platform.system", return_value="Linux"):
            instalar_hook(repo_path, "pre-commit", contenido_hook)

        # Assert
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        hook_bat_path = repo_path / ".git" / "hooks" / "pre-commit.bat"

        assert hook_path.exists(), "El hook sin extensión debe existir en Linux"
        assert not hook_bat_path.exists(), "No debe existir versión .bat en Linux"

    def test_debe_incluir_shebang_en_hook_linux(self, tmp_path: Path) -> None:
        """Debe instalar hooks con shebang correcto en Linux."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        contenido_hook = "#!/usr/bin/env python3\nprint('test')"

        # Act
        with patch("platform.system", return_value="Linux"):
            instalar_hook(repo_path, "pre-push", contenido_hook)

        # Assert
        hook_path = repo_path / ".git" / "hooks" / "pre-push"
        contenido = hook_path.read_text(encoding="utf-8")

        assert contenido.startswith("#!/usr/bin/env python3"), "El hook debe tener shebang correcto"


class TestInstalacionHooksWindows:
    """Tests para la instalación de hooks en sistemas Windows."""

    @pytest.mark.skipif(platform.system() != "Windows", reason="Test específico de Windows")
    def test_debe_instalar_hook_bat_en_windows_real(self, tmp_path: Path) -> None:
        """Debe instalar hooks como archivos .bat en Windows real."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        contenido_hook = "@echo off\necho test"

        # Act
        instalar_hook(repo_path, "pre-commit", contenido_hook)

        # Assert
        hook_path = repo_path / ".git" / "hooks" / "pre-commit.bat"
        assert hook_path.exists(), "El hook .bat debe existir en Windows"

    def test_debe_instalar_hook_bat_en_windows_mockeado(self, tmp_path: Path) -> None:
        """Debe instalar hooks como .bat cuando se detecta Windows (mockeado)."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        contenido_hook = "@echo off\necho test"

        # Act
        with patch("platform.system", return_value="Windows"):
            instalar_hook(repo_path, "pre-commit", contenido_hook)

        # Assert
        hook_bat_path = repo_path / ".git" / "hooks" / "pre-commit.bat"
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"

        assert hook_bat_path.exists(), "El hook .bat debe existir en Windows"
        assert not hook_path.exists(), "No debe existir versión sin extensión en Windows"

    def test_debe_no_aplicar_chmod_en_windows(self, tmp_path: Path) -> None:
        """Debe omitir chmod en Windows (no tiene permisos Unix)."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        contenido_hook = "@echo off\necho test"

        # Act
        with patch("platform.system", return_value="Windows"):
            # No debe lanzar excepción
            instalar_hook(repo_path, "pre-push", contenido_hook)

        # Assert
        hook_path = repo_path / ".git" / "hooks" / "pre-push.bat"
        assert hook_path.exists(), "El hook debe instalarse sin aplicar chmod"


class TestPrevencionSobrescrituraHooks:
    """Tests para prevención de sobrescritura de hooks existentes."""

    def test_debe_rechazar_instalacion_si_hook_existe(self, tmp_path: Path) -> None:
        """Debe rechazar instalar un hook si ya existe uno previo."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        hook_path.write_text("#!/bin/bash\necho 'existing hook'", encoding="utf-8")

        contenido_nuevo = "#!/bin/bash\necho 'new hook'"

        # Act & Assert
        with pytest.raises(FileExistsError, match="El hook pre-commit ya existe"):
            with patch("platform.system", return_value="Linux"):
                instalar_hook(repo_path, "pre-commit", contenido_nuevo)

    def test_debe_rechazar_instalacion_si_hook_bat_existe_en_windows(self, tmp_path: Path) -> None:
        """Debe rechazar instalar si el hook .bat ya existe en Windows."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        hook_path = repo_path / ".git" / "hooks" / "pre-commit.bat"
        hook_path.write_text("@echo off\necho existing", encoding="utf-8")

        contenido_nuevo = "@echo off\necho nuevo"

        # Act & Assert
        with pytest.raises(FileExistsError, match="El hook pre-commit ya existe"):
            with patch("platform.system", return_value="Windows"):
                instalar_hook(repo_path, "pre-commit", contenido_nuevo)

    def test_debe_preservar_hook_existente_al_fallar(self, tmp_path: Path) -> None:
        """Debe preservar el contenido del hook existente si la instalación falla."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        hook_path = repo_path / ".git" / "hooks" / "pre-push"
        contenido_original = "#!/bin/bash\necho 'original'"
        hook_path.write_text(contenido_original, encoding="utf-8")

        contenido_nuevo = "#!/bin/bash\necho 'nuevo'"

        # Act
        try:
            with patch("platform.system", return_value="Linux"):
                instalar_hook(repo_path, "pre-push", contenido_nuevo)
        except FileExistsError:
            pass

        # Assert
        contenido_actual = hook_path.read_text(encoding="utf-8")
        assert contenido_actual == contenido_original, "El hook original debe permanecer intacto"


class TestManejoErrores:
    """Tests para el manejo de errores y validaciones."""

    def test_debe_lanzar_valueerror_si_no_es_repo_git(self, tmp_path: Path) -> None:
        """Debe lanzar ValueError si el directorio no es un repositorio Git válido."""
        # Arrange
        dir_path = tmp_path / "no_repo"
        dir_path.mkdir()
        contenido_hook = "#!/bin/bash\necho 'test'"

        # Act & Assert
        with pytest.raises(
            ValueError,
            match="El directorio .* no es un repositorio Git válido",
        ):
            instalar_hook(dir_path, "pre-commit", contenido_hook)

    def test_debe_lanzar_valueerror_si_nombre_hook_invalido(self, tmp_path: Path) -> None:
        """Debe lanzar ValueError si el nombre del hook no está en la whitelist."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        contenido_hook = "#!/bin/bash\necho 'malicious'"

        # Act & Assert
        with pytest.raises(ValueError, match="Hook no permitido: malicious-hook"):
            instalar_hook(repo_path, "malicious-hook", contenido_hook)

    def test_debe_lanzar_valueerror_si_directorio_hooks_no_existe(self, tmp_path: Path) -> None:
        """Debe lanzar ValueError si el directorio .git/hooks/ no existe."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        # No crear .git/hooks/
        contenido_hook = "#!/bin/bash\necho 'test'"

        # Act & Assert
        with pytest.raises(ValueError, match="Directorio de hooks no encontrado"):
            instalar_hook(repo_path, "pre-commit", contenido_hook)

    def test_debe_validar_contenido_no_vacio(self, tmp_path: Path) -> None:
        """Debe rechazar contenido de hook vacío."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        contenido_hook = ""

        # Act & Assert
        with pytest.raises(ValueError, match="El contenido del hook no puede estar vacío"):
            instalar_hook(repo_path, "pre-commit", contenido_hook)

    def test_debe_validar_contenido_solo_espacios(self, tmp_path: Path) -> None:
        """Debe rechazar contenido de hook que solo contiene espacios."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        contenido_hook = "   \n\t  \n  "

        # Act & Assert
        with pytest.raises(ValueError, match="El contenido del hook no puede estar vacío"):
            instalar_hook(repo_path, "pre-commit", contenido_hook)


class TestCompatibilidadMultiplataforma:
    """Tests para compatibilidad entre Linux, Windows y macOS."""

    @pytest.mark.parametrize(
        "sistema,extension_esperada",
        [
            ("Linux", ""),
            ("Windows", ".bat"),
            ("Darwin", ""),  # macOS
        ],
    )
    def test_debe_usar_extension_correcta_segun_plataforma(
        self, tmp_path: Path, sistema: str, extension_esperada: str
    ) -> None:
        """Debe usar la extensión correcta según el sistema operativo."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        # Usar contenido válido según la plataforma
        if sistema == "Windows":
            contenido_hook = "@echo off\necho test"
        else:
            contenido_hook = "#!/bin/bash\necho test"

        # Act
        with patch("platform.system", return_value=sistema):
            instalar_hook(repo_path, "pre-commit", contenido_hook)

        # Assert
        hook_path = repo_path / ".git" / "hooks" / f"pre-commit{extension_esperada}"
        assert (
            hook_path.exists()
        ), f"El hook debe tener extensión '{extension_esperada}' en {sistema}"

    def test_debe_manejar_rutas_con_espacios(self, tmp_path: Path) -> None:
        """Debe manejar correctamente rutas con espacios en el nombre."""
        # Arrange
        repo_path = tmp_path / "repo con espacios"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        contenido_hook = "#!/bin/bash\necho 'test'"

        # Act
        with patch("platform.system", return_value="Linux"):
            instalar_hook(repo_path, "pre-commit", contenido_hook)

        # Assert
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists(), "Debe manejar rutas con espacios correctamente"

    def test_debe_manejar_caracteres_unicode_en_contenido(self, tmp_path: Path) -> None:
        """Debe manejar correctamente caracteres Unicode en el contenido del hook."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        contenido_hook = "#!/bin/bash\n# Comentario con tildes: señal, información\necho '✅ Test'"

        # Act
        with patch("platform.system", return_value="Linux"):
            instalar_hook(repo_path, "pre-push", contenido_hook)

        # Assert
        hook_path = repo_path / ".git" / "hooks" / "pre-push"
        contenido_leido = hook_path.read_text(encoding="utf-8")
        assert contenido_leido == contenido_hook, "Debe preservar caracteres Unicode correctamente"


class TestContenidoHooks:
    """Tests para validación del contenido de los hooks instalados."""

    def test_debe_preservar_contenido_exacto_del_hook(self, tmp_path: Path) -> None:
        """Debe preservar el contenido exacto del hook sin modificaciones."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        contenido_hook = """#!/usr/bin/env python3
# Este es un hook de prueba
import sys

def main():
    print("Hook ejecutado")
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""

        # Act
        with patch("platform.system", return_value="Linux"):
            instalar_hook(repo_path, "pre-commit", contenido_hook)

        # Assert
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        contenido_leido = hook_path.read_text(encoding="utf-8")
        assert contenido_leido == contenido_hook, "El contenido debe ser idéntico al original"

    def test_debe_manejar_saltos_de_linea_unix(self, tmp_path: Path) -> None:
        """Debe manejar correctamente saltos de línea Unix (LF)."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        contenido_hook = "#!/bin/bash\necho 'line1'\necho 'line2'\n"

        # Act
        with patch("platform.system", return_value="Linux"):
            instalar_hook(repo_path, "pre-commit", contenido_hook)

        # Assert
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        contenido_leido = hook_path.read_text(encoding="utf-8")
        assert "\n" in contenido_leido, "Debe preservar saltos de línea Unix (LF)"
        assert "\r\n" not in contenido_leido, "No debe convertir a saltos de línea Windows (CRLF)"


class TestMejorasSeguridad:
    """Tests para mejoras opcionales de seguridad sugeridas por el auditor.

    Estas mejoras están clasificadas como:
    - Validación de shebang: Prioridad BAJA
    - Logging de operaciones: Prioridad BAJA
    - Límite de tamaño: Prioridad MUY BAJA
    """

    # ========== Tests para Validación de Shebang ==========

    @pytest.mark.parametrize(
        "shebang_valido",
        [
            "#!/bin/bash",
            "#!/bin/sh",
            "#!/usr/bin/env python",
            "#!/usr/bin/env python3",
        ],
    )
    def test_debe_permitir_shebangs_validos(self, tmp_path: Path, shebang_valido: str) -> None:
        """Debe permitir shebangs en la lista de shebangs permitidos."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        contenido_hook = f"{shebang_valido}\necho 'test'"

        # Act
        with patch("platform.system", return_value="Linux"):
            instalar_hook(repo_path, "pre-commit", contenido_hook)

        # Assert
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists(), "El hook con shebang válido debe instalarse correctamente"
        contenido_leido = hook_path.read_text(encoding="utf-8")
        assert contenido_leido.startswith(
            shebang_valido
        ), f"El hook debe comenzar con el shebang: {shebang_valido}"

    def test_debe_rechazar_hook_sin_shebang(self, tmp_path: Path) -> None:
        """Debe rechazar hooks que no comienzan con un shebang."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        contenido_hook = "echo 'test sin shebang'\nexit 0"

        # Act & Assert
        with pytest.raises(ValueError, match="El hook debe comenzar con un shebang"):
            with patch("platform.system", return_value="Linux"):
                instalar_hook(repo_path, "pre-commit", contenido_hook)

    @pytest.mark.parametrize(
        "shebang_no_permitido",
        [
            "#!/usr/bin/perl",
            "#!/usr/bin/ruby",
            "#!/usr/bin/env node",
            "#!/usr/bin/php",
        ],
    )
    def test_debe_rechazar_shebang_no_permitido(
        self, tmp_path: Path, shebang_no_permitido: str
    ) -> None:
        """Debe rechazar shebangs que no están en la whitelist."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        contenido_hook = f"{shebang_no_permitido}\nprint 'test'"

        # Act & Assert
        with pytest.raises(ValueError, match="Shebang no permitido"):
            with patch("platform.system", return_value="Linux"):
                instalar_hook(repo_path, "pre-commit", contenido_hook)

    def test_debe_validar_shebang_en_primera_linea(self, tmp_path: Path) -> None:
        """Debe validar que el shebang esté en la primera línea (ignorar comentarios posteriores)."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        contenido_hook = """#!/bin/bash
# Este es un comentario con #!/usr/bin/perl (no debe validarse)
echo 'test'
"""

        # Act
        with patch("platform.system", return_value="Linux"):
            instalar_hook(repo_path, "pre-commit", contenido_hook)

        # Assert
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists(), "El hook debe instalarse si el shebang está en la primera línea"

    def test_debe_rechazar_hook_con_espacios_antes_shebang(self, tmp_path: Path) -> None:
        """Debe rechazar hooks con espacios o líneas vacías antes del shebang."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        contenido_hook = "\n  #!/bin/bash\necho 'test'"

        # Act & Assert
        with pytest.raises(ValueError, match="El hook debe comenzar con un shebang"):
            with patch("platform.system", return_value="Linux"):
                instalar_hook(repo_path, "pre-commit", contenido_hook)

    # ========== Tests para Logging de Operaciones de Seguridad ==========

    def test_debe_loggear_intento_path_traversal(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Debe loggear warning cuando se detecta un intento de path traversal."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        contenido_hook = "#!/bin/bash\necho 'malicious'"

        # Intentar path traversal mediante nombre de hook manipulado
        hook_malicioso = "../../../etc/passwd"

        # Act
        with caplog.at_level("WARNING"):
            try:
                instalar_hook(repo_path, hook_malicioso, contenido_hook)
            except ValueError:
                pass  # Se espera que falle

        # Assert
        assert any(
            "path traversal" in record.message.lower() for record in caplog.records
        ), "Debe loggear un warning sobre path traversal detectado"

        # Verificar que el log incluye información relevante
        log_messages = [record.message for record in caplog.records]
        assert any(
            str(repo_path) in msg for msg in log_messages
        ), "El log debe incluir el repo_path"

    def test_debe_usar_nivel_warning_para_path_traversal(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Debe usar nivel WARNING para logs de path traversal."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        hook_path = repo_path / ".git" / "hooks" / ".." / ".." / "malicious"

        # Act
        with caplog.at_level("WARNING"):
            try:
                # Llamar directamente a validar_path_hook con path malicioso
                from ci_guardian.core.installer import validar_path_hook

                validar_path_hook(repo_path, hook_path.resolve())
            except ValueError:
                pass

        # Assert
        warning_records = [r for r in caplog.records if r.levelname == "WARNING"]
        assert len(warning_records) > 0, "Debe existir al menos un log de nivel WARNING"

    def test_no_debe_loggear_para_paths_validos(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """No debe loggear warnings para paths de hooks válidos."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)
        contenido_hook = "#!/bin/bash\necho 'valid hook'"

        # Act
        with caplog.at_level("WARNING"):
            with patch("platform.system", return_value="Linux"):
                instalar_hook(repo_path, "pre-commit", contenido_hook)

        # Assert
        warning_records = [r for r in caplog.records if r.levelname == "WARNING"]
        assert len(warning_records) == 0, "No debe loggear warnings para operaciones válidas"

    # ========== Tests para Límite de Tamaño de Contenido ==========

    def test_debe_permitir_hook_tamano_normal(self, tmp_path: Path) -> None:
        """Debe permitir instalar hooks de tamaño normal (< 100KB)."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)

        # Hook de ~10KB (normal)
        contenido_hook = "#!/bin/bash\n" + "echo 'test'\n" * 500

        # Act
        with patch("platform.system", return_value="Linux"):
            instalar_hook(repo_path, "pre-commit", contenido_hook)

        # Assert
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists(), "Debe instalar hooks de tamaño normal sin problemas"

    def test_debe_rechazar_hook_mayor_100kb(self, tmp_path: Path) -> None:
        """Debe rechazar hooks mayores a 100KB."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)

        # Hook de ~150KB (excede el límite)
        # Cada línea ~20 bytes, 7500 líneas ≈ 150KB
        contenido_hook = "#!/bin/bash\n" + "echo 'test line'\n" * 7500

        # Act & Assert
        with pytest.raises(ValueError, match="El hook es demasiado grande"):
            with patch("platform.system", return_value="Linux"):
                instalar_hook(repo_path, "pre-commit", contenido_hook)

    def test_debe_calcular_tamano_en_bytes_utf8(self, tmp_path: Path) -> None:
        """Debe calcular el tamaño en bytes UTF-8, no en caracteres."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)

        # Caracteres multibyte: cada emoji ≈ 4 bytes UTF-8
        # 30,000 emojis × 4 bytes = ~120KB (excede 100KB)
        contenido_hook = "#!/bin/bash\n" + "# 😀" * 30000

        # Act & Assert
        with pytest.raises(ValueError, match="El hook es demasiado grande"):
            with patch("platform.system", return_value="Linux"):
                instalar_hook(repo_path, "pre-commit", contenido_hook)

    def test_debe_manejar_correctamente_contenido_multibyte(self, tmp_path: Path) -> None:
        """Debe manejar correctamente contenido con caracteres multibyte (Unicode)."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)

        # Contenido pequeño con Unicode variado (< 100KB)
        contenido_hook = """#!/bin/bash
# Comentarios con Unicode: 日本語, العربية, 中文, Español
echo '✅ Test con emojis: 🚀 🎉 ✨'
echo 'Acentos: café, señor, información'
"""

        # Act
        with patch("platform.system", return_value="Linux"):
            instalar_hook(repo_path, "pre-commit", contenido_hook)

        # Assert
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists(), "Debe instalar hooks con caracteres multibyte"
        contenido_leido = hook_path.read_text(encoding="utf-8")
        assert contenido_leido == contenido_hook, "Debe preservar exactamente el contenido Unicode"

    def test_limite_tamano_exactamente_100kb(self, tmp_path: Path) -> None:
        """Debe permitir hooks de exactamente 100KB (límite exacto)."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)

        # Crear contenido de exactamente 100KB
        shebang = "#!/bin/bash\n"
        # 100KB - len(shebang) bytes
        bytes_restantes = (1024 * 100) - len(shebang.encode("utf-8"))
        contenido_hook = shebang + ("a" * bytes_restantes)

        # Act
        with patch("platform.system", return_value="Linux"):
            instalar_hook(repo_path, "pre-commit", contenido_hook)

        # Assert
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists(), "Debe permitir hooks de exactamente 100KB"
        tamano_bytes = len(hook_path.read_text(encoding="utf-8").encode("utf-8"))
        assert tamano_bytes == 1024 * 100, "El tamaño debe ser exactamente 100KB"

    def test_debe_rechazar_hook_un_byte_mayor_100kb(self, tmp_path: Path) -> None:
        """Debe rechazar hooks de 100KB + 1 byte."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git" / "hooks").mkdir(parents=True)

        # Crear contenido de 100KB + 1 byte
        shebang = "#!/bin/bash\n"
        bytes_restantes = (1024 * 100) - len(shebang.encode("utf-8")) + 1  # +1 byte
        contenido_hook = shebang + ("a" * bytes_restantes)

        # Act & Assert
        with pytest.raises(ValueError, match="El hook es demasiado grande"):
            with patch("platform.system", return_value="Linux"):
                instalar_hook(repo_path, "pre-commit", contenido_hook)
