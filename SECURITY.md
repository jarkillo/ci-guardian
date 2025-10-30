# Security Policy

## 🔒 Reporting a Vulnerability

CI Guardian takes security seriously. We appreciate your efforts to responsibly disclose your findings.

### Reporting Process

**DO NOT** open a public issue for security vulnerabilities. Instead:

1. **GitHub Security Advisory** (Preferred):
   - Go to https://github.com/jarkillo/ci-guardian/security/advisories/new
   - Click "Report a vulnerability"
   - Fill out the form with details

2. **Email** (Alternative):
   - Send an email to the maintainers via GitHub (see profile)
   - Subject: `[SECURITY] Brief description`
   - Include detailed information (see below)

### Information to Include

To help us triage and fix the issue quickly, please include:

```markdown
**Vulnerability Type**
(e.g., Command Injection, Path Traversal, XSS, etc.)

**Affected Component**
(e.g., src/ci_guardian/core/installer.py)

**Affected Versions**
(e.g., 0.1.0, dev branch, etc.)

**Description**
Clear description of the vulnerability and its impact.

**Proof of Concept**
Step-by-step instructions to reproduce:
1. ...
2. ...
3. ...

**Impact**
What can an attacker do with this vulnerability?

**Suggested Fix** (Optional)
If you have ideas for how to fix it.

**References** (Optional)
Links to relevant CVEs, CWEs, or documentation.
```

### Example Report

```markdown
**Vulnerability Type**: Command Injection

**Affected Component**: src/ci_guardian/validators/security.py

**Affected Versions**: 0.2.0 (hypothetical)

**Description**:
The function `ejecutar_bandit()` uses user-supplied input in a shell
command without proper sanitization.

**Proof of Concept**:
```python
# Malicious input
archivos = "test.py; rm -rf /"
ejecutar_bandit(archivos)  # Executes both commands
```

**Impact**:
An attacker could execute arbitrary commands on the system running
CI Guardian.

**Suggested Fix**:
Use subprocess.run() with a list of arguments instead of shell=True:
```python
subprocess.run(["bandit", "-r", archivo], shell=False)
```

**References**:
- CWE-78: OS Command Injection
- https://owasp.org/www-community/attacks/Command_Injection
```

## 🕐 Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Fix Timeline**: Depends on severity (see below)
- **Public Disclosure**: After fix is released + 7 days

### Severity Levels

| Severity | Response Time | Example |
|----------|---------------|---------|
| 🔴 **Critical** | 24-48 hours | Remote code execution, data loss |
| 🟠 **High** | 3-7 days | Authentication bypass, privilege escalation |
| 🟡 **Medium** | 7-14 days | Information disclosure, DoS |
| 🟢 **Low** | 14-30 days | Minor information leak, non-exploitable bug |

## 🛡️ Security Best Practices

CI Guardian follows security best practices:

### Development

- ✅ **TDD with security tests**: All security-critical code has tests
- ✅ **Static analysis**: Bandit, Ruff S-rules, MyPy
- ✅ **Code review**: All PRs reviewed before merge
- ✅ **No hardcoded secrets**: Use environment variables
- ✅ **Input validation**: Whitelist > blacklist
- ✅ **Least privilege**: Minimal permissions (0o755, not 0o777)

### Dependencies

- ✅ **Dependency scanning**: Safety, pip-audit
- ✅ **Pinned versions**: Exact versions in pyproject.toml
- ✅ **Regular updates**: Security patches applied promptly

### Operations

- ✅ **Secure defaults**: No `shell=True`, no `eval()`
- ✅ **Path validation**: `Path.resolve()` to prevent traversal
- ✅ **Encoding specified**: UTF-8 explicit in file operations

## 📋 Known Security Considerations

### By Design

1. **Hook Installation**: Requires write access to `.git/hooks/`
   - **Mitigation**: Only install hooks in repositories you trust
   - **Why**: Git hooks execute with user permissions by design

2. **Python Execution**: Hooks execute Python code
   - **Mitigation**: Review hook content before installation
   - **Why**: Necessary for hook functionality

3. **Local File System Access**: Reads/writes files
   - **Mitigation**: Path validation, whitelist of allowed hooks
   - **Why**: Required for Git hook management

### Out of Scope

The following are **not** considered security vulnerabilities:

- ❌ User installs malicious hooks manually (without CI Guardian)
- ❌ User has malware on their system already
- ❌ User provides malicious repository path intentionally
- ❌ Vulnerabilities in dependencies (report to upstream)
- ❌ Social engineering attacks

## 🏆 Security Hall of Fame

We recognize security researchers who help keep CI Guardian secure:

<!-- Future contributors will be listed here -->

_No vulnerabilities reported yet. Be the first!_

## 📚 Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE List](https://cwe.mitre.org/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

## 📞 Contact

- **Security Issues**: https://github.com/jarkillo/ci-guardian/security/advisories/new
- **General Questions**: https://github.com/jarkillo/ci-guardian/issues
- **Maintainer**: [@jarkillo](https://github.com/jarkillo)

## 🔄 Policy Updates

This security policy may be updated from time to time. Check back periodically for changes.

Last updated: 2025-10-30
