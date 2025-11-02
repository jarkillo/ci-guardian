# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 🛡️ **Runtime Module Validation (LIB-21)** - Fail-Fast Prevention
  - CLI validates hook modules exist BEFORE installing them
  - New `_validar_hook_existe()` function uses `import_module()`
  - Called in `install` command for each hook before installation
  - Fails with clear error message if module missing
  - Error message includes GitHub issue reporting link
  - Would have prevented v0.1.0 bug at install time instead of runtime
  - Tests validate function behavior with valid and invalid hooks
  - 2 new tests: valid hooks pass, invalid hooks fail with clear message

- ✅ **Module Validation Test (LIB-16)** - Post-Mortem Prevention Measure
  - New test validates HOOKS_ESPERADOS has corresponding modules
  - Test imports each module using `import_module()`
  - Fails immediately if hook listed but module doesn't exist
  - Clear error message with solution steps
  - Would have prevented v0.1.0 bug (pre-push in list, pre_push.py missing)
  - Test located in `tests/unit/test_cli.py`
  - Runs on every test suite execution

- 🔬 **Smoke Test Script (LIB-17)** - Pre-Release Validation
  - Created `scripts/smoke_test.sh` for manual pre-release validation
  - Installs CI Guardian from wheel (NOT editable install)
  - Tests complete workflow: build → install → commit → push
  - Validates CLI commands work (`--version`, `--help`)
  - Validates hook installation (100% status)
  - Validates pre-commit hook (ruff, black, bandit)
  - Validates commit-msg and post-commit hooks
  - Validates pre-push hook execution
  - Exit code 0 if all tests pass, != 0 if any fail
  - Prevents bugs like v0.1.0 from reaching production
  - Must run BEFORE `twine upload dist/*`

#### CI/CD & Quality Gates
- 🔬 **Smoke Tests in CI/CD Pipeline (LIB-18)** - Pre-release validation gate before PyPI publish
  - New `smoke-test` job in `.github/workflows/publish.yml`
  - Tests install from wheel (NOT editable) in clean environment
  - Validates CLI availability (`ci-guardian --version`, `--help`)
  - Tests full workflow: hook installation, commit, push
  - Verifies 100% hook installation via `ci-guardian status`
  - **Properly triggers pre-push hook** by using `git push origin HEAD` instead of hardcoded branch
  - Configures `init.defaultBranch=main` to ensure consistent branch naming
  - Conditionally tests push workflow only if pre-push hook exists
  - Blocks TestPyPI and PyPI publication if smoke tests fail
  - Prevents critical bugs from reaching production (Post-Mortem v0.1.0)
  - Integration with `publish-testpypi` and `publish-pypi` jobs via `needs` dependency

#### Documentation & Workflow
- 📝 **Pre-Commit Documentation Workflow** - Automated documentation sync with code changes
  - Updated `CLAUDE.md` with mandatory pre-commit checklist
  - Updated `git-workflow-manager` agent with documentation verification
  - Enforces README.md updates when CLI/API changes
  - Enforces CLAUDE.md updates when architecture changes
  - Mandatory CHANGELOG.md update for every commit
  - Verification of docstrings on new/modified functions
  - Documentation included in same commit as code changes

- 🧪 **Pre-Release Smoke Test Workflow** - Manual smoke test guide for releases
  - Updated `CLAUDE.md` with pre-release checklist
  - Updated `git-workflow-manager` agent with smoke test enforcement
  - Step-by-step local smoke test procedure before tagging
  - Prevents releases without wheel validation (Post-Mortem v0.1.0)
  - Version bump and CHANGELOG verification before release
  - Release checklist in agent ensures quality gates

- 🚨 **Lessons Learned - Post-Mortems (LIB-22)** - Documentation of critical bugs and prevention rules
  - New section in `CLAUDE.md`: "Lessons Learned - Post-Mortems"
  - Complete post-mortem of ModuleNotFoundError bug (v0.1.0 → v0.1.1)
  - Root cause analysis: documentation desync, excessive mocks, missing smoke tests
  - 4 mandatory prevention rules:
    - ✅ NUNCA documentar features no implementadas
    - ✅ SIEMPRE validar constantes hardcodeadas
    - ✅ SIEMPRE ejecutar smoke tests pre-release
    - ✅ MINIMIZAR mocks en tests críticos
  - Comprehensive pre-release checklist with 40+ verification steps
  - Smoke tests marked as CRÍTICO with examples from real bug
  - References to PRs #16, #17 and related issues (LIB-16 to LIB-21)

