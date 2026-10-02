# silentflow

Silent Flow Label website written in Python (Django)

## Local Docker development

Run from this directory (`silentflow/django`) with Docker Desktop running.
The existing `pgdb` container must be running on `pgdb_ain_ntwrk`, with the
restored `silentflow` database. Database credentials come from
`../docker-config.env`; keep that file private. Copied media lives in `../media`.

```powershell
docker compose -f compose.local.yml up --build -d
docker compose -f compose.local.yml exec backend python manage.py check
docker compose -f compose.local.yml logs --tail=100 backend
```

Open http://localhost:8000/ (admin: http://localhost:8000/control/).
Source edits reload automatically. Django serves static files and media locally.
The app is bound to the local machine only. It now runs Python 3.14.8 and
Django 6.1.1 with pinned current runtime dependencies. Debug mode and Django's
development server are for local use only.

The production Compose file and the shared PostgreSQL, nginx, and certbot
configurations are unchanged. The local stack starts only the application;
Redis is not used by the checked-in application settings. No migrations run
automatically. Page requests can populate the existing sorl thumbnail metadata
tables and the media cache; admin edits affect the connected local database.

```powershell
# Stop only the local Silent Flow application:
docker compose -f compose.local.yml down
```

The models use existing unmanaged tables in the PostgreSQL `label` schema.
Do not run migrations to try to recreate a missing music catalogue: restore
the database instead. Tests create their own catalogue tables in a separate,
disposable PostgreSQL database (see below).

### Original baseline (2026-10-03, before upgrade)

- Django system checks and `pip check` pass; the local container is healthy.
- Home, catalogue, artists, About, contact, a release, and admin login return
  HTTP 200. A nonexistent release returns HTTP 404.
- Database: PostgreSQL 13.21, 166 releases, 83 artists, 1,376 tracks.
- All referenced files are present: 166 covers, 162 website images, 1,376 MP3s.
  Sample images and audio return HTTP 200 with the expected content types.
- Initial measured requests: catalogue 231 queries (including thumbnail work),
  artists 82 queries, release detail 15 queries. These are local development
  observations, not production benchmarks.
- Browser interaction, audio playback/seeking, and mobile rendering still need
  browser checks. The development media server does not represent production
  nginx streaming behavior.

## Incremental upgrade plan

Keep Django templates, the existing catalogue schema, and a small dependency
set. All edits stay within Silent Flow; shared nginx, pgdb, and certbot services
are outside scope.

1. **Local baseline:** completed above. Preserve a working reference before
   changing runtime versions or presentation.
