# Deployment

GitHub stores source and runs CI; GitHub Pages cannot run this Python API, database or worker. A debug APK is also only a client, not a collector server.

## One Linux server with Docker

Install Docker and the Compose plugin, clone this repository, then:

```sh
docker compose up --build -d
docker compose logs -f
```

The API listens on the server's loopback port 8000, and both containers share a named persistent SQLite volume. Put Nginx or another TLS reverse proxy in front of it on your own domain. `COOKIE_SECURE=1` requires HTTPS; for local plain-HTTP testing remove this environment setting or set it to `0`.

Example Nginx location inside your existing HTTPS server block:

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 300s;
    client_max_body_size 16k;
}
```

Configure TLS certificates and edge request limits separately. Start with a few hundred tracked listings and measure collection success, disk use and job delay before increasing volume. The Python HTTP server is for controlled small-scale use; replace it for broad public traffic.

## Without Docker

Run these as two supervised services from the same working directory, under an unprivileged operating-system user:

```sh
python -m backend.server --host 127.0.0.1 --db /absolute/persistent/path/pricepulse.db
python -m backend.worker --db /absolute/persistent/path/pricepulse.db
```

Set `COOKIE_SECURE=1` in the API service environment behind HTTPS. Restart on failure with systemd or your host's process supervisor. Alternatively, host cron can call `python -m backend.worker --once --db ...` every minute; use a process lock such as `flock` to prevent overlapping cron batches.

## Backup and recovery

Use SQLite's online backup, not a bare copy of a WAL database:

```sh
python -m backend.manage backup /absolute/backup/path/pricepulse-backup.db
python -m backend.manage prune-errors
python -m backend.manage resume amazon
```

Global option `--db /path/db` goes before the subcommand if using a nondefault database. Review and fix a failed adapter before resuming it. Back up off the host and test restore. Stop API and worker before replacing the database with a backup. Preserve anonymous session identifiers as private data.

## Hosting limits

Do not store the SQLite database on an ephemeral free hosting filesystem. Free Render web services lose local files when restarted/spun down and cannot attach persistent disks. A sleeping API also cannot provide reliable continuous monitoring. This repository's Compose volume targets a persistent server instead. See [costs](COSTS.md).

No server, domain or remote database has been purchased or provisioned by this source-code delivery.
