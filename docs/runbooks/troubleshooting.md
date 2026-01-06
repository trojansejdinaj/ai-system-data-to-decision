# Troubleshooting Runbook

This guide covers common issues and solutions for local development.

---

## Getting Help

1. Check this runbook first
2. Search logs: `make logs`
3. Check [ADRs](../decisions/) for design decisions
4. Verify `.env` configuration

---

## Database Issues

### "Port 55432 already in use"

**Problem:** Docker Compose can't bind to the default port.

**Solution:**

1. Find what's using the port:
   ```bash
   lsof -i :55432
   kill -9 <PID>
   ```

2. Or change the port in `.env`:
   ```env
   POSTGRES_PORT=55433
   ```

3. Restart:
   ```bash
   make db-down
   make db-up
   ```

---

### "Connection refused" or "postgres not ready"

**Problem:** The app can't connect to the database.

**Solution:**

1. Check if Postgres is running:
   ```bash
   docker compose ps
   ```
   Should show `postgres ... (healthy)`

2. Wait for readiness:
   ```bash
   make db-wait
   ```

3. Check logs:
   ```bash
   make logs
   ```
   Look for error messages in the output.

4. Verify `.env`:
   ```bash
   cat .env | grep DATABASE_URL
   ```
   Should match the running container credentials.

5. Restart:
   ```bash
   make db-down
   make db-up
   make db-wait
   ```

---

### "POSTGRES_PASSWORD not set"

**Problem:** Docker Compose refuses to start because `POSTGRES_PASSWORD` is missing.

**Solution:**

1. Create `.env` from template:
   ```bash
   cp .env.example .env
   ```

2. Edit and set a password:
   ```bash
   cat .env
   # Edit POSTGRES_PASSWORD line to something like: POSTGRES_PASSWORD=devpassword123
   ```

3. Restart:
   ```bash
   make db-down
   make db-up
   ```

---

### "Database locked" or "Cannot acquire lock"

**Problem:** A long-running transaction or connection is holding a lock.

**Solution:**

1. Kill all idle connections:
   ```bash
   docker compose exec db psql -U d2d_user -d d2d_db -c \
     "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity 
      WHERE datname = 'd2d_db' AND pid <> pg_backend_pid();"
   ```

2. Try again:
   ```bash
   make migrate
   ```

---

## Application Issues

### "ModuleNotFoundError: No module named 'fastapi'"

**Problem:** Dependencies are not installed.

**Solution:**

```bash
make sync
```

This installs all dependencies from `pyproject.toml` using `uv`.

---

### "ImportError: cannot import name 'app' from 'src.app.main'"

**Problem:** Python path or package setup is broken.

**Solution:**

1. Verify `src/` has `__init__.py`:
   ```bash
   ls src/__init__.py
   ls src/app/__init__.py
   ```

2. Reinstall:
   ```bash
   make sync
   ```

3. Try running directly:
   ```bash
   cd /path/to/repo
   uv run python -c "from src.app.main import app; print(app)"
   ```

---

### "GET /health returns 404 or 500"

**Problem:** The API isn't responding correctly.

**Solution:**

1. Check the API is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. If no response, start it:
   ```bash
   make run
   ```

3. Check stdout/stderr for errors (should show reload output).

4. Verify the code in `src/app/main.py`:
   ```bash
   grep -A5 "@app.get" src/app/main.py
   ```
   Should have a `/health` route.

---

## Dependency Issues

### "ruff: command not found"

**Problem:** Development dependencies aren't installed.

**Solution:**

```bash
make sync
```

Then verify:

```bash
uv run ruff --version
```

---

### "uv: command not found"

**Problem:** `uv` isn't installed or not in PATH.

**Solution:**

1. Install `uv`:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Add to PATH (if needed):
   ```bash
   export PATH="$HOME/.cargo/bin:$PATH"
   ```

3. Verify:
   ```bash
   uv --version
   ```

---

## Migration Issues

### "Alembic revision fails with 'No changes detected'"

**Problem:** The model change wasn't detected by Alembic.

**Solution:**

1. Verify the model was edited correctly (check imports, column definitions).

2. If you added a new model class, ensure it's imported in `env.py`:
   ```bash
   grep "from src.app.db" src/app/db/migrations/env.py
   ```

