# Security Policy

## Supported Versions

Only the latest release on the `main` branch receives security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## Reporting a Vulnerability

We take the security of this project seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report
- **Preferred Method:** Use GitHub's [Private Vulnerability Reporting](https://github.com/darkdevil2806/shared-chat-extractor/security/advisories/new) feature directly on this repository.
- **Alternative:** Open a confidential security advisory or contact the maintainer directly via GitHub.

**Please do not report security vulnerabilities through public GitHub issues.**

### What to Include in Your Report
To help us triage and resolve the issue quickly, please provide:
1. A description of the vulnerability and its potential impact.
2. Step-by-step reproduction instructions or a minimal Proof of Concept (PoC).
3. The platform, Python version, and operating system used.

### Response Timeline
- **Initial Acknowledgment:** Within 48 hours of receipt.
- **Triage & Assessment:** Within 5 business days.
- **Fix & Disclosure:** Coordinated release with appropriate attribution.

---

## Scope & Guarantees

### Privacy & Data Handling
- **Local Execution Only:** This tool operates entirely on your local machine. It does not collect telemetry, analytics, or transmit extracted chat contents to third-party endpoints.
- **Zero Credential Storage:** This tool does not prompt for, store, or transmit API tokens or platform credentials.

### Out of Scope
- Issues resulting from users intentionally extracting or publishing sensitive proprietary data contained within their own chat transcripts.
- Attacks requiring physical or root access to the user's local machine.
- Circumventing platform-level rate limits, CAPTCHAs, or Terms of Service violations.
