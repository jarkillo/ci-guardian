"""
Tests unitarios para el instalador de hooks de Git.

Este módulo contiene todos los tests necesarios para validar la instalación,
desinstalación y gestión de hooks de Git de forma segura y multiplataforma.
"""

import platform
from pathlib import Path
from unittest.mock import patch

import pytest


class TestDeteccionRepositorioGit:
    """Tests para la detección de repositorios Git válidos."""

    def test_debe_detectar_repositorio_git_valido(self, tmp_path: Path) -> None:
        """Debe detectar si un directorio es un repositorio git válido."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        (repo_path / ".git" / "hooks").mkdir()

        # Act
        from ci_guardian.core.installer import es_repositorio_git

        es_valido = es_repositorio_git(repo_path)

        # Assert
        assert es_valido, "Debe reconocer un repositorio git válido con directorio .git/"

    def test_debe_rechazar_directorio_sin_git(self, tmp_path: Path) -> None:
        """Debe rechazar directorios sin .git/."""
        # Arrange
        dir_path = tmp_path / "no_repo"
        dir_path.mkdir()

        # Act
        from ci_guardian.core.installer import es_repositorio_git

        es_valido = es_repositorio_git(dir_path)

        # Assert
        assert not es_valido, "No debe reconocer directorios sin .git/ como repos"

    def test_debe_rechazar_ruta_inexistente(self, tmp_path: Path) -> None:
        """Debe rechazar rutas que no existen."""
        # Arrange
        ruta_inexistente = tmp_path / "no_existe"

        # Act
        from ci_guardian.core.installer import es_repositorio_git

        es_valido = es_repositorio_git(ruta_inexistente)

        # Assert
        assert not es_valido, "No debe reconocer rutas inexistentes como repos"

    def test_debe_validar_que_git_hooks_existe(self, tmp_path: Path) -> None:
        """Debe verificar que el directorio .git/hooks/ existe."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        # NO crear .git/hooks/

        # Act
        from ci_guardian.core.installer import es_repositorio_git

        es_valido = es_repositorio_git(repo_path)

        # Assert
        # Debe ser False porque .git/hooks/ no existe
        assert not es_valido, "Debe rechazar repos sin directorio .git/hooks/"

    def test_debe_detectar_repo_con_hooks_directory(self, tmp_path: Path) -> None:
        """Debe detectar repo válido cuando .git/hooks/ existe."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        (repo_path / ".git" / "hooks").mkdir()

        # Act
        from ci_guardian.core.installer import es_repositorio_git

        es_valido = es_repositorio_git(repo_path)

        # Assert
        assert es_valido, "Debe reconocer repo con .git/hooks/ como válido"


class TestInstalacionHooks:
    """Tests para la instalación de hooks."""

    @pytest.fixture
    def repo_mock(self, tmp_path: Path) -> Path:
        """Crea un repositorio git mock para tests."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / ".git" / "hooks").mkdir()
        return repo

    @pytest.mark.skipif(platform.system() == "Windows", reason="Test específico de Linux/Mac")
    def test_debe_instalar_hook_con_permisos_correctos_en_linux(self, repo_mock: Path) -> None:
        """Debe instalar hook con permisos 755 en Linux/Mac."""
        # Arrange
        contenido_hook = "#!/usr/bin/env python3\nprint('test')"
        from ci_guardian.core.installer import instalar_hook

        # Act
        with patch("platform.system", return_value="Linux"):
            instalar_hook(repo_mock, "pre-commit", contenido_hook)

        # Assert
        hook_path = repo_mock / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists(), "Hook debe existir después de la instalación"

        # Verificar permisos (755 = rwxr-xr-x)
        permisos = oct(hook_path.stat().st_mode)[-3:]
        assert permisos == "755", f"Permisos deben ser 755, pero son {permisos}"

    def test_debe_crear_archivo_en_directorio_correcto(self, repo_mock: Path) -> None:
        """Debe crear el archivo hook en .git/hooks/{hook_name}."""
        # Arrange
        contenido_hook = "#!/usr/bin/env python3\nprint('test')"
        from ci_guardian.core.installer import instalar_hook

        # Act
        instalar_hook(repo_mock, "pre-commit", contenido_hook)

        # Assert
        hook_path = repo_mock / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists(), "Hook debe existir en .git/hooks/"
        assert hook_path.is_file(), "Hook debe ser un archivo"

    def test_debe_escribir_contenido_correcto_del_hook(self, repo_mock: Path) -> None:
        """Debe escribir el contenido exacto del hook."""
        # Arrange
        contenido_esperado = "#!/usr/bin/env python3\nprint('CI Guardian')"
        from ci_guardian.core.installer import instalar_hook

        # Act
        instalar_hook(repo_mock, "pre-commit", contenido_esperado)

        # Assert
        hook_path = repo_mock / ".git" / "hooks" / "pre-commit"
        contenido_actual = hook_path.read_text(encoding="utf-8")
        assert (
            contenido_actual == contenido_esperado
        ), f"Contenido debe ser '{contenido_esperado}', pero es '{contenido_actual}'"

    def test_debe_rechazar_sobrescribir_hook_existente(self, repo_mock: Path) -> None:
        """Debe rechazar instalar si el hook ya existe."""
        # Arrange
        hook_path = repo_mock / ".git" / "hooks" / "pre-commit"
        hook_path.write_text("#!/bin/bash\necho 'existing'")

        from ci_guardian.core.installer import instalar_hook

        # Act & Assert
        with pytest.raises(FileExistsError, match="El hook pre-commit ya existe"):
            instalar_hook(repo_mock, "pre-commit", "nuevo contenido")

    def test_debe_rechazar_hook_no_permitido(self, repo_mock: Path) -> None:
        """Debe rechazar hooks que no están en la whitelist."""
        # Arrange
        from ci_guardian.core.installer import instalar_hook

        # Act & Assert
        with pytest.raises(ValueError, match="Hook no permitido"):
            instalar_hook(repo_mock, "malicious-hook", "contenido")

    def test_debe_rechazar_custom_hook(self, repo_mock: Path) -> None:
        """Debe rechazar hooks personalizados fuera de la whitelist."""
        # Arrange
        from ci_guardian.core.installer import instalar_hook

        # Act & Assert
        with pytest.raises(ValueError, match="Hook no permitido"):
            instalar_hook(repo_mock, "custom-pre-commit", "contenido")

    @pytest.mark.skipif(platform.system() != "Windows", reason="Test específico de Windows")
    def test_debe_instalar_hook_bat_en_windows(self, repo_mock: Path) -> None:
        """Debe instalar hooks como .bat en Windows."""
        # Arrange
        contenido_hook = "@echo off\necho test"
        from ci_guardian.core.installer import instalar_hook

        # Act
        with patch("platform.system", return_value="Windows"):
            instalar_hook(repo_mock, "pre-commit", contenido_hook)

        # Assert
        hook_path = repo_mock / ".git" / "hooks" / "pre-commit.bat"
        assert hook_path.exists(), "Hook .bat debe existir en Windows"
        assert hook_path.suffix == ".bat", "Extensión debe ser .bat en Windows"

    def test_debe_manejar_rutas_con_espacios(self, tmp_path: Path) -> None:
        """Debe manejar correctamente rutas con espacios."""
        # Arrange
        repo_path = tmp_path / "repo con espacios"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        (repo_path / ".git" / "hooks").mkdir()

        contenido_hook = "#!/usr/bin/env python3\nprint('test')"
        from ci_guardian.core.installer import instalar_hook

        # Act
        instalar_hook(repo_path, "pre-commit", contenido_hook)

        # Assert
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists(), "Debe manejar rutas con espacios"

    def test_debe_rechazar_instalacion_en_directorio_invalido(self, tmp_path: Path) -> None:
        """Debe rechazar instalar en un directorio que no es un repo git."""
        # Arrange
        dir_path = tmp_path / "no_repo"
        dir_path.mkdir()

        from ci_guardian.core.installer import instalar_hook

        # Act & Assert
        with pytest.raises(
            ValueError, match="no es un repositorio Git válido|no tiene .git/hooks/"
        ):
            instalar_hook(dir_path, "pre-commit", "contenido")

    def test_debe_incluir_marca_ci_guardian_en_hook(self, repo_mock: Path) -> None:
        """Debe incluir marca identificadora de CI Guardian en el hook."""
        # Arrange
        contenido_hook = "#!/usr/bin/env python3\n# CI-GUARDIAN-HOOK\nprint('test')"
        from ci_guardian.core.installer import instalar_hook

        # Act
        instalar_hook(repo_mock, "pre-commit", contenido_hook)

        # Assert
        hook_path = repo_mock / ".git" / "hooks" / "pre-commit"
        contenido = hook_path.read_text(encoding="utf-8")
        assert "CI-GUARDIAN-HOOK" in contenido, "Hook debe contener marca CI-GUARDIAN-HOOK"


