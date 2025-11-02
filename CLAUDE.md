# CI Guardian - Documentación Interna para Claude Code

> **Última actualización**: 2025-10-30
> **Versión del proyecto**: 0.1.0
> **Python**: 3.12.12

---

## 🎯 Visión General

**CI Guardian** es una librería Python que automatiza y **asegura** el flujo de trabajo de desarrollo con Claude Code. Su objetivo principal es **garantizar calidad de código y prevenir bypass de validaciones** mediante:

- ✅ Instalación automática de Git hooks
- 🔒 Bloqueo del flag `--no-verify` (sistema de tokens)
- 🎨 Ejecución automática de Ruff y Black
- 🔐 Auditoría de seguridad (Bandit + Safety)
- 👤 Validación de autoría (rechaza Co-Authored-By: Claude)
- 🏃 Ejecución local de GitHub Actions (act con fallback)
- 🖥️ Soporte multiplataforma (Linux + Windows)

### Problema que Resuelve

Claude Code puede:
1. Intentar hacer commits con `--no-verify` para saltarse hooks
2. Añadirse como co-autor en commits
3. No ejecutar linters/formatters automáticamente
4. Consumir minutos de CI/CD con errores evitables

**CI Guardian previene TODO esto** mediante hooks inmutables y validación forzada.

---

## 🏗️ Arquitectura del Proyecto

### Estructura de Directorios

```
ci-library/
├── .claude/                          # Configuración de Claude Code
│   ├── agents/                       # Agentes especializados (TDD, security, etc.)
│   │   ├── tdd-ci-guardian.md        # Agente TDD (escribe tests primero)
│   │   ├── ci-guardian-implementer.md # Agente implementador (fase GREEN)
│   │   ├── ci-guardian-security-auditor.md # Auditor de seguridad
│   │   ├── git-workflow-manager.md   # Gestión de git/commits
│   │   └── pr-cop-reviewer.md        # Revisor de PRs
│   └── settings.local.json           # Configuración local
├── src/ci_guardian/                  # Código fuente
│   ├── __init__.py                   # Package principal (v0.1.0)
│   ├── cli.py                        # CLI con Click (LIB-8)
│   ├── core/                         # Funcionalidad core
│   │   ├── __init__.py
│   │   ├── installer.py              # Instalador de hooks (LIB-1)
│   │   ├── venv_manager.py           # Gestión de venv (LIB-2)
│   │   ├── hook_runner.py            # Ejecutor de validaciones
│   │   └── config.py                 # Gestión de configuración
│   ├── validators/                   # Validadores
│   │   ├── __init__.py
│   │   ├── code_quality.py           # Ruff + Black (LIB-4)
│   │   ├── security.py               # Bandit + Safety (LIB-5)
│   │   ├── authorship.py             # Anti Claude co-author (LIB-6)
│   │   └── no_verify_blocker.py      # Anti --no-verify (LIB-3)
│   ├── runners/                      # Ejecutores de herramientas
│   │   ├── __init__.py
│   │   └── github_actions.py         # GH Actions local (LIB-7)
│   ├── hooks/                        # Git hooks
│   │   ├── __init__.py
│   │   ├── pre-commit.py             # Hook pre-commit
│   │   ├── pre-push.py               # Hook pre-push
│   │   └── post-commit.py            # Hook post-commit (valida token)
│   └── templates/                    # Templates de hooks
│       └── hook_template.sh          # Template base para hooks
├── tests/                            # Tests (TDD obligatorio)
│   ├── unit/                         # Tests unitarios
│   │   ├── test_installer.py
│   │   ├── test_venv_manager.py
│   │   ├── test_code_quality.py
│   │   ├── test_security.py
│   │   ├── test_authorship.py
│   │   ├── test_no_verify_blocker.py
│   │   └── test_cli.py
│   └── integration/                  # Tests de integración
│       └── test_full_workflow.py
├── pyproject.toml                    # Configuración del proyecto
├── README.md                         # Documentación pública
├── CLAUDE.md                         # Esta documentación
├── LICENSE                           # MIT License
└── .gitignore                        # Git ignores

### Venv del Proyecto
venv/                                 # Python 3.12.12
├── bin/python                        # Python 3.12.12
├── lib/python3.12/site-packages/     # Dependencias instaladas
```

### Módulos Principales

#### 1. **core/** - Funcionalidad Base
- `installer.py`: Instala/desinstala hooks en `.git/hooks/`
- `venv_manager.py`: Detecta/crea entornos virtuales (Linux/Windows)
- `hook_runner.py`: Orquesta la ejecución de validadores en hooks
- `config.py`: Carga configuración desde `.ci-guardian.yaml`

#### 2. **validators/** - Validadores de Calidad
- `code_quality.py`: Ejecuta Ruff (linter) y Black (formatter)
- `security.py`: Ejecuta Bandit (code) y Safety (dependencies)
- `authorship.py`: Valida autoría de commits (rechaza Claude co-author)
- `no_verify_blocker.py`: Sistema de tokens para bloquear `--no-verify`

#### 3. **runners/** - Ejecutores de Herramientas
- `github_actions.py`: Ejecuta workflows localmente (act o custom)

#### 4. **hooks/** - Git Hooks
- `pre-commit.py`: Crea token, ejecuta Ruff/Black/Bandit
- `pre-push.py`: Ejecuta tests y GH Actions locales
- `post-commit.py`: Valida token (revierte si no existe)

#### 5. **cli.py** - Interfaz de Línea de Comandos
```bash
ci-guardian install      # Instala hooks en proyecto
ci-guardian uninstall    # Desinstala hooks
ci-guardian status       # Muestra estado de hooks
ci-guardian check        # Validación manual
ci-guardian configure    # Configuración interactiva
```

---

## 🔄 Workflow de Desarrollo TDD

### Principio Fundamental: **RED → GREEN → REFACTOR**

**NUNCA escribas código de producción sin una prueba que falle primero.**

### Proceso con Agentes

#### 1. **FASE RED** - Escribir Tests (Agente: tdd-ci-guardian)

```bash
# Ejemplo: Implementar LIB-1 (Hook Installer)

# 1. Crear rama desde Linear
git checkout -b lib-1-implement-hook-installer-pre-commit-pre-push-post-commit

# 2. Usar agente tdd-ci-guardian
# El agente escribirá TODOS los tests primero
```

**Tests que debe escribir el agente** (ejemplo LIB-1):

