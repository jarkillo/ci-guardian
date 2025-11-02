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
