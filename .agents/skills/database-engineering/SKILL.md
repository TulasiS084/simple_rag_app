---
name: database-engineering
description: Best practices for schema design, migrations, relational modeling, data integrity, indexing, and seed data.
---

# Database Engineering Skill

Standard database architecture and migration workflows.

## Guidelines

1. **Schema Migration Integrity**:
   - Write deterministic, reversible migrations.
   - Maintain referential integrity and sensible primary/foreign keys.

2. **Performance & Indices**:
   - Index high-cardinality query filters and foreign key joins.
   - Avoid N+1 queries.
