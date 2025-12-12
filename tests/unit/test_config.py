"""Tests para el módulo core/config.py de CI Guardian.

Este módulo implementa tests para la configuración centralizada con dataclasses.
Los tests se escriben PRIMERO siguiendo TDD estricto (fase RED).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


class TestCIGuardianConfigDefault:
    """Tests para generación de configuración por defecto."""

    def test_debe_generar_configuracion_por_defecto_con_todos_los_hooks(
        self,
    ) -> None:
        """Debe generar configuración por defecto con los 4 hooks."""
        # Arrange & Act
        from ci_guardian.core.config import CIGuardianConfig

        config = CIGuardianConfig.default()

        # Assert
        assert config is not None, "Debe retornar configuración"
        assert "pre-commit" in config.hooks, "Debe incluir pre-commit"
        assert "pre-push" in config.hooks, "Debe incluir pre-push"
        assert "post-commit" in config.hooks, "Debe incluir post-commit"
        assert "commit-msg" in config.hooks, "Debe incluir commit-msg"

    def test_debe_incluir_version_en_configuracion_por_defecto(self) -> None:
        """Debe incluir número de versión en config por defecto."""
        # Arrange & Act
        from ci_guardian.core.config import CIGuardianConfig

        config = CIGuardianConfig.default()

        # Assert
        assert hasattr(config, "version"), "Debe tener atributo version"
        assert config.version is not None, "Version no debe ser None"
        assert len(config.version) > 0, "Version no debe estar vacía"

    def test_pre_commit_debe_tener_ruff_black_bandit_por_defecto(self) -> None:
        """Pre-commit debe tener validadores ruff, black, bandit por defecto."""
        # Arrange & Act
        from ci_guardian.core.config import CIGuardianConfig

        config = CIGuardianConfig.default()

        # Assert
        pre_commit = config.hooks["pre-commit"]
        assert pre_commit.enabled is True, "Pre-commit debe estar habilitado"
        assert "ruff" in pre_commit.validadores, "Debe incluir ruff"
        assert "black" in pre_commit.validadores, "Debe incluir black"
        assert "bandit" in pre_commit.validadores, "Debe incluir bandit"

    def test_pre_push_debe_tener_tests_por_defecto(self) -> None:
        """Pre-push debe tener validador tests por defecto."""
        # Arrange & Act
        from ci_guardian.core.config import CIGuardianConfig

        config = CIGuardianConfig.default()

        # Assert
        pre_push = config.hooks["pre-push"]
        assert pre_push.enabled is True, "Pre-push debe estar habilitado"
        assert "tests" in pre_push.validadores, "Debe incluir tests"

    def test_debe_incluir_configuracion_de_validadores(self) -> None:
        """Debe incluir configuración detallada para validadores."""
        # Arrange & Act
        from ci_guardian.core.config import CIGuardianConfig

        config = CIGuardianConfig.default()

        # Assert
        assert hasattr(config, "validadores"), "Debe tener atributo validadores"
        assert "ruff" in config.validadores, "Debe configurar ruff"
        assert "black" in config.validadores, "Debe configurar black"
        assert "bandit" in config.validadores, "Debe configurar bandit"


class TestCIGuardianConfigFromYAML:
    """Tests para carga de configuración desde archivo YAML."""

    def test_debe_cargar_configuracion_desde_yaml_valido(self, tmp_path: Path) -> None:
        """Debe cargar configuración desde archivo YAML válido."""
        # Arrange
        config_path = tmp_path / ".ci-guardian.yaml"
        config_data = {
            "version": "0.1.0",
            "hooks": {
                "pre-commit": {
                    "enabled": True,
                    "validadores": ["ruff", "black"],
                }
            },
            "validadores": {"ruff": {"enabled": True, "auto-fix": False}},
        }
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(config_data, f)

        # Act
        from ci_guardian.core.config import CIGuardianConfig

        config = CIGuardianConfig.from_yaml(config_path)

        # Assert
        assert config.version == "0.1.0", "Debe cargar version correcta"
        assert "pre-commit" in config.hooks, "Debe cargar hook pre-commit"
        assert config.hooks["pre-commit"].enabled is True
        assert "ruff" in config.hooks["pre-commit"].validadores

    def test_debe_retornar_defaults_si_archivo_no_existe(self, tmp_path: Path) -> None:
        """Debe retornar configuración por defecto si archivo no existe."""
        # Arrange
        config_path = tmp_path / "inexistente.yaml"

        # Act
        from ci_guardian.core.config import CIGuardianConfig

        config = CIGuardianConfig.from_yaml(config_path)

        # Assert - debe ser equivalente a default()
        default = CIGuardianConfig.default()
        assert config.version == default.version
        assert len(config.hooks) == len(default.hooks)

    def test_debe_lanzar_error_con_yaml_corrupto(self, tmp_path: Path) -> None:
        """Debe lanzar ValueError si el YAML está corrupto."""
        # Arrange
        config_path = tmp_path / ".ci-guardian.yaml"
        config_path.write_text("invalid: yaml: [corrupted", encoding="utf-8")

        # Act & Assert
        from ci_guardian.core.config import CIGuardianConfig

        with pytest.raises(ValueError, match="YAML.*inválido|corrupto|error"):
            CIGuardianConfig.from_yaml(config_path)

    def test_debe_manejar_yaml_vacio_como_defaults(self, tmp_path: Path) -> None:
        """Debe usar defaults si el YAML está vacío."""
        # Arrange
        config_path = tmp_path / ".ci-guardian.yaml"
        config_path.write_text("", encoding="utf-8")

        # Act
        from ci_guardian.core.config import CIGuardianConfig

        config = CIGuardianConfig.from_yaml(config_path)

        # Assert - debe retornar defaults
        assert config is not None
        assert len(config.hooks) > 0

    def test_debe_validar_hooks_desconocidos_con_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Debe generar warning si el YAML contiene hooks desconocidos."""
        # Arrange
        config_path = tmp_path / ".ci-guardian.yaml"
        config_data = {
            "version": "0.1.0",
            "hooks": {
                "pre-commit": {"enabled": True, "validadores": ["ruff"]},
                "hook-desconocido": {"enabled": True, "validadores": ["foo"]},
            },
        }
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(config_data, f)

        # Act
        from ci_guardian.core.config import CIGuardianConfig

        config = CIGuardianConfig.from_yaml(config_path)

        # Assert - debe cargar config válido e ignorar/advertir desconocido
        assert config is not None
        # Warning debería estar en logs (si se implementa logging)


