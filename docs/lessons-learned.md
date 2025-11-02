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
