"""
Tests unitarios para el validador anti --no-verify.

Este módulo contiene todos los tests necesarios para validar el sistema de tokens
que previene el uso de `git commit --no-verify` para saltarse los hooks.
"""

import platform
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest


class TestGeneracionTokens:
    """Tests para la generación de tokens criptográficamente seguros."""

    def test_debe_generar_token_con_longitud_minima(self) -> None:
        """Debe generar token de al menos 32 caracteres (256 bits)."""
        # Act
        from ci_guardian.validators.no_verify_blocker import generar_token_seguro

        token = generar_token_seguro()

        # Assert
        assert (
            len(token) >= 32
        ), f"Token debe tener al menos 32 caracteres (256 bits), obtuvo {len(token)}"
        assert isinstance(token, str), "Token debe ser una cadena de texto"

    def test_debe_generar_tokens_unicos(self) -> None:
        """Cada invocación debe generar un token diferente."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import generar_token_seguro

        # Act
        token1 = generar_token_seguro()
        token2 = generar_token_seguro()
        token3 = generar_token_seguro()

        # Assert
        assert token1 != token2, "Los tokens deben ser únicos"
        assert token2 != token3, "Los tokens deben ser únicos"
        assert token1 != token3, "Los tokens deben ser únicos"

    def test_debe_usar_secrets_module_no_random(self) -> None:
        """Debe usar el módulo secrets (criptográficamente seguro), no random."""
        # Arrange
        import inspect

        # Act & Assert
        # Verificar que el código usa secrets.token_hex
        from ci_guardian.validators import no_verify_blocker

        codigo_fuente = inspect.getsource(no_verify_blocker.generar_token_seguro)
        assert "secrets" in codigo_fuente, "Debe usar el módulo secrets"
        assert (
            "token_hex" in codigo_fuente or "token_urlsafe" in codigo_fuente
        ), "Debe usar secrets.token_hex o secrets.token_urlsafe"
        assert "random" not in codigo_fuente.lower(), "NO debe usar el módulo random"

    def test_debe_generar_token_hexadecimal_valido(self) -> None:
        """Debe generar token en formato hexadecimal válido."""
        # Act
        from ci_guardian.validators.no_verify_blocker import generar_token_seguro

        token = generar_token_seguro()

        # Assert
        # Token hexadecimal solo contiene caracteres 0-9 y a-f
        assert all(
            c in "0123456789abcdef" for c in token
        ), "Token debe contener solo caracteres hexadecimales (0-9, a-f)"

    def test_debe_generar_token_sin_espacios_ni_saltos_linea(self) -> None:
        """Debe generar token sin espacios, saltos de línea u otros caracteres."""
        # Act
        from ci_guardian.validators.no_verify_blocker import generar_token_seguro

        token = generar_token_seguro()

        # Assert
        assert " " not in token, "Token no debe contener espacios"
        assert "\n" not in token, "Token no debe contener saltos de línea"
        assert "\r" not in token, "Token no debe contener retornos de carro"
        assert "\t" not in token, "Token no debe contener tabulaciones"


class TestGuardadoTokens:
    """Tests para el guardado de tokens en .git/CI_GUARDIAN_TOKEN."""

    @pytest.fixture
    def repo_mock(self, tmp_path: Path) -> Path:
        """Crea un repositorio git mock para tests."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        return repo_path

    def test_debe_guardar_token_en_archivo_correcto(self, repo_mock: Path) -> None:
        """Debe guardar token en .git/CI_GUARDIAN_TOKEN."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import guardar_token

        token = "a" * 64  # Token de ejemplo

        # Act
        guardar_token(repo_mock, token)

        # Assert
        token_path = repo_mock / ".git" / "CI_GUARDIAN_TOKEN"
        assert token_path.exists(), "Archivo de token debe existir"
        assert token_path.is_file(), "Debe ser un archivo, no un directorio"

    def test_debe_guardar_contenido_token_correctamente(self, repo_mock: Path) -> None:
        """Debe escribir el contenido del token exactamente como se proporcionó."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import guardar_token

        token = "abc123def456" * 5  # Token de prueba

        # Act
        guardar_token(repo_mock, token)

        # Assert
        token_path = repo_mock / ".git" / "CI_GUARDIAN_TOKEN"
        contenido = token_path.read_text(encoding="utf-8").strip()
        assert contenido == token, f"Contenido debe ser '{token}', obtuvo '{contenido}'"

    def test_debe_sobrescribir_token_anterior_si_existe(self, repo_mock: Path) -> None:
        """Debe sobrescribir el token anterior sin error si ya existe."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import guardar_token

        token_viejo = "old_token_12345" * 4
        token_nuevo = "new_token_67890" * 4

        # Act
        guardar_token(repo_mock, token_viejo)
        guardar_token(repo_mock, token_nuevo)  # Sobrescribir

        # Assert
        token_path = repo_mock / ".git" / "CI_GUARDIAN_TOKEN"
        contenido = token_path.read_text(encoding="utf-8").strip()
        assert contenido == token_nuevo, "Debe contener el token nuevo"
        assert token_viejo not in contenido, "No debe contener el token viejo"

    def test_debe_rechazar_repo_sin_directorio_git(self, tmp_path: Path) -> None:
        """Debe rechazar guardar token en directorio sin .git/."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import guardar_token

        dir_no_repo = tmp_path / "no_repo"
        dir_no_repo.mkdir()
        token = "a" * 64

        # Act & Assert
        with pytest.raises(ValueError, match="no es un repositorio Git válido"):
            guardar_token(dir_no_repo, token)

    def test_debe_validar_path_para_prevenir_path_traversal(self, repo_mock: Path) -> None:
        """Debe prevenir path traversal en el nombre del archivo."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import guardar_token

        token = "a" * 64

        # Act
        guardar_token(repo_mock, token)

        # Assert
        token_path = repo_mock / ".git" / "CI_GUARDIAN_TOKEN"
        # Verificar que el path resuelto está dentro de .git/
        assert (
            token_path.resolve().parent == (repo_mock / ".git").resolve()
        ), "Token debe estar en .git/, no fuera por path traversal"

    def test_debe_crear_archivo_con_permisos_seguros(self, repo_mock: Path) -> None:
        """Debe crear archivo con permisos 600 (solo dueño lee/escribe)."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import guardar_token

        token = "a" * 64

        # Act
        guardar_token(repo_mock, token)

        # Assert
        if platform.system() != "Windows":
            token_path = repo_mock / ".git" / "CI_GUARDIAN_TOKEN"
            permisos = oct(token_path.stat().st_mode)[-3:]
            assert permisos == "600", f"Permisos deben ser 600 (solo dueño), obtuvo {permisos}"

    def test_debe_rechazar_token_vacio(self, repo_mock: Path) -> None:
        """Debe rechazar guardar token vacío."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import guardar_token

        token_vacio = ""

        # Act & Assert
        with pytest.raises(ValueError, match="Token no puede estar vacío"):
            guardar_token(repo_mock, token_vacio)


class TestValidacionConsumoTokens:
    """Tests para la validación y consumo de tokens."""

    @pytest.fixture
    def repo_mock(self, tmp_path: Path) -> Path:
        """Crea un repositorio git mock para tests."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        return repo_path

    def test_debe_retornar_true_cuando_token_existe(self, repo_mock: Path) -> None:
        """Debe retornar True cuando el archivo de token existe y es válido."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import validar_y_consumir_token

        token_path = repo_mock / ".git" / "CI_GUARDIAN_TOKEN"
        token_path.write_text("valid_token_abc123" * 4, encoding="utf-8")

        # Act
        resultado = validar_y_consumir_token(repo_mock)

        # Assert
        assert resultado is True, "Debe retornar True cuando token existe"

    def test_debe_retornar_false_cuando_token_no_existe(self, repo_mock: Path) -> None:
        """Debe retornar False cuando el archivo de token no existe."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import validar_y_consumir_token

        # No crear archivo de token

        # Act
        resultado = validar_y_consumir_token(repo_mock)

        # Assert
        assert resultado is False, "Debe retornar False cuando token no existe"

    def test_debe_eliminar_archivo_token_despues_validar(self, repo_mock: Path) -> None:
        """Debe eliminar el archivo de token después de validarlo (consumir)."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import validar_y_consumir_token

        token_path = repo_mock / ".git" / "CI_GUARDIAN_TOKEN"
        token_path.write_text("valid_token_abc123" * 4, encoding="utf-8")

        # Act
        validar_y_consumir_token(repo_mock)

        # Assert
        assert not token_path.exists(), "Archivo de token debe ser eliminado después de validar"

    def test_debe_retornar_false_cuando_token_esta_vacio(self, repo_mock: Path) -> None:
        """Debe retornar False cuando el archivo existe pero está vacío."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import validar_y_consumir_token

        token_path = repo_mock / ".git" / "CI_GUARDIAN_TOKEN"
        token_path.write_text("", encoding="utf-8")  # Archivo vacío

        # Act
        resultado = validar_y_consumir_token(repo_mock)

        # Assert
        assert resultado is False, "Debe retornar False cuando token está vacío"

    def test_debe_retornar_false_cuando_token_solo_espacios(self, repo_mock: Path) -> None:
        """Debe retornar False cuando el token contiene solo espacios."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import validar_y_consumir_token

        token_path = repo_mock / ".git" / "CI_GUARDIAN_TOKEN"
        token_path.write_text("   \n\t  ", encoding="utf-8")  # Solo whitespace

        # Act
        resultado = validar_y_consumir_token(repo_mock)

        # Assert
        assert resultado is False, "Debe retornar False cuando token solo tiene espacios"

    def test_debe_eliminar_token_invalido_despues_validar(self, repo_mock: Path) -> None:
        """Debe eliminar token inválido después de validar."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import validar_y_consumir_token

        token_path = repo_mock / ".git" / "CI_GUARDIAN_TOKEN"
        token_path.write_text("   ", encoding="utf-8")  # Token inválido

        # Act
        validar_y_consumir_token(repo_mock)

        # Assert
        assert not token_path.exists(), "Token inválido debe ser eliminado"

    def test_debe_rechazar_repo_sin_directorio_git(self, tmp_path: Path) -> None:
        """Debe rechazar validar en directorio sin .git/."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import validar_y_consumir_token

        dir_no_repo = tmp_path / "no_repo"
        dir_no_repo.mkdir()

        # Act & Assert
        with pytest.raises(ValueError, match="no es un repositorio Git válido"):
            validar_y_consumir_token(dir_no_repo)

    def test_debe_manejar_errores_permisos_lectura(self, repo_mock: Path) -> None:
        """Debe manejar errores cuando no hay permisos para leer el token."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import validar_y_consumir_token

        token_path = repo_mock / ".git" / "CI_GUARDIAN_TOKEN"
        token_path.write_text("valid_token" * 8, encoding="utf-8")

        if platform.system() != "Windows":
            token_path.chmod(0o000)  # Sin permisos

            # Act & Assert
            with pytest.raises(PermissionError):
                validar_y_consumir_token(repo_mock)

            # Cleanup
            token_path.chmod(0o600)