class TestCIGuardianConfigToYAML:
    """Tests para serialización de configuración a YAML."""

    def test_debe_serializar_configuracion_a_yaml(self, tmp_path: Path) -> None:
        """Debe serializar configuración a archivo YAML válido."""
        # Arrange
        from ci_guardian.core.config import CIGuardianConfig

        config = CIGuardianConfig.default()
        output_path = tmp_path / "output.yaml"

        # Act
        config.to_yaml(output_path)

        # Assert
        assert output_path.exists(), "Debe crear archivo YAML"

        # Verificar que puede volver a cargar
        loaded = CIGuardianConfig.from_yaml(output_path)
        assert loaded.version == config.version

    def test_yaml_generado_debe_ser_valido_y_legible(self, tmp_path: Path) -> None:
        """El YAML generado debe ser válido y legible por humanos."""
        # Arrange
        from ci_guardian.core.config import CIGuardianConfig

        config = CIGuardianConfig.default()
        output_path = tmp_path / "output.yaml"

        # Act
        config.to_yaml(output_path)

        # Assert - leer como texto y verificar formato
        contenido = output_path.read_text(encoding="utf-8")
        assert "version:" in contenido
        assert "hooks:" in contenido
        assert "pre-commit:" in contenido
        assert "validadores:" in contenido

    def test_debe_preservar_orden_de_claves_en_yaml(self, tmp_path: Path) -> None:
        """Debe preservar orden lógico de claves en YAML."""
        # Arrange
        from ci_guardian.core.config import CIGuardianConfig

        config = CIGuardianConfig.default()
        output_path = tmp_path / "output.yaml"

        # Act
        config.to_yaml(output_path)

        # Assert - version debe estar al inicio
        contenido = output_path.read_text(encoding="utf-8")
        lineas = contenido.split("\n")
        primera_linea = lineas[0]
        assert "version" in primera_linea, "Version debe ser primera clave"


class TestCargarConfiguracion:
    """Tests para función de conveniencia cargar_configuracion()."""

    def test_debe_cargar_desde_directorio_repo(self, tmp_path: Path) -> None:
        """Debe cargar configuración desde directorio de repositorio."""
        # Arrange
        config_path = tmp_path / ".ci-guardian.yaml"
        config_data = {
            "version": "0.1.0",
            "hooks": {"pre-commit": {"enabled": True, "validadores": ["ruff"]}},
        }
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(config_data, f)

        # Act
        from ci_guardian.core.config import cargar_configuracion

        config = cargar_configuracion(tmp_path)

        # Assert
        assert config.version == "0.1.0"
        assert "pre-commit" in config.hooks

    def test_debe_retornar_defaults_si_no_existe_config_en_repo(self, tmp_path: Path) -> None:
        """Debe retornar defaults si no existe .ci-guardian.yaml en repo."""
        # Arrange - directorio vacío (sin .ci-guardian.yaml)

        # Act
        from ci_guardian.core.config import cargar_configuracion

        config = cargar_configuracion(tmp_path)

        # Assert - debe ser configuración por defecto
        assert config is not None
        assert len(config.hooks) > 0


