# Guía de Publicación en PyPI

Esta guía explica cómo publicar CI Guardian en PyPI (Python Package Index).

## Prerrequisitos

1. **Cuenta en TestPyPI** (para pruebas):
   - Registrarse en: https://test.pypi.org/account/register/
   - Crear API token: https://test.pypi.org/manage/account/token/
   - Alcance del token: "Entire account (all projects)"

2. **Cuenta en PyPI** (para producción):
   - Registrarse en: https://pypi.org/account/register/
   - Crear API token: https://pypi.org/manage/account/token/
   - Alcance del token: "Entire account (all projects)"

3. **Configurar credenciales**:
   ```bash
   # Copiar plantilla
   cp .pypirc.example ~/.pypirc

   # Editar y añadir tus API tokens
   nano ~/.pypirc

   # Proteger el archivo
   chmod 600 ~/.pypirc
   ```

## Proceso de Publicación

### 1. Publicar en TestPyPI (Prueba)

```bash
# Activar venv
source venv/bin/activate

# Publicar
./scripts/publish.sh test
```

Esto hará:
- ✅ Verificar que estás en rama `main`
- ✅ Verificar que no hay cambios sin commitear
- ✅ Limpiar builds anteriores
- ✅ Construir paquetes (wheel + tar.gz)
- ✅ Validar con `twine check`
- ✅ Subir a TestPyPI

**Resultado**: https://test.pypi.org/project/ci-guardian/

### 2. Probar Instalación desde TestPyPI

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

### 3. Publicar en PyPI Oficial

⚠️ **IMPORTANTE**: Esta acción NO se puede deshacer. Solo puedes publicar una vez por versión.

```bash
# Activar venv
source venv/bin/activate

# Publicar (pedirá confirmación)
./scripts/publish.sh prod
```

**Resultado**: https://pypi.org/project/ci-guardian/

### 4. Verificar Instalación

```bash
# Crear venv temporal
python -m venv /tmp/test-ci-guardian-prod
source /tmp/test-ci-guardian-prod/bin/activate

# Instalar desde PyPI
pip install ci-guardian

# Probar
ci-guardian --version
cd /tmp/test-project
ci-guardian install

# Limpiar
deactivate
rm -rf /tmp/test-ci-guardian-prod
```

## Publicación Manual (sin script)

Si prefieres hacerlo manualmente:

```bash
# 1. Limpiar
rm -rf dist/ build/ src/*.egg-info

# 2. Build
python -m build

# 3. Validar
twine check dist/*

# 4. Publicar en TestPyPI
twine upload --repository testpypi dist/*

# 5. Publicar en PyPI
twine upload --repository pypi dist/*
```

## Troubleshooting

### Error: "File already exists"

Cada versión solo puede publicarse UNA vez. Para republicar:
1. Actualiza el número de versión en `pyproject.toml`
2. Commitea el cambio
3. Crea un nuevo tag: `git tag v0.X.Y`
4. Publica de nuevo

### Error: "Invalid credentials"

Verifica:
- Que `~/.pypirc` existe y tiene los tokens correctos
- Que el formato es correcto (ver `.pypirc.example`)
- Que los tokens no han expirado

### Error: "HTTPError: 403 Forbidden"

Tu token no tiene permisos. Crea un nuevo token con alcance "Entire account".

## Checklist Pre-Publicación

Antes de publicar a PyPI oficial:

- [ ] Todos los tests pasan (`pytest`)
- [ ] Coverage ≥72% (`pytest --cov`)
- [ ] README actualizado
- [ ] CHANGELOG actualizado
- [ ] Versión actualizada en `pyproject.toml`
- [ ] Tag de Git creado (`git tag v0.X.Y`)
- [ ] Build exitoso (`python -m build`)
- [ ] Validación exitosa (`twine check dist/*`)
- [ ] Probado en TestPyPI
- [ ] Instalación desde TestPyPI funciona

## Versiones y Tags

Seguimos Semantic Versioning (semver.org):
- **Major** (X.0.0): Cambios incompatibles
- **Minor** (0.X.0): Nueva funcionalidad compatible
- **Patch** (0.0.X): Bug fixes

Ejemplo:
```bash
# Actualizar versión en pyproject.toml
# version = "0.2.0"

# Commitear
git add pyproject.toml
git commit -m "build: bump version to 0.2.0"

# Crear tag
git tag v0.2.0
git push origin main --tags

# Publicar
./scripts/publish.sh prod
```

## Referencias

- PyPI: https://pypi.org
- TestPyPI: https://test.pypi.org
- Packaging Guide: https://packaging.python.org/
- Twine Docs: https://twine.readthedocs.io/
- Semantic Versioning: https://semver.org/
