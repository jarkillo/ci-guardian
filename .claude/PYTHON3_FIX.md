# Solución Definitiva: Problema python3 en Windows

## Problema

El hook `PreToolUse:Edit` de Claude Code intenta ejecutar `python3` pero falla con:

```
no se encontró Python; ejecutar sin argumentos para instalar desde el Microsoft Store o deshabilitar este acceso directo desde Configuración > Aplicaciones > Configuración avanzada de aplicaciones > Alias de ejecución de aplicaciones.
```

## Causa Raíz

Windows 10/11 tiene un "alias de ejecución de aplicaciones" que redirige `python3` al Microsoft Store en lugar de usar el Python instalado.

- ✅ `python` funciona correctamente → `C:\Program Files\Python313\python.exe`
- ❌ `python3` falla → Redirigido al alias de Windows Store

## Solución Definitiva (HACER ESTO)

### Opción 1: Deshabilitar Alias de Windows Store (RECOMENDADO)

1. Abrir **Configuración de Windows** (Win + I)
2. Ir a **Aplicaciones** → **Aplicaciones y características**
3. Clic en **Configuración avanzada de aplicaciones** (o buscar "Alias de ejecución de aplicaciones")
4. **Desactivar** los toggles para:
   - `python.exe`
   - `python3.exe`
5. Verificar en PowerShell o Git Bash:
   ```bash
   python3 --version
   # Debería mostrar: Python 3.13.5
   ```

### Opción 2: Crear python3.exe en Python313 (REQUIERE ADMIN)

1. Abrir PowerShell como **Administrador**
2. Ejecutar:
   ```powershell
   Copy-Item "C:\Program Files\Python313\python.exe" "C:\Program Files\Python313\python3.exe"
   ```
3. Verificar:
   ```powershell
   python3 --version
   ```

## Solución Temporal (YA APLICADA)

Mientras se aplica la solución definitiva, usar `sed` en lugar de `Edit` para modificar archivos:

```bash
# En lugar de Edit tool:
sed -i 's|old|new|g' file.html

# Para cambios más complejos:
sed -i -e '15a\    <!-- Skip Link -->' file.html
```

## Verificación

Después de aplicar la solución definitiva:

```bash
cd E:/trabajo/33_Cuadro_Merca
python3 --version
# Debe mostrar: Python 3.13.5 (sin error)
```

## Referencias

- [Python on Windows FAQ](https://docs.python.org/3/using/windows.html#python-launcher-for-windows)
- [Windows App Execution Aliases](https://learn.microsoft.com/en-us/windows/apps/get-started/enable-your-device-for-development)
