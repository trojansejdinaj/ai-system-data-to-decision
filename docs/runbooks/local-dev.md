# Local Development Workflow

## Prerequisites

- Python 3.12+
- `uv` (Python package/dependency manager)
- Docker + Docker Compose
- Git

## Initial Setup

### 1. Clone & Install Dependencies

```bash
git clone <repo-url>
cd applied-ai-systems/portfolios/01-ai-system-data-to-decision
make sync
```

This runs `uv sync` to install all dependencies (FastAPI, SQLAlchemy, Alembic, etc.) into a virtual environment.

### 2. Configure Environment

Copy the template and set your database password:

```bash
cp .env.example .env
```

Edit `.env` and set `POSTGRES_PASSWORD` to a real value:

```env
POSTGRES_DB=d2d_db
POSTGRES_USER=d2d_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_PORT=55432
DATABASE_URL=postgresql+psycopg://d2d_user:your_secure_password_here@localhost:55432/d2d_db
```

> **Warning:** Never commit `.env` to git. It's in `.gitignore`.

### 3. Start the Database

```bash
make db-up
```

This starts Postgres 16 in a Docker container. Check logs:

```bash
make logs
```

The database is ready when you see:
```
database system is ready to accept connections
```

### 4. Run Migrations

```bash
make migrate
```

This waits for the database to be healthy, then runs all pending migrations. See [migrations runbook](./migrations.md) for details.

### 5. Start the API

```bash
make run
```

The API starts on `http://localhost:8000` with auto-reload enabled.

Verify it's running:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

---

## Daily Workflow

### Running the App

```bash
make run
```

The API auto-reloads when you edit Python files in `src/`.

### Running Tests

```bash
make test
```

Runs pytest on all files in `tests/`.

### Code Quality

Format your code:
```bash
make fmt
```

Lint and auto-fix:
```bash
make lint
```

Both use `ruff` (fast Python linter/formatter).

### Creating a New Migration

After modifying SQLAlchemy models, create a migration:

```bash
make revision m="add users table"
```

This generates a migration file in `src/app/db/migrations/versions/`. Edit it if needed, then apply:

```bash
make migrate
```

---

## Database Management

### Check DB Status

```bash
docker compose ps
```

### View DB Logs

```bash
make logs
```

### Stop the Database

```bash
make db-down
```

This stops the container but preserves the volume (data persists).

### Reset the Database

To start fresh:

```bash
make db-down
docker volume rm $(docker volume ls -q | grep d2d)
make db-up
make migrate
```

> **Warning:** This deletes all data. Use only in local dev.

### Connect to the Database Manually

```bash
docker compose exec db psql -U d2d_user -d d2d_db
```

Then run SQL queries (e.g., `SELECT COUNT(*) FROM my_table;`).

---

## Troubleshooting

- **Port already in use:** Docker Compose tries to bind port 55432. Kill the process or change `POSTGRES_PORT` in `.env`.
- **Database not ready:** Run `make db-wait` to manually wait for readiness.
- **Migrations fail:** Check `make logs` and verify `DATABASE_URL` in `.env`.
- **Import errors:** Run `make sync` to reinstall dependencies.

See [troubleshooting runbook](./troubleshooting.md) for more.

---

## Key Make Targets

| Command | Purpose |
|---------|---------|
| `make sync` | Install/update dependencies |
| `make run` | Start the API (port 8000) |
| `make test` | Run tests |
| `make fmt` | Format code |
| `make lint` | Lint and auto-fix |
| `make db-up` | Start Postgres |
| `make db-down` | Stop Postgres |
| `make db-wait` | Wait for DB readiness |
| `make migrate` | Apply migrations |
| `make revision m="msg"` | Create a new migration |
| `make logs` | Tail Docker logs |

---

## Next Steps

- Read [architecture](../architecture/) docs for system design
- See [database runbook](./database.md) for schema and connection details
- Check [migrations runbook](./migrations.md) for managing schema changes
