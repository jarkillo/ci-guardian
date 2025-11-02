#!/bin/bash
# Smoke test script for CI Guardian pre-release validation
# Prevents bugs like v0.1.0 from reaching production by testing actual wheel installation

set -e  # Exit on error

echo "🔬 Ejecutando smoke tests pre-release..."

# Get project root (script is in scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 1. Build del paquete
echo "📦 Building package..."
rm -rf dist/ build/ *.egg-info  # Clean previous builds
python -m build

# Find most recent wheel
WHEEL_PATH=$(ls -t dist/ci_guardian-*.whl | head -1)
if [ ! -f "$WHEEL_PATH" ]; then
    echo "❌ Error: No wheel found in dist/"
    exit 1
fi
echo "   Using wheel: $WHEEL_PATH"

# 2. Crear entorno de prueba limpio
echo "🧪 Creating clean test environment..."
SMOKE_DIR=$(mktemp -d)
echo "   Test directory: $SMOKE_DIR"

# Cleanup on exit
trap "rm -rf $SMOKE_DIR" EXIT

cd "$SMOKE_DIR"
python -m venv venv
source venv/bin/activate

# 3. Instalar desde wheel (NO editable install)
echo "📥 Installing from wheel (NOT editable)..."
pip install --quiet "$PROJECT_ROOT/$WHEEL_PATH"

# 4. Verificar CLI funciona
echo "✅ Testing CLI..."
ci-guardian --version || {
    echo "❌ Error: ci-guardian --version failed"
    exit 1
}

ci-guardian --help > /dev/null || {
    echo "❌ Error: ci-guardian --help failed"
    exit 1
}

# 5. Crear repo Git de prueba
echo "📁 Creating test Git repository..."
mkdir smoke-test
cd smoke-test
git init --initial-branch=main > /dev/null
git config user.name "Smoke Test"
git config user.email "smoke@test.com"

# 6. Instalar hooks
echo "🪝 Installing hooks..."
ci-guardian install || {
    echo "❌ Error: ci-guardian install failed"
    exit 1
}

# 7. Validar que todos los hooks existen (100%)
echo "📊 Checking hook status..."
STATUS_OUTPUT=$(ci-guardian status)
if ! echo "$STATUS_OUTPUT" | grep -q "100%"; then
    echo "❌ Error: Not all hooks installed (expected 100%)"
    echo "$STATUS_OUTPUT"
    exit 1
fi

# 8. Test commit (trigger pre-commit, commit-msg, post-commit)
echo "💾 Testing commit workflow..."
cat > test.py << 'PYEOF'
"""Smoke test module."""


def smoke_test() -> None:
    """Simple smoke test function."""
    print("smoke test")


if __name__ == "__main__":
    smoke_test()
PYEOF
git add test.py
git commit -m "test: smoke test" || {
    echo "❌ Error: git commit failed"
    exit 1
}

# 9. Test push (trigger pre-push if exists)
echo "📤 Testing push workflow..."
REMOTE_DIR="$SMOKE_DIR/smoke-remote.git"
git init --bare "$REMOTE_DIR" > /dev/null
git remote add origin "$REMOTE_DIR"
git push origin HEAD || {
    echo "❌ Error: git push failed"
    exit 1
}

echo ""
echo "✅ All smoke tests passed!"
echo "   Package is safe to publish to PyPI"
exit 0
