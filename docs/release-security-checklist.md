# Release Security Checklist

This checklist must be completed manually by the maintainer before every public release or re-publication of this repository.
Do not skip steps or assume prior runs are still valid — re-run each check against the current state of the branch.

---

## 1. Secrets Scan

- [ ] Run a secrets scanner (e.g. `truffleHog`, `gitleaks`, or `detect-secrets`) against the **entire working tree**.
- [ ] Confirm zero findings, or document and remediate any flagged items before proceeding.
- [ ] If a secret was ever committed and later removed, treat the history as compromised — rotate the credential immediately.

```bash
# Example using gitleaks (install separately)
gitleaks detect --source . --verbose
```

> **Note:** This is a manual step. CI may run an equivalent scan, but the maintainer is responsible for confirming the result before tagging a release.

---

## 2. Git History Review

- [ ] Review the full commit history for any of the following that should not be public:
  - API tokens, session cookies, or passwords (even partial or test values)
  - Internal hostnames, IP addresses, or private endpoint URLs
  - Internal usernames, employee names, or account identifiers
  - Test data that contains real user or business records
- [ ] Use `git log -p` or a tool like `git-secrets` / `truffleHog --since-commit` to scan history.
- [ ] If sensitive data is found in history, **do not publish**. Rewrite history with `git filter-repo` and rotate any exposed credentials before proceeding.

```bash
# Scan full history with gitleaks
gitleaks detect --source . --log-opts="--all" --verbose
```

---

## 3. `.env.example` Audit

- [ ] Open `.env.example` and verify every field listed is safe to be public.
- [ ] Acceptable fields: placeholder variable names, format hints (e.g. `VENDOR_TOKEN=your_token_here`).
- [ ] Remove or redact any field that contains:
  - A real token, password, or secret (even a test one)
  - An internal URL or hostname not intended for public use
  - Any value that could be mistaken for a working credential
- [ ] Confirm `.env` itself is listed in `.gitignore` and is **not** tracked.

---

## 4. README and Documentation Review

- [ ] Read through all README examples and code snippets.
- [ ] Confirm no example implies or requires:
  - Disabling authentication or TLS verification
  - Using hardcoded credentials in source code
  - Running with elevated or unrestricted permissions
- [ ] Confirm the README clearly states that a valid, **legally authorised** vendor account is required.
- [ ] Confirm no example URL points to an internal or non-public endpoint.

---

## 5. Error Message Review

- [ ] Review error handling code in `rest_client.py`, `auth/`, and any connector that surfaces upstream responses.
- [ ] Confirm that error messages returned to callers do **not** include:
  - Raw upstream API response bodies that may contain internal stack traces or system details
  - Internal hostnames, service names, or infrastructure identifiers
  - Full request URLs with embedded tokens or credentials
- [ ] If upstream errors are forwarded verbatim, add a sanitisation layer before the public release.

---

## Sign-off

Before tagging the release, confirm all items above are checked and record the following:

| Field              | Value |
|--------------------|-------|
| Reviewer           |       |
| Date               |       |
| Branch / Commit    |       |
| Secrets scan tool  |       |
| History scan range |       |
| Notes              |       |

A release must not be tagged until this checklist is fully completed and signed off.
