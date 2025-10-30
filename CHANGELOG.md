# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- LIB-2: Virtual Environment Manager - Detección/gestión de entornos virtuales
- LIB-4: Ruff & Black Integration - Ejecución automática de linters
- LIB-3: No-Verify Blocker - Sistema de tokens anti-bypass
- LIB-8: CLI Interface - Comandos install/uninstall/status/check
- LIB-6: Authorship Validator - Validación de autoría de commits
- LIB-5: Security Audit - Integración con Bandit y Safety
- LIB-7: GitHub Actions Runner - Ejecución local de workflows
- LIB-9: Integration Tests - Tests de flujo completo

## [0.1.0] - 2025-10-30

### Added

#### Core Features
- 🎉 **Hook Installer (LIB-1)** - Instalación de Git hooks con validación de seguridad
  - Detección de repositorios Git válidos
  - Instalación de hooks con permisos correctos (755 en Linux/macOS)
  - Soporte multiplataforma (Linux, macOS, Windows)
  - Prevención de sobrescritura de hooks existentes
  - Soporte UTF-8 con manejo de Unicode

#### Security Features
- 🔒 **Whitelist de nombres de hooks** - Solo permite: pre-commit, pre-push, post-commit, pre-rebase
- 🔒 **Prevención de path traversal** - Usa `Path.resolve()` y valida que hooks estén en `.git/hooks/`
- 🔒 **Validación de shebang** - Whitelist de interpreters permitidos (bash, sh, python, python3)
- 🔒 **Límite de tamaño** - Máximo 100KB por hook (previene ataques DoS)
- 🔒 **Logging de seguridad** - Logs WARNING cuando se detectan intentos de ataque
- 🔒 **Permisos seguros** - 755 (rwxr-xr-x) en Unix, sin archivos world-writable

#### Testing & Quality
- ✅ 51 tests implementados (1 skipped en Linux)
- ✅ 98.55% de cobertura de código
- ✅ Tests multiplataforma (Linux/Windows/macOS)
- ✅ 0 vulnerabilidades detectadas por Bandit y Ruff
- ✅ Type hints completos usando sintaxis Python 3.12+
- ✅ Docstrings en español, formato Google

#### Documentation
- 📚 README.md con badges y estado de desarrollo
- 📚 CONTRIBUTING.md con guía completa de contribución
- 📚 CODE_OF_CONDUCT.md (Contributor Covenant 2.1)
- 📚 SECURITY.md con política de reporte de vulnerabilidades
- 📚 CLAUDE.md con documentación interna para desarrollo
- 📚 LICENSE (MIT)

#### Infrastructure
- 🏗️ Estructura de proyecto Python moderna
- 🏗️ pyproject.toml con configuración completa
- 🏗️ .gitignore optimizado
- 🏗️ Agentes de Claude Code para TDD y security audit
- 🏗️ Fixtures de pytest reutilizables

### Changed
- N/A (primera versión)

### Deprecated
- N/A (primera versión)

### Removed
- N/A (primera versión)

### Fixed
- N/A (primera versión)

### Security
- Auditoría completa de seguridad con 0 vulnerabilidades encontradas
- Implementación de defensa en profundidad con múltiples capas de validación
- Prevención de command injection (no usa subprocess en esta versión)
- Prevención de symlink attacks mediante Path.resolve()

## Development Process

Este proyecto sigue **TDD estricto** (Test-Driven Development):
1. **RED**: Escribir tests que fallan
2. **GREEN**: Implementar código mínimo para pasar tests
3. **REFACTOR**: Mejorar código manteniendo tests verdes

Cada release pasa por:
- ✅ Tests automatizados (pytest)
- ✅ Linting (ruff)
- ✅ Formatting (black)
- ✅ Type checking (mypy)
- ✅ Security audit (bandit, ruff S-rules)
- ✅ Code review

## Links

- [GitHub Repository](https://github.com/jarkillo/ci-guardian)
- [Issue Tracker](https://github.com/jarkillo/ci-guardian/issues)
- [Pull Requests](https://github.com/jarkillo/ci-guardian/pulls)
- [Security Policy](https://github.com/jarkillo/ci-guardian/security/policy)

---

**Note**: Versions follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: Backwards-compatible new features
- **PATCH**: Backwards-compatible bug fixes

[Unreleased]: https://github.com/jarkillo/ci-guardian/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jarkillo/ci-guardian/releases/tag/v0.1.0