class TestRevocacionCommits:
    """Tests para la revocación de commits cuando no hay token."""

    @pytest.fixture
    def repo_mock(self, tmp_path: Path) -> Path:
        """Crea un repositorio git mock para tests."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        return repo_path

    @patch("ci_guardian.validators.no_verify_blocker.subprocess.run")
    def test_debe_ejecutar_git_reset_soft_head_1(
        self, mock_subprocess: Mock, repo_mock: Path
    ) -> None:
        """Debe ejecutar 'git reset --soft HEAD~1' para revertir commit."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import revertir_ultimo_commit

        mock_subprocess.return_value = MagicMock(
            returncode=0, stdout="HEAD is now at abc1234", stderr=""
        )

        # Act
        revertir_ultimo_commit(repo_mock)

        # Assert
        mock_subprocess.assert_called_once()
        args_llamada = mock_subprocess.call_args[0][0]
        assert args_llamada == [
            "git",
            "reset",
            "--soft",
            "HEAD~1",
        ], f"Debe llamar 'git reset --soft HEAD~1', llamó {args_llamada}"

    @patch("ci_guardian.validators.no_verify_blocker.subprocess.run")
    def test_debe_ejecutar_git_en_directorio_repo(
        self, mock_subprocess: Mock, repo_mock: Path
    ) -> None:
        """Debe ejecutar git en el directorio del repositorio (cwd)."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import revertir_ultimo_commit

        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # Act
        revertir_ultimo_commit(repo_mock)

        # Assert
        kwargs_llamada = mock_subprocess.call_args[1]
        assert (
            kwargs_llamada.get("cwd") == repo_mock
        ), f"Debe ejecutar git en {repo_mock}, ejecutó en {kwargs_llamada.get('cwd')}"

    @patch("ci_guardian.validators.no_verify_blocker.subprocess.run")
    def test_debe_retornar_true_cuando_reversion_exitosa(
        self, mock_subprocess: Mock, repo_mock: Path
    ) -> None:
        """Debe retornar (True, mensaje) cuando la reversión es exitosa."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import revertir_ultimo_commit

        mock_subprocess.return_value = MagicMock(
            returncode=0, stdout="HEAD is now at abc1234", stderr=""
        )

        # Act
        exito, mensaje = revertir_ultimo_commit(repo_mock)

        # Assert
        assert exito is True, "Debe retornar True cuando reversión exitosa"
        assert (
            "revertido" in mensaje.lower() or "exitosa" in mensaje.lower()
        ), f"Mensaje debe indicar éxito, obtuvo: {mensaje}"

    @patch("ci_guardian.validators.no_verify_blocker.subprocess.run")
    def test_debe_retornar_false_cuando_reversion_falla(
        self, mock_subprocess: Mock, repo_mock: Path
    ) -> None:
        """Debe retornar (False, mensaje) cuando git reset falla."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import revertir_ultimo_commit

        mock_subprocess.return_value = MagicMock(
            returncode=1, stdout="", stderr="fatal: ambiguous argument 'HEAD~1'"
        )

        # Act
        exito, mensaje = revertir_ultimo_commit(repo_mock)

        # Assert
        assert exito is False, "Debe retornar False cuando reversión falla"
        assert (
            "error" in mensaje.lower() or "fatal" in mensaje.lower()
        ), f"Mensaje debe indicar error, obtuvo: {mensaje}"

    @patch("ci_guardian.validators.no_verify_blocker.subprocess.run")
    def test_debe_manejar_caso_sin_commits_para_revertir(
        self, mock_subprocess: Mock, repo_mock: Path
    ) -> None:
        """Debe manejar caso donde no hay commits para revertir."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import revertir_ultimo_commit

        mock_subprocess.return_value = MagicMock(
            returncode=128, stdout="", stderr="fatal: ambiguous argument 'HEAD~1': unknown revision"
        )

        # Act
        exito, mensaje = revertir_ultimo_commit(repo_mock)

        # Assert
        assert exito is False, "Debe retornar False cuando no hay commits"
        assert (
            "no hay commits" in mensaje.lower() or "sin commits" in mensaje.lower()
        ), f"Mensaje debe indicar falta de commits, obtuvo: {mensaje}"

    @patch("ci_guardian.validators.no_verify_blocker.subprocess.run")
    def test_debe_usar_shell_false_para_seguridad(
        self, mock_subprocess: Mock, repo_mock: Path
    ) -> None:
        """Debe ejecutar subprocess con shell=False para prevenir command injection."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import revertir_ultimo_commit

        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # Act
        revertir_ultimo_commit(repo_mock)

        # Assert
        kwargs_llamada = mock_subprocess.call_args[1]
        assert (
            kwargs_llamada.get("shell") is False or "shell" not in kwargs_llamada
        ), "Debe usar shell=False o no especificarlo (default False)"

    @patch("ci_guardian.validators.no_verify_blocker.subprocess.run")
    def test_debe_rechazar_repo_sin_directorio_git(
        self, mock_subprocess: Mock, tmp_path: Path
    ) -> None:
        """Debe rechazar revertir en directorio sin .git/."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import revertir_ultimo_commit

        dir_no_repo = tmp_path / "no_repo"
        dir_no_repo.mkdir()

        # Act & Assert
        with pytest.raises(ValueError, match="no es un repositorio Git válido"):
            revertir_ultimo_commit(dir_no_repo)

        # No debe llamar subprocess
        mock_subprocess.assert_not_called()


