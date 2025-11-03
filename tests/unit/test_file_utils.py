"""Tests para validators/file_utils.py - Filtrado centralizado de archivos Python."""

from pathlib import Path

import pytest


class TestFiltrarArchivosPythonSeguros:
    """Tests para la función filtrar_archivos_python_seguros."""

    def test_debe_filtrar_solo_archivos_python(self, tmp_path: Path) -> None:
        """Debe filtrar solo archivos con extensión .py."""
        # Arrange
        py_file = tmp_path / "test.py"
        py_file.write_text("print('test')")
        txt_file = tmp_path / "readme.txt"
        txt_file.write_text("readme")
        js_file = tmp_path / "script.js"
        js_file.write_text("console.log('test')")

        archivos = [py_file, txt_file, js_file]

        # Act
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        resultado = filtrar_archivos_python_seguros(archivos, repo_path=tmp_path)

        # Assert
        assert len(resultado) == 1
        assert resultado[0] == py_file

    def test_debe_excluir_directorios_venv(self, tmp_path: Path) -> None:
        """Debe excluir archivos en directorios venv."""
        # Arrange
        (tmp_path / "venv").mkdir()
        venv_file = tmp_path / "venv" / "lib.py"
        venv_file.write_text("# venv file")

        normal_file = tmp_path / "main.py"
        normal_file.write_text("# normal file")

        archivos = [venv_file, normal_file]

        # Act
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        resultado = filtrar_archivos_python_seguros(archivos, repo_path=tmp_path)

        # Assert
        assert len(resultado) == 1
        assert resultado[0] == normal_file

    def test_debe_excluir_directorios_dot_venv(self, tmp_path: Path) -> None:
        """Debe excluir archivos en directorios .venv."""
        # Arrange
        (tmp_path / ".venv").mkdir()
        venv_file = tmp_path / ".venv" / "lib.py"
        venv_file.write_text("# venv file")

        normal_file = tmp_path / "main.py"
        normal_file.write_text("# normal file")

        archivos = [venv_file, normal_file]

        # Act
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        resultado = filtrar_archivos_python_seguros(archivos, repo_path=tmp_path)

        # Assert
        assert len(resultado) == 1
        assert resultado[0] == normal_file

    def test_debe_excluir_directorios_git(self, tmp_path: Path) -> None:
        """Debe excluir archivos en directorio .git."""
        # Arrange
        (tmp_path / ".git").mkdir()
        git_file = tmp_path / ".git" / "hooks" / "pre-commit.py"
        git_file.parent.mkdir(parents=True)
        git_file.write_text("# git file")

        normal_file = tmp_path / "main.py"
        normal_file.write_text("# normal file")

        archivos = [git_file, normal_file]

        # Act
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        resultado = filtrar_archivos_python_seguros(archivos, repo_path=tmp_path)

        # Assert
        assert len(resultado) == 1
        assert resultado[0] == normal_file

    def test_debe_excluir_directorios_pycache(self, tmp_path: Path) -> None:
        """Debe excluir archivos en __pycache__."""
        # Arrange
        (tmp_path / "__pycache__").mkdir()
        cache_file = tmp_path / "__pycache__" / "test.cpython-312.pyc"
        cache_file.write_text("# cache file")

        normal_file = tmp_path / "main.py"
        normal_file.write_text("# normal file")

        archivos = [cache_file, normal_file]

        # Act
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        resultado = filtrar_archivos_python_seguros(archivos, repo_path=tmp_path)

        # Assert
        assert len(resultado) == 1
        assert resultado[0] == normal_file

    def test_debe_excluir_directorios_build_dist(self, tmp_path: Path) -> None:
        """Debe excluir archivos en build/ y dist/."""
        # Arrange
        (tmp_path / "build").mkdir()
        build_file = tmp_path / "build" / "lib.py"
        build_file.write_text("# build file")

        (tmp_path / "dist").mkdir()
        dist_file = tmp_path / "dist" / "package.py"
        dist_file.write_text("# dist file")

        normal_file = tmp_path / "main.py"
        normal_file.write_text("# normal file")

        archivos = [build_file, dist_file, normal_file]

        # Act
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        resultado = filtrar_archivos_python_seguros(archivos, repo_path=tmp_path)

        # Assert
        assert len(resultado) == 1
        assert resultado[0] == normal_file

    def test_debe_rechazar_path_traversal(self, tmp_path: Path) -> None:
        """Debe rechazar archivos con path traversal (..)."""
        # Arrange
        archivo_malicioso = Path("../etc/passwd.py")

        # Act & Assert
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        with pytest.raises(ValueError, match="(?i)path traversal detectado"):
            filtrar_archivos_python_seguros([archivo_malicioso], repo_path=tmp_path)

    def test_debe_validar_path_traversal_por_defecto(self, tmp_path: Path) -> None:
        """Debe validar path traversal por defecto (validar_path_traversal=True)."""
        # Arrange
        archivo_malicioso = Path("../../malicious.py")

        # Act & Assert
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        with pytest.raises(ValueError, match="(?i)path traversal"):
            filtrar_archivos_python_seguros([archivo_malicioso], repo_path=tmp_path)

    def test_debe_permitir_deshabilitar_validacion_path_traversal(self, tmp_path: Path) -> None:
        """Debe permitir deshabilitar validación de path traversal."""
        # Arrange
        archivo = Path("../test.py")  # Path traversal pero validación deshabilitada

        # Act
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        resultado = filtrar_archivos_python_seguros(
            [archivo], repo_path=tmp_path, validar_path_traversal=False
        )

        # Assert - No debe lanzar error, pero puede no encontrar archivo
        # (es OK porque validar_existencia puede estar activo)
        assert isinstance(resultado, list)

    def test_debe_validar_existencia_de_archivos_por_defecto(self, tmp_path: Path) -> None:
        """Debe validar que archivos existan por defecto (validar_existencia=True)."""
        # Arrange
        archivo_existente = tmp_path / "exists.py"
        archivo_existente.write_text("# exists")
        archivo_inexistente = tmp_path / "not_exists.py"

        archivos = [archivo_existente, archivo_inexistente]

        # Act
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        resultado = filtrar_archivos_python_seguros(archivos, repo_path=tmp_path)

        # Assert
        assert len(resultado) == 1
        assert resultado[0] == archivo_existente

    def test_debe_permitir_deshabilitar_validacion_existencia(self, tmp_path: Path) -> None:
        """Debe permitir deshabilitar validación de existencia."""
        # Arrange
        archivo_inexistente = tmp_path / "not_exists.py"

        # Act
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        resultado = filtrar_archivos_python_seguros(
            [archivo_inexistente], repo_path=tmp_path, validar_existencia=False
        )

        # Assert
        assert len(resultado) == 1
        assert resultado[0] == archivo_inexistente

    def test_debe_usar_directorios_excluidos_por_defecto(self, tmp_path: Path) -> None:
        """Debe usar DIRECTORIOS_EXCLUIDOS por defecto."""
        # Arrange
        (tmp_path / "venv").mkdir()
        venv_file = tmp_path / "venv" / "lib.py"
        venv_file.write_text("# venv")

        normal_file = tmp_path / "main.py"
        normal_file.write_text("# normal")

        archivos = [venv_file, normal_file]

        # Act
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        resultado = filtrar_archivos_python_seguros(archivos, repo_path=tmp_path)

        # Assert
        assert len(resultado) == 1
        assert resultado[0] == normal_file

    def test_debe_permitir_directorios_excluidos_personalizados(self, tmp_path: Path) -> None:
        """Debe permitir especificar directorios excluidos personalizados."""
        # Arrange
        (tmp_path / "custom_dir").mkdir()
        custom_file = tmp_path / "custom_dir" / "lib.py"
        custom_file.write_text("# custom")

        normal_file = tmp_path / "main.py"
        normal_file.write_text("# normal")

        archivos = [custom_file, normal_file]

        # Act
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        resultado = filtrar_archivos_python_seguros(
            archivos, repo_path=tmp_path, excluir_directorios={"custom_dir"}
        )

        # Assert
        assert len(resultado) == 1
        assert resultado[0] == normal_file

    def test_debe_manejar_lista_vacia(self, tmp_path: Path) -> None:
        """Debe manejar lista vacía de archivos."""
        # Arrange
        archivos: list[Path] = []

        # Act
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        resultado = filtrar_archivos_python_seguros(archivos, repo_path=tmp_path)

        # Assert
        assert resultado == []

    def test_debe_retornar_lista_vacia_si_todos_excluidos(self, tmp_path: Path) -> None:
        """Debe retornar lista vacía si todos los archivos son excluidos."""
        # Arrange
        (tmp_path / "venv").mkdir()
        venv_file = tmp_path / "venv" / "lib.py"
        venv_file.write_text("# venv")

        (tmp_path / ".git").mkdir()
        git_file = tmp_path / ".git" / "config.py"
        git_file.write_text("# git")

        archivos = [venv_file, git_file]

        # Act
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        resultado = filtrar_archivos_python_seguros(archivos, repo_path=tmp_path)

        # Assert
        assert resultado == []

    def test_debe_manejar_archivos_en_subdirectorios_profundos(self, tmp_path: Path) -> None:
        """Debe manejar archivos en subdirectorios profundos."""
        # Arrange
        deep_dir = tmp_path / "src" / "ci_guardian" / "validators"
        deep_dir.mkdir(parents=True)
        deep_file = deep_dir / "test.py"
        deep_file.write_text("# deep file")

        archivos = [deep_file]

        # Act
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        resultado = filtrar_archivos_python_seguros(archivos, repo_path=tmp_path)

        # Assert
        assert len(resultado) == 1
        assert resultado[0] == deep_file

    def test_debe_excluir_si_cualquier_parte_del_path_es_excluida(self, tmp_path: Path) -> None:
        """Debe excluir si CUALQUIER parte del path está en directorios excluidos."""
        # Arrange
        nested_dir = tmp_path / "src" / "venv" / "lib"
        nested_dir.mkdir(parents=True)
        nested_file = nested_dir / "test.py"
        nested_file.write_text("# nested in venv")

        archivos = [nested_file]

        # Act
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        resultado = filtrar_archivos_python_seguros(archivos, repo_path=tmp_path)

        # Assert
        assert len(resultado) == 0