#### Runners
- 🎬 **GitHub Actions Local Executor (LIB-7)** - Ejecución local de workflows de GitHub Actions
  - Integración con act (https://github.com/nektos/act) para ejecutar workflows en Docker
  - Modo fallback con pytest, ruff, black cuando act no está disponible
  - Auto-detección de workflow files (ci.yml, test.yml)
  - Auto-detección de modo (act vs fallback)
  - Eventos soportados: push, pull_request, workflow_dispatch, schedule
  - Timeout configurable (default: 300s para act, 60s para fallback)
  - 34 tests comprehensivos, 78% de cobertura
  - Security features:
    - Path traversal prevention (Path.resolve strict)
    - File size validation (max 1MB)
    - Timeout handling (prevents DoS)
    - Git repository validation
    - Comprehensive security logging
    - Whitelist de eventos permitidos
  - Cross-platform support (Linux, macOS, Windows)
  - Documentación completa en docstrings
  - Manejo robusto de errores con exception chaining

#### Core Features
- 🔒 **Anti --no-verify Validator (LIB-3)** - Sistema de tokens para prevenir bypass de hooks
  - Token criptográficamente seguro (256 bits usando secrets.token_hex)
  - Validación single-use: el token se consume al validar
  - Reversion automática de commits con --no-verify
  - Permisos seguros (600) en archivos de token
  - Detección de archivos corruptos o con permisos inseguros
  - 42 tests, 94% de cobertura
  - Prevención de command injection, path traversal
  - Documentación clara del timing correcto de generación de tokens

- 👤 **Authorship Validator (LIB-6)** - Validación de autoría de commits
  - Rechaza commits con Co-Authored-By: Claude
  - Validación de formato de mensaje de commit
  - 38 tests, 90% de cobertura
  - Hook commit-msg instalado y funcionando

- 🎨 **Code Quality Executor (LIB-4)** - Ejecución de Ruff y Black
  - Ejecutor de Ruff (linter) con output JSON
  - Ejecutor de Black (formatter) con verificación
  - Validación de archivos Python
  - Manejo de timeouts (60s)
  - 42 tests, 99% de cobertura
  - subprocess seguro (shell=False)

#### Infrastructure & Workflow
- 🔧 **Pre-commit hooks** - Framework de pre-commit instalado y configurado
  - 15 hooks activos: trailing whitespace, EOF fixer, YAML/JSON/TOML checks
  - Code quality: Ruff linter + formatter, Black formatter
  - Security: Bandit security linter
  - Type checking: MyPy static type checker
  - Custom hooks: Anti --no-verify in commit messages
  - Large files detection (max 1MB)
  - Private keys detection, merge conflicts detection
  - Se ejecutan automáticamente en cada commit

- 🔒 **Branch Protection Rules** - Protección estricta de ramas principales
  - `main` bloqueada: solo merge mediante Pull Request
  - `dev` bloqueada: solo merge mediante Pull Request
  - `enforce_admins: true` - Nadie puede hacer push directo (ni siquiera admins)
  - Force push bloqueado en ambas ramas
  - Eliminación de ramas bloqueada
  - Verificado y funcionando correctamente

- 📁 **Improved .gitignore** - Reorganización completa con 256 líneas
  - 13 secciones claramente organizadas
  - Cobertura completa de herramientas de CI Guardian
  - Patterns específicos: `.ruff_cache/`, `.pre-commit-cache/`, bandit/safety reports
  - CI Guardian specific: `.ci-guardian-token`, `*.hook.backup`
  - GitHub Actions (act): `.actrc`, `.secrets`
  - Expandido OS support: macOS, Windows, Linux patterns completos
  - IDEs adicionales: Sublime Text, Emacs
  - Security patterns: .env variants, credentials, certificates

### Changed
- **Development Workflow** - Ahora es obligatorio usar Pull Requests
  - No se puede hacer push directo a `main` o `dev`
  - Todos los commits pasan por pre-commit hooks automáticamente
  - Workflow: feature branch → push → PR → merge

### Fixed
- 🐛 **Token Generation Timing (LIB-3)** - Documentación del timing correcto
  - Documentado que el token debe generarse al FINAL del pre-commit
  - Previene tokens huérfanos de commits abortados
  - Ejemplos de uso correcto e incorrecto añadidos
  - Configuración de Bandit para skip de falsos positivos (B404, B603, B607)

### Security
- 🔒 **P1 Vulnerability Fix (LIB-3)** - Prevención de reuso de tokens
  - Documentado el patrón arquitectónico correcto
  - Token solo debe generarse después de todas las validaciones
  - Previene ataque: commit abort → token orphan → reuse with --no-verify

### Fixed
- 🧪 **Refactor CLI Tests to Minimize Excessive Mocking (LIB-19)** - Post-Mortem Prevention Measure
  - Eliminated excessive mocking of `instalar_hook` function in 5 tests
  - Tests now use REAL hook installation and validate actual filesystem state
  - Validates hooks exist on filesystem with correct content
  - Validates hooks contain correct module imports (`ci_guardian.hooks.{modulo_nombre}`)
  - Validates hook permissions (755 on Linux) and .bat extension on Windows
  - Tests now would have caught the v0.1.0 bug (missing pre_push.py module)
  - Only mocks external I/O (Path.cwd), not internal logic
  - All 358 tests still pass, coverage maintained at 73%
  - Refactored tests:
    - `test_debe_instalar_hooks_exitosamente_cuando_esta_en_repo_git`
    - `test_debe_rechazar_instalacion_cuando_hooks_ya_existen`
    - `test_debe_sobrescribir_hooks_cuando_se_usa_flag_force`
    - `test_debe_instalar_hooks_con_permisos_755_en_linux`
    - `test_debe_instalar_hooks_bat_en_windows`

### Planned
- LIB-2: Virtual Environment Manager - Detección/gestión de entornos virtuales (COMPLETED, needs integration)
- LIB-5: Security Audit - Integración con Bandit y Safety
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
