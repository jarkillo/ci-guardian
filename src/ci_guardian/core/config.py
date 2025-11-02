"""Gestión centralizada de configuración de CI Guardian.

Este módulo proporciona dataclasses para configuración tipada y funciones
para carga/guardado desde archivos YAML.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Logger para el módulo
logger = logging.getLogger(__name__)


@dataclass
class ValidadorConfig:
    """Configuración de un validador individual.

    Attributes:
        enabled: Si el validador está habilitado
        timeout: Tiempo máximo de ejecución en segundos
        options: Opciones personalizadas del validador
    """

    enabled: bool = True
    timeout: int = 60
    options: dict[str, str | int | bool] = field(default_factory=dict)


@dataclass
class HookConfig:
    """Configuración de un hook Git.

    Attributes:
        enabled: Si el hook está habilitado
        validadores: Lista de validadores a ejecutar
        skip_on_env: Variable de entorno para skip temporal
    """

    enabled: bool = True
    validadores: list[str] = field(default_factory=list)
    skip_on_env: str | None = None


@dataclass
class CIGuardianConfig:
    """Configuración completa de CI Guardian.

    Attributes:
        version: Versión de CI Guardian
        hooks: Configuración de hooks Git (pre-commit, pre-push, etc.)
        validadores: Configuración detallada de validadores
    """

    version: str
    hooks: dict[str, HookConfig] = field(default_factory=dict)
    validadores: dict[str, ValidadorConfig] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path) -> CIGuardianConfig:
        """Carga configuración desde archivo YAML con validación.

        Args:
            path: Ruta al archivo .ci-guardian.yaml

        Returns:
            Configuración cargada y validada

        Raises:
            ValueError: Si el archivo YAML está corrupto o es inválido
        """
        if not path.exists():
            logger.debug(f"Archivo de configuración no existe: {path}, usando defaults")
            return cls.default()

        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # Si el YAML está vacío o es None, usar defaults
            if not data:
                logger.debug("Archivo de configuración vacío, usando defaults")
                return cls.default()

            # Parsear hooks
            hooks_data = data.get("hooks", {})
            hooks = {}
            for hook_name, hook_dict in hooks_data.items():
                if isinstance(hook_dict, dict):
                    hooks[hook_name] = HookConfig(
                        enabled=hook_dict.get("enabled", True),
                        validadores=hook_dict.get("validadores", []),
                        skip_on_env=hook_dict.get("skip_on_env"),
                    )
                else:
                    logger.warning(f"Hook '{hook_name}' tiene formato inválido, ignorando")

            # Parsear validadores
            validadores_data = data.get("validadores", {})
            validadores = {}
            for val_name, val_dict in validadores_data.items():
                if isinstance(val_dict, dict):
                    # Extraer enabled, timeout y el resto son options
                    enabled = val_dict.get("enabled", True)
                    timeout = val_dict.get("timeout", 60)

                    # Options son todos los campos excepto enabled y timeout
                    options = {k: v for k, v in val_dict.items() if k not in ("enabled", "timeout")}

                    validadores[val_name] = ValidadorConfig(
                        enabled=enabled, timeout=timeout, options=options
                    )
                else:
                    logger.warning(f"Validador '{val_name}' tiene formato inválido, ignorando")

            # Versión (default si no existe)
            version = data.get("version")
            if not version:
                # Obtener versión actual de ci_guardian
                try:
                    from ci_guardian import __version__

                    version = __version__
                except Exception:
                    version = "0.1.0"

            return cls(version=version, hooks=hooks, validadores=validadores)

        except yaml.YAMLError as e:
            raise ValueError(f"Error parseando YAML: archivo corrupto o inválido - {e}") from e
        except Exception as e:
            raise ValueError(f"Error cargando configuración: {e}") from e

    @classmethod
    def default(cls) -> CIGuardianConfig:
        """Genera configuración por defecto.

        Returns:
            Configuración con valores por defecto para todos los hooks
        """
        # Obtener versión actual
        try:
            from ci_guardian import __version__

            version = __version__
        except Exception:
            version = "0.1.0"

        return cls(
            version=version,
            hooks={
                "pre-commit": HookConfig(
                    enabled=True,
                    validadores=["ruff", "black", "bandit"],
                ),
                "commit-msg": HookConfig(
                    enabled=True,
                    validadores=["authorship"],
                ),
                "post-commit": HookConfig(
                    enabled=True,
                    validadores=["no-verify-token"],
                ),
                "pre-push": HookConfig(
                    enabled=True,
                    validadores=["tests"],
                    skip_on_env="CI_GUARDIAN_SKIP_TESTS",
                ),
            },
            validadores={
                "ruff": ValidadorConfig(
                    enabled=True,
                    timeout=60,
                    options={"auto-fix": False},
                ),
                "black": ValidadorConfig(
                    enabled=True,
                    timeout=60,
                    options={"line-length": 100},
                ),
                "bandit": ValidadorConfig(
                    enabled=True,
                    timeout=60,
                    options={"severity": "medium"},
                ),
            },
        )

    def to_yaml(self, path: Path) -> None:
        """Guarda configuración a archivo YAML.

        Args:
            path: Ruta donde guardar el archivo
        """
        # Convertir dataclasses a dict
        data: dict[str, Any] = {
            "version": self.version,
            "hooks": {},
            "validadores": {},
        }

        # Serializar hooks
        for hook_name, hook_config in self.hooks.items():
            hook_dict: dict[str, Any] = {
                "enabled": hook_config.enabled,
                "validadores": hook_config.validadores,
            }
            if hook_config.skip_on_env:
                hook_dict["skip_on_env"] = hook_config.skip_on_env
            data["hooks"][hook_name] = hook_dict

        # Serializar validadores
        for val_name, val_config in self.validadores.items():
            val_dict: dict[str, Any] = {
                "enabled": val_config.enabled,
                "timeout": val_config.timeout,
            }
            # Añadir options
            val_dict.update(val_config.options)
            data["validadores"][val_name] = val_dict

        # Escribir YAML preservando orden (version primero)
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                data,
                f,
                default_flow_style=False,
                sort_keys=False,  # Preservar orden
                allow_unicode=True,
            )


def cargar_configuracion(repo_path: Path) -> CIGuardianConfig:
    """Carga configuración desde .ci-guardian.yaml o retorna defaults.

    Args:
        repo_path: Ruta al directorio del repositorio Git

    Returns:
        Configuración cargada y validada

    Raises:
        ValueError: Si el archivo de configuración tiene formato inválido
    """
    config_path = repo_path / ".ci-guardian.yaml"
    return CIGuardianConfig.from_yaml(config_path)
