"""
Tests para el sistema de configuración protegida (LIB-33).

Estos tests verifican:
1. Validadores marcados como protected no se pueden deshabilitar vía CLI
2. Sistema de hash SHA256 para detectar modificación programática
3. Regeneración de hash después de modificación manual
4. Bypass prevention de Claude Code
"""

import hashlib

import pytest
import yaml

from ci_guardian.core.config import CIGuardianConfig, ValidadorConfig


class TestValidadorProtegido:
    """Tests para validadores con flag protected."""

    def test_debe_permitir_validador_con_protected_true(self):
        """Debe crear validador con protected=True."""
        # Arrange & Act
        validador = ValidadorConfig(enabled=True, timeout=60, protected=True)

        # Assert
        assert validador.protected is True, "Debe permitir protected=True"
        assert validador.enabled is True

    def test_debe_permitir_validador_con_protected_false(self):
        """Debe crear validador con protected=False."""
        # Arrange & Act
        validador = ValidadorConfig(enabled=True, timeout=60, protected=False)

        # Assert
        assert validador.protected is False, "Debe permitir protected=False"

    def test_debe_usar_protected_false_por_defecto(self):
        """Debe usar protected=False como valor por defecto."""
        # Arrange & Act
        validador = ValidadorConfig(enabled=True, timeout=60)

        # Assert
        assert validador.protected is False, "Por defecto protected debe ser False"


class TestIntegridadConfig:
    """Tests para validación de integridad con hash SHA256."""

    def test_debe_calcular_hash_sha256_correcto(self):
        """Debe calcular hash SHA256 del contenido YAML."""
        # Arrange
        contenido = """version: 0.2.0
hooks:
  pre-commit:
    enabled: true
    validadores:
      - ruff
      - black
"""
        expected_hash = hashlib.sha256(contenido.encode("utf-8")).hexdigest()

        # Act
        from ci_guardian.core.config import calcular_hash_config

        hash_calculado = calcular_hash_config(contenido)

        # Assert
        assert hash_calculado == f"sha256:{expected_hash}"
        assert len(hash_calculado) == 71  # "sha256:" + 64 chars hex

    def test_debe_validar_integridad_cuando_hash_coincide(self, tmp_path):
        """Debe pasar validación cuando el hash coincide."""
        # Arrange
        config_path = tmp_path / ".ci-guardian.yaml"
        # Crear data sin _integrity
        data_sin_integrity = {
            "version": "0.2.0",
            "hooks": {"pre-commit": {"enabled": True}},
        }

        # Calcular hash como lo hace el código de producción
        contenido_sin_integrity = yaml.dump(
            data_sin_integrity, default_flow_style=False, allow_unicode=True
        )
        hash_correcto = hashlib.sha256(contenido_sin_integrity.encode("utf-8")).hexdigest()

        # Añadir sección _integrity
        data_completo = {
            **data_sin_integrity,
            "_integrity": {"hash": f"sha256:{hash_correcto}", "allow_programmatic": False},
        }

        # Escribir YAML completo
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(data_completo, f, default_flow_style=False, allow_unicode=True)

        # Act
        config = CIGuardianConfig.from_yaml(config_path)

        # Assert
        assert config.version == "0.2.0", "Debe cargar config correctamente"

    def test_debe_rechazar_cuando_hash_no_coincide(self, tmp_path):
        """Debe lanzar error cuando el hash no coincide (modificación detectada)."""
        # Arrange
        config_path = tmp_path / ".ci-guardian.yaml"
        contenido = """version: 0.2.0
hooks:
  pre-commit:
    enabled: true

_integrity:
  hash: "sha256:deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
  allow_programmatic: false
"""
        config_path.write_text(contenido, encoding="utf-8")

        # Act & Assert
        with pytest.raises(ValueError, match="INTEGRIDAD COMPROMETIDA"):
            CIGuardianConfig.from_yaml(config_path)

    def test_debe_permitir_config_sin_integrity_hash(self, tmp_path):
        """Debe permitir cargar config sin hash (modo legacy)."""
        # Arrange
        config_path = tmp_path / ".ci-guardian.yaml"
        contenido = """version: 0.2.0
hooks:
  pre-commit:
    enabled: true
"""
        config_path.write_text(contenido, encoding="utf-8")

        # Act
        config = CIGuardianConfig.from_yaml(config_path)

        # Assert
        assert config.version == "0.2.0", "Debe funcionar sin hash (legacy)"

    def test_debe_permitir_modificacion_cuando_allow_programmatic_true(self, tmp_path):
        """Debe saltarse validación si allow_programmatic=true."""
        # Arrange
        config_path = tmp_path / ".ci-guardian.yaml"
        contenido = """version: 0.2.0
hooks:
  pre-commit:
    enabled: true

_integrity:
  hash: "sha256:wronghashwronghashwronghashwronghashwronghashwronghashwronghash"
  allow_programmatic: true
"""
        config_path.write_text(contenido, encoding="utf-8")

        # Act
        config = CIGuardianConfig.from_yaml(config_path)

        # Assert
        assert config.version == "0.2.0", "Debe permitir carga con allow_programmatic"