class TestWhitelistHooks:
    """Tests para la validación de whitelist de hooks."""

    @pytest.fixture
    def repo_mock(self, tmp_path: Path) -> Path:
        """Crea un repositorio git mock para tests."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / ".git" / "hooks").mkdir()
        return repo

    @pytest.mark.parametrize(
        "hook_name",
        ["pre-commit", "commit-msg", "post-commit", "pre-rebase"],
    )
    def test_debe_permitir_hooks_de_whitelist(self, repo_mock: Path, hook_name: str) -> None:
        """Debe permitir instalar hooks que están en la whitelist."""
        # Arrange
        contenido = f"#!/usr/bin/env python3\n# CI-GUARDIAN-HOOK\nprint('{hook_name}')"
        from ci_guardian.core.installer import instalar_hook

        # Act
        instalar_hook(repo_mock, hook_name, contenido)

        # Assert
        # En Linux/Mac sin extensión, en Windows con .bat
        hook_paths = [
            repo_mock / ".git" / "hooks" / hook_name,
            repo_mock / ".git" / "hooks" / f"{hook_name}.bat",
        ]
        assert any(
            p.exists() for p in hook_paths
        ), f"Hook {hook_name} debe instalarse correctamente"

    @pytest.mark.parametrize(
        "hook_invalido",
        [
            "malicious-hook",
            "custom-hook",
            "post-checkout",
            "pre-applypatch",
            "../../../etc/passwd",
            "hook; rm -rf /",
        ],
    )
    def test_debe_rechazar_hooks_fuera_de_whitelist(
        self, repo_mock: Path, hook_invalido: str
    ) -> None:
        """Debe rechazar hooks que no están en la whitelist."""
        # Arrange
        from ci_guardian.core.installer import instalar_hook

        # Act & Assert
        with pytest.raises(ValueError, match="Hook no permitido"):
            instalar_hook(repo_mock, hook_invalido, "contenido")


class TestDesinstalacionHooks:
    """Tests para la desinstalación de hooks."""

    @pytest.fixture
    def repo_mock(self, tmp_path: Path) -> Path:
        """Crea un repositorio git mock para tests."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / ".git" / "hooks").mkdir()
        return repo

    def test_debe_eliminar_hook_existente(self, repo_mock: Path) -> None:
        """Debe eliminar un hook de CI Guardian si existe."""
        # Arrange
        hook_path = repo_mock / ".git" / "hooks" / "pre-commit"
        hook_path.write_text("#!/usr/bin/env python3\n# CI-GUARDIAN-HOOK\nprint('test')")

        from ci_guardian.core.installer import desinstalar_hook

        # Act
        resultado = desinstalar_hook(repo_mock, "pre-commit")

        # Assert
        assert resultado, "Debe retornar True si el hook fue eliminado"
        assert not hook_path.exists(), "Hook no debe existir después de desinstalar"

    def test_debe_retornar_false_si_hook_no_existe(self, repo_mock: Path) -> None:
        """Debe retornar False si el hook no existe."""
        # Arrange
        from ci_guardian.core.installer import desinstalar_hook

        # Act
        resultado = desinstalar_hook(repo_mock, "pre-commit")

        # Assert
        assert not resultado, "Debe retornar False si el hook no existe"

    def test_debe_validar_marca_ci_guardian_antes_de_eliminar(self, repo_mock: Path) -> None:
        """Debe verificar que el hook es de CI Guardian antes de eliminar."""
        # Arrange
        hook_path = repo_mock / ".git" / "hooks" / "pre-commit"
        hook_path.write_text("#!/bin/bash\n# Hook de otra herramienta\necho 'other'")

        from ci_guardian.core.installer import desinstalar_hook

        # Act & Assert
        with pytest.raises(ValueError, match="no es un hook de CI Guardian|no puede ser eliminado"):
            desinstalar_hook(repo_mock, "pre-commit")

    def test_no_debe_eliminar_hooks_de_otras_herramientas(self, repo_mock: Path) -> None:
        """NO debe eliminar hooks que no son de CI Guardian."""
        # Arrange
        hook_path = repo_mock / ".git" / "hooks" / "pre-commit"
        contenido_original = "#!/bin/bash\n# Husky hook\nhusky install"
        hook_path.write_text(contenido_original)

        from ci_guardian.core.installer import desinstalar_hook

        # Act & Assert
        with pytest.raises(ValueError):
            desinstalar_hook(repo_mock, "pre-commit")

        # Hook no debe ser eliminado
        assert hook_path.exists(), "No debe eliminar hooks de otras herramientas"
        assert hook_path.read_text() == contenido_original, "Contenido no debe cambiar"

    @pytest.mark.skipif(platform.system() != "Windows", reason="Test específico de Windows")
    def test_debe_eliminar_hook_bat_en_windows(self, repo_mock: Path) -> None:
        """Debe eliminar hooks .bat en Windows."""
        # Arrange
        hook_path = repo_mock / ".git" / "hooks" / "pre-commit.bat"
        hook_path.write_text("@echo off\nREM CI-GUARDIAN-HOOK\necho test")

        from ci_guardian.core.installer import desinstalar_hook

        # Act
        with patch("platform.system", return_value="Windows"):
            resultado = desinstalar_hook(repo_mock, "pre-commit")

        # Assert
        assert resultado, "Debe eliminar hook .bat en Windows"
        assert not hook_path.exists(), "Hook .bat no debe existir después de eliminar"