```python
# tests/unit/test_installer.py

class TestHookInstaller:
    """Tests para el instalador de hooks."""

    def test_debe_detectar_repositorio_git_valido(self, tmp_path):
        """Debe detectar si un directorio es un repo git válido."""
        # Arrange
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        (repo_path / ".git").mkdir()

        # Act
        es_valido = es_repositorio_git(repo_path)

        # Assert
        assert es_valido, "Debe reconocer un repo git válido"

    def test_debe_rechazar_directorio_sin_git(self, tmp_path):
        """Debe rechazar directorios sin .git."""
        # Arrange
        dir_path = tmp_path / "no_repo"
        dir_path.mkdir()

        # Act
        es_valido = es_repositorio_git(dir_path)

        # Assert
        assert not es_valido, "No debe reconocer directorios sin .git"

    def test_debe_instalar_hook_con_permisos_correctos_en_linux(self, tmp_path):
        """Debe instalar hook con permisos 755 en Linux."""
        # Arrange
        repo_path = crear_repo_mock(tmp_path)
        contenido_hook = "#!/bin/bash\necho 'test'"

        # Act
        with patch('platform.system', return_value='Linux'):
            instalar_hook(repo_path, "pre-commit", contenido_hook)

        # Assert
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists(), "Hook debe existir"
        assert oct(hook_path.stat().st_mode)[-3:] == "755", "Permisos deben ser 755"

    def test_debe_rechazar_instalacion_si_hook_existe(self, tmp_path):
        """Debe rechazar instalar si el hook ya existe."""
        # Arrange
        repo_path = crear_repo_mock(tmp_path)
        hook_path = repo_path / ".git" / "hooks" / "pre-commit"
        hook_path.write_text("#!/bin/bash\necho 'existing'")

        # Act & Assert
        with pytest.raises(FileExistsError, match="El hook pre-commit ya existe"):
            instalar_hook(repo_path, "pre-commit", "nuevo contenido")

    def test_debe_validar_nombre_hook_con_whitelist(self, tmp_path):
        """Debe validar que el nombre del hook esté en la whitelist."""
        # Arrange
        repo_path = crear_repo_mock(tmp_path)

        # Act & Assert
        with pytest.raises(ValueError, match="Hook no permitido: malicious-hook"):
            instalar_hook(repo_path, "malicious-hook", "contenido")

    @pytest.mark.skipif(platform.system() != "Windows", reason="Test específico de Windows")
    def test_debe_instalar_hook_bat_en_windows(self, tmp_path):
        """Debe instalar hooks como .bat en Windows."""
        # Arrange
        repo_path = crear_repo_mock(tmp_path)
        contenido_hook = "@echo off\necho test"

        # Act
        with patch('platform.system', return_value='Windows'):
            instalar_hook(repo_path, "pre-commit", contenido_hook)

        # Assert
        hook_path = repo_path / ".git" / "hooks" / "pre-commit.bat"
        assert hook_path.exists(), "Hook .bat debe existir en Windows"
```

**Ejecutar tests (deben fallar):**
```bash
source venv/bin/activate
pytest tests/unit/test_installer.py -v
# Todos deben FALLAR (RED)
```

#### 2. **FASE GREEN** - Implementar Código (Agente: ci-guardian-implementer)

El agente `ci-guardian-implementer` escribe el **código mínimo** para pasar los tests:

```python
# src/ci_guardian/core/installer.py

from pathlib import Path
import platform
from typing import List

# Whitelist de hooks permitidos
HOOKS_PERMITIDOS = {"pre-commit", "pre-push", "post-commit", "pre-rebase"}


def es_repositorio_git(repo_path: Path) -> bool:
    """
    Verifica si un directorio es un repositorio Git válido.

    Args:
        repo_path: Ruta al directorio a verificar

    Returns:
        True si es un repo Git válido, False en caso contrario
    """
    return (repo_path / ".git").is_dir()


def instalar_hook(repo_path: Path, hook_name: str, contenido: str) -> None:
    """
    Instala un hook de Git en el repositorio.

    Args:
        repo_path: Ruta al repositorio Git
        hook_name: Nombre del hook (pre-commit, pre-push, etc.)
        contenido: Contenido del hook

    Raises:
        ValueError: Si el nombre del hook no está en la whitelist
        FileExistsError: Si el hook ya existe
        ValueError: Si no es un repositorio Git válido
    """
    # Validar que sea un repo git
    if not es_repositorio_git(repo_path):
        raise ValueError(f"El directorio {repo_path} no es un repositorio Git válido")

    # Validar nombre del hook (whitelist)
    if hook_name not in HOOKS_PERMITIDOS:
        raise ValueError(f"Hook no permitido: {hook_name}")

    # Determinar extensión según plataforma
    extension = ".bat" if platform.system() == "Windows" else ""
    hook_path = repo_path / ".git" / "hooks" / f"{hook_name}{extension}"

    # No sobrescribir hooks existentes
    if hook_path.exists():
        raise FileExistsError(f"El hook {hook_name} ya existe")

    # Escribir hook
    hook_path.write_text(contenido, encoding="utf-8")

    # Permisos de ejecución en Linux/Mac
    if platform.system() != "Windows":
        hook_path.chmod(0o755)
```

**Ejecutar tests (deben pasar):**
```bash
pytest tests/unit/test_installer.py -v
# Todos deben PASAR (GREEN) ✅
```

#### 3. **FASE REFACTOR** - Mejorar Código

Una vez GREEN, refactorizar manteniendo tests verdes:
- Extraer funciones auxiliares
- Mejorar nombres
- Añadir documentación
- Optimizar lógica

#### 4. **Commit con Conventional Commits** (Agente: git-workflow-manager)

```bash
# Fase RED
git add tests/unit/test_installer.py
git commit -m "test(core): add failing tests for hook installer

- Test git repository detection
- Test hook installation with correct permissions
- Test existing hook rejection
- Test hook name whitelist validation
- Test Windows .bat script support"

# Fase GREEN
git add src/ci_guardian/core/installer.py
git commit -m "feat(core): implement hook installer with cross-platform support

- Detect valid git repositories
- Install hooks with proper permissions (755 on Linux)
- Prevent overwriting existing hooks
- Whitelist validation for hook names
- Windows .bat script support"

# Fase REFACTOR (si aplica)
git add src/ci_guardian/core/installer.py
git commit -m "refactor(core): extract hook validation logic to separate function"
```

---

## 📋 Issues de Linear (Team: Librerias)

### Issues Urgentes (Prioridad 1)

- **LIB-1**: Hook installer (pre-commit, pre-push, post-commit)
- **LIB-2**: Virtual environment detection/management (Linux/Windows)
- **LIB-3**: Anti --no-verify validator (sistema de tokens)
- **LIB-8**: CLI (install, uninstall, status, check, configure)
- **LIB-9**: Tests unitarios e integración (coverage ≥75%)

### Issues High (Prioridad 2)

- **LIB-4**: Ruff and Black executor
- **LIB-5**: Security audit (Bandit + Safety)
- **LIB-6**: Authorship validator (anti Claude co-author)

### Issues Medium (Prioridad 3)

- **LIB-7**: GitHub Actions executor local (act con fallback)

### Orden de Implementación Recomendado

