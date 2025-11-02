"""
Validador de seguridad con Bandit y Safety.

Este módulo ejecuta herramientas de auditoría de seguridad:
- Bandit: SAST (Static Application Security Testing)
- Safety: Vulnerability scanner para dependencias
"""

import json
import subprocess
from pathlib import Path
from typing import Any


def ejecutar_bandit(directorio: Path, formato: str = "json") -> tuple[bool, dict[str, Any]]:
    """
    Ejecuta Bandit en un directorio.

    Args:
        directorio: Path al directorio a escanear
        formato: Formato de output (json, txt, html)

    Returns:
        Tupla (exito, resultados):
        - exito: True si no hay vulnerabilidades HIGH/CRITICAL
        - resultados: Dict con vulnerabilidades encontradas

    Raises:
        ValueError: Si directorio no existe, hay path traversal o formato inválido
    """
    # Validar formato (whitelist)
    FORMATOS_PERMITIDOS = {"json", "txt", "html", "xml", "csv"}
    if formato not in FORMATOS_PERMITIDOS:
        raise ValueError(f"Formato inválido: {formato}. Formatos permitidos: {FORMATOS_PERMITIDOS}")

    # Validación de seguridad: prevenir path traversal
    if ".." in str(directorio):
        raise ValueError("Path traversal detectado: ruta inválida fuera del proyecto")

    # Validar que el directorio existe
    if not directorio.exists():
        raise ValueError(f"El directorio {directorio} no existe: directorio inválido")

    # Ejecutar bandit
    try:
        resultado = subprocess.run(
            [
                "bandit",
                "-r",
                str(directorio),
                "-f",
                formato,
                "--exclude",
                "tests,venv,.git",
            ],
            capture_output=True,
            text=True,
            timeout=120,
            shell=False,  # CRÍTICO: prevenir command injection
        )

        # Parsear JSON de forma segura
        if formato == "json":
            try:
                data = json.loads(resultado.stdout)
            except json.JSONDecodeError as e:
                return (
                    False,
                    {
                        "error": "Error parseando output de Bandit: JSON inválido",
                        "detalle": str(e)[:100],  # Limitar longitud
                    },
                )
        else:
            data = {"raw": resultado.stdout}

        # Verificar si hay vulnerabilidades HIGH
        # Nota: _totals a veces no se actualiza correctamente en Bandit,
        # mejor contar directamente desde results
        results = data.get("results", [])
        high_count = sum(1 for r in results if r.get("issue_severity") == "HIGH")

        return (high_count == 0, data)

    except FileNotFoundError:
        # Bandit no está instalado
        return (False, {"error": "bandit no está instalado"})

    except subprocess.TimeoutExpired:
        # Timeout ejecutando Bandit
        return (False, {"error": "timeout ejecutando Bandit después de 120 segundos"})