class TestHookConfig:
    """Tests para dataclass HookConfig."""

    def test_debe_tener_valores_por_defecto_razonables(self) -> None:
        """HookConfig debe tener valores por defecto razonables."""
        # Arrange & Act
        from ci_guardian.core.config import HookConfig

        hook = HookConfig()

        # Assert
        assert hook.enabled is True, "enabled debe ser True por defecto"
        assert isinstance(hook.validadores, list), "validadores debe ser lista"
        assert len(hook.validadores) == 0, "validadores vacía por defecto"

    def test_debe_soportar_lista_de_validadores(self) -> None:
        """HookConfig debe soportar lista de validadores."""
        # Arrange & Act
        from ci_guardian.core.config import HookConfig

        hook = HookConfig(validadores=["ruff", "black", "bandit"])

        # Assert
        assert "ruff" in hook.validadores
        assert "black" in hook.validadores
        assert "bandit" in hook.validadores

    # NOTE: test_debe_soportar_skip_on_env_opcional ELIMINADO en v0.3.1
    # skip_on_env fue removido por razones de seguridad (contradecía objetivo anti-bypass).


class TestValidadorConfig:
    """Tests para dataclass ValidadorConfig."""

    def test_debe_tener_valores_por_defecto(self) -> None:
        """ValidadorConfig debe tener valores por defecto."""
        # Arrange & Act
        from ci_guardian.core.config import ValidadorConfig

        validador = ValidadorConfig()

        # Assert
        assert validador.enabled is True, "enabled True por defecto"
        assert validador.timeout == 60, "timeout 60 segundos por defecto"
        assert isinstance(validador.options, dict), "options dict por defecto"

    def test_debe_soportar_opciones_personalizadas(self) -> None:
        """ValidadorConfig debe soportar opciones personalizadas."""
        # Arrange & Act
        from ci_guardian.core.config import ValidadorConfig

        validador = ValidadorConfig(
            enabled=True, timeout=120, options={"line-length": "100", "auto-fix": "false"}
        )

        # Assert
        assert validador.timeout == 120
        assert validador.options["line-length"] == "100"
        assert validador.options["auto-fix"] == "false"


class TestConfigIntegration:
    """Tests de integración para flujo completo de configuración."""

    def test_flujo_completo_default_to_yaml_from_yaml(self, tmp_path: Path) -> None:
        """Test de flujo completo: default → to_yaml → from_yaml."""
        # Arrange
        from ci_guardian.core.config import CIGuardianConfig

        config_original = CIGuardianConfig.default()
        config_path = tmp_path / ".ci-guardian.yaml"

        # Act - Guardar y recargar
        config_original.to_yaml(config_path)
        config_recargado = CIGuardianConfig.from_yaml(config_path)

        # Assert - debe ser equivalente
        assert config_recargado.version == config_original.version
        assert len(config_recargado.hooks) == len(config_original.hooks)
        assert (
            config_recargado.hooks["pre-commit"].validadores
            == config_original.hooks["pre-commit"].validadores
        )

    def test_compatibilidad_con_pre_push_existente(self, tmp_path: Path) -> None:
        """Debe ser compatible con estructura usada en pre_push.py."""
        # Arrange - estructura actual de pre_push.py
        config_path = tmp_path / ".ci-guardian.yaml"
        config_data = {
            "hooks": {
                "pre-push": {
                    "enabled": True,
                    "validadores": ["tests"],
                }
            }
        }
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(config_data, f)

        # Act
        from ci_guardian.core.config import cargar_configuracion

        config = cargar_configuracion(tmp_path)

        # Assert
        pre_push = config.hooks.get("pre-push")
        assert pre_push is not None, "Debe cargar pre-push"
        assert pre_push.enabled is True
        assert "tests" in pre_push.validadores

    def test_compatibilidad_con_cli_configure_existente(self, tmp_path: Path) -> None:
        """Debe ser compatible con estructura generada por cli.configure()."""
        # Arrange - estructura actual de cli.configure()
        config_path = tmp_path / ".ci-guardian.yaml"
        config_data = {
            "version": "0.1.1",
            "hooks": {
                "pre-commit": {
                    "enabled": True,
                    "validadores": ["ruff", "black", "bandit"],
                },
                "pre-push": {
                    "enabled": True,
                    "validadores": ["tests", "github-actions"],
                },
                "post-commit": {
                    "enabled": True,
                    "validadores": ["authorship", "no-verify-blocker"],
                },
            },
            "validadores": {
                "ruff": {"enabled": True, "auto-fix": False},
                "black": {"enabled": True, "line-length": 100},
                "bandit": {"enabled": True, "severity": "medium"},
            },
        }
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(config_data, f)

        # Act
        from ci_guardian.core.config import CIGuardianConfig

        config = CIGuardianConfig.from_yaml(config_path)

        # Assert
        assert config.version == "0.1.1"
        assert "pre-commit" in config.hooks
        assert "pre-push" in config.hooks
        assert "post-commit" in config.hooks
        assert "ruff" in config.validadores
        assert config.validadores["black"].options.get("line-length") == 100
