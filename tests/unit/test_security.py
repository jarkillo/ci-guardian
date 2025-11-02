# tests/unit/test_security.py
"""
Tests para validadores de seguridad (Bandit y Safety).

Siguiendo TDD: Estos tests están diseñados para FALLAR primero (RED),
luego se implementará el código mínimo para que pasen (GREEN).
"""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest


class TestEjecutorBandit:
    """Tests para el ejecutor de Bandit (SAST)."""

    @pytest.fixture
    def directorio_python_valido(self, tmp_path):
        """Crea directorio con código Python válido."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        # Archivo sin vulnerabilidades
        archivo_seguro = src_dir / "seguro.py"
        archivo_seguro.write_text(
            '"""Módulo seguro."""\n\n\ndef funcion_segura():\n    return "OK"\n',
            encoding="utf-8",
        )

        return src_dir

    @pytest.fixture
    def mock_subprocess_bandit_sin_vulnerabilidades(self):
        """Mock de subprocess.run simulando Bandit sin vulnerabilidades."""
        return MagicMock(
            returncode=0,
            stdout=json.dumps(
                {"results": [], "metrics": {"_totals": {"HIGH": 0, "MEDIUM": 0, "LOW": 0}}}
            ),
            stderr="",
        )

    @pytest.fixture
    def mock_subprocess_bandit_con_vulnerabilidades_high(self):
        """Mock de subprocess.run simulando Bandit con vulnerabilidades HIGH."""
        return MagicMock(
            returncode=1,
            stdout=json.dumps(
                {
                    "results": [
                        {
                            "issue_severity": "HIGH",
                            "issue_confidence": "HIGH",
                            "issue_text": "Use of exec detected.",
                            "line_number": 42,
                            "filename": "src/vulnerable.py",
                            "test_id": "B102",
                        },
                        {
                            "issue_severity": "MEDIUM",
                            "issue_confidence": "MEDIUM",
                            "issue_text": "Use of assert detected.",
                            "line_number": 10,
                            "filename": "src/test.py",
                            "test_id": "B101",
                        },
                    ],
                    "metrics": {"_totals": {"HIGH": 1, "MEDIUM": 1, "LOW": 0}},
                }
            ),
            stderr="",
        )

    def test_debe_ejecutar_bandit_con_argumentos_correctos(
        self, directorio_python_valido, mock_subprocess_bandit_sin_vulnerabilidades
    ):
        """Debe ejecutar Bandit con argumentos correctos."""
        from ci_guardian.validators.security import ejecutar_bandit

        # Arrange
        with patch(
            "subprocess.run", return_value=mock_subprocess_bandit_sin_vulnerabilidades
        ) as mock_run:
            # Act
            exitoso, resultados = ejecutar_bandit(directorio_python_valido)

            # Assert
            assert mock_run.called, "Debe ejecutar Bandit"
            args_llamada = mock_run.call_args[0][0]
            assert args_llamada[0] == "bandit", "Debe ejecutar el comando 'bandit'"
            assert "-r" in args_llamada, "Debe usar modo recursivo (-r)"
            assert "-f" in args_llamada and "json" in args_llamada, "Debe usar formato JSON"
            assert str(directorio_python_valido) in " ".join(
                args_llamada
            ), "Debe incluir el directorio a escanear"

            # Verificar que NO se usa shell=True (seguridad)
            assert (
                mock_run.call_args.kwargs.get("shell", False) is False
            ), "NUNCA debe usar shell=True (vulnerabilidad de command injection)"

    def test_debe_parsear_output_json_correctamente(
        self, directorio_python_valido, mock_subprocess_bandit_con_vulnerabilidades_high
    ):
        """Debe parsear output JSON de Bandit correctamente."""
        from ci_guardian.validators.security import ejecutar_bandit

        # Arrange
        with patch("subprocess.run", return_value=mock_subprocess_bandit_con_vulnerabilidades_high):
            # Act
            exitoso, resultados = ejecutar_bandit(directorio_python_valido)

            # Assert
            assert isinstance(resultados, dict), "Debe retornar dict con resultados parseados"
            assert "results" in resultados, "Debe incluir 'results' del JSON"
            assert len(resultados["results"]) == 2, "Debe parsear todas las vulnerabilidades"

    def test_debe_retornar_true_cuando_no_hay_vulnerabilidades_high(
        self, directorio_python_valido, mock_subprocess_bandit_sin_vulnerabilidades
    ):
        """Debe retornar True si no hay vulnerabilidades HIGH/CRITICAL."""
        from ci_guardian.validators.security import ejecutar_bandit

        # Arrange
        with patch("subprocess.run", return_value=mock_subprocess_bandit_sin_vulnerabilidades):
            # Act
            exitoso, resultados = ejecutar_bandit(directorio_python_valido)

            # Assert
            assert exitoso is True, "Debe retornar True cuando no hay vulnerabilidades HIGH"

    def test_debe_retornar_false_cuando_hay_vulnerabilidades_high(
        self, directorio_python_valido, mock_subprocess_bandit_con_vulnerabilidades_high
    ):
        """Debe retornar False si hay vulnerabilidades HIGH."""
        from ci_guardian.validators.security import ejecutar_bandit

        # Arrange
        with patch("subprocess.run", return_value=mock_subprocess_bandit_con_vulnerabilidades_high):
            # Act
            exitoso, resultados = ejecutar_bandit(directorio_python_valido)

            # Assert
            assert exitoso is False, "Debe retornar False cuando hay vulnerabilidades HIGH"

    def test_debe_filtrar_vulnerabilidades_por_severidad(
        self, directorio_python_valido, mock_subprocess_bandit_con_vulnerabilidades_high
    ):
        """Debe filtrar vulnerabilidades por severidad (HIGH, MEDIUM, LOW)."""
        from ci_guardian.validators.security import ejecutar_bandit

        # Arrange
        with patch("subprocess.run", return_value=mock_subprocess_bandit_con_vulnerabilidades_high):
            # Act
            exitoso, resultados = ejecutar_bandit(directorio_python_valido)

            # Assert
            assert "metrics" in resultados, "Debe incluir métricas de severidad"
            assert (
                resultados["metrics"]["_totals"]["HIGH"] == 1
            ), "Debe contar 1 vulnerabilidad HIGH"
            assert (
                resultados["metrics"]["_totals"]["MEDIUM"] == 1
            ), "Debe contar 1 vulnerabilidad MEDIUM"

    def test_debe_excluir_directorios_tests_y_venv(
        self, directorio_python_valido, mock_subprocess_bandit_sin_vulnerabilidades
    ):
        """Debe excluir directorios tests/, venv/ del escaneo."""
        from ci_guardian.validators.security import ejecutar_bandit

        # Arrange
        with patch(
            "subprocess.run", return_value=mock_subprocess_bandit_sin_vulnerabilidades
        ) as mock_run:
            # Act
            ejecutar_bandit(directorio_python_valido)

            # Assert
            args_llamada = mock_run.call_args[0][0]
            args_str = " ".join(args_llamada)

            # Debe incluir flags de exclusión
            assert "-x" in args_llamada or "--exclude" in args_str, "Debe usar flag de exclusión"
            # La implementación puede excluir usando -x o --exclude-dirs
            # Verificamos que se mencionan los directorios a excluir
            assert any(
                "test" in arg.lower() or "venv" in arg.lower() for arg in args_llamada
            ), "Debe excluir tests/ y venv/"

    def test_debe_manejar_timeout_de_120_segundos(
        self, directorio_python_valido, mock_subprocess_bandit_sin_vulnerabilidades
    ):
        """Debe configurar timeout de 120 segundos para prevenir bloqueos."""
        from ci_guardian.validators.security import ejecutar_bandit

        # Arrange
        with patch(
            "subprocess.run", return_value=mock_subprocess_bandit_sin_vulnerabilidades
        ) as mock_run:
            # Act
            ejecutar_bandit(directorio_python_valido)

            # Assert
            assert "timeout" in mock_run.call_args.kwargs, "Debe configurar timeout"
            timeout_usado = mock_run.call_args.kwargs["timeout"]
            assert timeout_usado >= 60, "Timeout debe ser al menos 60 segundos"
            assert timeout_usado <= 180, "Timeout no debe exceder 180 segundos"

    def test_debe_usar_shell_false_por_seguridad(
        self, directorio_python_valido, mock_subprocess_bandit_sin_vulnerabilidades
    ):
        """CRÍTICO: Debe usar shell=False para prevenir command injection."""
        from ci_guardian.validators.security import ejecutar_bandit

        # Arrange
        with patch(
            "subprocess.run", return_value=mock_subprocess_bandit_sin_vulnerabilidades
        ) as mock_run:
            # Act
            ejecutar_bandit(directorio_python_valido)

            # Assert
            assert (
                mock_run.call_args.kwargs.get("shell", False) is False
            ), "NUNCA debe usar shell=True - vulnerabilidad crítica de command injection"

    def test_debe_manejar_error_cuando_bandit_no_esta_instalado(self, directorio_python_valido):
        """Debe manejar FileNotFoundError cuando Bandit no está instalado."""
        from ci_guardian.validators.security import ejecutar_bandit

        # Arrange
        with patch("subprocess.run", side_effect=FileNotFoundError("bandit not found")):
            # Act
            exitoso, resultados = ejecutar_bandit(directorio_python_valido)

            # Assert
            assert exitoso is False, "Debe retornar False cuando Bandit no está instalado"
            assert "bandit" in str(resultados).lower(), "Debe indicar que Bandit no está instalado"

    def test_debe_validar_path_para_prevenir_path_traversal(self, tmp_path):
        """Debe validar path para prevenir path traversal."""
        from ci_guardian.validators.security import ejecutar_bandit

        # Arrange
        directorio_malicioso = tmp_path / ".." / ".." / "etc"

        # Act & Assert
        with pytest.raises(ValueError, match="path traversal|ruta inválida|fuera del proyecto"):
            ejecutar_bandit(directorio_malicioso)

    def test_debe_rechazar_directorio_inexistente(self, tmp_path):
        """Debe rechazar directorios que no existen."""
        from ci_guardian.validators.security import ejecutar_bandit

        # Arrange
        directorio_inexistente = tmp_path / "no_existe"

        # Act & Assert
        with pytest.raises(ValueError, match="no existe|directorio inválido"):
            ejecutar_bandit(directorio_inexistente)

    def test_debe_capturar_stdout_y_stderr(
        self, directorio_python_valido, mock_subprocess_bandit_sin_vulnerabilidades
    ):
        """Debe capturar stdout y stderr para procesar resultados."""
        from ci_guardian.validators.security import ejecutar_bandit

        # Arrange
        with patch(
            "subprocess.run", return_value=mock_subprocess_bandit_sin_vulnerabilidades
        ) as mock_run:
            # Act
            ejecutar_bandit(directorio_python_valido)

            # Assert
            assert mock_run.call_args.kwargs.get("capture_output") is True or (
                mock_run.call_args.kwargs.get("stdout") == subprocess.PIPE
                and mock_run.call_args.kwargs.get("stderr") == subprocess.PIPE
            ), "Debe capturar stdout y stderr"
            assert mock_run.call_args.kwargs.get("text") is True, "Debe procesar output como texto"

    def test_debe_manejar_timeout_exception(self, directorio_python_valido):
        """Debe manejar TimeoutExpired cuando Bandit tarda demasiado."""
        from ci_guardian.validators.security import ejecutar_bandit

        # Arrange
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("bandit", 120)):
            # Act
            exitoso, resultados = ejecutar_bandit(directorio_python_valido)

            # Assert
            assert exitoso is False, "Debe retornar False cuando hay timeout"
            assert (
                "timeout" in str(resultados).lower() or "tiempo" in str(resultados).lower()
            ), "Debe indicar que hubo timeout"

    def test_debe_soportar_parametro_formato(
        self, directorio_python_valido, mock_subprocess_bandit_sin_vulnerabilidades
    ):
        """Debe soportar parámetro formato (json, txt, html)."""
        from ci_guardian.validators.security import ejecutar_bandit

        # Arrange
        with patch(
            "subprocess.run", return_value=mock_subprocess_bandit_sin_vulnerabilidades
        ) as mock_run:
            # Act
            ejecutar_bandit(directorio_python_valido, formato="json")

            # Assert
            args_llamada = mock_run.call_args[0][0]
            assert "-f" in args_llamada and "json" in args_llamada, "Debe usar formato especificado"


class TestEjecutorSafety:
    """Tests para el ejecutor de Safety (vulnerability scanner)."""

    @pytest.fixture
    def pyproject_toml_mock(self, tmp_path):
        """Crea un pyproject.toml mock."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            """
