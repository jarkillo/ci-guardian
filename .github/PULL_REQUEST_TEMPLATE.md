## 📋 Summary

<!-- Provide a brief description of what this PR does -->

## 🎯 Motivation

<!-- Why is this change needed? What problem does it solve? -->

## 🔄 Changes

<!-- List the specific changes made in this PR -->

-
-
-

## 🧪 Testing

### Test Coverage

<!-- Describe the tests you've added or modified -->

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All existing tests pass
- [ ] Coverage meets or exceeds 75%

### Test Results

```bash
# Paste pytest output here
# Example:
# ======================== test session starts =========================
# tests/unit/test_module.py::TestClass::test_function PASSED [ 100%]
# ======================== X passed in 0.30s ==========================
```

**Coverage**: X% (previous: Y%)

### Manual Testing

<!-- Describe any manual testing you performed -->

- [ ] Tested on Linux
- [ ] Tested on Windows (or mocked with platform.system())
- [ ] Tested on macOS (or mocked)
- [ ] Tested with Python 3.9
- [ ] Tested with Python 3.12+

## 📚 Documentation

<!-- Have you updated relevant documentation? -->

- [ ] Docstrings added/updated (Spanish, Google style)
- [ ] README.md updated (if applicable)
- [ ] CHANGELOG.md updated
- [ ] Type hints complete (Python 3.12+ syntax)

## ✅ Quality Checklist

<!-- Ensure all checks pass before requesting review -->

### Code Quality

- [ ] `pytest` - All tests pass
- [ ] `pytest --cov` - Coverage ≥ 75%
- [ ] `ruff check .` - No linting errors
- [ ] `black --check .` - Code is formatted
- [ ] `mypy src/` - Type checking passes (if applicable)

### Security

- [ ] No `shell=True` with user input
- [ ] No `eval()` or `exec()`
- [ ] Paths validated with `Path.resolve()`
- [ ] No hardcoded secrets
- [ ] Secure permissions (0o755, not 0o777)

### TDD Process

- [ ] Tests written FIRST (RED phase)
- [ ] Implementation makes tests pass (GREEN phase)
- [ ] Code refactored if needed (REFACTOR phase)
- [ ] Each phase has its own commit

## 🔗 Related Issues

<!-- Link to related issues. Use keywords to auto-close them -->

- Closes #
- Related to #
- Depends on #

## 📸 Screenshots (if applicable)

<!-- Add screenshots for UI changes or CLI output -->

## 🚀 Breaking Changes

<!-- Does this PR introduce breaking changes? -->

- [ ] No breaking changes
- [ ] Breaking changes (describe below)

<!-- If yes, describe the breaking changes and migration path -->

## 📝 Additional Notes

<!-- Any additional information reviewers should know -->

---

### Commit Messages

<!-- List your commits to verify they follow Conventional Commits -->

```
Example:
- feat(core): implement venv detection
- test(core): add tests for venv detection
- docs(readme): update installation instructions
```

### For Reviewers

<!-- Help reviewers understand what to focus on -->

**Focus areas**:
-

**Questions for reviewers**:
-

---

<!--
Before submitting:
1. Ensure your branch is up to date with `dev`
2. Run all quality checks locally
3. Write clear commit messages
4. Fill out this template completely
5. Request review from maintainers

Thank you for contributing to CI Guardian! 🎉
-->
