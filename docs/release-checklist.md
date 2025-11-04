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