3. Create the migration manually:
   ```bash
   uv run alembic revision -m "add my_table" --autogenerate
   ```

4. Edit `src/app/db/migrations/versions/abc123_*.py` with your SQL:
   ```python
   def upgrade() -> None:
       op.create_table('my_table', ...)
   
   def downgrade() -> None:
       op.drop_table('my_table')
   ```

5. Apply:
   ```bash
   make migrate
   ```

---

### "Migration fails with SQL syntax error"

**Problem:** The generated or manual migration has invalid SQL.

**Solution:**

1. Check the error:
   ```bash
   make migrate
   ```

2. Open the migration file and fix the SQL:
   ```bash
   nano src/app/db/migrations/versions/abc123_*.py
   ```

3. Re-run:
   ```bash
   make migrate
   ```

---

### "Can't downgrade migration"

**Problem:** The `downgrade()` function is missing or broken.

**Solution:**

1. Check the file:
   ```bash
   grep -A5 "def downgrade" src/app/db/migrations/versions/abc123_*.py
   ```

2. If empty, add it manually:
   ```python
   def downgrade() -> None:
       op.drop_table('my_table')  # Or whatever undoes upgrade()
   ```

3. Try downgrading:
   ```bash
   uv run alembic downgrade -1
   ```

---

## Code Quality Issues

### "Lint errors: line too long, unused import"

**Problem:** Code doesn't match ruff's style rules.

**Solution:**

Auto-fix:

```bash
make lint
```

Or format only:

```bash
make fmt
```

Check the rules in `pyproject.toml`:

```bash
grep -A10 "\[tool.ruff" pyproject.toml
```

---

### "Pytest fails: test discovery error"

**Problem:** Tests aren't being found or imported.

**Solution:**

1. Check test file naming:
   ```bash
   ls tests/test_*.py
   ```
   Must start with `test_`.

2. Check `pytest.ini`:
   ```bash
   cat pytest.ini
   ```
   Should have `testpaths = ["tests"]`.

3. Verify imports in the test file:
   ```bash
   grep "^import\|^from" tests/test_health.py
   ```

4. Run with verbose output:
   ```bash
   uv run pytest -v
   ```

---

## Docker Issues

### "Docker daemon not running"

**Problem:** Docker service isn't started.

**Solution:**

1. Start Docker:
   ```bash
   # macOS
   open /Applications/Docker.app
   
   # Linux (systemd)
   sudo systemctl start docker
   ```

2. Verify:
   ```bash
   docker ps
   ```

---

### "Cannot connect to Docker socket"

**Problem:** User doesn't have Docker permissions.

**Solution:**

1. Add your user to the docker group:
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

2. Verify:
   ```bash
   docker ps
   ```

---

### "Container exits immediately"

**Problem:** The database container won't stay running.

**Solution:**

1. Check logs:
   ```bash
   docker compose logs db
   ```

2. Check the image:
   ```bash
   docker compose ps
   ```

3. Look for common issues:
   - Permissions problem on volume
   - Invalid environment variable
   - Port conflict

4. Reset:
   ```bash
   docker compose down -v
   docker compose up
   ```

---

## File & Permission Issues

### "Permission denied" on `.env`

**Problem:** The `.env` file has wrong permissions.

**Solution:**

```bash
chmod 600 .env
```

---

### ".gitignore not working for .env"

**Problem:** `.env` is still being tracked by git.

**Solution:**

```bash
git rm --cached .env
git commit -m "Stop tracking .env"
git status  # Should no longer list .env
```

---

## Getting More Help

1. **Check logs:**
   ```bash
   make logs
   docker compose logs db
   ```

2. **Check status:**
   ```bash
   docker compose ps
   docker system df
   ```

3. **Clean everything:**
   ```bash
   docker compose down -v
   make sync
   make db-up
   make db-wait
   make migrate
   make run
   ```

4. **Search ADRs:** Check [decisions](../decisions/) for design rationale.

---

## Next Steps

- See [local dev runbook](./local-dev.md) for setup
- See [database runbook](./database.md) for DB-specific issues
- See [migrations runbook](./migrations.md) for migration help
