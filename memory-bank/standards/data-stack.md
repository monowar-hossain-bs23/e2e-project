# Data Stack

## Overview
Basha Pass uses PostgreSQL with Django's native ORM, leveraging standard UUID4 primary keys and standard Django model fields for maximum simplicity, reliability, and built-in compatibility without external database extensions.

## Database
PostgreSQL (Latest Stable)

**Rationale**:
- Provides rock-solid ACID transactions, relational integrity, and high performance.
- Native JSONB support where semi-structured data is beneficial.
- Managed hosting available widely or self-hostable with standard Docker containers.

## ORM / Database Client
Django ORM

**Rationale**:
- Deeply integrated into Django MTV architecture and Django Admin.
- Provides robust, declarative migrations out of the box.
- Standard UUID4 primary keys (`models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`) for non-enumerable, secure IDs across entities without requiring PostgreSQL extensions or external libraries.
- Standard `EmailField` and `CharField` with normalized lowercase handling in service layers rather than database-level CITEXT.

## Decision Relationships
- **PostgreSQL + Django ORM**: Django's migrations manage the schema directly against PostgreSQL.
- **Service Layer Data Access**: Services encapsulate business invariants, audit logging, and queries, keeping models clean and focused on schema and basic validation.