1. **LIB-1** (Hook installer) → Base del sistema
2. **LIB-2** (Venv manager) → Necesario para ejecutar herramientas
3. **LIB-4** (Ruff/Black) → Validación básica de calidad
4. **LIB-3** (Anti --no-verify) → Feature crítica de seguridad
5. **LIB-8** (CLI) → Interfaz de usuario
6. **LIB-6** (Authorship) → Validación de autoría
7. **LIB-5** (Security) → Auditoría completa
8. **LIB-7** (GH Actions) → Feature avanzada
9. **LIB-9** (Tests) → Continuo durante todo el desarrollo

---

## 🔐 Patrones de Seguridad Críticos

### 1. Subprocess Execution - NUNCA shell=True

```python
# ❌ VULNERABLE - Command Injection
def ejecutar_ruff_inseguro(archivos: str):
    os.system(f"ruff check {archivos}")  # NUNCA

# ✅ SEGURO
def ejecutar_ruff_seguro(archivos: List[Path]) -> bool:
    """Ejecuta Ruff de forma segura."""
    archivos_validos = [str(f) for f in archivos if f.exists() and f.suffix == ".py"]

    resultado = subprocess.run(
        ["ruff", "check", "--output-format=json"] + archivos_validos,
        capture_output=True,
        text=True,
        timeout=60,
        shell=False  # CRÍTICO
    )
    return resultado.returncode == 0
```

### 2. Path Traversal - Validar Todas las Rutas

```python
# ❌ VULNERABLE
def escribir_hook_inseguro(repo_path: str, hook_name: str):
    path = Path(repo_path) / ".git" / "hooks" / hook_name
    path.write_text("content")

# ✅ SEGURO
def escribir_hook_seguro(repo_path: Path, hook_name: str):
    """Escribe hook validando path."""
    # Whitelist de nombres
    if hook_name not in HOOKS_PERMITIDOS:
        raise ValueError(f"Hook no permitido: {hook_name}")

    # Validar repo git
    repo = repo_path.resolve()
    if not (repo / ".git" / "hooks").is_dir():
        raise ValueError("Directorio de hooks no encontrado")

    # Prevenir path traversal
    hook_path = (repo / ".git" / "hooks" / hook_name).resolve()
    if not hook_path.parent == (repo / ".git" / "hooks").resolve():
        raise ValueError("Path traversal detectado")

    hook_path.write_text(contenido, encoding="utf-8")
    hook_path.chmod(0o755)  # rwxr-xr-x, NO 0o777
```

### 3. Token Generation - Criptográficamente Seguro

```python
# ❌ VULNERABLE - Predecible
def generar_token_inseguro():
    return str(time.time())

# ✅ SEGURO
def generar_token_seguro() -> str:
    """Genera token criptográficamente seguro."""
    import secrets
    return secrets.token_hex(32)  # 256 bits de entropía
```

---

## 🖥️ Compatibilidad Multiplataforma

### Detección de Sistema Operativo

```python
import platform

sistema = platform.system()
# "Linux", "Windows", "Darwin" (macOS)
```

### Rutas Multiplataforma

```python
from pathlib import Path

# ✅ SIEMPRE usar pathlib.Path
venv_path = Path("venv")

# Detección de ejecutable Python en venv
if platform.system() == "Windows":
    python_exe = venv_path / "Scripts" / "python.exe"
else:
    python_exe = venv_path / "bin" / "python"
```

### Tests Específicos de Plataforma

```python
import pytest
import platform

@pytest.mark.skipif(platform.system() != "Windows", reason="Test específico de Windows")
def test_windows_specific():
    # Test solo se ejecuta en Windows
    pass

@pytest.mark.skipif(platform.system() != "Linux", reason="Test específico de Linux")
def test_linux_specific():
    # Test solo se ejecuta en Linux
    pass
```

---

## 🧪 Testing

### Configuración Pytest

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
    "-v",
    "--cov=ci_guardian",
    "--cov-report=term-missing",
    "--cov-fail-under=75",
    "--timeout=30",
]
markers = [
    "slow: tests lentos",
    "integration: tests de integración",
    "linux: tests específicos de Linux",
    "windows: tests específicos de Windows",
]
```

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Solo unitarios
pytest tests/unit/

# Solo integración
pytest tests/integration/

# Con cobertura
pytest --cov=ci_guardian --cov-report=html

# Específicos de plataforma
pytest -m "not windows"  # En Linux
pytest -m "not linux"    # En Windows
```

### Fixtures Comunes

```python
# tests/conftest.py

import pytest
from pathlib import Path

@pytest.fixture
def repo_git_mock(tmp_path):
    """Crea un repositorio git mock."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / ".git" / "hooks").mkdir()
    return repo

@pytest.fixture
def archivos_python_mock(tmp_path):
    """Crea archivos Python de prueba."""
    archivos = []
    for i in range(3):
        archivo = tmp_path / f"test_{i}.py"
        archivo.write_text(f"def funcion_{i}():\n    pass\n")
        archivos.append(archivo)
    return archivos
```

---

## 🛠️ Herramientas y Versiones

### Versiones Actuales (2025-10-30)

```toml
# pyproject.toml
requires-python = ">=3.9"
dependencies = [
    "click>=8.1.7",
    "pyyaml>=6.0.2",
    "colorama>=0.4.6",
    "ruff>=0.8.0",
    "black>=24.0.0",
    "bandit[toml]>=1.8.0",
    "safety>=3.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-cov>=6.0.0",
    "pytest-mock>=3.14.0",
    "pytest-timeout>=2.3.0",
    "mypy>=1.11.0",
]
```

### Configuración Ruff

```toml
[tool.ruff]
line-length = 100
target-version = "py39"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "S", "T20", "RET", "SIM"]
ignore = ["E501", "S603", "S607"]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "T201"]  # Allow assert and print
```

### Configuración Black

```toml
[tool.black]
line-length = 100
target-version = ["py39", "py310", "py311", "py312", "py313"]
```

### Configuración Bandit

```toml
[tool.bandit]
exclude_dirs = ["tests", "build", "dist"]
skips = ["B101"]  # Allow assert
```

---

## 🤖 Guía de Uso de Agentes

### 1. tdd-ci-guardian (RED Phase)

**Cuándo usar:**
- Al iniciar cualquier nueva funcionalidad
- Al corregir bugs (escribir test que reproduzca el bug primero)
- Siempre ANTES de escribir código de producción

**Qué hace:**
- Escribe TODOS los tests necesarios
- Cubre: happy paths, edge cases, errores, multiplataforma
- Usa mocks para subprocess, filesystem, git
- Assertions descriptivas en español

**Ejemplo:**
```
User: "Necesito implementar LIB-2 (venv manager)"
Assistant: "Voy a usar el agente tdd-ci-guardian para escribir las pruebas primero"
```

### 2. ci-guardian-implementer (GREEN Phase)

**Cuándo usar:**
- Después de tener tests que fallan
- Solo cuando los tests están en ROJO

**Qué hace:**
- Escribe el código MÍNIMO para pasar tests
- No añade features extra
- Aplica Black automáticamente
- Type hints completos
- Docstrings en español