class TestFiltrarArchivosPythonSegurosCompatibilidad:
    """Tests de compatibilidad con código existente en cli.py y code_quality.py."""

    def test_compatibilidad_con_cli_filtrar_archivos_proyecto(self, tmp_path: Path) -> None:
        """Debe replicar comportamiento de cli._filtrar_archivos_proyecto."""
        # Arrange - Simular archivos como en cli.py
        (tmp_path / "src").mkdir()
        src_file = tmp_path / "src" / "main.py"
        src_file.write_text("# src")

        (tmp_path / "venv").mkdir()
        venv_file = tmp_path / "venv" / "lib.py"
        venv_file.write_text("# venv")

        archivos = [src_file, venv_file]

        # Act
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        resultado = filtrar_archivos_python_seguros(archivos, repo_path=tmp_path)

        # Assert - Debe excluir venv igual que cli.py
        assert len(resultado) == 1
        assert resultado[0] == src_file

    def test_compatibilidad_con_code_quality_filtrar_archivos_python(self, tmp_path: Path) -> None:
        """Debe replicar comportamiento de code_quality._filtrar_archivos_python."""
        # Arrange - Simular archivos como en code_quality.py
        py_file = tmp_path / "test.py"
        py_file.write_text("# python")

        txt_file = tmp_path / "readme.txt"
        txt_file.write_text("# text")

        inexistente = tmp_path / "not_exists.py"

        archivos = [py_file, txt_file, inexistente]

        # Act
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        resultado = filtrar_archivos_python_seguros(archivos, repo_path=tmp_path)

        # Assert - Solo .py existente, igual que code_quality.py
        assert len(resultado) == 1
        assert resultado[0] == py_file

    def test_compatibilidad_path_traversal_code_quality(self, tmp_path: Path) -> None:
        """Debe rechazar path traversal como code_quality._filtrar_archivos_python."""
        # Arrange
        archivo_malicioso = Path("../../../etc/passwd.py")

        # Act & Assert
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        with pytest.raises(ValueError, match="(?i)path traversal"):
            filtrar_archivos_python_seguros([archivo_malicioso], repo_path=tmp_path)


