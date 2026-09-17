---
name: git-integration
description: Guides worktree isolation, branching strategies, merge conflict detection, resolution protocols, and safe integration of parallel code streams.
---

# Git Integration Skill

Procedures for orchestrating multiple agent contributions safely with Git.

## Procedures

1. **Worktree & Branch Isolation**:
   - For independent features, assign distinct worktrees or branches (e.g. `feature/backend-api`, `feature/frontend-ui`).
   
2. **Pre-Merge Validation**:
   - Check file diffs against `ownership-map.json`.
   - Run tests on isolated branches before merging into the integration target.

3. **Conflict Protocol**:
   - When merge conflicts occur, identify the competing owners.
   - Never arbitrarily discard either branch's code; re-synchronize based on the architectural contract.
