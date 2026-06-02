# GitHub Actions — Required Secrets

Set these in your GitHub repo under **Settings → Secrets and variables → Actions**:

| Secret | Description | Example |
|--------|-------------|---------|
| `STAGING_HOST` | IP of the staging server | `34.172.62.72` |
| `STAGING_USER` | SSH username | `ubuntu` or `deploy` |
| `STAGING_SSH_KEY` | Full private SSH key content | `-----BEGIN OPENSSH...` |
| `STAGING_PORT` | SSH port (optional, default 22) | `22` |

## How the deploy works

1. Push to `stagging-deployment` → GitHub Actions triggers
2. SSH into `34.172.62.72`
3. `docker compose down && docker compose up -d --build` — rebuilds image from latest branch
4. Waits for health check at `/api/method/ping`
5. Runs `bench migrate` + `bench build` inside container
