---
name: architecture-design
description: Formulates system architecture, tech stack selection, module boundaries, API schemas, and ownership maps for software projects.
---

# Architecture Design Skill

Guidelines and standards for software architecture in a multi-agent environment.

## Procedures

1. **System Boundary Definition**:
   - Establish clean separation between client (frontend/mobile), server (backend services), and persistence (database).
   - Document boundaries in `architecture.json`.

2. **Interface & Contract Freezing**:
   - Produce `api-contract.json` specifying endpoints, request payloads, response codes, and error models.
   - Once frozen, downstream agents can build in parallel against mock interfaces.

3. **Ownership Mapping**:
   - Explicitly assign directory and file paths to specific agents in `ownership-map.json`.
   - Disallow conflicting file write claims across agents.