class TestDirectoriosExcluidosConstante:
    """Tests para la constante DIRECTORIOS_EXCLUIDOS."""

    def test_debe_existir_constante_directorios_excluidos(self) -> None:
        """Debe existir constante DIRECTORIOS_EXCLUIDOS."""
        from ci_guardian.validators.file_utils import DIRECTORIOS_EXCLUIDOS

        assert isinstance(DIRECTORIOS_EXCLUIDOS, set)

    def test_debe_incluir_venv_en_directorios_excluidos(self) -> None:
        """Debe incluir 'venv' en DIRECTORIOS_EXCLUIDOS."""
        from ci_guardian.validators.file_utils import DIRECTORIOS_EXCLUIDOS

        assert "venv" in DIRECTORIOS_EXCLUIDOS

    def test_debe_incluir_dot_venv_en_directorios_excluidos(self) -> None:
        """Debe incluir '.venv' en DIRECTORIOS_EXCLUIDOS."""
        from ci_guardian.validators.file_utils import DIRECTORIOS_EXCLUIDOS

        assert ".venv" in DIRECTORIOS_EXCLUIDOS

    def test_debe_incluir_git_en_directorios_excluidos(self) -> None:
        """Debe incluir '.git' en DIRECTORIOS_EXCLUIDOS."""
        from ci_guardian.validators.file_utils import DIRECTORIOS_EXCLUIDOS

        assert ".git" in DIRECTORIOS_EXCLUIDOS

    def test_debe_incluir_pycache_en_directorios_excluidos(self) -> None:
        """Debe incluir '__pycache__' en DIRECTORIOS_EXCLUIDOS."""
        from ci_guardian.validators.file_utils import DIRECTORIOS_EXCLUIDOS

        assert "__pycache__" in DIRECTORIOS_EXCLUIDOS

    def test_debe_incluir_build_dist_en_directorios_excluidos(self) -> None:
        """Debe incluir 'build' y 'dist' en DIRECTORIOS_EXCLUIDOS."""
        from ci_guardian.validators.file_utils import DIRECTORIOS_EXCLUIDOS

        assert "build" in DIRECTORIOS_EXCLUIDOS
        assert "dist" in DIRECTORIOS_EXCLUIDOS


