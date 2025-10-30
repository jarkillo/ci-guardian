# Guía de Contribución a CI Guardian 🤝

¡Gracias por tu interés en contribuir a CI Guardian! Este documento te guiará a través del proceso de contribución.

## 📋 Tabla de Contenidos

- [Código de Conducta](#código-de-conducta)
- [¿Cómo puedo contribuir?](#cómo-puedo-contribuir)
- [Proceso de Desarrollo](#proceso-de-desarrollo)
- [Estándares de Código](#estándares-de-código)
- [Proceso de Pull Request](#proceso-de-pull-request)
- [Reportar Bugs](#reportar-bugs)
- [Sugerir Features](#sugerir-features)

## 📜 Código de Conducta

Este proyecto se adhiere al [Código de Conducta](CODE_OF_CONDUCT.md). Al participar, se espera que mantengas este código. Por favor reporta comportamiento inaceptable a través de los issues de GitHub.

## 🎯 ¿Cómo puedo contribuir?

Hay muchas formas de contribuir a CI Guardian:

- 🐛 **Reportar bugs**: Encuentra y reporta bugs
- ✨ **Sugerir features**: Propón nuevas funcionalidades
- 📝 **Mejorar documentación**: Corrige typos, añade ejemplos
- 💻 **Escribir código**: Implementa nuevas features o corrige bugs
- 🧪 **Mejorar tests**: Añade más casos de prueba
- 🔍 **Revisar PRs**: Ayuda a revisar pull requests

## 🔄 Proceso de Desarrollo

CI Guardian sigue **TDD estricto** (Test-Driven Development). Este es el proceso obligatorio:

### ⚠️ IMPORTANTE: Branch Protection Activo

> **Las ramas `main` y `dev` están protegidas**. NO se puede hacer push directo - todos los cambios deben ir mediante Pull Request. Además, **pre-commit hooks** se ejecutan automáticamente en cada commit.

**Implicaciones:**
- ❌ NO puedes hacer `git push origin dev` o `git push origin main`
- ✅ Debes crear una rama feature y abrir un Pull Request
- ✅ Pre-commit hooks validan automáticamente cada commit (Ruff, Black, Bandit, MyPy)
- ✅ Si los hooks fallan, el commit se bloquea hasta que corrijas los errores

### 1. Setup del Entorno

```bash
# Fork el repositorio en GitHub y clona tu fork
git clone https://github.com/TU-USUARIO/ci-guardian.git
cd ci-guardian

# Añade el upstream
git remote add upstream https://github.com/jarkillo/ci-guardian.git

# Crea y activa el entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instala dependencias
pip install -e ".[dev]"

# Instala pre-commit hooks (OBLIGATORIO)
pre-commit install
# Verifica que funciona
pre-commit run --all-files
```

**Pre-commit hooks instalados:**
- ✅ Hygiene: trailing whitespace, EOF, YAML/JSON/TOML syntax
- ✅ Ruff: linter + formatter (auto-fix)
- ✅ Black: code formatter
- ✅ Bandit: security linter
- ✅ MyPy: type checker
- ✅ Custom: anti --no-verify detection

### 2. Crear una Rama Feature

```bash
# Actualiza tu fork
git checkout dev
git pull upstream dev

# Crea tu rama feature (desde dev, NO desde main)
git checkout -b feat/nombre-descriptivo
# O para bugs: git checkout -b fix/nombre-descriptivo
```

### 3. Desarrollo con TDD (OBLIGATORIO)

#### FASE RED (Escribir Tests Primero)

**NUNCA escribas código de producción sin una prueba que falle primero.**

```bash
# 1. Escribe tus tests en tests/unit/ o tests/integration/
# 2. Los tests DEBEN fallar inicialmente
pytest tests/unit/test_tu_modulo.py -v

# Resultado esperado: FAILED (esto es bueno en TDD!)
```

**Ejemplo de test (FASE RED)**:

```python
# tests/unit/test_venv_manager.py

import pytest
from pathlib import Path
from ci_guardian.core.venv_manager import detectar_venv

class TestDeteccionVenv:
    """Tests para detección de entorno virtual."""

    def test_debe_detectar_venv_en_linux(self, tmp_path: Path) -> None:
        """Debe detectar venv en Linux con bin/python."""
        # Arrange
        venv_path = tmp_path / "venv"
        venv_path.mkdir()
        (venv_path / "bin").mkdir()
        (venv_path / "bin" / "python").touch()

        # Act
        es_venv = detectar_venv(venv_path)

        # Assert
        assert es_venv, "Debe detectar venv con bin/python"
```

**Commit de FASE RED**:

```bash
git add tests/unit/test_venv_manager.py
git commit -m "test(core): add failing tests for venv detection (RED)

- Test Linux venv detection
- Test Windows venv detection
- Test invalid venv rejection"
```

#### FASE GREEN (Implementar Código Mínimo)

Ahora implementa el código **MÍNIMO** necesario para hacer pasar los tests:

```python
# src/ci_guardian/core/venv_manager.py

from pathlib import Path

def detectar_venv(venv_path: Path) -> bool:
    """
    Detecta si un directorio es un entorno virtual válido.

    Args:
        venv_path: Ruta al directorio a verificar

    Returns:
        True si es un venv válido, False en caso contrario
    """
    # Implementación mínima para pasar el test
    python_bin = venv_path / "bin" / "python"
    return python_bin.exists()
```

**Ejecutar tests (deben pasar)**:

```bash
pytest tests/unit/test_venv_manager.py -v
# Resultado esperado: PASSED ✅
```

**Commit de FASE GREEN**:

```bash
git add src/ci_guardian/core/venv_manager.py
git commit -m "feat(core): implement venv detection (GREEN)

- Detect Linux venv with bin/python
- Return False for invalid paths"
```

#### FASE REFACTOR (Mejorar Código)

Si es necesario, refactoriza manteniendo los tests verdes:

```bash
# Refactoriza el código
# Ejecuta tests después de cada cambio
pytest tests/unit/test_venv_manager.py -v

# Commit de refactor (opcional)
git commit -m "refactor(core): extract venv validation to separate function"
```

### 4. Validación de Calidad

Antes de hacer push, asegúrate de que todo pasa:

```bash
# Tests (OBLIGATORIO)
pytest

# Coverage (mínimo 75%, apuntamos a 95%+)
pytest --cov=ci_guardian --cov-report=term-missing --cov-fail-under=75

# Linting (OBLIGATORIO)
ruff check .

# Formatting (OBLIGATORIO)
black --check .

# Type checking (RECOMENDADO)
mypy src/ci_guardian
```

Si todo pasa, estás listo para hacer push:

```bash
git push origin feat/nombre-descriptivo
```

## 📏 Estándares de Código

### Type Hints (Python 3.12+)

**OBLIGATORIO**: Usar sintaxis moderna de Python 3.12+

```python
# ✅ CORRECTO (Python 3.12+)
def procesar_archivos(
    archivos: list[Path],
    opciones: dict[str, str] | None = None
) -> tuple[int, str]:
    """Procesa archivos."""
    pass

# ❌ INCORRECTO (sintaxis antigua)
from typing import List, Dict, Optional, Tuple

def procesar_archivos(
    archivos: List[Path],
    opciones: Optional[Dict[str, str]] = None
) -> Tuple[int, str]:
    pass
```

**Reglas**:
- Usar `list[T]`, `dict[K,V]`, `set[T]`, `tuple[T1, T2]` (minúsculas)
- Usar `|` para Union/Optional: `str | None` en lugar de `Optional[str]`
- Usar `type` keyword para aliases: `type PathLike = Path | str`
- Usar `from collections.abc import Sequence` para abstracciones

### Docstrings (Español, Google Style)

**OBLIGATORIO**: Todas las funciones públicas deben tener docstrings en español.

```python
def instalar_hook(
    repo_path: Path,
    hook_name: str,
    contenido: str
) -> None:
    """
    Instala un hook de Git en el repositorio.

    Valida el repositorio, el nombre del hook y el contenido antes de
    escribir el archivo. Aplica permisos de ejecución en Linux/macOS.

    Args:
        repo_path: Ruta al repositorio Git
        hook_name: Nombre del hook (pre-commit, pre-push, etc.)
        contenido: Contenido del hook a instalar

    Raises:
        ValueError: Si el repo no es válido o el hook no está permitido
        FileExistsError: Si el hook ya existe

    Example:
        >>> repo = Path("/home/user/proyecto")
        >>> instalar_hook(repo, "pre-commit", "#!/bin/bash\\necho test")
    """
    pass
```

### Convenciones de Nombres

```python
# Variables y funciones: snake_case
nombre_archivo = "test.py"
def procesar_datos():
    pass

# Constantes: UPPER_SNAKE_CASE
MAX_HOOK_SIZE = 1024 * 100
HOOKS_PERMITIDOS = {"pre-commit", "pre-push"}

# Clases: PascalCase
class HookInstaller:
    pass

# Funciones privadas: _prefijo
def _validar_internamente():
    pass
```

### Seguridad (CRÍTICO)

**NUNCA**:
- ❌ Usar `shell=True` con `subprocess`
- ❌ Usar `os.system()` o `eval()`
- ❌ Usar permisos `0o777` (world-writable)
- ❌ Confiar en user input sin validar

**SIEMPRE**:
- ✅ Validar paths con `Path.resolve()`
- ✅ Usar whitelists para nombres de archivos
- ✅ Usar `secrets.token_hex()` para tokens
- ✅ Especificar encoding UTF-8 explícitamente

### Testing

**Requisitos**:
- ✅ Coverage mínimo: 75% (apuntamos a 95%+)
- ✅ Patrón Arrange-Act-Assert
- ✅ Assertions descriptivas en español
- ✅ Usar `@pytest.mark.skipif` para tests específicos de plataforma
- ✅ Usar mocks para subprocess y filesystem

**Ejemplo**:

```python
def test_debe_rechazar_path_traversal(self, tmp_path: Path) -> None:
    """Debe rechazar intentos de path traversal."""
    # Arrange
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    (repo_path / ".git" / "hooks").mkdir(parents=True)

    # Act & Assert
    with pytest.raises(ValueError, match="Path traversal detectado"):
        validar_path_hook(repo_path, "../../etc/passwd")
```

## 🔄 Proceso de Pull Request

### 1. Crear el PR

```bash
# Después de push, crea el PR en GitHub
gh pr create --base dev --head tu-usuario:feat/nombre-descriptivo
```

**Título del PR**: Usar Conventional Commits

```
feat(core): implement venv detection for Linux and Windows
fix(security): prevent path traversal in hook installer
docs(readme): add contributing guidelines
```

**Descripción del PR**: Incluir

```markdown
## Summary
Breve descripción de qué hace el PR

## Changes
- Lista de cambios específicos
- Otro cambio

## Testing
- ✅ All tests pass (X passed, Y skipped)
- ✅ Coverage: X%
- ✅ Tested on Linux/Windows

## Related Issues
- Closes #123
```

### 2. Revisión del PR

Tu PR será revisado por:
- Mantenedores del proyecto
- CI/CD automático (cuando esté configurado)
- Posiblemente otros contributors

**Espera feedback en**:
- Calidad del código
- Cobertura de tests
- Seguridad
- Documentación

### 3. Merge

Una vez aprobado, un mantenedor hará merge a `dev`. Después:

```bash
# Actualiza tu rama local
git checkout dev
git pull upstream dev

# Limpia tu rama feature local
git branch -d feat/nombre-descriptivo

# Elimina la rama feature remota
git push origin --delete feat/nombre-descriptivo
```

**Nota**: Ya NO necesitas hacer `git push origin dev` porque:
- Las ramas `main` y `dev` están protegidas (branch protection activo)
- NO se puede hacer push directo - solo mediante Pull Request
- El merge ya está en `upstream/dev`, así que solo necesitas hacer `pull`

## 🐛 Reportar Bugs

### Antes de Reportar

1. **Busca** en issues existentes: https://github.com/jarkillo/ci-guardian/issues
2. **Verifica** que estás usando la última versión
3. **Prueba** en un entorno limpio (nuevo venv)

### Template de Bug Report

```markdown
**Describe el bug**
Descripción clara y concisa del bug.

**Para Reproducir**
Pasos para reproducir el comportamiento:
1. Ir a '...'
2. Ejecutar '...'
3. Ver error

**Comportamiento Esperado**
Descripción de qué esperabas que pasara.

**Screenshots**
Si aplica, añade screenshots.

**Entorno:**
 - OS: [e.g. Ubuntu 22.04, Windows 11]
 - Python: [e.g. 3.12.0]
 - CI Guardian: [e.g. 0.1.0]

**Logs**
```
Pega aquí los logs relevantes
```

**Contexto Adicional**
Cualquier otra información relevante.
```

## ✨ Sugerir Features

### Antes de Sugerir

1. **Verifica** el roadmap: Ver si ya está planeado
2. **Busca** en issues: Puede que alguien ya lo haya sugerido
3. **Piensa** en el alcance: ¿Encaja con la visión del proyecto?

### Template de Feature Request

```markdown
**¿Tu feature está relacionada con un problema?**
Descripción clara del problema: "Estoy frustrado cuando [...]"

**Describe la solución que te gustaría**
Descripción clara de qué quieres que pase.

**Describe alternativas que has considerado**
Otras soluciones o features que has considerado.

**¿Por qué es importante?**
Explica por qué esta feature beneficiaría al proyecto.

**Contexto Adicional**
Screenshots, mockups, código de ejemplo, etc.
```

## 🎓 Recursos Útiles

- [Python Type Hints (3.12+)](https://docs.python.org/3.12/library/typing.html)
- [Pytest Documentation](https://docs.pytest.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [TDD by Example](https://www.amazon.com/Test-Driven-Development-Kent-Beck/dp/0321146530)

## 📞 ¿Necesitas Ayuda?

- 💬 **Discusiones**: Usa [GitHub Discussions](https://github.com/jarkillo/ci-guardian/discussions)
- 🐛 **Bugs**: Abre un [Issue](https://github.com/jarkillo/ci-guardian/issues)
- 📧 **Privado**: Contacta a los mantenedores (ver SECURITY.md para temas de seguridad)

## 🙏 Gracias

¡Gracias por contribuir a CI Guardian! Tu tiempo y esfuerzo hacen que este proyecto sea mejor para todos.

---

**Mantenedores**:
- [@jarkillo](https://github.com/jarkillo) - Creator & Maintainer
