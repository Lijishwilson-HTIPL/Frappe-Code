# Deployment Comment — Frappe Bench (Hephzibah Technologies)

## Repository

- **Repo:** `Lijishwilson-HTIPL/Frappe-Code`
- **Working branch:** `Lijish-up`
- **Staging branch:** `stagging-deployment` ← currently active deploy target
- **Main branch:** `main` — never push directly to this
- **Push command (staging):** `git push target stagging-deployment`

### Remotes

| Remote | URL | Purpose |
|--------|-----|---------|
| `target` | `github.com/Lijishwilson-HTIPL/Frappe-Code` | Primary push target |
| `origin` | `github.com/corporaterulers/Frappe_Crm.git` | Upstream CRM reference |
| `college` | `github.com/corporaterulers/erpnext.git` | Upstream ERP reference |

---

## App Structure

All five apps are **plain tracked directories** — no git submodules. One `git pull` fetches everything.

```
apps/
├── frappe/      # Core framework
├── erpnext/     # ERP — custom logo, Career Inquiry DocType
├── hrms/        # HR — custom logo, Job Applicant extensions
├── crm/         # SBIQ CRM — Leads Journey, auto-email, status flow
└── helpdesk/    # Helpdesk — Ticket Journey, Ticket Data Tab
```

---

## Making a Change

| Change type | Action |
|-------------|--------|
| DocType fields / schema | Edit the app JSON file directly, then `bench migrate` |
| CRM layout / fixtures | Change in UI → `bench --site mysite.local export-fixtures` |
| Python / JS logic | Edit the `.py` / `.js` file directly |

**Never** modify the schema via direct SQL or `frappe.db` calls — those changes are wiped on the next `bench migrate` or fresh install. All schema changes must live in JSON files.

---

## Local Verify Before Push

```bash
# Apply schema changes
bench --site mysite.local migrate

# Rebuild frontend (run after any JS / Vue / logo change)
bench build --app erpnext --app hrms --app crm --app helpdesk
```

---

## Commit and Push

```bash
git add apps/<changed-files>
git commit -m "feat/fix: <description>"
# Push to working branch first, then merge to staging:
git push target Lijish-up
git checkout stagging-deployment && git merge Lijish-up && git push target stagging-deployment && git checkout Lijish-up
```

**Do not commit:**
- `sites/mysite.local/site_config.json` — contains DB credentials, auto-created by `bench new-site`

---

## Deploying to an Existing Server

```bash
# 1. Stash any local changes that would block the pull
git stash push -m "local changes before pull"

# 2. Pull all app changes
git pull origin stagging-deployment

# 2a. Fix Redis configs (REQUIRED on first deploy or after server migration)
#     Redis config files hardcode the original home path. If the server user differs
#     from whoever last ran `bench setup redis`, Redis will refuse to start.
#     Run this once to regenerate configs for the current server:
~/.local/bin/bench setup redis
redis-server config/redis_cache.conf --daemonize yes
redis-server config/redis_queue.conf --daemonize yes
#     Verify both are up:
ss -tlnp | grep -E '13000|11000'

# 3. Apply DocType schema changes
bench --site mysite.local migrate

# 4. Rebuild frontend assets (frappe MUST be rebuilt separately first)
bench build --app frappe
bench build --app erpnext --app hrms --app crm --app helpdesk

# 5. Clear cache (REQUIRED — list view JS files are served dynamically via
#    the Frappe API and are cached in Redis; skipping this causes old UI to persist)
bench --site mysite.local clear-cache
bench --site mysite.local clear-website-cache

# 6. Restart services
bench restart
# Production:
sudo supervisorctl restart all
```

> **Why clear-cache is mandatory:** `project_list.js`, `task_list.js`, and other
> DocType JS files are NOT compiled into the app bundle — they are served live by
> the Frappe API and cached in Redis. Without clearing cache, the browser receives
> the old JS even after a pull + build + restart.

> **assets.json hash mismatch:** If CSS looks broken after deploy, the `bench build`
> for frappe may have updated `assets.json` with new hashes but failed to write the
> actual CSS files. Fix: run `bench build --app frappe` again explicitly (not bundled
> with other apps), then `clear-cache` and `restart`.

---

## Docker Deployment

A `Dockerfile` + `docker-compose.yml` are included for container-based deploys.

**What the Dockerfile does:**
1. Clones `stagging-deployment` from GitHub (`--depth 1`)
2. Runs `bench setup env` and installs all apps via pip (editable mode)
3. Installs frontend deps with yarn for each app
4. Regenerates `Procfile` and Redis configs inside the container (overrides local hardcoded paths)
5. Runs `bench start` as the entrypoint