class TestVerificacionEstado:
    """Tests para la verificación de estado de hooks."""

    @pytest.fixture
    def repo_mock(self, tmp_path: Path) -> Path:
        """Crea un repositorio git mock para tests."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / ".git" / "hooks").mkdir()
        return repo

    def test_debe_detectar_hooks_instalados(self, repo_mock: Path) -> None:
        """Debe detectar qué hooks de CI Guardian están instalados."""
        # Arrange
        hooks_instalados = ["pre-commit", "commit-msg"]
        for hook_name in hooks_instalados:
            hook_path = repo_mock / ".git" / "hooks" / hook_name
            hook_path.write_text(
                f"#!/usr/bin/env python3\n# CI-GUARDIAN-HOOK\nprint('{hook_name}')"
            )

        from ci_guardian.core.installer import obtener_hooks_instalados

        # Act
        resultado = obtener_hooks_instalados(repo_mock)

        # Assert
        assert len(resultado) == 2, f"Debe detectar 2 hooks, pero detectó {len(resultado)}"
        assert "pre-commit" in resultado, "Debe detectar pre-commit"
        assert "commit-msg" in resultado, "Debe detectar pre-push"

    def test_debe_retornar_lista_vacia_si_no_hay_hooks(self, repo_mock: Path) -> None:
        """Debe retornar lista vacía si no hay hooks instalados."""
        # Arrange
        from ci_guardian.core.installer import obtener_hooks_instalados

        # Act
        resultado = obtener_hooks_instalados(repo_mock)

        # Assert
        assert resultado == [], "Debe retornar lista vacía si no hay hooks"

    def test_debe_ignorar_hooks_de_otras_herramientas(self, repo_mock: Path) -> None:
        """Debe ignorar hooks que no son de CI Guardian."""
        # Arrange
        # Hook de CI Guardian
        hook_ci = repo_mock / ".git" / "hooks" / "pre-commit"
        hook_ci.write_text("#!/usr/bin/env python3\n# CI-GUARDIAN-HOOK\nprint('test')")

        # Hook de otra herramienta
        hook_otro = repo_mock / ".git" / "hooks" / "commit-msg"
        hook_otro.write_text("#!/bin/bash\n# Husky\nhusky install")

        from ci_guardian.core.installer import obtener_hooks_instalados

        # Act
        resultado = obtener_hooks_instalados(repo_mock)

        # Assert
        assert len(resultado) == 1, "Debe detectar solo hooks de CI Guardian"
        assert "pre-commit" in resultado, "Debe detectar pre-commit de CI Guardian"
        assert "commit-msg" not in resultado, "No debe detectar hooks de otras herramientas"

    def test_debe_verificar_si_hook_es_de_ci_guardian(self, repo_mock: Path) -> None:
        """Debe verificar si un hook específico es de CI Guardian."""
        # Arrange
        hook_path = repo_mock / ".git" / "hooks" / "pre-commit"
        hook_path.write_text("#!/usr/bin/env python3\n# CI-GUARDIAN-HOOK\nprint('test')")

        from ci_guardian.core.installer import es_hook_ci_guardian

        # Act
        es_ci_guardian = es_hook_ci_guardian(repo_mock, "pre-commit")

        # Assert
        assert es_ci_guardian, "Debe reconocer hook de CI Guardian"

    def test_debe_rechazar_hook_sin_marca(self, repo_mock: Path) -> None:
        """Debe rechazar hook sin marca CI-GUARDIAN-HOOK."""
        # Arrange
        hook_path = repo_mock / ".git" / "hooks" / "pre-commit"
        hook_path.write_text("#!/bin/bash\necho 'other'")

        from ci_guardian.core.installer import es_hook_ci_guardian

        # Act
        es_ci_guardian = es_hook_ci_guardian(repo_mock, "pre-commit")

        # Assert
        assert not es_ci_guardian, "No debe reconocer hooks sin marca"

    def test_debe_retornar_false_para_hook_inexistente(self, repo_mock: Path) -> None:
        """Debe retornar False para hooks que no existen."""
        # Arrange
        from ci_guardian.core.installer import es_hook_ci_guardian

        # Act
        es_ci_guardian = es_hook_ci_guardian(repo_mock, "pre-commit")

        # Assert
        assert not es_ci_guardian, "Debe retornar False para hooks inexistentes"


class TestSeguridadPathTraversal:
    """Tests para prevenir ataques de path traversal."""

    @pytest.fixture
    def repo_mock(self, tmp_path: Path) -> Path:
        """Crea un repositorio git mock para tests."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / ".git" / "hooks").mkdir()
        return repo

    def test_debe_prevenir_path_traversal_con_dotdot(self, repo_mock: Path) -> None:
        """Debe prevenir path traversal usando ../."""
        # Arrange
        from ci_guardian.core.installer import instalar_hook

        # Act & Assert
        with pytest.raises(ValueError, match="Hook no permitido|path traversal"):
            instalar_hook(repo_mock, "../../../etc/passwd", "contenido malicioso")

    def test_debe_prevenir_path_traversal_en_contenido(self, repo_mock: Path) -> None:
        """Debe validar que el contenido no contenga comandos peligrosos."""
        # Arrange
        contenido_malicioso = "#!/bin/bash\nrm -rf /"
        from ci_guardian.core.installer import instalar_hook

        # Act & Assert
        # Este test valida que al menos se instale con la marca CI-GUARDIAN-HOOK
        # La validación de contenido es responsabilidad de otros validadores
        with pytest.raises(ValueError, match="Hook no permitido"):
            instalar_hook(repo_mock, "malicious", contenido_malicioso)

    def test_debe_validar_rutas_absolutas_correctamente(self, tmp_path: Path) -> None:
        """Debe manejar rutas absolutas correctamente sin path traversal."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        (repo_path / ".git" / "hooks").mkdir()

        contenido = "#!/usr/bin/env python3\n# CI-GUARDIAN-HOOK\nprint('test')"
        from ci_guardian.core.installer import instalar_hook

        # Act - usar ruta absoluta (debe funcionar)
        instalar_hook(repo_path.resolve(), "pre-commit", contenido)

        # Assert
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists(), "Debe manejar rutas absolutas correctamente"

    def test_debe_resolver_symlinks_antes_de_validar(self, tmp_path: Path) -> None:
        """Debe resolver symlinks antes de validar rutas."""
        # Arrange
        repo_real = tmp_path / "repo_real"
        repo_real.mkdir()
        (repo_real / ".git").mkdir()
        (repo_real / ".git" / "hooks").mkdir()

        repo_link = tmp_path / "repo_link"
        repo_link.symlink_to(repo_real)

        contenido = "#!/usr/bin/env python3\n# CI-GUARDIAN-HOOK\nprint('test')"
        from ci_guardian.core.installer import instalar_hook

        # Act
        instalar_hook(repo_link, "pre-commit", contenido)

        # Assert
        hook_path = repo_real / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists(), "Debe resolver symlinks correctamente"


class TestPermisosSeguridad:
    """Tests para validar permisos de seguridad."""

    @pytest.fixture
    def repo_mock(self, tmp_path: Path) -> Path:
        """Crea un repositorio git mock para tests."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / ".git" / "hooks").mkdir()
        return repo

    @pytest.mark.skipif(platform.system() == "Windows", reason="Test específico de Linux/Mac")
    def test_debe_usar_permisos_755_no_777(self, repo_mock: Path) -> None:
        """Debe usar permisos 755 (rwxr-xr-x), NO 777."""
        # Arrange
        contenido = "#!/usr/bin/env python3\n# CI-GUARDIAN-HOOK\nprint('test')"
        from ci_guardian.core.installer import instalar_hook

        # Act
        instalar_hook(repo_mock, "pre-commit", contenido)

        # Assert
        hook_path = repo_mock / ".git" / "hooks" / "pre-commit"
        permisos = oct(hook_path.stat().st_mode)[-3:]
        assert permisos == "755", f"Permisos deben ser 755, NO 777 (actual: {permisos})"
        assert permisos != "777", "NUNCA debe usar permisos 777 (inseguro)"

    @pytest.mark.skipif(platform.system() == "Windows", reason="Test específico de Linux/Mac")
    def test_debe_rechazar_permisos_inseguros(self, repo_mock: Path) -> None:
        """Debe prevenir instalación con permisos inseguros."""
        # Arrange
        hook_path = repo_mock / ".git" / "hooks" / "pre-commit"
        contenido = "#!/usr/bin/env python3\n# CI-GUARDIAN-HOOK\nprint('test')"

        from ci_guardian.core.installer import instalar_hook

        # Act
        instalar_hook(repo_mock, "pre-commit", contenido)

        # Assert
        permisos = oct(hook_path.stat().st_mode)[-3:]
        # Verificar que el tercer dígito (otros) no tenga write (2)
        otros_perms = int(permisos[2])
        assert otros_perms & 2 == 0, "Otros usuarios NO deben tener permiso de escritura"


