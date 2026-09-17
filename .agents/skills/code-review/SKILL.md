---
name: code-review
description: Systematic code audit checklist covering correctness, design patterns, security pitfalls, maintainability, test coverage, and documentation.
---

# Code Review Skill

Rigorous, impartial code inspection guidelines for Antigravity code reviewers.

## Checklist

1. **Architecture & Contract Compliance**:
   - Does the implementation abide by `architecture.json` and `api-contract.json`?
2. **Correctness & Edge Cases**:
   - Are null/undefined values, network timeouts, and concurrency handled?
3. **Security Audit**:
   - Are inputs sanitized? No SQL/Command injections? No hardcoded keys?
4. **Test Adequacy**:
   - Do tests cover non-trivial branching paths and error scenarios?
