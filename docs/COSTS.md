# Costs and capacity

Software dependencies are free and open source or built into Python. Running on your own existing computer needs no cloud subscription, but uses electricity, bandwidth and a continuously running process. That is the simplest zero-subscription testing path.

| Component | Included implementation | Possible cost / boundary |
|---|---|---|
| Source hosting / CI | Public GitHub repository, standard test runners | Standard public runners are free under GitHub's documented rules; private runner minutes, larger runners, artifact/cache storage and future quotas can cost money |
| API / monitoring | Python API and separate worker | Persistent always-on server compute is required; no server was provisioned |
| Database | SQLite on one persistent volume | Disk, backup and restore capacity; never rely on a sleeping ephemeral free instance |
| Collection | Bounded HTML retrieval | Bandwidth, source rate limits, authorized feed licensing, parser maintenance; no proxy/bypass service included |
| Notifications | In-app records and browser polling | No SMS/email provider cost in this release; those providers and native push delivery require separate implementation |
| Android | Java wrapper and manual debug build | Build dependencies need downloads; Play publishing/signing and a hosted backend remain separate |
| Domain / HTTPS | Host-independent instructions | Domain registration generally costs money; TLS may be supplied by your host or certificate service |
| High traffic | Small single-server design | Edge request limits, pagination, more CPU, durable accounts, PostgreSQL and distributed queue work required |

Capacity arithmetic: 1,000 listings checked every six hours produce up to 4,000 product requests/day, plus discovery and robot requests, and around 1.46 million successful observation rows/year. At an **illustrative measured-later** 0.5–1 KB per indexed observation, that is roughly 0.73–1.46 GB/year before backups and auxiliary tables. This is a planning estimate, not a benchmark. A million products multiply it by 1,000 and are far beyond this release. Inspect actual database page size and request bandwidth on your data.

Retain observations by default to preserve recorded extrema. Error-log pruning after 30 days is provided. If you later delete historical observations, change the UI to distinguish retained-window extrema from lifetime extrema; archive or persist lifetime summary information explicitly.

Verified provider documentation on 10 October 2026:

- [GitHub Actions billing and usage](https://docs.github.com/en/actions/concepts/billing-and-usage): standard public repository runners are free; private quotas, runner types and storage limits still matter.
- [Render free instances](https://render.com/docs/free): free web services sleep after 15 minutes idle, have ephemeral files, and cannot attach persistent disks. Render grants 750 free instance hours per workspace/month. Free Postgres expires after 30 days. Free web services are unsuitable for this app's durable SQLite history and uninterrupted worker.

Check provider billing dashboards before deployment. This project does not include a promise of unlimited lifetime free hosting, storage or scheduled collection.
