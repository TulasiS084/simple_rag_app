---
name: software-project-management
description: Decomposes product requirements into structured project plans, task dependencies, milestone registries, and parallel execution roadmaps.
---

# Software Project Management Skill

This skill provides step-by-step procedures for managing multi-agent software engineering projects.

## Procedures

1. **Requirements Ingestion**:
   - Extract goals, technical constraints, non-functional requirements, and target timeline.
   - Clarify any ambiguous acceptance criteria with stakeholders.

2. **Work Breakdown & Task Registration**:
   - Decompose features into discrete, isolated tasks adhering to `task.schema.json`.
   - Explicitly define `owner`, `filesOrAreaOwned`, `inputs`, `outputs`, and `acceptanceCriteria`.

3. **Dependency Mapping & Parallel Stream Identification**:
   - Identify which streams can execute concurrently (e.g. Frontend UI vs. Backend APIs once the API contract is frozen).
   - Prevent simultaneous writes to shared files by distinct agents.

4. **Tracking & Progress Review**:
   - Keep `project-plan.json` updated with live milestone and task completion statuses.
