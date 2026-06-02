# PostgreSQL Migrations

This folder stores raw PostgreSQL migration/query files for Neolysis domain schema work.

Tracked files such as `001_neolysis_core_docking_kg_schema.sql` are intended to be reviewed and committed.

Local scratch files are ignored by `neolysis-backend/.gitignore`:

- `*.local.sql`
- `*.dump.sql`
- `*.bak.sql`
- `tmp/`

Alembic is still configured under `neolysis-backend/alembic/`. These raw SQL files can be translated into Alembic Python revisions when the service-layer project workflow is moved from in-memory storage to persistent PostgreSQL tables.