class TestEdgeCases:
    """Tests de edge cases y casos límite."""

    def test_debe_manejar_archivos_con_espacios_en_nombre(self, tmp_path: Path) -> None:
        """Debe manejar archivos con espacios en el nombre."""
        # Arrange
        archivo_espacios = tmp_path / "mi archivo.py"
        archivo_espacios.write_text("# espacios")

        # Act
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        resultado = filtrar_archivos_python_seguros([archivo_espacios], repo_path=tmp_path)

        # Assert
        assert len(resultado) == 1
        assert resultado[0] == archivo_espacios

    def test_debe_manejar_archivos_con_unicode(self, tmp_path: Path) -> None:
        """Debe manejar archivos con caracteres Unicode."""
        # Arrange
        archivo_unicode = tmp_path / "测试.py"
        archivo_unicode.write_text("# unicode")

        # Act
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        resultado = filtrar_archivos_python_seguros([archivo_unicode], repo_path=tmp_path)

        # Assert
        assert len(resultado) == 1
        assert resultado[0] == archivo_unicode

    def test_debe_manejar_archivos_fuera_del_repo(self, tmp_path: Path) -> None:
        """Debe manejar archivos fuera del repo (para testing con mocks)."""
        # Arrange
        otro_dir = tmp_path / "otro_proyecto"
        otro_dir.mkdir()
        archivo_externo = otro_dir / "external.py"
        archivo_externo.write_text("# external")

        repo_path = tmp_path / "mi_proyecto"
        repo_path.mkdir()

        # Act
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        resultado = filtrar_archivos_python_seguros(
            [archivo_externo], repo_path=repo_path, validar_existencia=False
        )

        # Assert - Debe incluirlo (para compatibilidad con mocks en tests)
        assert len(resultado) == 1
        assert resultado[0] == archivo_externo
