# CI Guardian 🛡️

> Git hooks automation for Claude Code projects - Enforces code quality, security, and prevents hook bypass

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: ruff](https://img.shields.io/badge/linting-ruff-red.svg)](https://github.com/astral-sh/ruff)

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
ruff:
  enabled: true
  fail_on_error: true

black:
  enabled: true
  check_only: false  # false = autoformat, true = solo verifica

security:
  bandit: true
  safety: true
  block_on_critical: true

authorship:
  block_claude_coauthor: true
  allowed_coauthors:
    - "TuCompañero <email@example.com>"

github_actions:
  enabled: true
  use_act: true
  workflows:
    - ".github/workflows/test.yml"
```

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

# Actualizar configuración
ci-guardian configure
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
├── cli.py              # CLI con Click
├── core/
│   ├── config.py       # Gestión de configuración
│   ├── venv_manager.py # Detección/creación de venv
│   └── hook_runner.py  # Ejecución de validaciones
├── validators/
│   ├── code_quality.py # Ruff & Black
│   ├── security.py     # Bandit & Safety
│   ├── authorship.py   # Validación de autoría
│   └── no_verify_blocker.py  # Anti --no-verify
├── runners/
│   └── github_actions.py  # Ejecución local de GH Actions
├── hooks/
│   ├── pre-commit.py
│   ├── pre-push.py
│   └── post-commit.py
└── templates/
    └── hook_template.sh
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feat/amazing-feature`)
3. Escribe tests PRIMERO (TDD)
4. Implementa tu feature
5. Asegúrate de que todo pasa (`pytest`)
6. Commit con conventional commits (`feat(scope): description`)
7. Push y crea un Pull Request

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
