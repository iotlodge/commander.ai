# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it by:

1. **DO NOT** open a public GitHub issue
2. Email the maintainers or open a private security advisory on GitHub
3. Include details about the vulnerability and steps to reproduce

We will acknowledge your report within 48 hours and work on a fix as quickly as possible.

## Security Best Practices

When deploying Commander.ai:

- Use environment variables for sensitive data (API keys, database credentials)
- Enable authentication in production (JWT tokens)
- Keep dependencies up to date
- Use HTTPS for all external communications
- Follow the principle of least privilege for database access
- Regularly review and rotate API keys

## Disclosure Policy

- We will investigate all legitimate reports
- We will keep you informed of our progress
- We will credit you in our security advisories (unless you prefer to remain anonymous)
