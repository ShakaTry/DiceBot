# 🔒 Security Policy

## 🛡️ Supported Versions

We actively support security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | ✅ Current        |
| < 1.0   | ❌ Not supported  |

## 🚨 Reporting a Vulnerability

### 🔐 For Security Issues

**DO NOT** create public issues for security vulnerabilities.

Instead, please report security issues through one of these channels:

1. **GitHub Security Advisories** (Recommended)
   - Go to https://github.com/ShakaTry/DiceBot/security/advisories
   - Click "Report a vulnerability"
   - Provide detailed information

2. **Private Contact**
   - Contact the maintainer directly
   - Include "SECURITY" in the subject line

### 📋 Information to Include

Please include the following information:

- **Type of issue** (e.g., buffer overflow, SQL injection, XSS, etc.)
- **Full paths** of source file(s) related to the issue
- **Location** of the affected source code (tag/branch/commit or direct URL)
- **Special configuration** required to reproduce the issue
- **Step-by-step instructions** to reproduce the issue
- **Proof-of-concept or exploit code** (if possible)
- **Impact** of the issue, including how an attacker might exploit it

### ⏱️ Response Timeline

- **Initial Response**: Within 48 hours
- **Investigation**: 1-7 days depending on complexity
- **Fix Development**: 1-14 days
- **Public Disclosure**: After fix is released

## 🔒 Security Features

### 💰 Financial Security
- **Decimal precision**: All monetary calculations use Python's `Decimal` class
- **Input validation**: Strict validation of all betting parameters
- **Rate limiting**: Built-in delays between bets
- **Audit trails**: Comprehensive logging of all financial transactions

### 🎲 Gambling Integrity
- **Provably Fair**: HMAC-SHA512 verification compatible with Bitsler
- **Nonce tracking**: Sequential nonce constraint implementation
- **Seed rotation**: Automatic seed management and verification
- **Result verification**: All game results can be independently verified

### 🛡️ Application Security
- **Dependency scanning**: Automated vulnerability detection with Safety and pip-audit
- **Code analysis**: Static security analysis with Bandit and CodeQL
- **Secret detection**: TruffleHog scanning for leaked credentials
- **Access control**: Principle of least privilege

### 🔐 Infrastructure Security
- **Environment isolation**: Separate staging/production environments
- **Secret management**: All sensitive data stored in environment variables
- **Secure communications**: HTTPS/TLS for all external communications
- **Monitoring**: Real-time security event monitoring

## 🔍 Security Scanning

### Automated Scans
Our CI/CD pipeline includes:

- **CodeQL Analysis**: Advanced security vulnerability detection
- **Bandit**: Python security linting
- **Safety**: Known vulnerability database checking
- **Semgrep**: Additional static analysis
- **TruffleHog**: Secret detection
- **Dependency Audit**: Supply chain security

### Manual Security Review
- Code review for all changes affecting financial calculations
- Regular security architecture reviews
- Penetration testing for critical updates

## 📚 Security Resources

### Best Practices
- Always use `Decimal` for monetary values
- Validate all user inputs
- Use environment variables for secrets
- Follow the principle of least privilege
- Keep dependencies updated

### Documentation
- [Provably Fair Implementation](docs/provably_fair.md)
- [Financial Security Guidelines](docs/financial_security.md)
- [Deployment Security](docs/deployment_security.md)

## 🏆 Security Hall of Fame

We recognize security researchers who help improve DiceBot's security:

<!-- Add contributors who report security issues -->

## 📞 Contact

For any security-related questions or concerns:

- **Security Issues**: Use GitHub Security Advisories
- **General Questions**: Create a discussion in the repository
- **Documentation**: Check the security documentation in `/docs`

---

*This security policy is reviewed and updated regularly to ensure it remains current with best practices and threat landscape changes.*
