---
name: backend-development
description: Guides the design, implementation, validation, and unit testing of backend services, APIs, and business logic.
---

# Backend Development Skill

Procedures for robust, testable, and contract-compliant backend engineering.

## Standards

1. **API Adherence**:
   - Strictly follow `api-contract.json`. Validate all incoming request schemas and outgoing response structures.

2. **Error Handling & Logging**:
   - Provide consistent error shapes `{ error: string, details?: any, status: number }`.
   - Never leak stack traces, database internals, or environment secrets to clients.

3. **Verification**:
   - Always implement automated unit tests covering happy paths, edge cases, and invalid inputs.