2. **Runtime and correctness:** target the latest stable Python, Django, and
   compatible maintained dependencies, pinned and tested together. As checked
   on 2026-10-03, the official pages list
   [Python 3.14.8](https://www.python.org/downloads/) and
   [Django 6.1.1](https://www.djangoproject.com/download/). Recheck when starting.
   **Prerequisite:** Django 6.1 requires
   [PostgreSQL 15+](https://docs.djangoproject.com/en/6.1/ref/databases/#postgresql-notes),
   and the owner has upgraded the local database to 19beta3. This prerequisite
   is resolved locally; verify the production database before deployment. Update removed APIs,
   declare the production web server dependency, and replace the placeholder
   tests with meaningful regression checks that account for unmanaged tables.
3. **Performance and security:** reduce repeated artist/release queries, measure
   cold and warm thumbnail requests, and tune workers for a shared 2 GB VM.
   Prefer simple caching only where measured. Externalize production secrets,
   verify hosts/cookies/CSRF/HTTPS settings, review admin access and uploads,
   audit dependencies, and establish backup/rollback steps. Coordinate any
   proxy-level protection separately without editing shared services.
4. **Images and frontend:** benchmark AVIF at larger responsive dimensions
   against existing JPEG thumbnails. Keep originals, fallbacks, and bounded
   generation sizes; generate incrementally to protect CPU and disk space.
   Add srcset, dimensions, lazy loading below the fold, semantic HTML, and
   simpler CSS/JS. Avoid adding a frontend framework or mandatory build stack.
5. **Visuals and mobile:** retain the quiet identity with clearer typography,
   spacing, contrast, keyboard focus, and touch targets. Make the logo a home
   link and add an explicit Menu control. Redesign the homepage introduction
   around the label identity and music discovery. Use larger cover-led release
   cards, clear full-release downloads, and stronger artist/release links.
   Preserve `/catalogue/` through a redirect if adopting `/releases/`.
6. **Player and About:** implement a small vanilla-JS player using the supplied
   reference image, native audio, a track list, seek/volume controls, keyboard
   access, mobile interaction, and playback error handling. Rewrite About and
   submissions with a welcoming invitation, simple email instructions, and
   restrained gradients or motion that respects reduced-motion preferences.
7. **SEO and verification:** create distinct titles/descriptions, canonical
   URLs, sitemap/robots handling, social previews, appropriate music structured
   data, and useful internal links. Incorporate Silent Flow, Silent Flow label,
   ambient label, experimental netlabel, Creative Commons music, and release
   names naturally. Verify release-specific permissions before promoting
   music for video use. Check redirects, accessibility, mobile layouts, player
   behavior, media sizes, query counts, and production configuration before
   deploying, with a database backup and a reversible application rollout.

The initial audit found deprecated URL APIs, an embedded secret and debug
defaults, artist links pointing to the live domain, unpublished recommendations,
repeated artist queries, obsolete frontend dependencies, and weak metadata.
The runtime/backend items are addressed below; frontend and SEO work remains.

## Runtime upgrade completed (2026-10-03)

- Python 3.14.8, Django 6.1.1, Pillow 12.3.0, psycopg 3.3.6,
  sorl-thumbnail 13.1.0, Gunicorn 26.2.0, and their runtime dependencies are
  pinned in `requirements.txt`. Obsolete and unused Python dependencies were
  removed. Frontend dependencies are still part of the upcoming frontend pass.
- Corrected the app module and PostgreSQL app registration, replaced removed
  URL APIs, preserved Unicode slugs, and added GET/HEAD handling with 405 for
  unsupported methods. Missing pages return 404; legacy release links redirect
  to their matching release instead of the homepage.
- Artist listing queries fell from 82 to 2. Related releases are active-only
  and limited to six; admin relationship lists use joined queries. Artist
  release links stay on the current host.
- Warm local requests now use 1 query for home, 1 for catalogue, 2 for artists,
  and 5 for the sampled release. Cold thumbnail generation still costs extra
  database queries and CPU; the upcoming image pass will address that separately.
- Stale thumbnail metadata now triggers regeneration of the missing derivative
  without deleting originals or clearing the whole cache. This also repairs
  thumbnail 404s found in the copied baseline.
- Removed the embedded production secret and insecure debug default. Production
  reads database/host/secret settings from the environment and enables secure
  cookies and HTTPS redirects. The reverse-proxy header is trusted only when
  explicitly enabled. Local settings retain HTTP for development.
- The production image runs as UID/GID 10001. Gunicorn defaults to two workers
  with two threads, bounded worker lifetimes, and stdout/stderr logging.
- With owner approval, backed up the local database and applied the built-in
  auth field-width migration. Existing `sf.0001_initial` and `sf.0002` history
  dates from 2017 and was preserved. The restored `sf.0001_initial` file describes
  unmanaged model state and generates no catalogue-table SQL. Backup location:
  `artifacts/backups/silentflow-before-django61-20261003-015537.dump` (ignored by
  Git; contains private database data). Media originals were not changed.

### Verification

Ten regression tests pass against an isolated PostgreSQL 18 container, covering
public pages, hidden releases, legacy and Unicode URLs, HTTP methods, artist
query counts, admin lists/forms, security headers, and missing thumbnail repair.
The test database has no connection to the shared `pgdb` network.

```powershell
docker compose -f compose.test.yml run --rm tests
docker compose -f compose.test.yml down
```

Django system checks, migration consistency, `migrate --check`, and `pip check`
pass. A PyPI advisory lookup found no published advisories for the installed
package versions at verification time; that does not cover OS or frontend
packages. Browser checks in Edge at 1440 px and 390 px found no horizontal
page overflow, missing images, local HTTP errors, or JavaScript errors on home,
catalogue, artists, and a release page. Playback progressed successfully.
The screenshots and temporary browser tools are in ignored `artifacts/browser`.

The production image builds, collects static files as a non-root user, and
serves a request through Gunicorn with the simulated HTTPS proxy header.
Deployment checks leave two deliberate warnings: HSTS is not applied to every
subdomain and the domain is not opted into the browser preload list. These
require checking the actual domain configuration, not blindly enabling flags.

### Production preparation (no deployment performed)

Use `.env.example` as a checklist for the existing `../docker-config.env`.
Set a new private `DJANGO_SECRET_KEY`; startup now refuses a missing secret.
Set `DJANGO_TRUST_PROXY=1` with the existing private nginx proxy, and keep the
backend port unpublished. Preserve the existing database credentials. Set
`GUNICORN_WORKERS=2` to override the copied environment file's older value of 3.
Verify a supported, stable PostgreSQL version on the VM before rollout; the
local beta database is a development environment, not a production recommendation.

Before rollout, back up the database and media, review `manage.py migrate --plan`,
and run migrations with a database owner account. Keep elevated credentials out
of the running application. The legacy catalogue models remain unmanaged.

For a SQL-only application of the change made locally, use
[`scripts/migrate_django_6_1.sql`](scripts/migrate_django_6_1.sql). It widens
`public.auth_user.first_name` from 30 to 150 characters and records
`auth.0012_alter_user_first_name_max_length` in Django's migration history.
It is transactional and safe to rerun, preserves existing `sf` history, and
rejects unexpected field definitions or missing prerequisite migrations.
The earlier `restore_local_database_permissions.sql` is a separate restore
repair; it is not needed on production if the app already has database access.

On the **Linux production VM**, from the `silentflow/django` directory:

```sh
# Save this backup somewhere private; stop if pg_dump fails.
umask 077
docker exec pgdb pg_dump -U postgres -d silentflow -Fc > ~/silentflow-before-django61.dump
# Run only after confirming the backup succeeded.
docker exec -i pgdb psql -X -v ON_ERROR_STOP=1 -U postgres -d silentflow < scripts/migrate_django_6_1.sql
```

Use the actual table-owner account if it differs from `postgres`. Alternatively,
execute the entire SQL file in a database editor connected to `silentflow` as
that owner. A lock timeout rolls back the migration; retry during a quiet period.
After deploying the updated application, run `python manage.py migrate --check`.
This SQL script does not update PostgreSQL or deploy the new application.

Ensure UID/GID 10001 can read originals and write Silent Flow's media cache,
upload directories, and existing static volume. Existing root-owned volumes
may need an ownership/permission adjustment limited to Silent Flow's storage.
The production entrypoint runs `collectstatic --noinput` at startup so the
shared nginx static volume receives updated assets; it does not run migrations.
Do not remove original media or old cached derivatives during rollout.

The legacy image is retained locally as `silentflow-local-backend:legacy-baseline`.
Rollback requires matching application source and runtime, because development
Compose bind-mounts the source directory; switching the image alone is not a
source rollback. Keep the database backup private and copy it to your backup
location before removing local artifacts.

Next: responsive AVIF images and frontend simplification, then navigation,
mobile/visual refinements, About/submissions, the reference-based player, and SEO.

[![CC BY 4.0][cc-by-shield]][cc-by]

[cc-by]: http://creativecommons.org/licenses/by/4.0/
[cc-by-shield]: https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg
