# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

**Do not open a public issue for security vulnerabilities.**

Please report security vulnerabilities by emailing **blackroad.systems@gmail.com** with:

1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if any)

We will acknowledge receipt within 48 hours and provide a detailed response within 7 business days.

## Security Measures

- All dependencies are pinned to specific versions
- GitHub Actions are pinned to commit hashes
- Dependabot monitors for vulnerable dependencies
- CodeQL analysis runs on every push and PR
- Secret scanning via TruffleHog on all commits
- Dependency review on all pull requests
- NPM audit runs in CI pipeline

## Responsible Disclosure

We follow responsible disclosure practices. We ask that you:

- Allow reasonable time for us to fix the issue before public disclosure
- Do not access or modify other users' data
- Do not perform actions that could harm the service or its users

---

Copyright (c) 2024-2026 BlackRoad OS, Inc. All Rights Reserved.