**Ejemplo:**
```
User: "Los tests de venv_manager están fallando, implementa el código"
Assistant: "Voy a usar el agente ci-guardian-implementer para implementar la solución mínima"
```

### 3. ci-guardian-security-auditor (Security Review)

**Cuándo usar:**
- Antes de merge a main
- Después de implementar subprocess execution
- Después de operaciones de filesystem
- Antes de releases

**Qué hace:**
- Audita command injection
- Audita path traversal
- Verifica permisos de archivos
- Valida token generation
- Ejecuta bandit, safety, pip-audit

**Ejemplo:**
```
User: "Acabo de terminar el instalador de hooks, revísalo"
Assistant: "Voy a usar el agente ci-guardian-security-auditor para auditar la seguridad"
```

### 4. git-workflow-manager (Git & Commits)

**Cuándo usar:**
- Después de completar una fase TDD (RED, GREEN, REFACTOR)
- Al crear PRs
- Al actualizar CHANGELOG

**Qué hace:**
- Genera mensajes de commit con Conventional Commits
- Crea descripciones de PR profesionales
- Recomienda semantic versioning
- Valida branching strategy

**Ejemplo:**
```
User: "He terminado la fase GREEN de LIB-1"
Assistant: "Voy a usar el agente git-workflow-manager para crear el commit apropiado"
```

### 5. pr-cop-reviewer (PR Review)

**Cuándo usar:**
- Después de crear un PR
- Antes de merge a dev o main
- Cuando CI pasa pero quieres validación extra

**Qué hace:**
- Revisa 10 categorías de calidad
- Valida TDD compliance
- Analiza bot findings (CodeQL, etc.)
- Verifica seguridad y performance
- Da veredicto: APPROVE/REQUEST CHANGES/BLOCK

---

## 📝 Convenciones de Código

### Nomenclatura

```python
# Variables y funciones: snake_case
nombre_archivo = "test.py"
def procesar_datos():
    pass

# Constantes: UPPER_SNAKE_CASE
HOOKS_PERMITIDOS = {"pre-commit", "pre-push"}
MAX_TIMEOUT = 60

# Clases: PascalCase
class HookInstaller:
    pass

# Variables privadas: _prefijo
def _funcion_interna():
    pass
```

### Type Hints

**IMPORTANTE**: Usar **sintaxis moderna de Python 3.12+** para type hints.

#### Sintaxis Básica (Python 3.12+)

```python
from pathlib import Path
from collections.abc import Sequence  # Preferir collections.abc sobre typing

# ✅ Python 3.12: Usar | para Optional (Union)
def instalar_hook(
    repo_path: Path,
    hook_name: str,
    contenido: str | None = None  # En lugar de Optional[str]
) -> None:
    """Instala un hook."""
    pass

# ✅ Python 3.12: list, dict, tuple (minúsculas) en lugar de List, Dict, Tuple
def ejecutar_comando(
    comando: list[str],  # En lugar de List[str]
    env: dict[str, str] | None = None  # En lugar de Optional[Dict[str, str]]
) -> tuple[int, str, str]:  # En lugar de Tuple[int, str, str]
    """Retorna (código, stdout, stderr)."""
    pass

# ✅ Python 3.12: Type aliases con keyword 'type'
type HookName = str
type HookContent = str
type PathLike = Path | str

def procesar_hook(
    nombre: HookName,
    contenido: HookContent,
    ruta: PathLike
) -> bool:
    """Procesa un hook."""
    pass
```

#### Generics Modernos (PEP 695)

```python
# ❌ ANTIGUO (Python <3.12)
from typing import TypeVar, Generic

T = TypeVar('T')

class Container(Generic[T]):
    def __init__(self, valor: T) -> None:
        self.valor = valor

# ✅ MODERNO (Python 3.12+)
class Container[T]:
    def __init__(self, valor: T) -> None:
        self.valor = valor

# ✅ Funciones genéricas
def obtener_primero[T](items: list[T]) -> T | None:
    """Obtiene el primer elemento de una lista."""
    return items[0] if items else None
```

#### Override Decorator (PEP 698)

```python
from typing import override

class ValidadorBase:
    def validar(self, dato: str) -> bool:
        return True

class ValidadorCustom(ValidadorBase):
    @override  # Valida que estamos sobrescribiendo un método existente
    def validar(self, dato: str) -> bool:
        return len(dato) > 0
```

#### Collections.abc vs typing

```python
# ❌ DEPRECADO en Python 3.9+
from typing import List, Dict, Set, Tuple, Sequence, Iterable

# ✅ MODERNO (Python 3.12+)
from collections.abc import Sequence, Iterable, Mapping

def procesar_archivos(
    archivos: Sequence[Path],  # Acepta list, tuple, etc.
    opciones: Mapping[str, str]  # Acepta dict y otros mappings
) -> Iterable[str]:  # Retorna cualquier iterable
    """Procesa archivos."""
    pass

# Para tipos básicos, usar minúsculas built-in
def simple(
    nums: list[int],
    config: dict[str, bool],
    valores: set[str]
) -> tuple[int, int]:
    pass
```

#### Type Narrowing y Type Guards

```python
from typing import TypeGuard

def es_path(obj: object) -> TypeGuard[Path]:
    """Type guard para verificar si un objeto es Path."""
    return isinstance(obj, Path)

def procesar(entrada: str | Path) -> str:
    if es_path(entrada):
        # Aquí el type checker sabe que entrada es Path
        return str(entrada.resolve())
    else:
        # Aquí el type checker sabe que entrada es str
        return entrada
```

#### Type Hints para Callbacks

```python
from collections.abc import Callable

# ✅ MODERNO
type ValidadorCallback = Callable[[str], bool]
type ProcessorCallback = Callable[[Path, dict[str, str]], None]

def ejecutar_con_validacion(
    dato: str,
    validador: ValidadorCallback
) -> bool:
    """Ejecuta validación usando callback."""
    return validador(dato)
```

#### Literal Types para Constantes

```python
from typing import Literal

# Literal types para valores específicos
type Sistema = Literal["Linux", "Windows", "Darwin"]
type HookType = Literal["pre-commit", "pre-push", "post-commit", "pre-rebase"]

def detectar_sistema() -> Sistema:
    """Detecta el sistema operativo."""
    import platform
    return platform.system()  # type: ignore[return-value]

def validar_hook_name(name: str) -> HookType:
    """Valida el nombre del hook."""
    if name not in {"pre-commit", "pre-push", "post-commit", "pre-rebase"}:
        raise ValueError(f"Hook inválido: {name}")
    return name  # type: ignore[return-value]
```

#### Self Type para Method Chaining

```python
from typing import Self

class Builder:
    def __init__(self) -> None:
        self.config: dict[str, str] = {}

    def add_option(self, key: str, value: str) -> Self:
        """Añade una opción y retorna self para chaining."""
        self.config[key] = value
        return self

    def build(self) -> dict[str, str]:
        """Construye la configuración final."""
        return self.config

# Uso con method chaining
config = Builder().add_option("key1", "val1").add_option("key2", "val2").build()
```

