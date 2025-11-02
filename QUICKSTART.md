# 🚀 Guía de Inicio Rápido - CI Guardian

Esta guía te muestra cómo usar CI Guardian en **tu proyecto** en 5 minutos.

---

## 📦 Paso 1: Instalar CI Guardian

### Opción A: Con entorno virtual (RECOMENDADO)

```bash
# Navega a tu proyecto
cd /ruta/a/tu/proyecto

# Crea un entorno virtual (solo la primera vez)
python -m venv venv

# Activa el entorno virtual
source venv/bin/activate  # En Linux/Mac
# O en Windows:
venv\Scripts\activate

# Instala CI Guardian
pip install ci-guardian

# Verifica la instalación
ci-guardian --version
# Debería mostrar: ci-guardian, version 0.1.0
```

### Opción B: Instalación global (NO recomendado)

```bash
pip install ci-guardian
```

---

## 📋 Paso 2: Verificar que tu proyecto es un repositorio Git

CI Guardian **REQUIERE** que tu proyecto sea un repositorio Git:

```bash
# Verifica si ya es un repo Git
git status

# Si dice "fatal: not a git repository", inicialízalo:
git init
git config user.name "Tu Nombre"
git config user.email "tu@email.com"
```

---

## ⚙️ Paso 3: Instalar los Hooks de Git

```bash
# Instalar todos los hooks
ci-guardian install

# Deberías ver:
# ✓ 4 hooks instalados exitosamente
```

### ¿Qué acaba de pasar?

CI Guardian instaló 4 hooks de Git en tu proyecto:

1. **pre-commit**: Se ejecuta ANTES de cada commit
   - Ejecuta Ruff (linter)
   - Ejecuta Black (formatter)
   - Ejecuta Bandit (security scanner)
   - Crea un token de seguridad

2. **commit-msg**: Se ejecuta AL ESCRIBIR el mensaje de commit
   - Valida que no haya "Co-Authored-By: Claude"
   - Valida que no haya atribuciones a Claude

3. **post-commit**: Se ejecuta DESPUÉS de cada commit
   - Valida que el token de seguridad exista
   - Si usaste `--no-verify`, REVIERTE el commit

4. **pre-push**: Se ejecuta ANTES de hacer push
   - Ejecuta tests (si tienes pytest)
   - Ejecuta GitHub Actions localmente (si tienes workflows)

---

## ✅ Paso 4: Verificar la Instalación

```bash
# Ver estado de los hooks
ci-guardian status

# Deberías ver:
# CI Guardian v0.1.0
#
# Estado de hooks:
#   ✓ pre-commit: instalado
#   ✓ commit-msg: instalado
#   ✓ post-commit: instalado
#   ✓ pre-push: instalado
#
# ✓ Todos los hooks están instalados (100%)
```

---

## 🎨 Paso 5: Hacer tu Primer Commit

Ahora cada vez que hagas commit, CI Guardian validará tu código automáticamente:

```bash
# Crea un archivo de prueba
echo "print('hello world')" > test.py

# Añade el archivo
git add test.py

# Intenta hacer commit
git commit -m "feat: add test file"

# CI Guardian ejecutará:
# 1. Ruff (linter) ✓
# 2. Black (formatter) ✓
# 3. Bandit (security) ✓
# 4. Validación de autoría ✓
#
# Si todo está bien, el commit se completará
# Si hay errores, el commit se rechazará y verás los errores
```

### Ejemplo de Commit Exitoso

```
$ git commit -m "feat: add test file"
Ejecutando pre-commit...
✓ Ruff: sin errores
✓ Black: formato correcto
✓ Bandit: sin vulnerabilidades
✓ Token generado
[main a1b2c3d] feat: add test file
 1 file changed, 1 insertion(+)
 create mode 100644 test.py
Ejecutando post-commit...
✓ Token validado
```

### Ejemplo de Commit con Errores

```
$ git commit -m "feat: add test file"
Ejecutando pre-commit...
❌ Ruff encontró 3 errores:

test.py:1:1: F401 'os' imported but unused
test.py:5:80: E501 line too long (95 > 88 characters)
test.py:10:1: W292 no newline at end of file

Commit rechazado. Arregla los errores y vuelve a intentar.
```

---

## 🔧 Paso 6 (Opcional): Configurar CI Guardian

Si quieres personalizar qué validaciones ejecutar:

```bash
# Crear archivo de configuración
ci-guardian configure

# Esto crea .ci-guardian.yaml
```

Edita `.ci-guardian.yaml` según tus necesidades:

```yaml
# .ci-guardian.yaml

ruff:
  enabled: true
  fail_on_error: true

black:
  enabled: true
  check_only: false  # false = autoformat, true = solo check

security:
  bandit: true
  safety: true
  block_on_critical: true

authorship:
  block_claude_coauthor: true
  allowed_coauthors: []

github_actions:
  enabled: false  # Cambia a true si tienes workflows
  use_act: true
  workflows:
    - ".github/workflows/test.yml"
```

---

## 🎯 Casos de Uso Comunes

### Caso 1: Proyecto Nuevo