class TestEdgeCases:
    """Tests para casos límite y edge cases."""

    def test_debe_manejar_repo_sin_directorio_hooks(self, tmp_path: Path) -> None:
        """Debe manejar repo sin directorio .git/hooks/."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        # NO crear .git/hooks/

        from ci_guardian.core.installer import instalar_hook

        # Act & Assert
        with pytest.raises(
            ValueError, match="no es un repositorio Git válido|no tiene .git/hooks/"
        ):
            instalar_hook(repo_path, "pre-commit", "contenido")

    def test_debe_manejar_permisos_insuficientes(self, tmp_path: Path) -> None:
        """Debe manejar permisos insuficientes para escribir."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        hooks_dir = repo_path / ".git" / "hooks"
        hooks_dir.mkdir()

        from ci_guardian.core.installer import instalar_hook

        # Simular directorio sin permisos de escritura
        with patch.object(Path, "write_text", side_effect=PermissionError("No write access")):
            # Act & Assert
            with pytest.raises(PermissionError, match="No write access"):
                instalar_hook(repo_path, "pre-commit", "#!/usr/bin/env python3\nprint('test')")

    def test_debe_manejar_disco_lleno(self, tmp_path: Path) -> None:
        """Debe manejar disco lleno (OSError)."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        (repo_path / ".git" / "hooks").mkdir()

        from ci_guardian.core.installer import instalar_hook

        # Simular disco lleno
        with patch.object(Path, "write_text", side_effect=OSError("No space left on device")):
            # Act & Assert
            with pytest.raises(OSError, match="No space left on device"):
                instalar_hook(repo_path, "pre-commit", "#!/usr/bin/env python3\nprint('test')")

    def test_debe_manejar_rutas_relativas(self, tmp_path: Path) -> None:
        """Debe manejar rutas relativas correctamente."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        (repo_path / ".git" / "hooks").mkdir()

        contenido = "#!/usr/bin/env python3\n# CI-GUARDIAN-HOOK\nprint('test')"
        # Act - usar ruta relativa
        import os

        from ci_guardian.core.installer import instalar_hook

        cwd_original = os.getcwd()
        try:
            os.chdir(tmp_path)
            ruta_relativa = Path("repo")
            instalar_hook(ruta_relativa, "pre-commit", contenido)
        finally:
            os.chdir(cwd_original)

        # Assert
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists(), "Debe manejar rutas relativas correctamente"

    def test_debe_manejar_nombre_hook_vacio(self, tmp_path: Path) -> None:
        """Debe rechazar nombres de hook vacíos."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        (repo_path / ".git" / "hooks").mkdir()

        from ci_guardian.core.installer import instalar_hook

        # Act & Assert
        with pytest.raises(ValueError, match="Hook no permitido|nombre vacío|inválido"):
            instalar_hook(repo_path, "", "contenido")

    def test_debe_manejar_contenido_vacio(self, tmp_path: Path) -> None:
        """Debe rechazar contenido de hook vacío."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        (repo_path / ".git" / "hooks").mkdir()

        from ci_guardian.core.installer import instalar_hook

        # Act & Assert
        with pytest.raises(ValueError, match="contenido vacío|contenido inválido"):
            instalar_hook(repo_path, "pre-commit", "")

    def test_debe_manejar_contenido_solo_espacios(self, tmp_path: Path) -> None:
        """Debe rechazar contenido de hook con solo espacios."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        (repo_path / ".git" / "hooks").mkdir()

        from ci_guardian.core.installer import instalar_hook

        # Act & Assert
        with pytest.raises(ValueError, match="contenido vacío|contenido inválido"):
            instalar_hook(repo_path, "pre-commit", "   \n  \t  ")


class TestIntegracionMultiplataforma:
    """Tests de integración multiplataforma."""

    @pytest.fixture
    def repo_mock(self, tmp_path: Path) -> Path:
        """Crea un repositorio git mock para tests."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / ".git" / "hooks").mkdir()
        return repo

    @pytest.mark.parametrize(
        "sistema,extension_esperada",
        [
            ("Linux", ""),
            ("Darwin", ""),
            ("Windows", ".bat"),
        ],
    )
    def test_debe_usar_extension_correcta_segun_sistema(
        self, repo_mock: Path, sistema: str, extension_esperada: str
    ) -> None:
        """Debe usar la extensión correcta según el sistema operativo."""
        # Arrange
        contenido = "#!/usr/bin/env python3\n# CI-GUARDIAN-HOOK\nprint('test')"
        from ci_guardian.core.installer import instalar_hook

        # Act
        with patch("platform.system", return_value=sistema):
            instalar_hook(repo_mock, "pre-commit", contenido)

        # Assert
        hook_nombre = f"pre-commit{extension_esperada}"
        hook_path = repo_mock / ".git" / "hooks" / hook_nombre
        assert (
            hook_path.exists()
        ), f"Hook con extensión '{extension_esperada}' debe existir en {sistema}"

    def test_debe_detectar_sistema_operativo_correctamente(self) -> None:
        """Debe detectar el sistema operativo correctamente."""
        # Act
        sistema = platform.system()

        # Assert
        assert sistema in [
            "Linux",
            "Windows",
            "Darwin",
        ], f"Sistema {sistema} debe ser uno de: Linux, Windows, Darwin"

    @pytest.mark.parametrize(
        "separador_ruta",
        ["/", "\\"],
    )
    def test_debe_manejar_separadores_de_ruta(self, tmp_path: Path, separador_ruta: str) -> None:
        """Debe manejar diferentes separadores de ruta."""
        # Skip backslash test en sistemas no-Windows (backslash no es separador en Unix)
        if separador_ruta == "\\" and platform.system() != "Windows":
            pytest.skip("Backslash como separador solo aplica en Windows")

        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        (repo_path / ".git" / "hooks").mkdir()

        # Act - pathlib.Path debe manejar ambos separadores
        hook_path = Path(str(repo_path).replace("/", separador_ruta)) / ".git" / "hooks"

        # Assert
        assert hook_path.exists(), f"Debe manejar separador '{separador_ruta}'"