class TestWorkflowCompleto:
    """Tests para el workflow completo pre-commit → post-commit."""

    @pytest.fixture
    def repo_mock(self, tmp_path: Path) -> Path:
        """Crea un repositorio git mock para tests."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        return repo_path

    @patch("ci_guardian.validators.no_verify_blocker.subprocess.run")
    def test_debe_validar_commit_normal_exitosamente(
        self, mock_subprocess: Mock, repo_mock: Path
    ) -> None:
        """Debe validar commit normal (con pre-commit) exitosamente."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import (
            generar_token_seguro,
            guardar_token,
            verificar_commit_sin_hooks,
        )

        # Simular pre-commit: generar y guardar token
        token = generar_token_seguro()
        guardar_token(repo_mock, token)

        # Act
        # Simular post-commit: verificar token
        resultado = verificar_commit_sin_hooks(repo_mock)

        # Assert
        assert resultado is True, "Debe validar commit normal como exitoso"
        # No debe llamar git reset
        mock_subprocess.assert_not_called()

    @patch("ci_guardian.validators.no_verify_blocker.subprocess.run")
    def test_debe_revertir_commit_con_no_verify(
        self, mock_subprocess: Mock, repo_mock: Path
    ) -> None:
        """Debe revertir commit hecho con --no-verify (sin token)."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import verificar_commit_sin_hooks

        # NO crear token (simular --no-verify)
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # Act
        resultado = verificar_commit_sin_hooks(repo_mock)

        # Assert
        assert resultado is False, "Debe retornar False cuando no hay token"
        # Debe llamar git reset para revertir
        mock_subprocess.assert_called_once()
        args_llamada = mock_subprocess.call_args[0][0]
        assert "git" in args_llamada[0].lower(), "Debe ejecutar git"
        assert "reset" in args_llamada, "Debe ejecutar reset"

    @patch("ci_guardian.validators.no_verify_blocker.subprocess.run")
    def test_debe_consumir_token_en_commit_valido(
        self, mock_subprocess: Mock, repo_mock: Path
    ) -> None:
        """Debe consumir (eliminar) token después de commit válido."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import (
            generar_token_seguro,
            guardar_token,
            verificar_commit_sin_hooks,
        )

        token = generar_token_seguro()
        guardar_token(repo_mock, token)
        token_path = repo_mock / ".git" / "CI_GUARDIAN_TOKEN"

        # Act
        verificar_commit_sin_hooks(repo_mock)

        # Assert
        assert not token_path.exists(), "Token debe ser consumido después de validar"

    def test_debe_detectar_multiples_commits_sin_token(self, repo_mock: Path) -> None:
        """Debe detectar y rechazar múltiples commits consecutivos sin token."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import verificar_commit_sin_hooks

        # Act - Múltiples verificaciones sin token
        resultado1 = verificar_commit_sin_hooks(repo_mock)
        resultado2 = verificar_commit_sin_hooks(repo_mock)
        resultado3 = verificar_commit_sin_hooks(repo_mock)

        # Assert
        assert resultado1 is False, "Primer commit sin token debe ser rechazado"
        assert resultado2 is False, "Segundo commit sin token debe ser rechazado"
        assert resultado3 is False, "Tercer commit sin token debe ser rechazado"

    def test_workflow_completo_commit_valido(self, repo_mock: Path) -> None:
        """Test del workflow completo: generar token → validar → consumir."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import (
            generar_token_seguro,
            guardar_token,
            validar_y_consumir_token,
        )

        # Act
        # 1. Pre-commit: generar y guardar token
        token = generar_token_seguro()
        guardar_token(repo_mock, token)

        # 2. Commit ejecuta...

        # 3. Post-commit: validar y consumir token
        token_valido = validar_y_consumir_token(repo_mock)

        # Assert
        assert token_valido is True, "Token debe ser válido"
        token_path = repo_mock / ".git" / "CI_GUARDIAN_TOKEN"
        assert not token_path.exists(), "Token debe ser consumido"


