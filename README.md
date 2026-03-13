# Mealie Backup Automation

This repository contains a simple tool and a Helm chart to automate backups of your Mealie instance.

## Features
- Triggers a backup via Mealie API.
- Downloads the backup file locally.
- Notifies a success URL (e.g. Healthchecks.io).
- Deployed as a Kubernetes CronJob.
- Durable storage via hostPath mount.

## Components
- `src/backup.py`: Python script that performs the backup operations.
- `Dockerfile`: Container image based on Python 3.14 (experimental).
- `chart/mealie-backup`: Helm chart for deploying the backup job.

## Configuration (Helm Values)
| Parameter | Description | Default |
|-----------|-------------|---------|
| `mealie.url` | Your Mealie instance URL | `https://demo.mealie.io` |
| `mealie.token` | Admin API token | `""` |
| `backup.hostPath` | Path on the host node to store backups | `/opt/mealie/backups` |
| `backup.mountPath` | Path inside the container | `/backups` |
| `backup.successUrl` | URL to ping after successful backup | `""` |
| `cronSchedule` | Cron schedule for the backup | `0 2 * * *` |

## GitHub Actions
- **Lint**: Runs on every push to `main` and pull requests. Lints Python code and the Helm chart.
- **Publish**: Runs on new version tags (e.g. `v1.0.0`). Builds/pushes the Docker image and publishes the Helm chart using `chart-releaser`.

## Deployment
```bash
helm install mealie-backup ./chart/mealie-backup \
  --set mealie.url="https://mealie.yourdomain.com" \
  --set mealie.token="YOUR_API_TOKEN" \
  --set backup.hostPath="/mnt/backups/mealie"
```
