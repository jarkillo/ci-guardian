#!/bin/bash
# Script para publicar ci-guardian en PyPI
#
# Uso:
#   ./scripts/publish.sh test    # Publicar en TestPyPI
#   ./scripts/publish.sh prod    # Publicar en PyPI oficial

set -e

if [ "$#" -ne 1 ]; then
    echo "❌ Error: Especifica 'test' o 'prod'"
    echo "Uso: $0 {test|prod}"
    exit 1
fi

MODE="$1"

echo "🔍 Verificando que estamos en main..."
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "main" ]; then
    echo "❌ Error: Debes estar en la rama 'main' para publicar"
    echo "   Rama actual: $BRANCH"
    exit 1
fi

echo "🔍 Verificando que no hay cambios sin commitear..."
if ! git diff-index --quiet HEAD --; then
    echo "❌ Error: Hay cambios sin commitear"
    echo "   Commit tus cambios primero: git add . && git commit"
    exit 1
fi

echo "🧹 Limpiando builds anteriores..."
rm -rf dist/ build/ src/*.egg-info

echo "🔨 Construyendo paquetes..."
python -m build

echo "✅ Validando paquetes con twine..."
twine check dist/*

if [ "$MODE" = "test" ]; then
    echo "📦 Publicando en TestPyPI..."
    echo "   URL: https://test.pypi.org/project/ci-guardian/"
    twine upload --repository testpypi dist/*

    echo ""
    echo "✅ Publicado en TestPyPI exitosamente!"
    echo ""
    echo "Para probar la instalación:"
    echo "  pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ ci-guardian"
    echo ""

elif [ "$MODE" = "prod" ]; then
    echo "⚠️  ¡ATENCIÓN! Vas a publicar en PyPI OFICIAL"
    echo "   Esto NO se puede deshacer. Solo se puede publicar una vez por versión."
    echo ""
    read -p "¿Estás seguro? (escribe 'yes' para continuar): " confirm

    if [ "$confirm" != "yes" ]; then
        echo "❌ Publicación cancelada"
        exit 1
    fi

    echo "📦 Publicando en PyPI..."
    echo "   URL: https://pypi.org/project/ci-guardian/"
    twine upload --repository pypi dist/*

    echo ""
    echo "✅ Publicado en PyPI exitosamente!"
    echo ""
    echo "Para instalar:"
    echo "  pip install ci-guardian"
    echo ""

else
    echo "❌ Error: Modo inválido '$MODE'. Usa 'test' o 'prod'"
    exit 1
fi
