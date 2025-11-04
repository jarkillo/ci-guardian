"""
CLI (Command Line Interface) para CI Guardian.

Este módulo proporciona la interfaz de línea de comandos principal
usando Click framework.
"""

from __future__ import annotations

import platform
import sys
from pathlib import Path

import click
import colorama

from ci_guardian import __version__
from ci_guardian.core.installer import (
    desinstalar_hook,
    es_repositorio_git,
    instalar_hook,
    obtener_hooks_instalados,
)
from ci_guardian.validators.code_quality import ejecutar_black, ejecutar_ruff

# Hooks que debe gestionar CI Guardian
HOOKS_ESPERADOS = ["pre-commit", "commit-msg", "post-commit", "pre-push"]


def _obtener_repo_path(repo: str) -> Path:
    """
    Obtiene y valida el path del repositorio.

    Args:
        repo: Path al repositorio (string)

    Returns:
        Path resuelto y validado

    Raises:
        ValueError: Si se detecta path traversal o no es repo git
    """
    # Validar path traversal usando función centralizada
    from ci_guardian.validators.common import validar_path_seguro

    validar_path_seguro(repo, "repositorio")

    # Resolver path
    repo_path = Path.cwd() if repo == "." else Path(repo).resolve()

    # Validar que sea repo git
    if not es_repositorio_git(repo_path):
        raise ValueError(f"El directorio {repo_path} no es un repositorio Git válido")

    return repo_path


def _validar_hook_existe(hook_name: str) -> None:
    """
    Valida que el módulo del hook exista antes de instalar.

    Esta función previene el bug de v0.1.0 donde hooks rotos se instalaban
    porque no se validaba la existencia del módulo Python correspondiente.

    Args:
        hook_name: Nombre del hook (pre-commit, pre-push, etc.)

    Raises:
        ValueError: Si el módulo del hook no existe
    """
    from importlib import import_module

    modulo_nombre = hook_name.replace("-", "_")
    modulo_path = f"ci_guardian.hooks.{modulo_nombre}"

    try:
        import_module(modulo_path)
    except ModuleNotFoundError as e:
        raise ValueError(
            f"No se puede instalar el hook '{hook_name}': "
            f"el módulo '{modulo_path}' no existe.\n"
            f"Esto es un bug de CI Guardian. Por favor reporta en: "
            f"https://github.com/jarkillo/ci-guardian/issues"
        ) from e


def _obtener_contenido_hook(hook_name: str) -> str:
    """
    Genera el contenido de un hook de CI Guardian.

    Crea un script que:
    1. Intenta activar el venv local del proyecto si existe
    2. Si no hay venv local, usa el Python que ejecutó ci-guardian install
    3. Ejecuta el hook Python como módulo

    Args:
        hook_name: Nombre del hook (pre-commit, pre-push, post-commit)

    Returns:
        Contenido del hook con shebang y marca CI-GUARDIAN-HOOK
    """
    # Convertir nombre de hook de kebab-case a snake_case para módulo Python
    # pre-commit → pre_commit
    modulo_nombre = hook_name.replace("-", "_")

    # Obtener ruta al Python actual (el que tiene ci_guardian instalado)
    python_ejecutable = sys.executable

    # En Windows, usar batch script
    if platform.system() == "Windows":
        return f"""@echo off
REM CI-GUARDIAN-HOOK
REM {hook_name} hook instalado por CI Guardian v{__version__}

REM Activar venv local si existe
if exist "venv\\Scripts\\activate.bat" (
    call venv\\Scripts\\activate.bat
) else if exist ".venv\\Scripts\\activate.bat" (
    call .venv\\Scripts\\activate.bat
) else if exist "env\\Scripts\\activate.bat" (
    call env\\Scripts\\activate.bat
) else if exist ".env\\Scripts\\activate.bat" (
    call .env\\Scripts\\activate.bat
)

REM Ejecutar hook usando el Python que instaló CI Guardian
"{python_ejecutable}" -m ci_guardian.hooks.{modulo_nombre} %*
exit /b %ERRORLEVEL%
"""

    # En Linux/macOS, usar bash script
    return f"""#!/bin/bash
# CI-GUARDIAN-HOOK
# {hook_name} hook instalado por CI Guardian v{__version__}

# Activar venv local si existe
if [ -d "venv/bin" ]; then
    source venv/bin/activate
elif [ -d ".venv/bin" ]; then
    source .venv/bin/activate
elif [ -d "env/bin" ]; then
    source env/bin/activate
elif [ -d ".env/bin" ]; then
    source .env/bin/activate
fi

# Ejecutar hook usando el Python que instaló CI Guardian
"{python_ejecutable}" -m ci_guardian.hooks.{modulo_nombre} "$@"
exit $?
"""


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """CI Guardian - Git hooks automation."""
    # Inicializar colorama en Windows para soporte de colores
    if platform.system() == "Windows":
        colorama.init()