class TestBypassPrevention:
    """Tests para prevenir que Claude deshabilite validadores protegidos."""

    def test_debe_detectar_intento_de_deshabilitar_validador_protegido(self):
        """Debe detectar cuando se intenta deshabilitar un validador protected."""
        # Arrange
        validador = ValidadorConfig(enabled=True, timeout=60, protected=True)

        # Act & Assert
        # Cuando protected=True, intentar cambiar enabled debería ser detectable
        assert validador.protected is True
        # La lógica de prevención estará en el código que USE este validador

    def test_debe_permitir_deshabilitar_validador_no_protegido(self):
        """Debe permitir deshabilitar validador con protected=False."""
        # Arrange & Act
        validador_original = ValidadorConfig(enabled=True, timeout=60, protected=False)
        validador_deshabilitado = ValidadorConfig(enabled=False, timeout=60, protected=False)

        # Assert
        assert validador_original.enabled is True
        assert validador_deshabilitado.enabled is False
        assert validador_deshabilitado.protected is False


class TestRegeneracionHash:
    """Tests para regeneración de hash después de modificación manual."""

    def test_debe_regenerar_hash_despues_de_modificacion_manual(self, tmp_path):
        """Debe regenerar hash correcto después de editar YAML manualmente."""
        # Arrange
        config_path = tmp_path / ".ci-guardian.yaml"
        contenido_original = """version: 0.2.0
hooks:
  pre-commit:
    enabled: true
"""
        # Usuario edita el archivo (sin hash)
        config_path.write_text(contenido_original, encoding="utf-8")

        # Act: Regenerar hash
        from ci_guardian.core.config import regenerar_hash_config

        regenerar_hash_config(config_path)

        # Assert: Archivo ahora tiene hash válido
        config = CIGuardianConfig.from_yaml(config_path)
        assert config.version == "0.2.0"

        # Verificar que el hash fue añadido
        contenido_final = config_path.read_text(encoding="utf-8")
        assert "_integrity:" in contenido_final
        assert "hash:" in contenido_final
        assert "sha256:" in contenido_final

    def test_debe_preservar_contenido_original_al_regenerar_hash(self, tmp_path):
        """Debe preservar el contenido original al añadir hash."""
        # Arrange
        config_path = tmp_path / ".ci-guardian.yaml"
        contenido_original = """version: 0.2.0
hooks:
  pre-commit:
    enabled: true
    validadores:
      - ruff
      - black
"""
        config_path.write_text(contenido_original, encoding="utf-8")

        # Act
        from ci_guardian.core.config import regenerar_hash_config

        regenerar_hash_config(config_path)

        # Assert: Contenido original preservado
        config = CIGuardianConfig.from_yaml(config_path)
        assert config.version == "0.2.0"
        assert config.hooks["pre-commit"].enabled is True
        assert "ruff" in config.hooks["pre-commit"].validadores
        assert "black" in config.hooks["pre-commit"].validadores

    def test_debe_serializar_campo_protected_en_to_yaml(self, tmp_path):
        """Debe incluir el campo protected al guardar configuración con to_yaml()."""
        # Arrange
        from ci_guardian.core.config import CIGuardianConfig, ValidadorConfig

        config = CIGuardianConfig(
            version="0.2.0",
            validadores={
                "bandit": ValidadorConfig(enabled=True, timeout=60, protected=True),
                "ruff": ValidadorConfig(enabled=True, timeout=60, protected=False),
            },
        )
        config_path = tmp_path / ".ci-guardian.yaml"

        # Act
        config.to_yaml(config_path)

        # Assert: Leer YAML y verificar que protected está presente
        import yaml

        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert "validadores" in data
        assert "bandit" in data["validadores"]
        assert "ruff" in data["validadores"]
        assert data["validadores"]["bandit"]["protected"] is True, "Debe serializar protected=True"
        assert data["validadores"]["ruff"]["protected"] is False, "Debe serializar protected=False"
