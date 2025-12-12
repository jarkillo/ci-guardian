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
        protected: Si está protegido contra deshabilitación programática (LIB-33)
        options: Opciones personalizadas del validador
    """

    enabled: bool = True
    timeout: int = 60
    protected: bool = False
    options: dict[str, str | int | bool] = field(default_factory=dict)


@dataclass
class HookConfig:
    """Configuración de un hook Git.

    Attributes:
        enabled: Si el hook está habilitado
        validadores: Lista de validadores a ejecutar

    NOTE: skip_on_env fue REMOVIDO en v0.3.1 por razones de seguridad.
          Para deshabilitar validadores, editar .ci-guardian.yaml con config protegida.
    """

    enabled: bool = True
    validadores: list[str] = field(default_factory=list)


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

            # Validar integridad si existe sección _integrity (LIB-33)
            integrity_data = data.get("_integrity", {})
            if integrity_data and not integrity_data.get("allow_programmatic", True):
                # Hay hash y allow_programmatic=False, validar integridad
                expected_hash = integrity_data.get("hash")
                if expected_hash:
                    # Crear copia de data sin _integrity para calcular hash
                    import hashlib

                    data_sin_integrity = {k: v for k, v in data.items() if k != "_integrity"}
                    contenido_sin_integrity = yaml.dump(
                        data_sin_integrity, default_flow_style=False, allow_unicode=True
                    )
                    hash_actual = hashlib.sha256(
                        contenido_sin_integrity.encode("utf-8")
                    ).hexdigest()
                    hash_actual_full = f"sha256:{hash_actual}"

                    if hash_actual_full != expected_hash:
                        raise ValueError(
                            "❌ INTEGRIDAD COMPROMETIDA: El archivo .ci-guardian.yaml fue "
                            "modificado de forma no autorizada.\n\n"
                            "Si modificaste el archivo manualmente, regenera el hash con:\n"
                            "  ci-guardian config --regenerate-hash\n\n"
                            f"Hash esperado: {expected_hash}\n"
                            f"Hash actual:   {hash_actual_full}"
                        )

            # Parsear hooks
            hooks_data = data.get("hooks", {})
            hooks = {}
            for hook_name, hook_dict in hooks_data.items():
                if isinstance(hook_dict, dict):
                    hooks[hook_name] = HookConfig(
                        enabled=hook_dict.get("enabled", True),
                        validadores=hook_dict.get("validadores", []),
                    )
                else:
                    logger.warning(f"Hook '{hook_name}' tiene formato inválido, ignorando")

            # Parsear validadores
            validadores_data = data.get("validadores", {})
            validadores = {}
            for val_name, val_dict in validadores_data.items():
                if isinstance(val_dict, dict):
                    # Extraer enabled, timeout, protected y el resto son options
                    enabled = val_dict.get("enabled", True)
                    timeout = val_dict.get("timeout", 60)
                    protected = val_dict.get("protected", False)

                    # Options son todos los campos excepto enabled, timeout y protected
                    options = {
                        k: v
                        for k, v in val_dict.items()
                        if k not in ("enabled", "timeout", "protected")
                    }

                    validadores[val_name] = ValidadorConfig(
                        enabled=enabled, timeout=timeout, protected=protected, options=options
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
            data["hooks"][hook_name] = hook_dict

        # Serializar validadores
        for val_name, val_config in self.validadores.items():
            val_dict: dict[str, Any] = {
                "enabled": val_config.enabled,
                "timeout": val_config.timeout,
                "protected": val_config.protected,  # LIB-33: Incluir protected
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


# Funciones para sistema de integridad (LIB-33)


def calcular_hash_config(contenido: str) -> str:
    """
    Calcula hash SHA256 del contenido de configuración.

    Args:
        contenido: Contenido del archivo YAML (sin sección _integrity)

    Returns:
        Hash en formato "sha256:<hex>" (71 caracteres)

    Example:
        >>> contenido = "version: 0.2.0\\nhooks:\\n  pre-commit:\\n    enabled: true"
        >>> hash_val = calcular_hash_config(contenido)
        >>> hash_val.startswith("sha256:")
        True
        >>> len(hash_val)
        71
    """
    import hashlib

    hash_hex = hashlib.sha256(contenido.encode("utf-8")).hexdigest()
    return f"sha256:{hash_hex}"


def regenerar_hash_config(config_path: Path) -> None:
    """
    Regenera el hash de integridad del archivo de configuración.

    Lee el archivo, elimina la sección _integrity si existe, calcula el hash
    del contenido restante, y añade la nueva sección _integrity con el hash.

    Args:
        config_path: Ruta al archivo .ci-guardian.yaml

    Raises:
        FileNotFoundError: Si el archivo no existe
        yaml.YAMLError: Si el archivo no es YAML válido

    Example:
        >>> config_path = Path(".ci-guardian.yaml")
        >>> regenerar_hash_config(config_path)
        # Archivo ahora tiene _integrity con hash SHA256 válido
    """
    import hashlib

    import yaml

    if not config_path.exists():
        raise FileNotFoundError(f"Archivo de configuración no encontrado: {config_path}")

    # Leer y parsear YAML
    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data:
        data = {}

    # Eliminar sección _integrity si existe
    data.pop("_integrity", None)

    # Serializar a YAML (sin _integrity)
    contenido_sin_integrity = yaml.dump(data, default_flow_style=False, allow_unicode=True)

    # Calcular hash del contenido sin _integrity
    hash_hex = hashlib.sha256(contenido_sin_integrity.encode("utf-8")).hexdigest()

    # Añadir sección _integrity
    data["_integrity"] = {"hash": f"sha256:{hash_hex}", "allow_programmatic": False}

    # Escribir de vuelta
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    logger.info(f"Hash de integridad regenerado para {config_path}")
