# Multi-Agent Software Engineering Company

A production-grade, reusable multi-agent software engineering workforce built for Google Antigravity. This repository provides an end-to-end development organization where specialized agents collaborate across architecture, parallel implementation, continuous integration, quality assurance, security auditing, and release engineering.

---

## 1. Company Architecture & Organization Hierarchy

```
                      +-------------------+
                      |   HUMAN CLIENT    |
                      +---------+---------+
                                |
                                v
                      +-------------------+
                      |  PERSONAL MASTER  | (Global Orchestrator)
                      +---------+---------+
                                |
                                v
                      +-------------------+
                      |  PROJECT MANAGER  | (.agents/agents/project-manager)
                      +---------+---------+
                                |
        +-----------------------+-----------------------+
        |                       |                       |
        v                       v                       v
+------------------+  +-------------------+  +---------------------+
| TECHNICAL        |  | UI/UX LEAD        |  | DOCUMENTATION       |
| ARCHITECT        |  | (Design & Tokens) |  | AGENT               |
+--------+---------+  +-------------------+  +---------------------+
         |
         | (Freezes Architecture, Contracts & Ownership)
         v
+------------------------------------------------------------------+
|                  PARALLEL IMPLEMENTATION STREAMS                 |
|                                                                  |
|   +---------------+    +---------------+    +----------------+   |
|   | BACKEND LEAD  |    | FRONTEND LEAD |    | DATA LEAD      |   |
|   | (Services/API)|    | (Web UI/State)|    | (Schema/Query) |   |
|   +-------+-------+    +-------+-------+    +--------+-------+   |
|           |                    |                     |           |
|           v                    v                     v           |
|     (API Workers)      (UI Workers)          (Seed Workers)      |
|                                                                  |
|   +---------------+    +---------------+                         |
|   | MOBILE LEAD   |    | SECURITY LEAD |                         |
|   | (iOS/Android) |    | (Audit/OWASP) |                         |
|   +---------------+    +---------------+                         |
+---------------------------------+--------------------------------+
                                  |
                                  v
                    +---------------------------+
                    |    INTEGRATION MANAGER    |
                    | (Conflict Detection/Merge)|
                    +-------------+-------------+
                                  |
                                  v
                    +---------------------------+
                    |          QA LEAD          |
                    |  (Unit, Integration, E2E) |
                    +-------------+-------------+
                                  |
                     +------------+------------+
                     |                         |
                     v                         v
           +--------------------+    +--------------------+
           |   CODE REVIEWER    |    | BROWSER/E2E TESTER |
           +--------------------+    +--------------------+
                                  |
                                  v
                    +---------------------------+
                    |    DEVOPS/RELEASE LEAD    |
                    |   (Packaging & Release)   |
                    +---------------------------+
```

---

## 2. Agent Workforce Roster

| Agent Name | Role | Primary Responsibility | Directory / File Scope |
| :--- | :--- | :--- | :--- |
| **`project-manager`** | Project Manager | Requirement ingestion, planning, task dispatch, blocker tracking | `.agents/`, `project-plan.json` |
| **`technical-architect`** | Technical Architect | Tech stack selection, contract design, module boundaries | `architecture.json`, `api-contract.json` |
| **`backend-lead`** | Backend Lead | REST/GraphQL APIs, business logic, server unit tests | `backend/`, `server/` |
| **`frontend-lead`** | Frontend Lead | Web client components, state management, client tests | `frontend/`, `src/` |
| **`mobile-lead`** | Mobile Lead | Cross-platform / native mobile apps, navigation, offline sync | `mobile/` |
| **`data-lead`** | Data / Database Lead | Schemas, SQL migrations, query optimization, seeds | `database/`, `migrations/` |
| **`uiux-lead`** | UI/UX Lead | User journeys, design tokens, responsive layout rules | `design/`, `tokens.json` |
| **`security-lead`** | Security Lead | OWASP audit, secret scanning, dependency risks, auth review | Security audits, PR checks |
| **`devops-release-lead`** | DevOps & Release Lead | Build pipelines, Dockerfiles, CI/CD, release reports | `deploy/`, `release-report.json` |
| **`qa-lead`** | QA Lead | Overall test planning, defect triage, regression suites | `tests/`, `qa-report.json` |
| **`integration-manager`**| Integration Manager | Worktree merging, collision detection, automated builds | Entire codebase (synchronization) |
| **`code-reviewer`** | Code Reviewer | Line-by-line inspection, correctness, maintainability | Impartial audit (read-only) |
| **`browser-e2e-tester`** | Browser & E2E Tester | Playwright/browser automation, DOM journeys, UI regression | `tests/e2e/` |
| **`documentation-agent`**| Technical Writer | README, API manuals, architecture specs, release changelogs | `README.md`, `docs/` |

---

## 3. How to Start a Project

1. **Activate the Project Manager**:
   In Antigravity chat or CLI, type:
   ```text
   /agents
   ```
   Select **`project-manager`** (or invoke it through the global **`personal-master`**).

2. **Submit Your Product Goal**:
   ```text
   "Build a SaaS booking system with an Express API, React frontend, and SQLite database."
   ```

3. **Execution Pipeline**:
   - The Project Manager creates `project-plan.json`.
   - The Technical Architect produces `architecture.json`, `api-contract.json`, and `ownership-map.json`.
   - Backend, Frontend, and Data leads execute in parallel according to their ownership zones.
   - The Integration Manager merges outputs and verifies build integrity.
   - The QA Lead and Code Reviewer validate tests and audit code quality.
   - The DevOps Lead and Documentation Agent finalize packaging and release notes.

---

## 4. Parallel Development & Worktree Isolation

To prevent concurrent file conflicts:
1. **Ownership Map (`ownership-map.json`)**: Every file and folder is strictly assigned to one departmental lead.
2. **Contract-Driven Decoupling**: Frontend and Backend leads work concurrently against the frozen `api-contract.json`.
3. **Integration Synchronization**: The `integration-manager` is the only agent permitted to merge disparate feature streams. If semantic or structural collisions are detected, the Integration Manager coordinates resolution rather than silently overwriting code.

---

## 5. Adding New Agents & Custom Workers

When a project requires specialized capabilities (e.g. `graphql-worker`, `flutter-worker`, `ml-engineer`):
1. Use the global **`agent-template-builder`** meta-agent:
   ```text
   "Create a workspace-local worker agent named 'graphql-worker' specializing in Apollo GraphQL schemas and resolvers."
   ```
2. The agent template builder creates `.agents/agents/<worker-name>/agent.md` with appropriate YAML frontmatter and tools.
3. Update `.agents/registry/agent-registry.json` to register the new worker under its parent lead.
