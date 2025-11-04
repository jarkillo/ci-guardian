# Configuración de Trusted Publisher para PyPI

Esta guía te ayudará a configurar la publicación automática en PyPI usando OpenID Connect (Trusted Publisher), el método moderno y seguro que **no requiere API tokens manuales**.

## 🔐 ¿Qué es Trusted Publisher?

Es un sistema de autenticación basado en OpenID Connect que permite a GitHub Actions publicar en PyPI sin necesidad de manejar tokens de API manualmente. GitHub verifica la identidad del workflow y PyPI confía en esa verificación.

**Ventajas**:
- ✅ No hay tokens que puedan filtrarse
- ✅ Permisos granulares por repositorio
- ✅ Automático desde GitHub Actions
- ✅ Más seguro que API tokens

---

## 📋 Paso 1: Configurar Trusted Publisher en TestPyPI

Primero configuramos TestPyPI para pruebas:

### 1.1. Crear cuenta en TestPyPI

1. Ve a: https://test.pypi.org/account/register/
2. Completa el registro
3. Verifica tu email

### 1.2. Configurar Trusted Publisher

1. Ve a: https://test.pypi.org/manage/account/publishing/
2. Haz clic en **"Add a new pending publisher"**
3. Completa el formulario:

```
PyPI Project Name: ci-guardian
Owner: jarkillo
Repository name: ci-guardian
Workflow name: publish.yml
Environment name: testpypi
```

4. Haz clic en **"Add"**

**⚠️ IMPORTANTE**: El proyecto `ci-guardian` NO necesita existir previamente en TestPyPI. Se creará automáticamente en la primera publicación.

---

## 📋 Paso 2: Configurar Environment en GitHub

GitHub Actions necesita un "environment" para usar Trusted Publishing:

### 2.1. Crear environment 'testpypi'

1. Ve a tu repositorio en GitHub: https://github.com/jarkillo/ci-guardian
2. Ve a **Settings** → **Environments**
3. Haz clic en **"New environment"**
4. Nombre: `testpypi`
5. (Opcional) Configura protecciones:
   - **Required reviewers**: Añade tu usuario si quieres aprobación manual
   - **Wait timer**: 0 minutos
   - **Deployment branches**: `Selected branches` → `main`

6. Haz clic en **"Configure environment"**

### 2.2. Crear environment 'pypi'

Repite el proceso para el environment de producción:

1. Nombre: `pypi`
2. **RECOMENDADO**: Configura protecciones:
   - **Required reviewers**: Añade tu usuario (seguridad extra)
   - **Deployment branches**: `Selected branches` → `main`

---

## 📋 Paso 3: Probar Publicación en TestPyPI

### 3.1. Ejecutar workflow manualmente

1. Ve a: https://github.com/jarkillo/ci-guardian/actions
2. Selecciona el workflow **"Publish to PyPI"**
3. Haz clic en **"Run workflow"**
4. Selecciona:
   - Branch: `main`
   - Environment: `testpypi`
5. Haz clic en **"Run workflow"**

### 3.2. Monitorear ejecución

El workflow hará:
1. ✅ Build de los paquetes (wheel + tarball)
2. ✅ Validación con `twine check`
3. ✅ Publicación en TestPyPI
4. ✅ Verificación de instalación

### 3.3. Verificar publicación

Una vez completado:
1. Ve a: https://test.pypi.org/project/ci-guardian/
2. Deberías ver tu paquete publicado

### 3.4. Probar instalación local

```bash
# Crear venv temporal
python -m venv /tmp/test-ci-guardian
source /tmp/test-ci-guardian/bin/activate

# Instalar desde TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            ci-guardian

# Probar que funciona
ci-guardian --version
ci-guardian --help

# Limpiar
deactivate
rm -rf /tmp/test-ci-guardian
```

---

## 📋 Paso 4: Configurar Trusted Publisher en PyPI Oficial

Una vez verificado que funciona en TestPyPI:

### 4.1. Crear cuenta en PyPI

1. Ve a: https://pypi.org/account/register/
2. Completa el registro
3. Verifica tu email
4. **IMPORTANTE**: Habilita 2FA (Two-Factor Authentication)

### 4.2. Configurar Trusted Publisher

1. Ve a: https://pypi.org/manage/account/publishing/
2. Haz clic en **"Add a new pending publisher"**
3. Completa el formulario:

```
PyPI Project Name: ci-guardian
Owner: jarkillo
Repository name: ci-guardian
Workflow name: publish.yml
Environment name: pypi
```

4. Haz clic en **"Add"**

---

## 📋 Paso 5: Publicar en PyPI Oficial

### 5.1. Opción A: Workflow Dispatch (Manual)

1. Ve a: https://github.com/jarkillo/ci-guardian/actions
2. Selecciona **"Publish to PyPI"**
3. Haz clic en **"Run workflow"**
4. Selecciona:
   - Branch: `main`
   - Environment: `pypi`
5. Haz clic en **"Run workflow"**
6. Si configuraste "Required reviewers", aprueba el deployment

