# Security Policy

## Scope

This security policy applies to **this repository** — the `mcp-buy123-vendor` MCP server code.

### In Scope

- Vulnerabilities in the MCP server implementation (e.g., improper input handling, credential exposure in logs, insecure defaults)
- Dependency vulnerabilities introduced by this project's `pyproject.toml`
- Logic flaws in tool registration, auth token handling, or REST client behaviour

### Out of Scope

- Vulnerabilities in the upstream Buy123 vendor platform itself
- Issues with Buy123's own API, authentication infrastructure, or web portal
- General security concerns about the vendor service — please report those directly to Buy123

## Reporting a Vulnerability

**Please do not open a public GitHub issue for security-sensitive findings.**

To report a vulnerability privately:

1. Email the maintainers at the address listed in `pyproject.toml` (or open a [GitHub private security advisory](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability) if available).
2. Include the following in your report:
   - A clear description of the vulnerability
   - Steps to reproduce or a proof-of-concept (if applicable)
   - Affected version(s) or commit range
   - Potential impact assessment
   - Any suggested mitigations (optional)

## Disclosure Expectations

- We aim to acknowledge receipt within **5 business days**.
- We will work with you to understand and address the issue before any public disclosure.
- We follow a **coordinated disclosure** model — please allow reasonable time for a fix before publishing details publicly.
- Credit will be given to reporters in the release notes unless anonymity is requested.

## Notes

This project wraps a third-party vendor API and is not an official product of Buy123. Security issues specific to the vendor platform are outside the maintainers' control and should be reported to the vendor directly.
