---
name: software-project-management
description: Comprehensive guide for multi-agent software project management — requirements ingestion, task decomposition using schema, parallel stream identification, milestone tracking, blocker management, and sprint retrospectives.
---

# Software Project Management Skill

Procedures for managing multi-agent software engineering projects from requirements to release.

---

## 1. Requirements Ingestion

Before writing a single task:
1. Extract: goals, user stories, technical constraints, non-functional requirements (performance, scale, security), target timeline
2. Identify: what is explicitly in scope vs explicitly out of scope
3. Clarify ALL ambiguous acceptance criteria — never assume
4. Identify dependencies on external systems, third-party APIs, or design decisions

**Output**: written scope statement reviewed with the user before proceeding.

---

## 2. Task Decomposition

Decompose each feature into discrete, isolated tasks using `task.schema.json`:

```json
{
  "taskId": "TASK-003",
  "title": "Implement user registration endpoint",
  "owner": "backend-lead",
  "status": "pending",
  "priority": "high",
  "filesOrAreaOwned": ["backend/src/modules/auth/"],
  "inputs": ["api-contract.json#/endpoints/auth/register", "database/schemas/users.sql"],
  "outputs": ["backend/src/modules/auth/auth.controller.ts", "backend/src/modules/auth/auth.service.ts"],
  "acceptanceCriteria": [
    "POST /api/v1/auth/register returns 201 with user data (no password)",
    "Returns 400 with field errors for invalid email or short password",
    "Returns 409 if email already exists",
    "Password is hashed with bcrypt before storage",
    "Unit tests cover all above cases"
  ],
  "dependsOn": ["TASK-001", "TASK-002"],
  "estimatedHours": 4
}
```

**Rules for task decomposition:**
- Each task must have one and only one `owner`
- Tasks must not claim overlapping `filesOrAreaOwned`
- `acceptanceCriteria` must be specific and testable — "implement auth" is not an acceptance criterion
- `dependsOn` must be populated correctly — downstream tasks can't start until dependencies are done

---

## 3. Dependency Mapping & Parallel Streams

Identify which tasks can run in parallel once prerequisites are satisfied:

```
Phase 1 (Sequential):
  TASK-001: technical-architect → [architecture.json, api-contract.json, ownership-map.json]

Phase 2 (Sequential):
  TASK-002: data-lead → [database schema, migrations]
  (backend needs schema before implementing ORM models)

Phase 3 (PARALLEL — all can run simultaneously):
  TASK-003: backend-lead → API implementation
  TASK-004: frontend-lead → UI implementation (mocks the API)
  TASK-005: uiux-lead → design system

Phase 4 (Sequential):
  TASK-006: integration-manager → merge all streams

Phase 5 (PARALLEL):
  TASK-007: qa-lead → full test suite
  TASK-008: security-lead → security audit

Phase 6 (Sequential, after Phase 5 PASS):
  TASK-009: devops-release-lead → CI/CD + release
  TASK-010: documentation-agent → docs
```

---

## 4. Project Plan Schema

Write `project-plan.json` after decomposition:

```json
{
  "projectId": "proj-001",
  "name": "User Management API",
  "status": "in-progress",
  "startDate": "2024-09-17",
  "targetDate": "2024-09-24",
  "milestones": [
    {
      "id": "M1",
      "name": "Architecture Complete",
      "completionCriteria": "architecture.json, api-contract.json, ownership-map.json all exist",
      "status": "completed"
    },
    {
      "id": "M2",
      "name": "Implementation Complete",
      "completionCriteria": "All TASK-003..005 completed and reported",
      "status": "in-progress"
    }
  ],
  "tasks": ["<task objects per task.schema.json>"]
}
```

---

## 5. Phase Gate Criteria

**Never advance to the next phase without verifying the gate:**

| Gate | Criteria |
|---|---|
| Architecture → Implementation | `architecture.json`, `api-contract.json`, `ownership-map.json` all exist and are valid |
| Implementation → Integration | All implementation tasks reported complete |
| Integration → QA | `integration-report.json` exists with build status PASS |
| QA → Release | `qa-report.json` with status PASS + security sign-off |
| Release → Done | `release-report.json` + docs published |

---

## 6. Blocker Management

When a task is blocked:
1. **Identify**: what exactly is blocking, which agent is waiting, what is needed to unblock
2. **Escalate immediately**: do not wait — notify the blocking owner and the PM
3. **Reassign if needed**: if the blocker is unresolvable, reassign the task or adjust the plan
4. **Never** let a blocked task sit silently — it will delay the entire downstream

---

## 7. Status Tracking

Update `project-plan.json` task statuses after every agent completion:

```
pending → in-progress → completed | blocked | failed
```

After each phase completes, write a status update:
```markdown
## Sprint Status Update — 2024-09-17

### Completed
- TASK-001: Architecture contracts frozen ✅
- TASK-002: Database schema migrated ✅

### In Progress
- TASK-003: backend-lead implementing auth routes (60% complete)
- TASK-004: frontend-lead implementing login UI (40% complete)

### Blocked
- TASK-005: uiux-lead waiting for brand guidelines from client

### Next Actions
- Unblock TASK-005: request brand guidelines from client today
```

---

## 8. Sprint Retrospective

After every release:
1. What went well?
2. What took longer than expected and why?
3. What should be done differently next sprint?
4. What technical debt was accumulated that needs to be addressed?
5. Update estimates based on retrospective findings

---

## 9. Non-Polling Multi-Agent Orchestration Protocol

### The Reactive Lifecycle
Multi-agent systems operate on an asynchronous, reactive event loop:
1. **Dispatch**: The orchestrator (`project-manager` or `workflow-manager`) invokes specialist agents via `invoke_subagent`.
2. **State Record**: Record dispatched tasks in `project-plan.json` or `workflow-state.json` with status `in-progress`.
3. **Yield Turn**: The orchestrator **stops calling tools** and concludes its turn immediately after dispatching.
4. **Autonomous Wakeup**: When subagents complete their work or post messages, the runtime automatically wakes up the orchestrator and delivers all completion reports directly into context.
5. **Evaluation & Advancement**: The orchestrator parses reports, validates contract artifacts, updates task statuses (`completed` or `blocked`), and proceeds to the next phase.

### Orchestration Anti-Patterns to Avoid
- ❌ **Polling Loop**: Calling `manage_subagents(Action: "list")` or repeatedly querying task status while tasks are in progress. This consumes tokens, exhausts turn limits, and clutters transcripts.
- ❌ **Premature Status Queries**: Repeatedly messaging active subagents asking "Are you done yet?". Subagents report back automatically upon task completion.
- ❌ **Unnecessary Timers**: Setting short recurring cron timers just to check task status when the reactive runtime already provides automatic notification upon completion.

### Proper Use of `manage_subagents`
- **Cancellation**: Terminating a runaway, deadlocked, or misbehaving agent (`Action: "kill"` or `"kill_all"`).
- **Emergency Inspection**: Inspecting task state only after an explicit failure alert or stuck condition, never during normal execution flow.