#### Reglas para CI Guardian

1. **SIEMPRE usar built-in types en minúsculas**: `list`, `dict`, `set`, `tuple`
2. **SIEMPRE usar `|` en lugar de `Optional` o `Union`**
3. **SIEMPRE usar `type` keyword para type aliases**
4. **USAR `@override`** cuando sobrescribas métodos de clases base
5. **PREFERIR `collections.abc`** sobre `typing` para abstracciones (Sequence, Iterable, Mapping)
6. **USAR generics modernos** con sintaxis `[T]` directamente en la clase/función
7. **USAR `Literal`** para conjuntos fijos de valores
8. **USAR `Self`** para method chaining

### Docstrings

```python
def funcion_ejemplo(param1: str, param2: int) -> bool:
    """
    Descripción breve de la función.

    Explicación más detallada si es necesario. Puede ser de varias líneas
    y explicar el propósito de la función, algoritmos usados, etc.

    Args:
        param1: Descripción del parámetro 1
        param2: Descripción del parámetro 2

    Returns:
        True si la operación fue exitosa, False en caso contrario

    Raises:
        ValueError: Si param2 es negativo
        FileNotFoundError: Si el archivo no existe

    Example:
        >>> funcion_ejemplo("test", 5)
        True
    """
    pass
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

def funcion():
    logger.debug("Información de depuración")
    logger.info("Operación exitosa")
    logger.warning("Advertencia")
    logger.error("Error recuperable")
    logger.critical("Error crítico")
```

---

## 🚀 Workflow Completo: Ejemplo LIB-1

### 1. Preparación

```bash
# Activar venv
source venv/bin/activate

# Crear rama desde Linear
git checkout -b lib-1-implement-hook-installer-pre-commit-pre-push-post-commit
```

### 2. Fase RED (tdd-ci-guardian)

```
Prompt: "Voy a implementar LIB-1 (Hook installer). Usa el agente tdd-ci-guardian
para escribir todos los tests necesarios siguiendo TDD."

Agente escribe:
- tests/unit/test_installer.py (todos los tests)
- Ejecuta: pytest tests/unit/test_installer.py -v
- Resultado: TODOS FALLAN ❌ (esperado)
```

### 3. Commit RED

```bash
git add tests/unit/test_installer.py
git commit -m "test(core): add failing tests for hook installer

- Test git repository detection
- Test hook installation with permissions
- Test existing hook rejection
- Test hook name whitelist
- Test cross-platform support (Linux/Windows)"
```

### 4. Fase GREEN (ci-guardian-implementer)

```
Prompt: "Los tests están fallando. Usa el agente ci-guardian-implementer
para implementar el código mínimo que los haga pasar."

Agente implementa:
- src/ci_guardian/core/installer.py
- Ejecuta: pytest tests/unit/test_installer.py -v
- Resultado: TODOS PASAN ✅
```

### 5. Commit GREEN

```bash
git add src/ci_guardian/core/installer.py
git commit -m "feat(core): implement hook installer with cross-platform support

- Detect valid git repositories
- Install hooks with proper permissions (755 on Linux)
- Prevent overwriting existing hooks
- Whitelist validation for hook names
- Windows .bat script support"
```

### 6. Fase REFACTOR (opcional)

Si hay mejoras, refactorizar manteniendo tests verdes.

### 7. Security Audit

```
Prompt: "He terminado LIB-1. Usa el agente ci-guardian-security-auditor
para revisar la seguridad antes de crear el PR."

Agente audita:
- Command injection
- Path traversal
- Permisos de archivos
- Input validation
```

### 8. Crear PR

```bash
git push origin lib-1-implement-hook-installer-pre-commit-pre-push-post-commit

gh pr create --title "feat(core): implement hook installer (LIB-1)" \
  --body "$(cat <<'EOF'
## Why
Implements the core hook installer functionality, which is the foundation
of the CI Guardian system. Without this, no hooks can be installed.

## What
- Git repository detection
- Hook installation with proper permissions
- Cross-platform support (Linux/Windows)
- Hook name whitelist validation
- Prevention of overwriting existing hooks

## How
- Uses pathlib.Path for cross-platform path handling
- Validates git repository structure before operations
- Sets chmod 755 on Linux, creates .bat scripts on Windows
- Whitelist prevents installation of malicious hooks

## Testing
- ✅ All tests pass (pytest)
- ✅ Coverage: 95% on core/installer.py
- ✅ Security audit: No vulnerabilities found
- ✅ Tested on Linux and Windows (mocked)

## Related
- Closes LIB-1
EOF
)"
```

### 9. PR Review

```
Prompt: "He creado el PR #1 para LIB-1. Usa el agente pr-cop-reviewer
para hacer una revisión completa antes del merge."

Agente revisa:
- 10 categorías de calidad
- TDD compliance
- Seguridad
- Performance
- Veredicto: APPROVE/REQUEST CHANGES/BLOCK
```

### 10. Merge y CHANGELOG

```bash
# Después de approval
git checkout dev
git merge lib-1-implement-hook-installer-pre-commit-pre-push-post-commit
git push origin dev

# Actualizar CHANGELOG.md
## [Unreleased]
### Added
- Hook installer with cross-platform support (LIB-1)
```

---

## 📚 Recursos y Referencias

### Documentación de Herramientas

- **Ruff**: https://github.com/astral-sh/ruff (usar context7 para docs actuales)
- **Black**: https://github.com/psf/black
- **Bandit**: https://bandit.readthedocs.io/
- **Safety**: https://pypi.org/project/safety/
- **Click**: https://click.palletsprojects.com/ (usar context7 para APIs modernas)
- **Pytest**: https://docs.pytest.org/

### Estándares

- **Conventional Commits**: https://www.conventionalcommits.org/
- **Semantic Versioning**: https://semver.org/
- **PEP 8**: https://pep8.org/
- **Keep a Changelog**: https://keepachangelog.com/

### Seguridad

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **CWE**: https://cwe.mitre.org/
- **Python Security**: https://python.readthedocs.io/en/stable/library/security_warnings.html

---

## ✅ Checklist de Calidad

Antes de considerar completa una funcionalidad:

### Tests
- [ ] Todos los tests pasan
- [ ] Coverage ≥75% en el módulo
- [ ] Tests multiplataforma (Linux/Windows con skipif)
- [ ] Mocks para subprocess, filesystem, git
- [ ] Edge cases cubiertos
- [ ] Tests escritos ANTES de la implementación (TDD)

### Código
- [ ] Type hints completos
- [ ] Docstrings en español
- [ ] Black aplicado (line-length=100)
- [ ] Ruff pasa sin errores
- [ ] MyPy pasa (type checking)
- [ ] No hay hardcoded secrets

