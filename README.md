> [!WARNING]
> **This project is no longer maintained: it has been replaced by [Lichen](https://github.com/Neuralflows/axon-terminal).**
> Este proyecto ya no se mantiene: lo sustituye [Lichen](https://github.com/Neuralflows/axon-terminal).
> `0.3.2` is the final release of `ci-guardian` on PyPI; the repository is archived.

# CI Guardian 🛡️

> Git hooks automation for Claude Code projects - Enforces code quality, security, and prevents hook bypass

<!-- Project Status & Version -->
[![Version](https://img.shields.io/badge/version-0.1.1-blue.svg)](https://github.com/jarkillo/ci-guardian/releases)
[![PyPI version](https://img.shields.io/pypi/v/ci-guardian.svg)](https://pypi.org/project/ci-guardian/)
[![PyPI downloads](https://img.shields.io/pypi/dm/ci-guardian.svg)](https://pypi.org/project/ci-guardian/)
[![Project Status](https://img.shields.io/badge/status-production%20ready-brightgreen.svg)](https://github.com/jarkillo/ci-guardian)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<!-- Testing & Quality -->
[![Tests](https://img.shields.io/badge/tests-373%20passed-success.svg)](https://github.com/jarkillo/ci-guardian)
[![Coverage](https://img.shields.io/badge/coverage-75%25-green.svg)](https://github.com/jarkillo/ci-guardian)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: ruff](https://img.shields.io/badge/linting-ruff-red.svg)](https://github.com/astral-sh/ruff)

<!-- GitHub Stats -->
[![GitHub stars](https://img.shields.io/github/stars/jarkillo/ci-guardian?style=social)](https://github.com/jarkillo/ci-guardian/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/jarkillo/ci-guardian?style=social)](https://github.com/jarkillo/ci-guardian/network/members)
[![GitHub issues](https://img.shields.io/github/issues/jarkillo/ci-guardian)](https://github.com/jarkillo/ci-guardian/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/jarkillo/ci-guardian)](https://github.com/jarkillo/ci-guardian/pulls)

## 🎯 ¿Qué es CI Guardian?

CI Guardian es una librería Python que automatiza y **asegura** tu flujo de trabajo de desarrollo con Claude Code. Instala hooks de Git que:

- ✅ **Ejecutan Ruff y Black** automáticamente antes de cada commit
- 🔒 **Auditan seguridad** con Bandit y Safety
- 🚫 **Bloquean `--no-verify`** para que Claude Code no pueda saltarse las validaciones
- 👤 **Validan autoría** de commits (rechaza "Co-Authored-By: Claude")
- 🏃 **Ejecutan GitHub Actions localmente** antes del push (ahorra minutos de CI/CD)
- 🖥️ **Multiplataforma**: Funciona en Linux y Windows

## 🚀 Instalación Rápida

```bash
# Instalar ci-guardian
pip install ci-guardian

# En tu proyecto, instalar hooks
cd tu-proyecto/
ci-guardian install
```

¡Listo! Ahora todos tus commits pasarán por validación automática.

📖 **¿Primera vez usando CI Guardian?** Lee la [Guía de Inicio Rápido](QUICKSTART.md) con ejemplos paso a paso.

## ✅ Estado del Desarrollo

**CI Guardian v0.1.0 está COMPLETO y listo para producción!** 🎉

| Módulo | Estado | Tests | Coverage | Descripción |
|--------|--------|-------|----------|-------------|
| 🟢 **Hook Installer** | ✅ Completo | 50 tests | 89% | Instalación de hooks con validación de seguridad |
| 🟢 **Venv Manager** | ✅ Completo | 50 tests | 89% | Detección/gestión de entornos virtuales (Linux/Windows) |
| 🟢 **Code Quality** | ✅ Completo | 60 tests | 96% | Integración con Ruff y Black |
| 🟢 **Security Audit** | ✅ Completo | 48 tests | 98% | Bandit + Safety |
| 🟢 **Authorship Validator** | ✅ Completo | 20 tests | 96% | Validación de autoría de commits |
| 🟢 **No-Verify Blocker** | ✅ Completo | 60 tests | 98% | Sistema de tokens anti-bypass |
| 🟢 **CLI** | ✅ Completo | 17 tests | 81% | Interfaz de línea de comandos (5 comandos) |
| 🟢 **GitHub Actions Runner** | ✅ Completo | 31 tests | 94% | Ejecución local de workflows |
| 🟢 **Integration Tests** | ✅ Completo | 17 tests | 100% | Tests end-to-end con Git real |

**Total: 373 tests passed | Coverage: 75%**

### ✨ Todas las Funcionalidades Implementadas

- ✅ **6 comandos CLI**: install, uninstall, status, check, configure, commit
- ✅ **4 hooks Git**: pre-commit, commit-msg, post-commit, pre-push
- ✅ **5 validadores**: Venv check, Code quality, Security, Authorship, Anti --no-verify
- ✅ **1 runner**: GitHub Actions local (act con fallback)
- ✅ **Soporte multiplataforma**: Linux, macOS, Windows
- ✅ **Seguridad auditada**: 0 vulnerabilidades HIGH/CRITICAL
- ✅ **TDD estricto**: 100% de funcionalidades con tests primero

## 📋 Características

### 🎨 Calidad de Código

- **Ruff**: Linter ultrarrápido con cientos de reglas
- **Black**: Formateo consistente sin discusiones
- Configuración automática si no existe

### 🔐 Seguridad

- **Bandit**: Detecta vulnerabilidades de seguridad en Python
- **Safety**: Verifica dependencias con vulnerabilidades conocidas
- Bloquea commits con problemas críticos de seguridad

### 🛡️ Protección Anti-Bypass

- **Sistema de tokens**: El pre-commit crea un token que post-commit valida
- Si el token no existe (usaste `--no-verify`), el commit se revierte automáticamente
- Claude Code no puede saltarse las validaciones

### 👨‍💻 Validación de Autoría

- Rechaza commits con "Co-Authored-By: Claude <noreply@anthropic.com>"
- Asegura que tú eres el autor de tu código
- Configurable para casos especiales

### ⚡ GitHub Actions Local

- Ejecuta tus workflows localmente antes del push
- Usa `act` si está instalado (requiere Docker)
- Fallback a ejecutor Python custom si no hay Docker
- Ahorra minutos de CI/CD y detecta errores antes

## 🖥️ Compatibilidad Multiplataforma

CI Guardian detecta automáticamente tu sistema operativo y entorno virtual:

| Feature | Linux | Windows |
|---------|-------|---------|
| Detección de venv | ✅ | ✅ |
| Hooks ejecutables | ✅ | ✅ (.bat) |
| Ruff & Black | ✅ | ✅ |
| Bandit & Safety | ✅ | ✅ |
| Token anti-bypass | ✅ | ✅ |

## 📖 Uso

### Instalación de Hooks

```bash
# En tu proyecto
ci-guardian install

# Instalar solo hooks específicos
ci-guardian install --hooks pre-commit,pre-push

# Ver configuración
ci-guardian status
```

### Configuración Personalizada

Crea un archivo `.ci-guardian.yaml` en la raíz de tu proyecto:

```yaml
# .ci-guardian.yaml
version: 0.2.0

hooks:
  pre-commit:
    enabled: true
    validadores:
      - ruff
      - black
      - bandit

validadores:
  ruff:
    enabled: true
    timeout: 60
    protected: false  # Permite deshabilitar
    auto-fix: true

  black:
    enabled: true
    timeout: 60
    protected: false
    line-length: 100

  bandit:
    enabled: true
    timeout: 60
    protected: true  # 🔒 NO se puede deshabilitar programáticamente
    severity: medium

  authorship:
    enabled: true
    timeout: 30
    protected: true  # 🔒 Previene que Claude se añada como co-autor
    block_claude_coauthor: true

# Sistema de Integridad (Opcional - LIB-33)
# Si está presente, previene modificación programática del archivo
# Para regenerar después de editar: ci-guardian configure --regenerate-hash
_integrity:
  hash: "sha256:<se calcula automáticamente>"
  allow_programmatic: false
```

**Validadores Protegidos** (🆕 v0.2.0):
- `protected: true` → El validador NO se puede deshabilitar programáticamente
- `protected: false` → Se puede deshabilitar según necesites
- Sistema de integridad SHA256 detecta modificaciones no autorizadas
- Regenerar hash después de editar: `ci-guardian configure --regenerate-hash`

### Comandos CLI

```bash
# Instalar hooks
ci-guardian install

# Desinstalar hooks
ci-guardian uninstall

# Ver estado
ci-guardian status

# Ejecutar validación manual
ci-guardian check

# Crear configuración
ci-guardian configure

# Regenerar hash de integridad después de editar manualmente (LIB-33)
ci-guardian configure --regenerate-hash

# Crear commit asegurando venv activo (LIB-32)
ci-guardian commit -m "feat: add new feature"
```

## 🧪 Testing

CI Guardian está construido con TDD (Test-Driven Development):

```bash
# Ejecutar tests
pytest

# Con cobertura
pytest --cov=ci_guardian --cov-report=html

# Solo tests de tu plataforma
pytest -m "not windows"  # En Linux
pytest -m "not linux"    # En Windows
```

## 🏗️ Arquitectura

```
src/ci_guardian/
├── cli.py                      # CLI con Click (6 comandos)
├── core/
│   ├── installer.py            # Instalación de hooks (LIB-1)
│   ├── venv_manager.py         # Detección/creación de venv (LIB-2)
│   └── venv_validator.py       # Validación de venv activo (LIB-32)
├── validators/
│   ├── code_quality.py         # Ruff & Black (LIB-4)
│   ├── security.py             # Bandit & Safety (LIB-5)
│   ├── authorship.py           # Validación de autoría (LIB-6)
│   └── no_verify_blocker.py    # Anti --no-verify (LIB-3)
├── runners/
│   └── github_actions.py       # Ejecución local de GH Actions (LIB-7)
├── hooks/
│   ├── pre_commit.py           # Ejecuta Ruff, Black, Bandit + genera token
│   ├── post_commit.py          # Valida token, revierte si bypass
│   └── pre_push.py             # Ejecuta tests y GH Actions
└── templates/
    └── hook_template.sh        # Template base para hooks
```

**Tests**: `tests/unit/` (336 tests) + `tests/integration/` (17 tests)

## 🗺️ Roadmap

### ✅ v0.1.0 - COMPLETADO (2025-01)

Todas las funcionalidades core están implementadas:

- ✅ **LIB-1**: Hook Installer (50 tests, 89% coverage)
- ✅ **LIB-2**: Virtual Environment Manager (50 tests, 89% coverage)
- ✅ **LIB-3**: No-Verify Blocker (60 tests, 98% coverage)
- ✅ **LIB-4**: Ruff & Black Integration (60 tests, 96% coverage)
- ✅ **LIB-5**: Security Audit (48 tests, 98% coverage)
- ✅ **LIB-6**: Authorship Validator (20 tests, 96% coverage)
- ✅ **LIB-7**: GitHub Actions Runner (31 tests, 94% coverage)
- ✅ **LIB-8**: CLI Interface (17 tests, 81% coverage)
- ✅ **LIB-9**: Integration Tests (17 tests, 100% coverage)

### 🔜 v0.2.0 - Mejoras Planeadas

- 📝 Publicación en PyPI
- 📚 Documentación completa en ReadTheDocs
- 🎨 Mejoras en output del CLI (colores, progress bars)
- 🔧 Configuración más granular
- 📊 Reportes de métricas de calidad

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! El proyecto sigue TDD estricto y un workflow basado en Pull Requests.

### ⚠️ Branch Protection Activo

> **IMPORTANTE**: Las ramas `main` y `dev` están protegidas. **NO se puede hacer push directo** - todos los cambios deben ir mediante Pull Request.

### 📝 Workflow de Contribución

1. **Fork** el proyecto
2. **Clone** tu fork localmente
3. **Configura pre-commit** (se ejecuta automáticamente en cada commit):
   ```bash
   source venv/bin/activate
   pre-commit install  # Ya está instalado en este repo
   ```
4. **Crea una rama** feature desde `dev`:
   ```bash
   git checkout -b feat/amazing-feature
   ```
5. **Escribe tests PRIMERO** (RED) - Todos los tests deben fallar
6. **Implementa** el código mínimo (GREEN) - Haz que los tests pasen
7. **Refactoriza** si es necesario (REFACTOR)
8. **Commit** con [Conventional Commits](https://www.conventionalcommits.org/):
   ```bash
   git commit -m "feat(scope): description"
   # Los pre-commit hooks se ejecutan automáticamente aquí ✓
   ```
9. **Push** tu rama feature:
   ```bash
   git push origin feat/amazing-feature
   ```
10. **Crea Pull Request** hacia `dev` (NO hacia `main`):
    ```bash
    gh pr create --base dev
    ```

### 🔧 Pre-commit Hooks

Los siguientes hooks se ejecutan **automáticamente** en cada commit:

- ✅ **Hygiene**: Trailing whitespace, EOF, YAML/JSON/TOML syntax
- ✅ **Ruff**: Linter + formatter (auto-fix)
- ✅ **Black**: Code formatter
- ✅ **Bandit**: Security linter
- ✅ **MyPy**: Type checker
- ✅ **Custom**: Anti --no-verify detection

Si algún hook falla, el commit se bloquea hasta que se corrija.

### Estándares de Calidad

- ✅ Coverage mínimo: 75% (apuntamos a 95%+)
- ✅ Type hints completos (Python 3.12+: `list[T]`, `str | None`)
- ✅ Docstrings en español, formato Google
- ✅ Tests multiplataforma (Linux/Windows)
- ✅ Sin vulnerabilidades de seguridad (Bandit, Ruff S-rules)
- ✅ Todos los pre-commit hooks deben pasar

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para la guía completa de contribución.
Ver [CLAUDE.md](CLAUDE.md) para documentación detallada del desarrollo.

## 📝 Licencia

MIT License - ver [LICENSE](LICENSE) para detalles.

## 🙏 Agradecimientos

- [Ruff](https://github.com/astral-sh/ruff) - El linter más rápido de Python
- [Black](https://github.com/psf/black) - El formateador sin compromises
- [Bandit](https://github.com/PyCQA/bandit) - Security linter
- [Safety](https://github.com/pyupio/safety) - Dependency security checker
- [act](https://github.com/nektos/act) - Run GitHub Actions locally

---

Hecho con ❤️ para proyectos con Claude Code