def ejecutar_safety(
    archivo_deps: Path | None = None,
) -> tuple[bool, list[dict[str, Any]]]:
    """
    Ejecuta Safety para escanear vulnerabilidades en dependencias.

    Args:
        archivo_deps: Path al archivo de dependencias (pyproject.toml, requirements.txt)
                     Si es None, se auto-detecta

    Returns:
        Tupla (exito, vulnerabilidades):
        - exito: True si no hay CVEs
        - vulnerabilidades: Lista de CVEs encontrados

    Raises:
        FileNotFoundError: Si el archivo especificado no existe
    """
    # Si se especifica un archivo, validar que existe
    if archivo_deps is not None:
        if not archivo_deps.exists():
            raise FileNotFoundError(f"El archivo {archivo_deps} no existe: no encontrado")
        archivo_a_usar = archivo_deps
    else:
        # Auto-detectar archivo de dependencias
        cwd = Path.cwd()
        pyproject = cwd / "pyproject.toml"
        requirements = cwd / "requirements.txt"

        if pyproject.exists():
            archivo_a_usar = pyproject
        elif requirements.exists():
            archivo_a_usar = requirements
        else:
            # Si no hay archivo, ejecutar sin --file
            archivo_a_usar = None

    # Construir comando
    cmd = ["safety", "check", "--json"]
    if archivo_a_usar is not None:
        cmd.extend(["--file", str(archivo_a_usar)])

    # Ejecutar safety
    try:
        resultado = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            shell=False,  # CRÍTICO: prevenir command injection
        )

        # Parsear JSON de forma segura
        try:
            vulnerabilidades = json.loads(resultado.stdout)
        except json.JSONDecodeError as e:
            return (
                False,
                [
                    {
                        "error": "Error parseando output de Safety: JSON inválido",
                        "detalle": str(e)[:100],  # Limitar longitud
                    }
                ],
            )

        # Validar que es una lista
        if not isinstance(vulnerabilidades, list):
            return (False, [{"error": "Output de Safety no es una lista válida"}])

        # Si la lista está vacía, no hay vulnerabilidades
        return (len(vulnerabilidades) == 0, vulnerabilidades)

    except FileNotFoundError:
        # Safety no está instalado
        return (False, [])

    except subprocess.TimeoutExpired:
        # Timeout ejecutando Safety
        return (False, [])


def generar_reporte_seguridad(
    resultados_bandit: dict[str, Any], vulnerabilidades_safety: list[dict[str, Any]]
) -> str:
    """
    Genera un reporte formateado de auditoría de seguridad.

    Args:
        resultados_bandit: Dict con resultados de Bandit
        vulnerabilidades_safety: Lista de CVEs encontrados por Safety

    Returns:
        String con el reporte formateado
    """
    # Extraer métricas de Bandit
    metrics = resultados_bandit.get("metrics", {}).get("_totals", {})
    high_count = metrics.get("HIGH", 0)
    medium_count = metrics.get("MEDIUM", 0)
    low_count = metrics.get("LOW", 0)

    # Calcular total de vulnerabilidades
    total_bandit = high_count + medium_count + low_count
    total_safety = len(vulnerabilidades_safety)
    total = total_bandit + total_safety

    # Construir reporte
    reporte = []
    reporte.append("═" * 50)
    reporte.append("    REPORTE DE AUDITORÍA DE SEGURIDAD")
    reporte.append("═" * 50)
    reporte.append("")

    # Sección Bandit
    reporte.append("📊 BANDIT (Static Analysis Security Testing)")
    reporte.append("─" * 50)
    if high_count > 0:
        reporte.append(f"❌ Vulnerabilidades HIGH: {high_count}")
    else:
        reporte.append(f"✅ Vulnerabilidades HIGH: {high_count}")

    if medium_count > 0:
        reporte.append(f"⚠️  Vulnerabilidades MEDIUM: {medium_count}")
    else:
        reporte.append(f"✅ Vulnerabilidades MEDIUM: {medium_count}")

    reporte.append(f"ℹ️  Vulnerabilidades LOW: {low_count}")
    reporte.append("")

    # Sección Safety
    reporte.append("📦 SAFETY (Dependency Vulnerability Scanner)")
    reporte.append("─" * 50)

    if total_safety == 0:
        reporte.append("✅ No se encontraron vulnerabilidades en dependencias")
    else:
        for cve in vulnerabilidades_safety:
            cve_id = cve.get("vulnerability", "UNKNOWN")
            package = cve.get("package_name", "unknown")
            version = cve.get("installed_version", "unknown")
            spec = cve.get("vulnerable_spec", "unknown")
            advisory = cve.get("advisory", "No description")

            reporte.append(f"❌ {cve_id} en {package} ({version})")
            reporte.append(f"   Versión vulnerable: {spec}")
            reporte.append(f"   Descripción: {advisory}")
            reporte.append("")

    # Total
    reporte.append("═" * 50)
    reporte.append(f"TOTAL: {total} vulnerabilidades encontradas")
    reporte.append("═" * 50)

    return "\n".join(reporte)