### Seguridad
- [ ] No usa shell=True con user input
- [ ] Paths validados (no path traversal)
- [ ] Permisos seguros (0o755, no 0o777)
- [ ] Tokens criptográficamente seguros (secrets.token_hex)
- [ ] Bandit pasa sin CRÍTICOS

### Git
- [ ] Commits siguen Conventional Commits
- [ ] Branch name desde Linear (lib-X-descripcion)
- [ ] Mensajes de commit descriptivos
- [ ] CHANGELOG actualizado

### Documentación
- [ ] README actualizado si cambia interfaz pública
- [ ] CLAUDE.md actualizado si cambia arquitectura
- [ ] Docstrings actualizados

---

## 🔄 Workflow de Commits y Releases

### Antes de Cada Commit

**IMPORTANTE**: Antes de crear cualquier commit, Claude Code debe verificar y actualizar la documentación relevante.

#### Checklist Pre-Commit Obligatorio

1. **Verificar cambios en interfaz pública**
   ```bash
   # Si modificaste CLI, core API, o funcionalidad pública
   git diff --cached | grep -E "(def |class |@click)"
   ```
   - Si hay cambios: Actualizar `README.md` con nuevos comandos/APIs
   - Actualizar ejemplos de uso si cambiaron
   - Actualizar badges si cambia versión o tests

2. **Verificar cambios en arquitectura**
   ```bash
   # Si añadiste/modificaste módulos, estructura, o patrones
   git diff --cached | grep -E "(^new file|^rename|^delete)"
   ```
   - Si hay cambios: Actualizar `CLAUDE.md` sección "Arquitectura del Proyecto"
   - Actualizar diagramas de estructura si aplicable
   - Actualizar orden de implementación si cambia

3. **Actualizar CHANGELOG.md**
   - SIEMPRE añadir entrada en sección `[Unreleased]`
   - Usar categorías: `Added`, `Changed`, `Fixed`, `Removed`, `Security`
   - Incluir referencia al issue de Linear (ej: `LIB-18`)

4. **Verificar docstrings**
   ```bash
   # Verificar que funciones nuevas/modificadas tienen docstrings
   ruff check --select D
   ```

#### Ejemplo de Workflow Pre-Commit

```bash
# 1. Claude Code termina implementación
# 2. ANTES de git add, revisar cambios:
git diff src/

# 3. Identificar si hay cambios en:
#    - CLI (cli.py) → Actualizar README.md sección "Uso"
#    - Core API (core/*.py) → Actualizar README.md sección "API"
#    - Arquitectura → Actualizar CLAUDE.md
#    - Hooks → Actualizar QUICKSTART.md

# 4. Actualizar documentación pertinente
vi README.md  # o CLAUDE.md, o ambos

# 5. Actualizar CHANGELOG.md
vi CHANGELOG.md
# Añadir en [Unreleased]:
# ### Added
# - Smoke tests in CI/CD pipeline before PyPI publish (LIB-18)

# 6. Ahora SÍ hacer commit incluyendo documentación
git add src/ README.md CHANGELOG.md
git commit -m "feat(ci): add smoke tests before PyPI publish

- Add smoke-test job in .github/workflows/publish.yml
- Tests install from wheel and validate full workflow
- Blocks publication if smoke tests fail
- Closes LIB-18"
```

### Antes de Cada Release

**CRÍTICO**: Antes de publicar a PyPI, SIEMPRE ejecutar smoke tests localmente.

#### Checklist Pre-Release Obligatorio

1. **Ejecutar smoke tests locales**
   ```bash
   # Build del paquete
   python -m build --clean

   # Crear venv limpio para smoke test
   python -m venv /tmp/release-smoke-test
   source /tmp/release-smoke-test/bin/activate

   # Instalar desde wheel (NO editable)
   pip install dist/ci_guardian-*.whl

   # Smoke tests básicos
   ci-guardian --version
   ci-guardian --help

   # Smoke test completo: crear repo y probar workflow
   cd /tmp
   git init smoke-repo
   cd smoke-repo
   git config user.name "Release Tester"
   git config user.email "release@test.com"

   # Instalar hooks
   ci-guardian install

   # Verificar 100% instalado
   ci-guardian status | grep "100%"

   # Test commit
   echo "print('release smoke test')" > test.py
   git add test.py
   git commit -m "test: release smoke test"

   echo "✅ Smoke tests pasados - Safe to release"
   ```

2. **Actualizar versión en pyproject.toml**
   ```toml
   [project]
   version = "0.1.2"  # Incrementar según semantic versioning
   ```

3. **Actualizar CHANGELOG.md**
   ```markdown
   ## [0.1.2] - 2025-11-02
   ### Added
   - Smoke tests in CI/CD pipeline (LIB-18)
   - Documentation update workflow (LIB-10)

   ### Fixed
   - Bug critical en pre-push hook (LIB-16)
   ```

4. **Crear tag y release**
   ```bash
   git tag -a v0.1.2 -m "Release v0.1.2: Smoke tests + Doc workflow"
   git push origin v0.1.2
   ```

5. **Workflow automático de CI/CD**
   - GitHub Actions detecta tag `v*`
   - Ejecuta job `build`
   - Ejecuta job `smoke-test` (GATE DE CALIDAD)
   - Solo si smoke tests pasan → `publish-pypi`
   - Publica a PyPI con Trusted Publisher

#### Por Qué Smoke Tests Son Críticos

**Problema real (Post-Mortem v0.1.0)**:
- Se publicó v0.1.0 a PyPI
- Bug crítico: `ModuleNotFoundError` en `pre-push` hook
- Usuarios instalaron paquete roto
- Se requirió hotfix urgente v0.1.1

**Root Cause**:
- NO se instaló el paquete desde `dist/` antes de publicar
- Solo se probó con `pip install -e .` (editable install)
- Bug solo aparecía en instalación real desde wheel

**Solución**:
- Smoke tests SIEMPRE instalan desde wheel (NO editable)
- Prueban workflow completo: install → commit → push
- Bloquean publicación si algo falla

---

## 🔄 Ciclo de Vida del Proyecto

```
1. Setup Inicial ✅
   - Estructura de directorios creada
   - pyproject.toml configurado
   - Venv con Python 3.12.12
   - Dependencias instaladas
   - Issues en Linear creados

2. Desarrollo (ACTUAL)
   → Implementar issues siguiendo TDD
   → Orden: LIB-1 → LIB-2 → LIB-4 → LIB-3 → LIB-8 → LIB-6 → LIB-5 → LIB-7

3. Testing & QA
   → Coverage ≥75%
   → Security audit completo
   → Tests en Linux y Windows

4. Documentation
   → README completo
   → Ejemplos de uso
   → API docs

5. Release
   → v0.1.0: Primera versión funcional
   → Publicación en PyPI
   → GitHub Release

6. Mantenimiento
   → Bug fixes
   → Nuevas features
   → Actualizaciones de dependencias
```