**docker-compose.yml services:**

| Service | Image | Purpose |
|---------|-------|---------|
| `frappe` | built from `Dockerfile` | Bench — web + workers |
| `db` | `mariadb:10.6` | Database |
| `redis-cache` | `redis:7-alpine` | Cache layer |
| `redis-queue` | `redis:7-alpine` | Background job queue |
| `redis-socketio` | `redis:7-alpine` | Realtime / socketio |

Site data persists via a Docker volume (`frappe_sites`).

**Rebuild and redeploy after a code push:**
```bash
# Always use --no-cache so Docker pulls the latest stagging-deployment commit
docker compose build --no-cache frappe
docker compose up -d

# After containers are up — clear cache and migrate inside the container
docker compose exec frappe bench --site mysite.local migrate
docker compose exec frappe bench --site mysite.local clear-cache
docker compose exec frappe bench --site mysite.local clear-website-cache
```

> **Why --no-cache:** Without it, Docker reuses the cached `git clone` layer and
> the container runs old code even though the branch was updated.

> **Why clear-cache after Docker up:** Same as bare-metal — DocType JS files
> (list views, form views) are Redis-cached. The new container starts with a
> fresh Redis but if the site volume is shared across rebuilds, stale cache
> entries can persist. Always clear after every redeploy.

**Note:** After first `docker compose up`, the site must be created manually:
```bash
docker compose exec frappe bench new-site mysite.local \
  --db-root-password root \
  --admin-password <password>

docker compose exec frappe bench --site mysite.local install-app erpnext
docker compose exec frappe bench --site mysite.local install-app hrms
docker compose exec frappe bench --site mysite.local install-app crm
docker compose exec frappe bench --site mysite.local install-app helpdesk

docker compose exec frappe bench --site mysite.local migrate
docker compose exec frappe bench --site mysite.local clear-cache
```

---

## API Credentials

The website backend reads Frappe API credentials from:

```
/var/www/html/frappe_backend_staging/.env   (on the 185 server)
```

```env
FRAPPE_URL=http://localhost:8000
FRAPPE_API_KEY=<api-key>
FRAPPE_API_SECRET=<api-secret>
```

Generate keys: Frappe Desk → Avatar → My Profile → API Access → Generate Keys

**Do not regenerate keys unless explicitly needed.** If you do, update the `.env` on the server immediately — the website backend will fail until you do.

---

## Known Gaps

| Gap | Detail |
|-----|--------|
| Redis down after deploy | `config/redis_cache.conf` and `config/redis_queue.conf` hardcode the home path of whoever last ran `bench setup redis`. On a new server or after a user change, Redis refuses to start (port 13000/11000 not listening) and the site throws `ConnectionRefusedError`. Fix: run `~/.local/bin/bench setup redis` then start both: `redis-server config/redis_cache.conf --daemonize yes && redis-server config/redis_queue.conf --daemonize yes`. See step 2a in deploy steps above. |
| No CI/CD pipeline | Pushes to `stagging-deployment` do not trigger an automated server deploy — all deploys are manual `docker compose build --no-cache && up -d` |
| Docker site creation | Not automated — must be run manually after first container boot |
| API key sync | Regenerating Frappe API keys requires a manual `.env` update on the backend server |
| Silent Docker build failures | The Dockerfile uses `bench build ... \|\| true` — if the build fails, the container still starts with stale/missing assets. Always verify CSS/JS after a redeploy |
| website_theme.json SCSS | Use `custom_overrides` field (raw SCSS vars) + pre-compiled `theme_scss` in the fixture. Named color fields (`primary_color`, `dark_color`, etc.) cause Bootstrap SCSS compilation failure during `bench migrate` |

---

## Quick Reference

| Task | Command |
|------|---------|
| Start (dev) | `bench start` |
| Run migrations | `bench --site mysite.local migrate` |
| Rebuild assets | `bench build --app <appname>` |
| Export fixtures | `bench --site mysite.local export-fixtures` |
| Clear cache | `bench --site mysite.local clear-cache && bench --site mysite.local clear-website-cache` |
| Clear cache (Docker) | `docker compose exec frappe bench --site mysite.local clear-cache` |
| Backup database | `bench --site mysite.local backup` |
| View error logs | `tail -f logs/worker.error.log` |
| Restart (prod) | `sudo supervisorctl restart all` |