### 5.2. Opción B: Release Automático (Recomendado)

El workflow se ejecuta automáticamente cuando creas un release:

```bash
# 1. Asegúrate de estar en main con la versión correcta
git checkout main
git pull

# 2. Verifica la versión en pyproject.toml
grep "version =" pyproject.toml
# Should show: version = "0.1.0"

# 3. Crear tag
git tag v0.1.0
git push origin v0.1.0

# 4. Crear release en GitHub
gh release create v0.1.0 \
  --title "v0.1.0 - Initial Release" \
  --notes "$(cat <<'EOF'
## 🎉 First Release of CI Guardian

### Features
- ✅ Hook installer (pre-commit, commit-msg, post-commit, pre-push)
- ✅ Virtual environment management (Linux/Windows)
- ✅ Anti --no-verify validator (token system)
- ✅ Code quality (Ruff + Black)
- ✅ Security audit (Bandit + Safety)
- ✅ Authorship validator (blocks Claude attribution)
- ✅ CLI interface
- ✅ Cross-platform support

### Installation
pip install ci-guardian

### Quick Start
cd your-project
ci-guardian install

See README for full documentation.
EOF
)"
```

El workflow se ejecutará automáticamente y publicará en PyPI.

---

## 🔍 Verificar Publicación

### 6.1. Verificar en PyPI

1. Ve a: https://pypi.org/project/ci-guardian/
2. Deberías ver tu paquete publicado

### 6.2. Probar instalación

```bash
# Crear venv temporal
python -m venv /tmp/test-ci-guardian-prod
source /tmp/test-ci-guardian-prod/bin/activate

# Instalar desde PyPI
pip install ci-guardian

# Probar
ci-guardian --version
cd /tmp
mkdir test-project
cd test-project
git init
git config user.name "Test"
git config user.email "test@test.com"
ci-guardian install

# Limpiar
deactivate
rm -rf /tmp/test-ci-guardian-prod /tmp/test-project
```

---

## 📊 Resumen de Configuración

### TestPyPI
- URL: https://test.pypi.org/manage/account/publishing/
- Project: `ci-guardian`
- Owner: `jarkillo`
- Repository: `ci-guardian`
- Workflow: `publish.yml`
- Environment: `testpypi`

### PyPI
- URL: https://pypi.org/manage/account/publishing/
- Project: `ci-guardian`
- Owner: `jarkillo`
- Repository: `ci-guardian`
- Workflow: `publish.yml`
- Environment: `pypi`

### GitHub Environments
- `testpypi`: Para publicación de prueba
- `pypi`: Para publicación oficial (con protecciones)

---

## 🚨 Troubleshooting

### Error: "Trusted publisher is not configured"

**Causa**: No has configurado el Trusted Publisher en PyPI.

**Solución**: Sigue el Paso 1 o Paso 4 según corresponda.

### Error: "Environment protection rules not satisfied"

**Causa**: Configuraste "Required reviewers" pero no has aprobado el deployment.

**Solución**:
1. Ve a: https://github.com/jarkillo/ci-guardian/actions
2. Selecciona el workflow run
3. Haz clic en **"Review deployments"**
4. Selecciona el environment y haz clic en **"Approve and deploy"**

### Error: "Workflow file not found"

**Causa**: El workflow `publish.yml` no existe en la rama main.

**Solución**: Asegúrate de hacer merge del PR #14 primero.

### Error: "Project name already exists"

**Causa**: El nombre `ci-guardian` ya está tomado en PyPI.

**Solución**:
- En TestPyPI: Prueba con `ci-guardian-test` o `ci-guardian-yourname`
- En PyPI: Si el nombre está tomado, deberás elegir otro nombre único

### El paquete no se instala después de publicar

**Causa**: PyPI puede tardar unos segundos en propagar los cambios.

**Solución**: Espera 1-2 minutos y vuelve a intentar.

---

## 📚 Referencias

- **PyPI Trusted Publishers**: https://docs.pypi.org/trusted-publishers/
- **GitHub Actions OpenID Connect**: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect
- **pypa/gh-action-pypi-publish**: https://github.com/pypa/gh-action-pypi-publish
- **GitHub Environments**: https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment

---

## ✅ Checklist

Antes de publicar en PyPI oficial:

- [ ] Cuenta en TestPyPI creada y verificada
- [ ] Trusted Publisher configurado en TestPyPI
- [ ] Environment `testpypi` creado en GitHub
- [ ] Publicación en TestPyPI exitosa
- [ ] Instalación desde TestPyPI verificada
- [ ] Cuenta en PyPI creada y verificada
- [ ] 2FA habilitado en PyPI
- [ ] Trusted Publisher configurado en PyPI
- [ ] Environment `pypi` creado en GitHub
- [ ] Environment `pypi` tiene protecciones configuradas
- [ ] Todos los tests pasan
- [ ] Coverage ≥75%
- [ ] README actualizado
- [ ] CHANGELOG actualizado
- [ ] Versión correcta en pyproject.toml
- [ ] Tag de Git creado