---

## 🎓 Aprendizajes y Decisiones

### Por qué Python 3.12
- Type hints mejorados
- Performance optimizations
- Pattern matching (match/case)
- Mejor error messages

### Por qué pathlib sobre os.path
- API más limpia y consistente
- Operadores intuitivos (/ para join)
- Multiplataforma automático
- Métodos convenientes (.exists(), .is_dir(), etc.)

### Por qué subprocess.run sobre os.system
- Más seguro (no shell=True)
- Control de timeout
- Captura de stdout/stderr
- Código de salida explícito

### Por qué sistema de tokens vs otros métodos
- Simple de implementar
- Difícil de bypassear
- No requiere modificar git internals
- Funciona en Linux y Windows

### Por qué TDD estricto
- Previene bugs desde el diseño
- Documentación viva (tests)
- Refactoring seguro
- Cobertura natural

---

## 🚨 Lessons Learned - Post-Mortems

Esta sección documenta bugs críticos que llegaron a producción, su análisis de causa raíz, y las reglas establecidas para prevenir su recurrencia.

### Post-Mortem #1: ModuleNotFoundError pre-push (v0.1.0 → v0.1.1)

**Fecha**: 2025-11-02
**Impacto**: CRÍTICO - Bug bloqueante en producción
**Severidad**: Los usuarios no podían hacer `git push` después de instalar ci-guardian

#### ¿Qué pasó?

La versión v0.1.0 se publicó a PyPI con un bug crítico:
- La documentación y el CLI prometían **4 hooks Git** (pre-commit, commit-msg, post-commit, **pre-push**)
- El módulo `src/ci_guardian/hooks/pre_push.py` **nunca se implementó**
- Cuando usuarios hacían `git push`, Git intentaba ejecutar el hook pre-push
- Resultado: `ModuleNotFoundError: No module named 'ci_guardian.hooks.pre_push'`
- Los usuarios no podían hacer push hasta desinstalar ci-guardian o remover el hook manualmente

#### ¿Por qué pasó? (Root Cause Analysis)

1. **Documentación desincronizada con implementación**:
   - `README.md` listaba 4 hooks sin verificar que existieran
   - La constante `HOOKS_ESPERADOS` en `cli.py` incluía `"pre-push"` hardcodeado
   - No había test que validara que cada hook en `HOOKS_ESPERADOS` tuviera un módulo correspondiente

2. **Tests con mocks excesivos**:
   - Tests de CLI mockeaban completamente la implementación del instalador
   - Tests nunca importaban los módulos reales de hooks
   - Mocks ocultaron que `pre_push.py` no existía

3. **Sin smoke tests post-build**:
   - Se probó el paquete con `pip install -e .` (editable install)
   - NO se instaló desde el wheel generado por `python -m build`
   - Bug solo aparecía en instalación real desde PyPI

4. **Documentación antes de implementación**:
   - Se actualizó README.md con features planificadas pero no implementadas
   - Violación del principio "Code First, Docs Second"

#### Prevención (OBLIGATORIO para futuros desarrollos)

##### ✅ **NUNCA documentar features no implementadas**

**Regla**: Si la documentación dice "4 hooks", el código debe instalar 4 hooks.

```python
# ❌ MAL - Documentar antes de implementar
# README.md dice "4 hooks: pre-commit, commit-msg, post-commit, pre-push"
# Pero solo existen 3 módulos

# ✅ BIEN - Documentar solo lo implementado
# README.md lista solo los hooks que realmente existen
# O agregar nota: "⚠️ pre-push hook en desarrollo (v0.2.0)"
```

**Checklist**:
- [ ] Si README dice "N features", código implementa N features
- [ ] Si falta implementar algo, NO actualizar docs hasta completar
- [ ] Usar badges "🚧 En desarrollo" para features parciales

##### ✅ **SIEMPRE validar constantes hardcodeadas**

**Regla**: Si hay una lista/diccionario con referencias a archivos/módulos, validar que existan.

```python
# ❌ MAL - Constante sin validación
HOOKS_ESPERADOS = ["pre-commit", "commit-msg", "post-commit", "pre-push"]
# Si falta pre_push.py, nadie se entera hasta producción

# ✅ BIEN - Test que valida la constante
def test_hooks_esperados_existen_como_modulos():
    """Valida que cada hook en HOOKS_ESPERADOS tiene módulo correspondiente."""
    for hook_name in HOOKS_ESPERADOS:
        module_name = hook_name.replace("-", "_")
        module_path = Path(__file__).parent.parent / "hooks" / f"{module_name}.py"
        assert module_path.exists(), f"Módulo {module_name}.py no existe para hook {hook_name}"
```

**Checklist**:
- [ ] Toda constante con nombres de archivos tiene test de existencia
- [ ] Toda constante con nombres de módulos tiene test de importación
- [ ] Tests fallan si constante referencia algo inexistente

##### ✅ **SIEMPRE ejecutar smoke tests pre-release**

**Regla**: Antes de publicar a PyPI, instalar desde `dist/` y probar workflow completo.

```bash
# ❌ MAL - Solo probar con editable install
pip install -e .
ci-guardian install

# ✅ BIEN - Smoke test desde wheel
python -m build --clean
python -m venv /tmp/smoke-test
source /tmp/smoke-test/bin/activate
pip install dist/ci_guardian-*.whl  # NO -e

# Probar workflow completo
git init test-repo
cd test-repo
ci-guardian install
echo "test" > file.txt
git add file.txt
git commit -m "test"  # Trigger pre-commit, commit-msg, post-commit
git push origin main  # Trigger pre-push (aquí falló v0.1.0)
```

**Checklist**:
- [ ] Build ejecutado (`python -m build`)
- [ ] Instalación desde wheel en venv limpio
- [ ] `ci-guardian --version` muestra versión correcta
- [ ] `ci-guardian install` funciona
- [ ] `git commit` funciona (pre-commit, commit-msg, post-commit)
- [ ] `git push` funciona (pre-push) - **CRÍTICO**

##### ✅ **MINIMIZAR mocks en tests críticos**

**Regla**: Tests de CLI deben usar implementaciones reales, NO mocks de toda la lógica.

```python
# ❌ MAL - Mockear todo
@patch('ci_guardian.cli.instalar_hooks')
def test_cli_install(mock_install):
    # Este test nunca importa módulos reales
    # No detecta ModuleNotFoundError
    pass

# ✅ BIEN - Mockear solo I/O externo
def test_cli_install_real(tmp_path):
    # Crear repo git real
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    # Ejecutar instalador REAL
    resultado = instalar_hooks(repo)

    # Verificar hooks existen
    assert (repo / ".git" / "hooks" / "pre-commit").exists()
    assert (repo / ".git" / "hooks" / "pre-push").exists()  # Fallaría en v0.1.0
```

**Checklist**:
- [ ] Tests de CLI usan implementación real del instalador
- [ ] Mockear solo subprocess, filesystem externo, git
- [ ] NO mockear lógica de negocio ni imports

