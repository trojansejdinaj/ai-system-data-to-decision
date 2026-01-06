# Database Runbook

## Overview

The system uses **PostgreSQL 16** as the primary data store. Database is managed locally via Docker Compose and migrations via Alembic (SQLAlchemy).

- **Host:** `localhost`
- **Port:** `55432` (default, configurable in `.env`)
- **Database:** `d2d_db` (default)
- **User:** `d2d_user` (default)
- **Password:** Set in `.env` (required)

---

## Connection String

The app connects via this SQLAlchemy URL:

```
postgresql+psycopg://d2d_user:PASSWORD@localhost:55432/d2d_db
```

This is set in `.env` as `DATABASE_URL` and read by:
- The FastAPI app (`src/app/core/config.py`)
- Alembic (`alembic.ini`)

---

## Starting & Stopping

### Start the Database

```bash
make db-up
```

Starts Postgres 16 in a Docker container with these features:
- Volume mount (`d2d_pg`) for persistence
- Healthcheck every 2 seconds (timeout 3s, retries 30)
- Environment variables loaded from `.env`

### Stop the Database

```bash
make db-down
```

Stops the container. **Data persists** in the Docker volume.

### Tail Logs

```bash
make logs
```

Shows real-time container output. Look for startup messages or errors.

---

## Health Checks

### Wait for Readiness

The `make migrate` target automatically runs `make db-wait`:

```bash
make db-wait
```

This polls `pg_isready` every second until Postgres responds. Used to avoid race conditions when the app starts before the DB is ready.

### Manual Check

```bash
docker compose exec db pg_isready -U d2d_user -d d2d_db
```

Returns:
- `accepting connections` — DB is ready
- `rejecting connections` — DB is starting up

---

## Direct Access

### Connect via psql

```bash
docker compose exec db psql -U d2d_user -d d2d_db
```

Then run SQL:

```sql
\d                    -- List tables
\dt                   -- List tables only
SELECT * FROM alembic_version;  -- Check migration version
SELECT COUNT(*) FROM your_table;  -- Count rows
```

Exit with `\q`.

### Connect from Your Machine

```bash
psql postgresql://d2d_user:PASSWORD@localhost:55432/d2d_db
```

(Requires `psql` installed locally.)

---

## Data Persistence

### Volume Storage

Data is stored in a Docker named volume called `d2d_pg`:

```bash
docker volume ls | grep d2d
```

To inspect:

```bash
docker volume inspect d2d_pg
```

Shows the mount path on your host machine.

### Backups

To export data:

```bash
docker compose exec db pg_dump -U d2d_user -d d2d_db > backup.sql
```

To restore:

```bash
cat backup.sql | docker compose exec -T db psql -U d2d_user -d d2d_db
```

---

## Reset/Clean Database

### Soft Reset (Keep Container)

```bash
docker compose down
docker volume rm $(docker volume ls -q | grep d2d)
docker compose up -d
make db-wait
make migrate
```

### Hard Reset

```bash
docker compose down -v  # -v removes volumes
docker compose up -d
make db-wait
make migrate
```

> **Warning:** This deletes all data. Use only in local dev or testing.

---

## Configuration

All database config is in `.env`, which is sourced by `docker-compose.yml` and the app:

```env
POSTGRES_DB=d2d_db
POSTGRES_USER=d2d_user
POSTGRES_PASSWORD=__SET_IN_.ENV__   # MUST be set
POSTGRES_PORT=55432
DATABASE_URL=postgresql+psycopg://d2d_user:__SET_IN_.ENV__@localhost:55432/d2d_db
```

Template is in `.env.example`. Never commit `.env`.

---

## Common Tasks

### Check Migration Status

```bash
docker compose exec db psql -U d2d_user -d d2d_db -c "SELECT * FROM alembic_version;"
```

Shows the current migration ID.

### Count Rows in a Table

```bash
docker compose exec db psql -U d2d_user -d d2d_db -c "SELECT COUNT(*) FROM your_table;"
```

### List All Tables

```bash
docker compose exec db psql -U d2d_user -d d2d_db -c "\dt"
```

### Drop a Table (Careful!)

```bash
docker compose exec db psql -U d2d_user -d d2d_db -c "DROP TABLE your_table;"
```

---

## Troubleshooting

### Port Already in Use

If port 55432 is already taken:

1. Find the process: `lsof -i :55432`
2. Kill it: `kill -9 <PID>`
3. Or change the port in `.env`: `POSTGRES_PORT=55433`

### Container Fails to Start

Check logs:

```bash
docker compose logs db
```

Look for:
- Permission errors
- Port conflicts
- Invalid credentials in `.env`

### Connection Refused

Postgres is running but not accepting connections:

1. Wait longer: `make db-wait`
2. Check health: `docker compose ps` (should show `healthy`)
3. Restart: `docker compose restart db`

### Database Locked

An old connection is holding a lock:

```bash
docker compose exec db psql -U d2d_user -d d2d_db -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE datname = 'd2d_db' AND pid <> pg_backend_pid();"
```

Then try again.

---

## Next Steps

- See [local dev runbook](./local-dev.md) for setup
- See [migrations runbook](./migrations.md) for schema management
- See [decisions/0004](../decisions/0004-db-readiness.md) for why we use healthchecks