[tool.poetry]
name = "test-project"
version = "0.1.0"

[tool.poetry.dependencies]
python = "^3.9"
requests = "2.25.0"
""",
            encoding="utf-8",
        )
        return pyproject

    @pytest.fixture
    def requirements_txt_mock(self, tmp_path):
        """Crea un requirements.txt mock."""
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("requests==2.25.0\nclick==8.0.0\n", encoding="utf-8")
        return requirements

    @pytest.fixture
    def mock_subprocess_safety_sin_vulnerabilidades(self):
        """Mock de subprocess.run simulando Safety sin vulnerabilidades."""
        return MagicMock(returncode=0, stdout="[]", stderr="")

    @pytest.fixture
    def mock_subprocess_safety_con_cves(self):
        """Mock de subprocess.run simulando Safety con CVEs encontrados."""
        return MagicMock(
            returncode=1,
            stdout=json.dumps(
                [
                    {
                        "vulnerability": "CVE-2023-12345",
                        "package_name": "requests",
                        "installed_version": "2.25.0",
                        "vulnerable_spec": "<2.26.0",
                        "advisory": "Request package has SSRF vulnerability",
                    },
                    {
                        "vulnerability": "CVE-2023-67890",
                        "package_name": "click",
                        "installed_version": "8.0.0",
                        "vulnerable_spec": "<8.0.2",
                        "advisory": "Click has arbitrary code execution vulnerability",
                    },
                ]
            ),
            stderr="",
        )

    def test_debe_ejecutar_safety_check(self, mock_subprocess_safety_sin_vulnerabilidades):
        """Debe ejecutar safety check correctamente."""
        from ci_guardian.validators.security import ejecutar_safety

        # Arrange
        with patch(
            "subprocess.run", return_value=mock_subprocess_safety_sin_vulnerabilidades
        ) as mock_run:
            # Act
            exitoso, vulnerabilidades = ejecutar_safety()

            # Assert
            assert mock_run.called, "Debe ejecutar Safety"
            args_llamada = mock_run.call_args[0][0]
            assert args_llamada[0] == "safety", "Debe ejecutar el comando 'safety'"
            assert "check" in args_llamada, "Debe usar subcomando 'check'"
            assert "--json" in args_llamada, "Debe usar formato JSON"

            # Verificar que NO se usa shell=True
            assert (
                mock_run.call_args.kwargs.get("shell", False) is False
            ), "NUNCA debe usar shell=True"

    def test_debe_parsear_output_json(self, mock_subprocess_safety_con_cves):
        """Debe parsear output JSON de Safety correctamente."""
        from ci_guardian.validators.security import ejecutar_safety

        # Arrange
        with patch("subprocess.run", return_value=mock_subprocess_safety_con_cves):
            # Act
            exitoso, vulnerabilidades = ejecutar_safety()

            # Assert
            assert isinstance(vulnerabilidades, list), "Debe retornar lista de vulnerabilidades"
            assert len(vulnerabilidades) == 2, "Debe parsear todos los CVEs"
            assert vulnerabilidades[0]["vulnerability"] == "CVE-2023-12345", "Debe incluir CVE ID"

    def test_debe_detectar_pyproject_toml_automaticamente(
        self, pyproject_toml_mock, mock_subprocess_safety_sin_vulnerabilidades
    ):
        """Debe detectar pyproject.toml automáticamente cuando archivo_deps=None."""
        from ci_guardian.validators.security import ejecutar_safety

        # Arrange
        with (
            patch(
                "subprocess.run", return_value=mock_subprocess_safety_sin_vulnerabilidades
            ) as mock_run,
            patch("pathlib.Path.cwd", return_value=pyproject_toml_mock.parent),
        ):
            # Act
            ejecutar_safety(archivo_deps=None)

            # Assert
            # Debe detectar automáticamente el archivo de dependencias
            # La implementación puede usar diferentes flags según el archivo
            assert mock_run.called, "Debe ejecutar Safety con auto-detección"

    def test_debe_detectar_requirements_txt_automaticamente(
        self, requirements_txt_mock, mock_subprocess_safety_sin_vulnerabilidades
    ):
        """Debe detectar requirements.txt automáticamente cuando archivo_deps=None."""
        from ci_guardian.validators.security import ejecutar_safety

        # Arrange
        with (
            patch(
                "subprocess.run", return_value=mock_subprocess_safety_sin_vulnerabilidades
            ) as mock_run,
            patch("pathlib.Path.cwd", return_value=requirements_txt_mock.parent),
        ):
            # Act
            ejecutar_safety(archivo_deps=None)

            # Assert
            assert mock_run.called, "Debe ejecutar Safety con auto-detección"

    def test_debe_retornar_true_cuando_no_hay_vulnerabilidades(
        self, mock_subprocess_safety_sin_vulnerabilidades
    ):
        """Debe retornar True si no hay vulnerabilidades."""
        from ci_guardian.validators.security import ejecutar_safety

        # Arrange
        with patch("subprocess.run", return_value=mock_subprocess_safety_sin_vulnerabilidades):
            # Act
            exitoso, vulnerabilidades = ejecutar_safety()

            # Assert
            assert exitoso is True, "Debe retornar True cuando no hay CVEs"
            assert len(vulnerabilidades) == 0, "Lista de vulnerabilidades debe estar vacía"

    def test_debe_retornar_false_cuando_hay_cves(self, mock_subprocess_safety_con_cves):
        """Debe retornar False si hay CVEs."""
        from ci_guardian.validators.security import ejecutar_safety

        # Arrange
        with patch("subprocess.run", return_value=mock_subprocess_safety_con_cves):
            # Act
            exitoso, vulnerabilidades = ejecutar_safety()

            # Assert
            assert exitoso is False, "Debe retornar False cuando hay CVEs"
            assert len(vulnerabilidades) > 0, "Debe incluir lista de CVEs"

    def test_debe_listar_cves_con_detalles(self, mock_subprocess_safety_con_cves):
        """Debe listar CVEs con detalles (CVE-ID, package, version, advisory)."""
        from ci_guardian.validators.security import ejecutar_safety

        # Arrange
        with patch("subprocess.run", return_value=mock_subprocess_safety_con_cves):
            # Act
            exitoso, vulnerabilidades = ejecutar_safety()

            # Assert
            cve_primera = vulnerabilidades[0]
            assert "vulnerability" in cve_primera, "Debe incluir CVE ID"
            assert "package_name" in cve_primera, "Debe incluir nombre del paquete"
            assert "installed_version" in cve_primera, "Debe incluir versión instalada"
            assert "vulnerable_spec" in cve_primera, "Debe incluir especificación vulnerable"
            assert "advisory" in cve_primera, "Debe incluir descripción del advisory"

    def test_debe_usar_shell_false_por_seguridad(self, mock_subprocess_safety_sin_vulnerabilidades):
        """CRÍTICO: Debe usar shell=False para prevenir command injection."""
        from ci_guardian.validators.security import ejecutar_safety

        # Arrange
        with patch(
            "subprocess.run", return_value=mock_subprocess_safety_sin_vulnerabilidades
        ) as mock_run:
            # Act
            ejecutar_safety()

            # Assert
            assert (
                mock_run.call_args.kwargs.get("shell", False) is False
            ), "NUNCA debe usar shell=True"

    def test_debe_manejar_timeout(self, mock_subprocess_safety_sin_vulnerabilidades):
        """Debe configurar timeout para prevenir bloqueos."""
        from ci_guardian.validators.security import ejecutar_safety

        # Arrange
        with patch(
            "subprocess.run", return_value=mock_subprocess_safety_sin_vulnerabilidades
        ) as mock_run:
            # Act
            ejecutar_safety()

            # Assert
            assert "timeout" in mock_run.call_args.kwargs, "Debe configurar timeout"
            timeout_usado = mock_run.call_args.kwargs["timeout"]
            assert timeout_usado >= 30, "Timeout debe ser al menos 30 segundos"

    def test_debe_manejar_error_cuando_safety_no_esta_instalado(self):
        """Debe manejar FileNotFoundError cuando Safety no está instalado."""
        from ci_guardian.validators.security import ejecutar_safety

        # Arrange
        with patch("subprocess.run", side_effect=FileNotFoundError("safety not found")):
            # Act
            exitoso, vulnerabilidades = ejecutar_safety()

            # Assert
            assert exitoso is False, "Debe retornar False cuando Safety no está instalado"
            assert isinstance(
                vulnerabilidades, (list, str)
            ), "Debe retornar mensaje de error o lista vacía"

    def test_debe_manejar_timeout_exception(self):
        """Debe manejar TimeoutExpired cuando Safety tarda demasiado."""
        from ci_guardian.validators.security import ejecutar_safety

        # Arrange
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("safety", 60)):
            # Act
            exitoso, vulnerabilidades = ejecutar_safety()

            # Assert
            assert exitoso is False, "Debe retornar False cuando hay timeout"

    def test_debe_rechazar_archivo_inexistente(self, tmp_path):
        """Debe rechazar archivo de dependencias que no existe."""
        from ci_guardian.validators.security import ejecutar_safety

        # Arrange
        archivo_inexistente = tmp_path / "no_existe.txt"

        # Act & Assert
        with pytest.raises(FileNotFoundError, match="no existe|no encontrado"):
            ejecutar_safety(archivo_deps=archivo_inexistente)

    def test_debe_capturar_stdout_y_stderr(self, mock_subprocess_safety_sin_vulnerabilidades):
        """Debe capturar stdout y stderr."""
        from ci_guardian.validators.security import ejecutar_safety

        # Arrange
        with patch(
            "subprocess.run", return_value=mock_subprocess_safety_sin_vulnerabilidades
        ) as mock_run:
            # Act
            ejecutar_safety()

            # Assert
            assert mock_run.call_args.kwargs.get("capture_output") is True or (
                mock_run.call_args.kwargs.get("stdout") == subprocess.PIPE
            ), "Debe capturar output"
            assert mock_run.call_args.kwargs.get("text") is True, "Debe usar modo texto"


class TestGeneradorReporteSeguridad:
    """Tests para generación de reportes de seguridad."""

    @pytest.fixture
    def resultados_bandit_sin_issues(self):
        """Resultados de Bandit sin vulnerabilidades."""
        return {"results": [], "metrics": {"_totals": {"HIGH": 0, "MEDIUM": 0, "LOW": 0}}}

    @pytest.fixture
    def resultados_bandit_con_issues(self):
        """Resultados de Bandit con vulnerabilidades."""
        return {
            "results": [
                {
                    "issue_severity": "HIGH",
                    "issue_confidence": "HIGH",
                    "issue_text": "Use of exec detected.",
                    "line_number": 42,
                    "filename": "src/vulnerable.py",
                    "test_id": "B102",
                },
                {
                    "issue_severity": "MEDIUM",
                    "issue_confidence": "MEDIUM",
                    "issue_text": "Possible SQL injection.",
                    "line_number": 100,
                    "filename": "src/db.py",
                    "test_id": "B608",
                },
            ],
            "metrics": {"_totals": {"HIGH": 1, "MEDIUM": 1, "LOW": 0}},
        }

    @pytest.fixture
    def vulnerabilidades_safety_vacias(self):
        """Lista vacía de vulnerabilidades de Safety."""
        return []

    @pytest.fixture
    def vulnerabilidades_safety_con_cves(self):
        """Lista de CVEs de Safety."""
        return [
            {
                "vulnerability": "CVE-2023-12345",
                "package_name": "requests",
                "installed_version": "2.25.0",
                "vulnerable_spec": "<2.26.0",
                "advisory": "SSRF vulnerability",
            },
            {
                "vulnerability": "CVE-2023-67890",
                "package_name": "urllib3",
                "installed_version": "1.26.0",
                "vulnerable_spec": "<1.26.5",
                "advisory": "Security bypass",
            },
        ]

    def test_debe_generar_reporte_con_secciones_claras(
        self, resultados_bandit_sin_issues, vulnerabilidades_safety_vacias
    ):
        """Debe generar reporte con secciones claras (Bandit, Safety)."""
        from ci_guardian.validators.security import generar_reporte_seguridad

        # Act
        reporte = generar_reporte_seguridad(
            resultados_bandit_sin_issues, vulnerabilidades_safety_vacias
        )

        # Assert
        assert isinstance(reporte, str), "Debe retornar string con reporte"
        assert "bandit" in reporte.lower(), "Debe incluir sección de Bandit"
        assert "safety" in reporte.lower(), "Debe incluir sección de Safety"

    def test_debe_incluir_summary_de_bandit(
        self, resultados_bandit_con_issues, vulnerabilidades_safety_vacias
    ):
        """Debe incluir summary de Bandit (contadores por severidad)."""
        from ci_guardian.validators.security import generar_reporte_seguridad

        # Act
        reporte = generar_reporte_seguridad(
            resultados_bandit_con_issues, vulnerabilidades_safety_vacias
        )

        # Assert
        assert "high" in reporte.lower(), "Debe mencionar vulnerabilidades HIGH"
        assert "medium" in reporte.lower(), "Debe mencionar vulnerabilidades MEDIUM"
        assert "1" in reporte, "Debe incluir contador de HIGH"

    def test_debe_incluir_lista_de_cves_de_safety(
        self, resultados_bandit_sin_issues, vulnerabilidades_safety_con_cves
    ):
        """Debe incluir lista de CVEs de Safety."""
        from ci_guardian.validators.security import generar_reporte_seguridad

        # Act
        reporte = generar_reporte_seguridad(
            resultados_bandit_sin_issues, vulnerabilidades_safety_con_cves
        )

        # Assert
        assert "CVE-2023-12345" in reporte, "Debe incluir CVE ID"
        assert "requests" in reporte, "Debe incluir nombre del paquete vulnerable"
        assert "2.25.0" in reporte, "Debe incluir versión instalada"

    def test_debe_usar_colores_para_severidad(
        self, resultados_bandit_con_issues, vulnerabilidades_safety_vacias
    ):
        """Debe usar códigos de color para indicar severidad."""
        from ci_guardian.validators.security import generar_reporte_seguridad

        # Act
        reporte = generar_reporte_seguridad(
            resultados_bandit_con_issues, vulnerabilidades_safety_vacias
        )

        # Assert
        # Colorama usa códigos ANSI o puede estar presente el término color/severidad
        # La implementación puede variar, verificamos que menciona severidades
        assert "HIGH" in reporte or "high" in reporte.lower(), "Debe indicar severidad HIGH"

    def test_debe_incluir_contadores_totales(
        self, resultados_bandit_con_issues, vulnerabilidades_safety_con_cves
    ):
        """Debe incluir contadores totales de vulnerabilidades."""
        from ci_guardian.validators.security import generar_reporte_seguridad

        # Act
        reporte = generar_reporte_seguridad(
            resultados_bandit_con_issues, vulnerabilidades_safety_con_cves
        )

        # Assert
        # Debe incluir algún tipo de contador o summary
        assert any(
            palabra in reporte.lower()
            for palabra in ["total", "encontradas", "vulnerabilidades", "issues"]
        ), "Debe incluir contador total"


class TestIntegracionSeguridad:
    """Tests de integración para el módulo de seguridad."""

    @pytest.fixture
    def proyecto_mock_completo(self, tmp_path):
        """Crea un proyecto Python completo para testing."""
        # Crear estructura de directorios
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        # Archivo Python
        (src_dir / "app.py").write_text(
            '"""Aplicación."""\n\n\ndef main():\n    return "OK"\n', encoding="utf-8"
        )

        # pyproject.toml
        (tmp_path / "pyproject.toml").write_text(
            """