#### Impacto y Mitigación

**Impacto**:
- 🔴 **Severidad**: CRÍTICO - Funcionalidad core bloqueada
- 🔴 **Usuarios afectados**: Todos los que instalaron v0.1.0
- 🔴 **Tiempo de exposición**: ~30 minutos (detección rápida gracias a smoke test manual post-publicación)

**Mitigación**:
1. **Inmediata** (30 min): Hotfix v0.1.1 publicado con fix
2. **Corto plazo** (2 horas): Issues creados (LIB-16 a LIB-21) para agregar smoke tests automáticos
3. **Largo plazo**: Esta documentación de lessons learned (LIB-22)

**Referencias**:
- Hotfix: [PR #16](https://github.com/jarkillo/ci-guardian/pull/16) (v0.1.1)
- Smoke tests CI/CD: [PR #17](https://github.com/jarkillo/ci-guardian/pull/17) (LIB-18)
- Issues relacionados: LIB-16, LIB-17, LIB-18, LIB-19, LIB-20, LIB-21

---

## 📋 Checklist Pre-Release (OBLIGATORIO)

**NUNCA publicar a PyPI sin completar TODOS estos pasos.**

Antes de ejecutar `twine upload dist/*` o crear release en GitHub:

### Tests

- [ ] **Todos los tests unitarios pasan**
  ```bash
  pytest tests/unit/ -v
  ```

- [ ] **Todos los tests de integración pasan**
  ```bash
  pytest tests/integration/ -v
  ```

- [ ] **Coverage ≥73%** (baseline actual del proyecto)
  ```bash
  pytest --cov=ci_guardian --cov-report=term-missing --cov-fail-under=73
  ```

- [ ] **No hay tests skipped críticos**
  ```bash
  pytest --strict-markers  # Falla si hay @pytest.mark.skip sin razón
  ```

- [ ] **Test de validación de módulos pasa** (LIB-16)
  ```bash
  pytest tests/unit/test_cli.py::test_hooks_esperados_existen_como_modulos -v
  ```

### Código

- [ ] **Black aplicado sin errores**
  ```bash
  black src/ tests/ --check --diff
  ```

- [ ] **Ruff pasa sin errores**
  ```bash
  ruff check src/ tests/
  ```

- [ ] **MyPy pasa type checking**
  ```bash
  mypy src/ --strict
  ```

- [ ] **Bandit no reporta issues CRÍTICOS**
  ```bash
  bandit -r src/ -ll  # Solo MEDIUM y HIGH
  ```

- [ ] **No hay TODOs críticos en el código**
  ```bash
  rg "TODO.*CRITICAL" src/  # Debe retornar vacío
  ```

### Smoke Tests (CRÍTICO ⚠️)

Este es el paso MÁS IMPORTANTE. El bug v0.1.0 pasó todos los tests pero falló en smoke test.

- [ ] **Build genera wheel sin errores**
  ```bash
  python -m build --clean
  ls -lh dist/  # Verificar que existe ci_guardian-*.whl
  ```

- [ ] **Instalación desde wheel funciona**
  ```bash
  python -m venv /tmp/release-smoke-test
  source /tmp/release-smoke-test/bin/activate
  pip install dist/ci_guardian-*.whl  # NO -e
  ```

- [ ] **CLI muestra versión correcta**
  ```bash
  ci-guardian --version  # Debe coincidir con pyproject.toml
  ```

- [ ] **CLI help funciona**
  ```bash
  ci-guardian --help
  ci-guardian install --help
  ci-guardian status --help
  ```

- [ ] **Instalación de hooks funciona**
  ```bash
  cd /tmp
  git init smoke-repo
  cd smoke-repo
  git config user.name "Test"
  git config user.email "test@test.com"
  ci-guardian install  # No debe fallar
  ```

- [ ] **Status muestra 100% hooks instalados**
  ```bash
  ci-guardian status | grep "100%"
  ```

- [ ] **git commit funciona sin ModuleNotFoundError**
  ```bash
  echo "print('test')" > test.py
  git add test.py
  git commit -m "test: smoke test"  # Trigger pre-commit, commit-msg, post-commit
  ```

- [ ] **git push funciona sin ModuleNotFoundError** ⚠️ **CRÍTICO**
  ```bash
  git init --bare /tmp/smoke-remote.git
  git remote add origin /tmp/smoke-remote.git
  git push origin HEAD  # Trigger pre-push - FALLÓ en v0.1.0
  ```

Si **CUALQUIER** smoke test falla, NO publicar. Investigar y fixear primero.

### Documentación

- [ ] **README.md actualizado** con nueva versión en badges
- [ ] **CHANGELOG.md actualizado** con cambios de la versión
  - Sección `[Unreleased]` movida a `[X.Y.Z] - YYYY-MM-DD`
  - Categorías: Added, Changed, Fixed, Removed, Security
- [ ] **Versión en pyproject.toml coincide con tag**
  ```bash
  grep "version =" pyproject.toml
  # version = "0.1.2"
  ```

- [ ] **Versión en __init__.py coincide**
  ```bash
  grep "__version__" src/ci_guardian/__init__.py
  # __version__ = "0.1.2"
  ```

- [ ] **Documentación NO promete features no implementadas**
  - Revisar README.md: toda feature listada existe en código
  - Revisar docstrings: toda API documentada está implementada

### GitHub

- [ ] **Todos los PRs mergeados a main**
  ```bash
  git checkout main
  git pull origin main
  # Verificar que main está actualizado
  ```

- [ ] **CI/CD pasa en main branch**
  - Verificar en GitHub Actions que último commit en main está verde

- [ ] **Tag de Git creado** con formato `vX.Y.Z`
  ```bash
  git tag -a v0.1.2 -m "Release v0.1.2: Brief description"
  git push origin v0.1.2
  ```

- [ ] **Release notes preparado en GitHub**
  - Ir a: https://github.com/USER/REPO/releases/new
  - Seleccionar tag v0.1.2
  - Copiar contenido de CHANGELOG.md para la versión
  - Publicar release

### Final Gate: CI/CD Smoke Tests

- [ ] **GitHub Actions smoke-test job pasa** (LIB-18)
  - Workflow automático ejecuta smoke tests en CI
  - Si falla, publicación a PyPI se bloquea automáticamente

### Publicación a PyPI

Solo después de que TODOS los checks pasen:

```bash
# TestPyPI primero (opcional pero recomendado)
twine upload --repository testpypi dist/*

# Verificar instalación desde TestPyPI
pip install --index-url https://test.pypi.org/simple/ ci-guardian

# Si todo funciona, publicar a PyPI
twine upload dist/*
```

---

**Fin de CLAUDE.md**

_Si tienes dudas sobre algún aspecto del proyecto, consulta esta documentación._
_Para empezar a desarrollar, sigue el Workflow Completo (sección correspondiente)._