class TestEdgeCasesSeguridad:
    """Tests para casos límite y seguridad del sistema de tokens."""

    @pytest.fixture
    def repo_mock(self, tmp_path: Path) -> Path:
        """Crea un repositorio git mock para tests."""
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()
        return repo_path

    def test_debe_rechazar_token_con_command_injection_attempt(self, repo_mock: Path) -> None:
        """Debe rechazar tokens con intentos de command injection."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import guardar_token

        token_malicioso = "abc123; rm -rf /; echo"  # noqa: S105 (test value, not real password)

        # Act & Assert
        # Debe rechazar o sanitizar el token
        with pytest.raises(ValueError, match="Token contiene caracteres no permitidos"):
            guardar_token(repo_mock, token_malicioso)

    def test_debe_rechazar_token_con_caracteres_especiales(self, repo_mock: Path) -> None:
        """Debe rechazar tokens con caracteres especiales peligrosos."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import guardar_token

        tokens_peligrosos = [
            "abc$(whoami)def",
            "abc`ls -la`def",
            "abc&&echo'pwned'",
            "abc|cat/etc/passwd",
        ]

        # Act & Assert
        for token in tokens_peligrosos:
            with pytest.raises(ValueError, match="Token contiene caracteres no permitidos"):
                guardar_token(repo_mock, token)

    def test_debe_validar_solo_caracteres_hexadecimales_en_token(self, repo_mock: Path) -> None:
        """Debe validar que token solo contenga caracteres hexadecimales."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import guardar_token

        token_valido = "abc123def456" * 5  # Solo hex
        token_invalido = "abc123XYZ456" * 5  # Contiene X, Y, Z (no hex minúsculas)

        # Act & Assert
        # Token válido debe guardarse sin problemas
        guardar_token(repo_mock, token_valido)
        token_path = repo_mock / ".git" / "CI_GUARDIAN_TOKEN"
        assert token_path.exists(), "Token válido debe guardarse"

        # Token inválido debe ser rechazado
        with pytest.raises(ValueError, match="Token contiene caracteres no permitidos"):
            guardar_token(repo_mock, token_invalido)

    def test_debe_prevenir_path_traversal_en_nombre_archivo(self, repo_mock: Path) -> None:
        """Debe prevenir path traversal en el path del archivo de token."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import guardar_token

        token = "a" * 64

        # Act
        guardar_token(repo_mock, token)

        # Assert
        token_path = repo_mock / ".git" / "CI_GUARDIAN_TOKEN"
        resolved_path = token_path.resolve()
        expected_parent = (repo_mock / ".git").resolve()

        assert (
            resolved_path.parent == expected_parent
        ), f"Token debe estar en {expected_parent}, está en {resolved_path.parent}"

    @patch("ci_guardian.validators.no_verify_blocker.subprocess.run")
    def test_debe_resistir_timing_attacks_en_validacion(
        self, mock_subprocess: Mock, repo_mock: Path
    ) -> None:
        """Debe usar comparación de tiempo constante para prevenir timing attacks."""
        # Arrange
        import time

        from ci_guardian.validators.no_verify_blocker import validar_y_consumir_token

        token_path = repo_mock / ".git" / "CI_GUARDIAN_TOKEN"

        # Test con token válido
        token_path.write_text("a" * 64, encoding="utf-8")
        inicio = time.perf_counter()
        _ = validar_y_consumir_token(repo_mock)  # Resultado no importa, medimos tiempo
        tiempo_valido = time.perf_counter() - inicio

        # Test sin token
        inicio = time.perf_counter()
        _ = validar_y_consumir_token(repo_mock)  # Resultado no importa, medimos tiempo
        tiempo_invalido = time.perf_counter() - inicio

        # Assert
        # Los tiempos deben ser similares (diferencia < 10ms)
        diferencia = abs(tiempo_valido - tiempo_invalido)
        assert diferencia < 0.01, (
            f"Diferencia de timing muy grande: {diferencia:.4f}s "
            "(posible timing attack vulnerability)"
        )

    @patch("ci_guardian.validators.no_verify_blocker.subprocess.run")
    def test_debe_manejar_race_condition_multiples_commits(
        self, mock_subprocess: Mock, repo_mock: Path
    ) -> None:
        """Debe manejar correctamente race conditions con múltiples commits rápidos."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import (
            generar_token_seguro,
            guardar_token,
            verificar_commit_sin_hooks,
        )

        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # Act
        # Simular dos commits muy rápidos
        token1 = generar_token_seguro()
        guardar_token(repo_mock, token1)

        # Primer commit valida y consume token
        resultado1 = verificar_commit_sin_hooks(repo_mock)

        # Segundo commit (sin pre-commit entre medio) no debe tener token
        resultado2 = verificar_commit_sin_hooks(repo_mock)

        # Assert
        assert resultado1 is True, "Primer commit debe ser válido"
        assert resultado2 is False, "Segundo commit debe fallar (sin nuevo token)"

    def test_debe_manejar_archivo_token_corrupto(self, repo_mock: Path) -> None:
        """Debe manejar archivo de token corrupto o con contenido inválido."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import validar_y_consumir_token

        token_path = repo_mock / ".git" / "CI_GUARDIAN_TOKEN"

        # Escribir datos binarios inválidos
        token_path.write_bytes(b"\x00\xff\xfe\xfd" * 16)

        # Act
        resultado = validar_y_consumir_token(repo_mock)

        # Assert
        assert resultado is False, "Debe rechazar archivo corrupto"
        assert not token_path.exists(), "Archivo corrupto debe ser eliminado"

    @pytest.mark.skipif(
        platform.system() == "Windows", reason="Test específico de Linux (permisos de archivos)"
    )
    def test_debe_detectar_archivo_token_con_permisos_inseguros(self, repo_mock: Path) -> None:
        """Debe detectar y rechazar archivo de token con permisos inseguros."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import validar_y_consumir_token

        token_path = repo_mock / ".git" / "CI_GUARDIAN_TOKEN"
        token_path.write_text("a" * 64, encoding="utf-8")
        token_path.chmod(0o777)  # Permisos inseguros (todos pueden leer/escribir)

        # Act & Assert
        with pytest.raises(PermissionError, match="permisos inseguros|demasiado permisivo"):
            validar_y_consumir_token(repo_mock)

    def test_debe_manejar_token_extremadamente_largo(self, repo_mock: Path) -> None:
        """Debe manejar tokens extremadamente largos sin problemas."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import (
            guardar_token,
        )

        # Token de 10KB (mucho más largo que los 64 chars esperados)
        token_largo = "a" * 10000

        # Act & Assert
        with pytest.raises(ValueError, match="demasiado largo|excede el límite"):
            guardar_token(repo_mock, token_largo)

    def test_debe_validar_tipo_dato_token(self, repo_mock: Path) -> None:
        """Debe validar que el token es del tipo correcto (str)."""
        # Arrange
        from ci_guardian.validators.no_verify_blocker import guardar_token

        # Act & Assert
        with pytest.raises(TypeError, match="debe ser una cadena|debe ser str"):
            guardar_token(repo_mock, 12345)  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="debe ser una cadena|debe ser str"):
            guardar_token(repo_mock, None)  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="debe ser una cadena|debe ser str"):
            guardar_token(repo_mock, ["token"])  # type: ignore[arg-type]