@main.command()
@click.option("--repo", default=".", help="Ruta al repositorio Git (default: directorio actual)")
@click.option("--force", is_flag=True, help="Forzar reinstalación de hooks existentes")
def install(repo: str, force: bool) -> None:
    """
    Instala los hooks de CI Guardian en el repositorio.

    Instala pre-commit, pre-push y post-commit hooks.
    """
    try:
        # Obtener y validar repo path
        repo_path = _obtener_repo_path(repo)

        # Si force está activo, eliminar hooks existentes primero (CI Guardian o no)
        if force:
            click.echo("Instalación forzada: eliminando hooks existentes...")
            hooks_dir = repo_path / ".git" / "hooks"
            for hook_name in HOOKS_ESPERADOS:
                # Eliminar hook directamente, sea de CI Guardian o de terceros
                hook_path = hooks_dir / hook_name
                if hook_path.exists():
                    try:
                        hook_path.unlink()
                        click.echo(f"  ✓ Eliminado: {hook_name}")
                    except OSError as e:
                        click.echo(f"  ⚠️  No se pudo eliminar {hook_name}: {e}", err=True)
                        # Continuar con los demás hooks

        # Instalar cada hook
        hooks_instalados = 0
        for hook_name in HOOKS_ESPERADOS:
            # Validar que el módulo del hook existe ANTES de instalar
            _validar_hook_existe(hook_name)

            contenido = _obtener_contenido_hook(hook_name)
            try:
                instalar_hook(repo_path, hook_name, contenido)
                hooks_instalados += 1
            except FileExistsError:
                click.echo(
                    f"Error: El hook {hook_name} ya existe. Usa --force para sobrescribir.",
                    err=True,
                )
                sys.exit(1)

        # Mensaje de éxito
        mensaje = f"✓ {hooks_instalados} hooks instalados exitosamente"
        if force:
            mensaje += " (instalación forzada)"

        click.echo(mensaje)
        sys.exit(0)

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error inesperado: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--repo", default=".", help="Ruta al repositorio Git (default: directorio actual)")
@click.option("--yes", "-y", is_flag=True, help="Desinstalar sin confirmación")
def uninstall(repo: str, yes: bool) -> None:
    """
    Desinstala los hooks de CI Guardian del repositorio.

    Por defecto pide confirmación, usa --yes para omitirla.
    """
    try:
        # Obtener y validar repo path
        repo_path = _obtener_repo_path(repo)

        # Pedir confirmación si no se usó --yes
        if not yes and not click.confirm("¿Deseas desinstalar los hooks de CI Guardian?"):
            click.echo("Operación cancelado.")
            sys.exit(0)

        # Desinstalar cada hook
        hooks_desinstalados = 0
        for hook_name in HOOKS_ESPERADOS:
            try:
                if desinstalar_hook(repo_path, hook_name):
                    hooks_desinstalados += 1
            except ValueError as e:
                # Hook existe pero no es de CI Guardian
                click.echo(f"Error: {e}", err=True)
                sys.exit(1)

        # Mensaje según resultado
        if hooks_desinstalados == 0:
            click.echo("No hay hooks de CI Guardian instalados.")
        else:
            click.echo(f"✓ {hooks_desinstalados} hooks desinstalados exitosamente.")

        sys.exit(0)

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error inesperado: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--repo", default=".", help="Ruta al repositorio Git (default: directorio actual)")
def status(repo: str) -> None:
    """
    Muestra el estado de los hooks de CI Guardian.

    Lista qué hooks están instalados y cuáles faltan.
    """
    try:
        # Obtener y validar repo path
        repo_path = _obtener_repo_path(repo)

        # Obtener hooks instalados
        hooks_instalados = obtener_hooks_instalados(repo_path)

        # Mostrar versión
        click.echo(f"CI Guardian v{__version__}")
        click.echo("")

        # Mostrar estado de cada hook
        click.echo("Estado de hooks:")
        todos_instalados = True
        for hook_name in HOOKS_ESPERADOS:
            if hook_name in hooks_instalados:
                click.echo(f"  ✓ {hook_name}: instalado")
            else:
                click.echo(f"  ✗ {hook_name}: faltante")
                todos_instalados = False

        click.echo("")

        # Mensaje según estado
        if len(hooks_instalados) == 0:
            click.echo("No hay hooks instalados. Ejecuta 'ci-guardian install' para instalarlos.")
        elif todos_instalados:
            click.echo("✓ Todos los hooks están instalados (100%)")
        else:
            porcentaje = (len(hooks_instalados) / len(HOOKS_ESPERADOS)) * 100
            click.echo(
                f"Instalados: {len(hooks_instalados)}/{len(HOOKS_ESPERADOS)} ({porcentaje:.0f}%)"
            )

        sys.exit(0)

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error inesperado: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--repo", default=".", help="Ruta al repositorio Git (default: directorio actual)")
def check(repo: str) -> None:
    """
    Ejecuta validaciones de calidad de código (Ruff y Black).

    Busca archivos Python en el proyecto y los valida.
    """
    try:
        # Obtener y validar repo path (verifica que sea repo git)
        repo_path = _obtener_repo_path(repo)

        # Buscar archivos Python recursivamente
        archivos_encontrados = list(repo_path.rglob("**/*.py"))

        # Filtrar archivos del proyecto (excluir venv, .git, etc.) usando función centralizada
        from ci_guardian.validators.file_utils import filtrar_archivos_python_seguros

        archivos = filtrar_archivos_python_seguros(
            archivos_encontrados, repo_path=repo_path, validar_existencia=False
        )

        # Verificar si hay archivos
        if not archivos:
            click.echo("No hay archivos Python para validar.")
            sys.exit(0)

        click.echo(f"Validando {len(archivos)} archivos Python...")

        # Ejecutar Ruff
        click.echo("\n1. Ejecutando Ruff (linter)...")
        try:
            ruff_ok, ruff_msg = ejecutar_ruff(archivos)
            if ruff_ok:
                click.echo(f"   ✓ {ruff_msg}")
            else:
                click.echo(f"   ✗ {ruff_msg}", err=True)
                sys.exit(1)
        except ValueError as e:
            # Path traversal detectado por ejecutar_ruff
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

        # Ejecutar Black
        click.echo("\n2. Ejecutando Black (formatter)...")
        try:
            black_ok, black_msg = ejecutar_black(archivos, check=True)
            if black_ok:
                click.echo(f"   ✓ {black_msg}")
            else:
                click.echo(f"   ✗ {black_msg}", err=True)
                sys.exit(1)
        except ValueError as e:
            # Path traversal detectado por ejecutar_black
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

        # Si llegamos aquí, todo pasó
        click.echo("\n✓ Validaciones completadas sin errores")
        sys.exit(0)

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error inesperado: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--repo", default=".", help="Ruta al repositorio Git (default: directorio actual)")
def configure(repo: str) -> None:
    """
    Crea archivo de configuración .ci-guardian.yaml.

    Genera configuración por defecto para el proyecto.
    """
    try:
        # Obtener y validar repo path
        repo_path = _obtener_repo_path(repo)

        # Path del archivo de configuración
        config_path = repo_path / ".ci-guardian.yaml"

        # Si existe, pedir confirmación
        if config_path.exists() and not click.confirm(
            "El archivo de configuración ya existe. ¿Sobrescribir?"
        ):
            click.echo("Operación cancelado.")
            sys.exit(0)

        # Generar configuración por defecto usando módulo centralizado
        from ci_guardian.core.config import CIGuardianConfig

        config = CIGuardianConfig.default()

        # Guardar a YAML
        config.to_yaml(config_path)

        click.echo(f"✓ Configuración creada en {config_path}")
        sys.exit(0)

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error inesperado: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "-m",
    "--message",
    required=True,
    help="Mensaje de commit",
)
@click.option(
    "--repo",
    default=".",
    help="Ruta al repositorio Git (default: directorio actual)",
)
def commit(message: str, repo: str) -> None:
    """
    Crea un commit verificando que el venv esté activo.

    Este comando valida que haya un venv activo ANTES de ejecutar git commit.
    Si no hay venv activo, muestra instrucciones claras para activarlo y
    cancela el commit para prevenir errores en los hooks.

    IMPORTANTE: Este comando NO activa el venv automáticamente (técnicamente
    imposible desde un subprocess). El usuario debe activar el venv manualmente.

    Ejemplo:
        source venv/bin/activate  # Activar primero
        ci-guardian commit -m "feat: add new feature"

    Implementado en LIB-32.
    """
    import subprocess

    from ci_guardian.core.venv_validator import esta_venv_activo

    try:
        # Obtener y validar repo path
        repo_path = _obtener_repo_path(repo)

        # Verificar venv activo
        venv_ok, mensaje = esta_venv_activo()

        if not venv_ok:
            click.echo("❌ ERROR: No hay entorno virtual activo", err=True)
            click.echo(
                "\nLos hooks de CI Guardian requieren un venv activo para ejecutar "
                "Ruff, Black, Bandit y pytest.",
                err=True,
            )

            # Intentar detectar venv para dar instrucciones específicas
            from ci_guardian.core.venv_manager import detectar_venv

            venv_path = detectar_venv(repo_path)
            if venv_path:
                click.echo(f"\n✓ Venv detectado en: {venv_path}", err=True)
                click.echo("\n📋 Para activar el venv:", err=True)
                if platform.system() == "Windows":
                    click.echo(f"  {venv_path}\\Scripts\\activate", err=True)
                else:
                    click.echo(f"  source {venv_path}/bin/activate", err=True)
            else:
                click.echo("\n⚠️  No se detectó un venv en el proyecto.", err=True)
                click.echo("\n📋 Crea y activa un venv:", err=True)
                click.echo("  python -m venv venv", err=True)
                if platform.system() == "Windows":
                    click.echo("  venv\\Scripts\\activate", err=True)
                else:
                    click.echo("  source venv/bin/activate", err=True)

            click.echo('\n💡 Luego ejecuta nuevamente: ci-guardian commit -m "..."', err=True)
            sys.exit(1)

        # Venv está activo, proceder con commit
        click.echo(f'🔨 Ejecutando: git commit -m "{message}"')

        resultado = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_path,
            capture_output=True,
            text=True,
            shell=False,  # CRÍTICO: nunca usar shell=True
        )

        # Mostrar salida
        if resultado.stdout:
            click.echo(resultado.stdout)

        if resultado.returncode == 0:
            click.echo("\n✓ Commit creado exitosamente")
            sys.exit(0)

        # Error en commit
        if resultado.stderr:
            click.echo(resultado.stderr, err=True)

        click.echo("\n❌ El commit falló", err=True)
        sys.exit(resultado.returncode)

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except FileNotFoundError:
        click.echo("❌ Error: Git no está instalado", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error inesperado: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