[tool.poetry.dependencies]
python = "^3.9"
requests = "2.28.0"
""",
            encoding="utf-8",
        )

        return tmp_path

    def test_workflow_completo_sin_vulnerabilidades(self, proyecto_mock_completo):
        """Debe ejecutar workflow completo: Bandit + Safety + Reporte."""
        from ci_guardian.validators.security import (
            ejecutar_bandit,
            ejecutar_safety,
            generar_reporte_seguridad,
        )

        # Arrange - Mocks de subprocess para Bandit y Safety
        def mock_run(cmd, **kwargs):
            if cmd[0] == "bandit":
                return MagicMock(
                    returncode=0,
                    stdout=json.dumps(
                        {"results": [], "metrics": {"_totals": {"HIGH": 0, "MEDIUM": 0, "LOW": 0}}}
                    ),
                    stderr="",
                )
            if cmd[0] == "safety":
                return MagicMock(returncode=0, stdout="[]", stderr="")
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=mock_run):
            # Act
            bandit_exitoso, bandit_resultados = ejecutar_bandit(proyecto_mock_completo / "src")
            safety_exitoso, safety_vulnerabilidades = ejecutar_safety()
            reporte = generar_reporte_seguridad(bandit_resultados, safety_vulnerabilidades)

            # Assert
            assert bandit_exitoso is True, "Bandit debe pasar"
            assert safety_exitoso is True, "Safety debe pasar"
            assert len(reporte) > 0, "Debe generar reporte"
            assert "bandit" in reporte.lower(), "Reporte debe incluir resultados de Bandit"
            assert "safety" in reporte.lower(), "Reporte debe incluir resultados de Safety"

    def test_workflow_completo_con_vulnerabilidades(self, proyecto_mock_completo):
        """Debe ejecutar workflow completo cuando hay vulnerabilidades."""
        from ci_guardian.validators.security import (
            ejecutar_bandit,
            ejecutar_safety,
            generar_reporte_seguridad,
        )

        # Arrange - Mocks con vulnerabilidades
        def mock_run(cmd, **kwargs):
            if cmd[0] == "bandit":
                return MagicMock(
                    returncode=1,
                    stdout=json.dumps(
                        {
                            "results": [
                                {
                                    "issue_severity": "HIGH",
                                    "issue_confidence": "HIGH",
                                    "issue_text": "Use of eval",
                                    "line_number": 10,
                                    "filename": "src/app.py",
                                    "test_id": "B307",
                                }
                            ],
                            "metrics": {"_totals": {"HIGH": 1, "MEDIUM": 0, "LOW": 0}},
                        }
                    ),
                    stderr="",
                )
            if cmd[0] == "safety":
                return MagicMock(
                    returncode=1,
                    stdout=json.dumps(
                        [
                            {
                                "vulnerability": "CVE-2023-99999",
                                "package_name": "requests",
                                "installed_version": "2.28.0",
                                "vulnerable_spec": "<2.28.2",
                                "advisory": "Security issue",
                            }
                        ]
                    ),
                    stderr="",
                )
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=mock_run):
            # Act
            bandit_exitoso, bandit_resultados = ejecutar_bandit(proyecto_mock_completo / "src")
            safety_exitoso, safety_vulnerabilidades = ejecutar_safety()
            reporte = generar_reporte_seguridad(bandit_resultados, safety_vulnerabilidades)

            # Assert
            assert bandit_exitoso is False, "Bandit debe fallar con vulnerabilidades HIGH"
            assert safety_exitoso is False, "Safety debe fallar con CVEs"
            assert "CVE-2023-99999" in reporte, "Reporte debe incluir CVE encontrado"
            assert "HIGH" in reporte or "high" in reporte.lower(), "Reporte debe indicar severidad"

    def test_manejo_de_errores_en_cascada(self, proyecto_mock_completo):
        """Debe manejar errores en cascada (Bandit falla, Safety continúa)."""
        from ci_guardian.validators.security import ejecutar_bandit, ejecutar_safety

        # Arrange - Bandit falla por timeout, Safety OK
        def mock_run(cmd, **kwargs):
            if cmd[0] == "bandit":
                raise subprocess.TimeoutExpired("bandit", 120)
            if cmd[0] == "safety":
                return MagicMock(returncode=0, stdout="[]", stderr="")
            return MagicMock(returncode=0, stdout="", stderr="")

        with patch("subprocess.run", side_effect=mock_run):
            # Act
            bandit_exitoso, bandit_resultados = ejecutar_bandit(proyecto_mock_completo / "src")
            safety_exitoso, safety_vulnerabilidades = ejecutar_safety()

            # Assert
            assert bandit_exitoso is False, "Bandit debe fallar por timeout"
            assert safety_exitoso is True, "Safety debe continuar y pasar"
            # El sistema debe ser resiliente y no crashear
