---
name: architecture-design
description: Comprehensive guide for designing scalable software architectures — API-first design, system boundary definition, technology selection, ownership mapping, 12-factor app principles, and architecture decision records.
---

# Architecture Design Skill

Guidelines and standards for software architecture in a multi-agent engineering company.

---

## 1. Architecture Process

```
Requirements → System Boundaries → Stack Selection → API Contract → Ownership Map → ADR
```

**Never start implementation until `architecture.json`, `api-contract.json`, and `ownership-map.json` are frozen.**

---

## 2. System Boundary Definition

Establish clean separation between layers:

```
┌─────────────────────────────────┐
│          CLIENT LAYER           │
│  Web (React) │ Mobile (RN/Flutter) │
└─────────────┬───────────────────┘
              │ HTTPS / REST / GraphQL
┌─────────────▼───────────────────┐
│         API LAYER               │
│  Express / Fastify / NestJS     │
│  Auth Middleware │ Route Guards  │
└─────────────┬───────────────────┘
              │
┌─────────────▼───────────────────┐
│       SERVICE LAYER             │
│  Business Logic │ Domain Rules  │
└─────────────┬───────────────────┘
              │
┌─────────────▼───────────────────┐
│       DATA LAYER                │
│  ORM / Repository │ Cache       │
└─────────────┬───────────────────┘
              │
┌─────────────▼───────────────────┐
│       PERSISTENCE               │
│  PostgreSQL │ MongoDB │ Redis   │
└─────────────────────────────────┘
```

Document this topology in `architecture.json`.

---

## 3. Technology Selection Criteria

When selecting a technology, evaluate:
1. **Team familiarity** — prefer known tech unless there's a strong reason to switch
2. **Community & maintenance** — active development, not abandoned
3. **Production maturity** — has it been battle-tested at scale?
4. **License** — compatible with the project's license
5. **Performance** — meets the project's throughput and latency requirements

Always document the **rationale** — record what alternatives were considered and why they were rejected.

---

## 4. API-First Design

Design the API contract before any implementation. The contract is the source of truth.

```json
// api-contract.json example
{
  "version": "1.0.0",
  "baseUrl": "/api/v1",
  "endpoints": [
    {
      "method": "POST",
      "path": "/auth/login",
      "auth": false,
      "requestBody": {
        "email": "string (required, email format)",
        "password": "string (required, min 8 chars)"
      },
      "responses": {
        "200": { "accessToken": "string", "refreshToken": "string" },
        "400": { "error": "string", "code": "VALIDATION_ERROR", "details": [] },
        "401": { "error": "string", "code": "INVALID_CREDENTIALS" }
      }
    }
  ]
}
```

**Rules:**
- Every endpoint must specify: method, path, auth requirement, request schema, response schemas for all status codes
- Once frozen, do not change the contract without versioning (`/api/v2/...`)
- Breaking changes require a new version — never break existing clients

---

## 5. Ownership Map

Prevent multiple agents from writing to the same files:

```json
// ownership-map.json
{
  "ownership": [
    { "owner": "frontend-lead", "paths": ["frontend/", "public/"] },
    { "owner": "backend-lead", "paths": ["backend/src/", "backend/tests/"] },
    { "owner": "data-lead", "paths": ["database/"] },
    { "owner": "devops-release-lead", "paths": [".github/", "Dockerfile", "docker-compose.yml"] }
  ]
}
```

- No two owners may claim the same path
- Agents must never write outside their owned paths
- Shared files (package.json, README.md) must have an explicit designated owner

---

## 6. 12-Factor Application Principles

| Factor | Requirement |
|---|---|
| Codebase | One repo per deployable service |
| Dependencies | Explicit in package.json/requirements.txt |
| Config | ALL config via environment variables — never in code |
| Backing Services | Treat DB/cache/queue as attached resources (swappable via config) |
| Build/Release/Run | Strictly separate build, release, and run stages |
| Processes | Stateless processes — no session state in memory |
| Port Binding | Services expose themselves via port — not embedded in a web server |
| Concurrency | Scale via process model — horizontal scaling |
| Disposability | Fast startup, graceful shutdown on SIGTERM |
| Dev/Prod Parity | Minimize environment differences |
| Logs | Write to stdout — let the platform aggregate |
| Admin Processes | Run admin tasks as one-off processes |

---

## 7. Architecture Decision Records (ADRs)

Document every significant architectural decision in `docs/decisions/`:

```markdown
# ADR-001: Use PostgreSQL as primary database

## Status
Accepted

## Context
Need a production-grade relational database supporting ACID transactions,
full-text search, and JSON documents.

## Decision
Use PostgreSQL 16.

## Rationale
- Superior JSON support (JSONB) vs MySQL
- Better window functions and CTEs than MySQL
- Active development and community
- Supports read replicas for scaling

## Alternatives Considered
- MySQL 8: rejected — weaker JSON support
- MongoDB: rejected — ACID transactions not as mature, schema flexibility not needed

## Consequences
- Requires PostgreSQL-specific SQL syntax in migrations
- pg driver required in Node.js
```

---

## 8. Scalability Patterns

Document these decisions in `architecture.json`:
- **Caching**: Redis for session cache, API response cache, rate limit counters
- **Database reads**: Read replicas for read-heavy endpoints
- **Job queues**: Bull/BullMQ for async tasks (emails, notifications, exports)
- **CDN**: Static assets served from CDN (S3 + CloudFront / Cloudflare)
- **Rate limiting**: At API gateway level for distributed rate limiting