```bash
# Crear proyecto
mkdir mi-proyecto
cd mi-proyecto

# Inicializar Git
git init
git config user.name "Tu Nombre"
git config user.email "tu@email.com"

# Crear venv e instalar CI Guardian
python -m venv venv
source venv/bin/activate
pip install ci-guardian

# Instalar hooks
ci-guardian install

# Crear archivo inicial
echo "# Mi Proyecto" > README.md
git add README.md
git commit -m "docs: add README"

# ¡Listo! Ya tienes CI Guardian funcionando
```

### Caso 2: Proyecto Existente

```bash
# Navegar a tu proyecto existente
cd /ruta/a/mi/proyecto/existente

# Asegúrate de tener un venv (recomendado)
python -m venv venv
source venv/bin/activate

# Instalar CI Guardian
pip install ci-guardian

# Instalar hooks
ci-guardian install

# Verificar
ci-guardian status

# ¡Listo! Próximo commit será validado
```

### Caso 3: Proyecto con Claude Code

```bash
# En tu proyecto con Claude Code
cd mi-proyecto-claude

# Activar venv
source venv/bin/activate

# Instalar CI Guardian
pip install ci-guardian

# Instalar hooks
ci-guardian install

# Ahora Claude Code NO podrá:
# ❌ Saltarse validaciones con --no-verify
# ❌ Añadirse como co-autor en commits
# ❌ Hacer commits con código sin formatear
# ❌ Hacer commits con vulnerabilidades críticas

# Pero SÍ podrá:
# ✅ Ayudarte a arreglar errores de Ruff
# ✅ Ayudarte a formatear con Black
# ✅ Ayudarte a resolver problemas de seguridad
# ✅ Escribir código de calidad desde el inicio
```

---

## 🛠️ Comandos Útiles

### Ver Estado de Hooks

```bash
ci-guardian status

# Muestra:
# - Versión de CI Guardian
# - Qué hooks están instalados
# - Porcentaje de cobertura
```

### Ejecutar Validación Manual

```bash
ci-guardian check

# Ejecuta las validaciones sin hacer commit:
# - Ruff sobre todos los archivos .py
# - Black sobre todos los archivos .py
# - Útil para verificar antes de commit
```

### Desinstalar Hooks

```bash
ci-guardian uninstall

# Elimina todos los hooks de CI Guardian
# Tu proyecto vuelve a su estado original
# (Útil si quieres probar sin hooks temporalmente)
```

### Reinstalar Hooks

```bash
# Si actualizaste CI Guardian o cambiaste configuración:
ci-guardian uninstall
ci-guardian install

# O más rápido:
ci-guardian install --force  # (Sobrescribe hooks existentes)
```

---

## ❓ Preguntas Frecuentes

### ¿Necesito tener Ruff y Black instalados?

No. CI Guardian los incluye como dependencias. Cuando instalas `ci-guardian`, también instalas `ruff`, `black`, `bandit` y `safety`.

### ¿Funciona en Windows?

Sí. CI Guardian detecta automáticamente tu sistema operativo y crea los hooks apropiados:
- Linux/Mac: Scripts bash (`#!/bin/bash`)
- Windows: Scripts batch (`.bat`)

### ¿Qué pasa si uso `git commit --no-verify`?

El hook **post-commit** detectará que no hay token de validación y **revertirá automáticamente el commit**. Verás un mensaje de error explicando qué pasó.

### ¿Puedo desactivar alguna validación?

Sí. Edita `.ci-guardian.yaml` y cambia `enabled: true` a `enabled: false` para cualquier validación que quieras desactivar.

### ¿CI Guardian funciona con pre-commit framework?

Sí, son compatibles. Puedes usar ambos simultáneamente. CI Guardian se enfoca en validaciones específicas para proyectos con Claude Code.

### ¿Afecta el rendimiento de mis commits?

Los hooks añaden ~2-5 segundos por commit dependiendo del tamaño de tu proyecto:
- Ruff: ~0.5s (muy rápido)
- Black: ~1s
- Bandit: ~1-2s
- Safety: ~1-2s (solo si tienes requirements.txt)

### ¿Qué hago si un commit es rechazado?

1. Lee el mensaje de error (te dirá qué falló)
2. Arregla los errores indicados
3. Vuelve a hacer `git add` y `git commit`

Ejemplo:
```bash
# Commit rechazado por Ruff
$ git commit -m "feat: add feature"
❌ Ruff: línea 10 demasiado larga

# Arreglar el archivo
# Volver a intentar
$ git add archivo.py
$ git commit -m "feat: add feature"
✅ Commit exitoso
```

---

## 🎓 Próximos Pasos

Ahora que tienes CI Guardian instalado:

1. **Lee la configuración avanzada**: [README.md](README.md)
2. **Personaliza las validaciones**: Edita `.ci-guardian.yaml`
3. **Integra con tu CI/CD**: CI Guardian complementa tus pipelines de GitHub Actions
4. **Aprende sobre el sistema anti-bypass**: [CLAUDE.md](CLAUDE.md#sistema-anti-bypass)

---

## 🆘 ¿Necesitas Ayuda?

- **Issues**: https://github.com/jarkillo/ci-guardian/issues
- **Documentación completa**: [README.md](README.md)
- **Documentación interna**: [CLAUDE.md](CLAUDE.md)

---

**¡Disfruta de tu código con calidad garantizada!** 🎉
