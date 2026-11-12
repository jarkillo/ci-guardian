# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.2] - 2026-11-12

### Deprecated

- Project no longer maintained: replaced by [Lichen](https://github.com/Neuralflows/axon-terminal). This is the final release; no code changes.

## [0.3.1] - 2025-12-12

### Fixed
- 🔧 **Improved Bandit JSON Error Handling** - Better debugging when Bandit fails
  - Detect when Bandit returns empty stdout
  - Capture stderr for debugging when JSON parsing fails
  - Show stdout preview (first 200 chars) in error messages
  - Enhanced error messages in pre_commit hook with debug info (detalle, stderr, stdout_preview)
  - Previously, Bandit errors were silently skipped with unclear messages

### Security
- 🚨 **BREAKING: Removed CI_GUARDIAN_SKIP_TESTS Bypass Vulnerability**
  - **BREAKING CHANGE**: Removed `CI_GUARDIAN_SKIP_TESTS` environment variable
  - This variable allowed trivial bypass: `CI_GUARDIAN_SKIP_TESTS=1 git push`
  - Contradicted core purpose of CI Guardian (preventing validation bypass)
  - Removed `skip_on_env` field from `HookConfig` dataclass
  - Cleaned all `skip_on_env` entries from `.ci-guardian.yaml.template`
  - Updated GitHub Actions smoke tests to install pytest instead of skip
  - **Migration**: Use protected config system instead:
    1. Edit `.ci-guardian.yaml` (set `enabled: false`)
    2. Run `ci-guardian configure --regenerate-hash`
    3. Commit changes (auditable in git)
  - More secure: requires manual file edit, SHA256 hash prevents programmatic modification
  - Reported by user - thank you!

### Changed
- 📝 **Updated Tests** - Reflect removal of CI_GUARDIAN_SKIP_TESTS
  - Removed `test_debe_permitir_skip_con_variable_entorno` from test_pre_push.py
  - Removed `test_debe_soportar_skip_on_env_opcional` from test_config.py
  - Added `esta_venv_activo()` mocks to all pre_push tests
  - All tests passing (10 passed, 1 skipped on Linux)

## [0.3.0] - 2025-11-06

### Added
- 🔒 **Protected Configuration System (LIB-33)** - Prevent Claude Bypass
  - New `protected: bool` field in `ValidadorConfig` dataclass
  - Validators with `protected: true` cannot be programmatically disabled
  - SHA256 hash integrity system in `.ci-guardian.yaml`
  - New `_integrity` section with `hash` and `allow_programmatic` fields
  - Automatic integrity validation in `CIGuardianConfig.from_yaml()`
  - Raises `ValueError` with clear instructions if hash mismatch detected
  - Functions: `calcular_hash_config()`, `regenerar_hash_config()`
  - Legacy mode: Files without `_integrity` section work normally
  - Bypass mode: `allow_programmatic: true` skips hash validation
  - 12 comprehensive tests covering all scenarios (protected validators, integrity validation, hash regeneration)

- 🔧 **CLI Command Extension: configure --regenerate-hash (LIB-33)**
  - New flag: `ci-guardian configure --regenerate-hash`
  - Regenerates SHA256 integrity hash after manual YAML edits
  - Shows helpful message: "Ahora puedes hacer commit del archivo actualizado"
  - Validates that `.ci-guardian.yaml` exists before proceeding
  - Clear error messages if config file not found

- 📝 **Configuration Template (LIB-33)** - Documentation & Examples
  - New file: `.ci-guardian.yaml.template`
  - Complete example with all validators (ruff, black, bandit, authorship, no-verify-token, tests)
  - Shows which validators should be `protected: true` (bandit, authorship, no-verify-token)
  - Explains `_integrity` section and how to regenerate hash
  - Includes inline documentation and usage examples
- 📦 **Venv Validator Module (LIB-32)** - Pre-Hook Environment Validation
  - New `src/ci_guardian/core/venv_validator.py` module
  - Function `esta_venv_activo() -> tuple[bool, str]` detects if venv is active
  - Dual detection method: `VIRTUAL_ENV` env variable (priority) and `sys.prefix != sys.base_prefix`
  - Clear error messages with activation instructions for Linux/Mac and Windows
  - Suggests using `ci-guardian commit` command as alternative
  - 9 comprehensive unit tests with 100% coverage on new module
  - Tests use mocks for `os.getenv`, `sys.prefix`, `sys.base_prefix`
  - Edge cases covered: empty strings, paths with spaces, priority testing

- 🪝 **Venv Validation in Hooks (LIB-32)** - UX Improvement
  - Integrated venv validation as FIRST step in `pre_commit.py`
  - Integrated venv validation as FIRST step in `pre_push.py`
  - Blocks hook execution if venv not detected
  - Prevents confusing `ModuleNotFoundError` messages when users forget to activate venv
  - Shows clear instructions for activating venv manually
  - Suggests `ci-guardian commit` command for convenience

- 🔧 **New CLI Command: commit (LIB-32)** - Convenient Commits
  - New command: `ci-guardian commit -m "message"`
  - Verifies venv is active before executing `git commit`
  - Attempts to detect and report venv path automatically
  - Shows clear instructions if venv not found
  - Executes git commit safely (shell=False, hardcoded command array)
  - Better UX for users who forget to activate their environment
  - Security: No command injection risk

### Fixed
- 🐛 **Critical: Pre-commit Hook Bandit False-Positives**
  - Fixed bug where pre-commit hook failed with exit code 1 even when Bandit reported 0 HIGH vulnerabilities
  - Root cause: Inconsistent vulnerability counting between `ejecutar_bandit()` (used `results[]`) and `pre_commit.py` (used `metrics._totals.HIGH` which can be stale)
  - Solution: Use consistent counting method from `results[]` in both places
  - Added explicit check: only fail if `high_count > 0`
  - Improved error handling for Bandit timeouts and JSON parsing errors
  - Impact: Prevents blocking legitimate commits with 0 HIGH vulnerabilities while maintaining security enforcement

- 💾 **Automatic Backup in `--force` Flag**
  - `ci-guardian install --force` now detects existing hooks from ANY tool (not just CI Guardian)
  - Shows origin of each hook (CI Guardian vs other tools)
  - Requests interactive confirmation before proceeding
  - Creates automatic backup in `.git/hooks.backup.TIMESTAMP/` with preserved permissions
  - Safely removes existing hooks and installs CI Guardian hooks
  - Impact: Allows installing CI Guardian in projects with existing hooks while preserving originals

### Security
- ✅ **LIB-32 Security Audit** - Bandit Clean
  - Bandit scan: Only LOW severity warnings (expected subprocess imports)
  - No command injection risk: `shell=False` with hardcoded command arrays
  - No path traversal issues (module doesn't operate with user paths)
  - All subprocess calls use timeout and proper error handling

### Documentation
- 📚 Updated README.md with new `ci-guardian commit` command
- 📚 Updated CLI command count from 5 to 6
- 📚 Added `venv_validator.py` to architecture diagram
- 📚 Updated validator count from 4 to 5
- 📚 Updated CLAUDE.md with LIB-32 and LIB-33 issues
- 📚 Updated implementation order in CLAUDE.md

## [0.2.0] - 2025-11-04

### Added
- 🎯 **Pre-Push Hook Implementation (LIB-14)** - 4th Hook Complete
  - Implemented `src/ci_guardian/hooks/pre_push.py` module (originally documented in v0.1.0 but missing)
  - Executes pytest before allowing push to repository
  - Executes GitHub Actions locally if configured (via LIB-7 runner)
  - Respects `.ci-guardian.yaml` configuration
  - Skip functionality with `CI_GUARDIAN_SKIP_TESTS=1` environment variable
  - Cross-platform support (Linux/Windows)
  - Security: Uses subprocess safely (shell=False), handles timeouts
  - 12 new unit tests, 81% coverage on new module
  - Updated `HOOKS_ESPERADOS` in cli.py to include pre-push
  - Updated `HOOKS_PERMITIDOS` whitelist in installer.py
  - Now CI Guardian installs 4 hooks instead of 3 (pre-commit, commit-msg, post-commit, **pre-push**)
  - **Fixes v0.1.0 critical bug** where pre-push was documented but module didn't exist
  - Total tests: 373 passed (was 358), coverage: 75% (was 73%)

- 🛡️ **Runtime Module Validation (LIB-21)** - Fail-Fast Prevention
  - CLI validates hook modules exist BEFORE installing them
  - New `_validar_hook_existe()` function uses `import_module()`
  - Called in `install` command for each hook before installation
  - Fails with clear error message if module missing
  - Error message includes GitHub issue reporting link
  - Would have prevented v0.1.0 bug at install time instead of runtime
  - Tests validate function behavior with valid and invalid hooks
  - 2 new tests: valid hooks pass, invalid hooks fail with clear message

- 🧪 **End-to-End Git Push Test (LIB-20)** - Post-Mortem Prevention Measure
  - New integration test validates complete workflow: install → commit → push
  - Test executes `ci-guardian install`, creates commit, then performs `git push`
  - Creates local bare repository for testing (no external dependencies)
  - Validates that push succeeds without ModuleNotFoundError
  - Would have caught v0.1.0 bug where pre-push module was missing
  - Test located in `tests/integration/test_full_workflow.py`
  - Marked with `@pytest.mark.integration` for CI/CD execution
  - Clear error message if push fails with ModuleNotFoundError

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

#### Code Quality & Refactoring
- 📦 **Centralized Python File Filtering (LIB-27)** - DRY principle applied to file filtering
  - New `validators/file_utils.py` module with `filtrar_archivos_python_seguros()`
  - Centralized filtering logic eliminates 62 lines of duplicated code
  - Previously duplicated in `cli.py` (31 lines) and `code_quality.py` (31 lines)
  - Inconsistency fixed: cli.py filtered by directories, code_quality.py didn't
  - Configurable validation: path traversal, existence checks, directory exclusions
  - DIRECTORIOS_EXCLUIDOS constant: venv, .venv, .git, __pycache__, build, dist, node_modules
  - 29 comprehensive unit tests, 100% coverage
  - Security features: path traversal prevention, safe path validation
  - Benefits: improved maintainability, consistent behavior, single source of truth

- 🧪 **Unit Tests for Git Hooks (LIB-28)** - Comprehensive hook testing
  - New `tests/unit/test_commit_msg.py` - 16 tests, 94% coverage
  - New `tests/unit/test_post_commit.py` - 14 tests, 100% coverage
  - New `tests/unit/test_pre_commit.py` - 17 tests, 97% coverage
  - Total: 47 new tests for hooks that only had integration tests
  - Tests cover: happy paths, error handling, edge cases, timeouts
  - Proper mocking pattern: mock at usage location, not definition location
  - Key learning: `patch("ci_guardian.hooks.post_commit.validar_y_consumir_token")` ✅
  - Coverage improvement: 76.51% → 90.70% (overall project coverage)
  - All hooks now have ≥94% coverage: commit-msg (94%), post-commit (100%), pre-commit (97%)
  - Benefits: easier debugging, better documentation via tests, higher confidence

- ✨ **CLI Coverage Improvement (LIB-29)** - Exception handling and edge cases
  - CLI coverage improved from 90% to 99% (only 1 line missing: Windows batch string)
  - 8 new tests for generic exception handling in all CLI commands
  - Tests for ValueError handling in check command (path traversal in ruff/black)
  - Fixed colorama.init() test for Windows (invoke main with subcommand)
  - Fixed test for "100%" message when all hooks installed
  - Coverage breakdown: install (99%), uninstall (99%), status (99%), check (99%), configure (99%)
  - Total project coverage: 92.33% (was 90.70%)
  - Total tests: 503 passed, 10 skipped (was 496 passed)
  - Benefits: robust error handling, production-ready CLI, comprehensive test suite

### Changed
- **Development Workflow** - Ahora es obligatorio usar Pull Requests
  - No se puede hacer push directo a `main` o `dev`
  - Todos los commits pasan por pre-commit hooks automáticamente
  - Workflow: feature branch → push → PR → merge

- **Test Coverage Baseline** - Updated from 75% to 92%
  - Project-wide coverage improved from 76% to 92.33%
  - All critical modules now at 90%+ coverage
  - CLI module: 99% coverage (185/186 lines)
  - Core modules: config (90%), installer (89%), venv_manager (89%)
  - Validators: file_utils (100%), code_quality (98%), no_verify_blocker (94%)
  - Hooks: post_commit (100%), pre_commit (97%), commit_msg (94%)

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

[Unreleased]: https://github.com/jarkillo/ci-guardian/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/jarkillo/ci-guardian/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/jarkillo/ci-guardian/releases/tag/v0.1.0
