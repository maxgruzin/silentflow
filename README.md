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
Completed runtime, frontend, custom player, and SEO work is described below.
Production verification and rollout remain separate steps.

## Runtime upgrade completed (2026-10-03)

- Python 3.14.8, Django 6.1.1, Pillow 12.3.0, psycopg 3.3.6,
  sorl-thumbnail 13.1.0, Gunicorn 26.2.0, and their runtime dependencies are
  pinned in `requirements.txt`. Obsolete and unused Python dependencies were
  removed. The frontend pass below also removes the old browser dependencies.
- Corrected the app module and PostgreSQL app registration, replaced removed
  URL APIs, preserved Unicode slugs, and added GET/HEAD handling with 405 for
  unsupported methods. Missing pages return 404; legacy release links redirect
  to their matching release instead of the homepage.
- Artist listing queries fell from 82 to 2. Related releases are active-only
  and limited to six; admin relationship lists use joined queries. Artist
  release links stay on the current host.
- Warm local requests now use 1 query for home, 1 for catalogue, 2 for artists,
  and 5 for the sampled release. Cold thumbnail generation still costs extra
  database queries and CPU; use the image preparation command below before rollout.
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

Twenty-six regression tests pass against an isolated PostgreSQL 18 container, covering
public pages, hidden releases, legacy and Unicode URLs, HTTP methods, artist
query counts, admin lists/forms, security headers, missing thumbnail repair,
responsive AVIF/JPEG output, uncropped website images, metadata, safe external
links, lossless downloads, catalogue redirects, and local media byte ranges.
SEO checks cover sitemap exclusions, Unicode canonical URLs, indexing controls,
social metadata, accurate release/track data, and safe JSON-LD serialization.
Public upload, static, and thumbnail permissions are checked under Gunicorn's
restrictive umask so the separate nginx container can still read new assets.
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
New public asset files use mode 0644 and directories use 0755, including thumbnail
directories created under Gunicorn's umask 0027. Existing directories need the
one-time permission preparation below. These are public media/static directories;
never apply these permissions to configuration, secrets, or private backups.

The legacy image is retained locally as `silentflow-local-backend:legacy-baseline`.
Rollback requires matching application source and runtime, because development
Compose bind-mounts the source directory; switching the image alone is not a
source rollback. Keep the database backup private and copy it to your backup
location before removing local artifacts.

### Production commands for the owner

Run these stages on the **Linux VM in Bash**, not in local PowerShell. They keep
the existing Compose project, network, and volumes and replace only `backend`.
Do not run `compose down`, `down -v`, or start the whole stack. The image overlay
is `django/compose.release.yml`; `--no-deps` avoids starting the unused Redis
dependency or any shared services. See [Docker's Compose options](https://docs.docker.com/reference/cli/docker/compose/up/).

**1. Inspect and retain the working release.** Adjust the project path and backup
destination first. Use a private backup disk/location with room for media, static
files, and the current image; the 40 GB VM may not have space for another copy.
Pause admin edits/uploads until verification finishes. Stop on any failed command.

```bash
cd /var/containers/silentflow
set -eu
umask 077
SF_BACKUP_ROOT=/path/to/private/backup
test -d "$SF_BACKUP_ROOT"
df -h . "$SF_BACKUP_ROOT"
du -sh media

SF_PROJECT=$(docker inspect -f '{{ index .Config.Labels "com.docker.compose.project" }}' silentflow_backend)
test -n "$SF_PROJECT"
test "$SF_PROJECT" != '<no value>'
docker inspect -f '{{range .Mounts}}{{println .Destination "<-" .Source}}{{end}}' silentflow_backend
docker exec pgdb psql -X -U postgres -d silentflow -c 'SHOW server_version;'
```

Verify the mounts really are this project's `/home/app/media` and
`/home/app/staticfiles`, and that the database runs **stable PostgreSQL 15 or
newer**. Stop if it is older or a beta; upgrading the shared database is a separate
operation. The supplied proxy templates already forward HTTPS information and
route `/robots.txt` and `/sitemap.xml` to Django; confirm the deployed templates
match them. No proxy configuration change is part of these commands.

```bash
SF_RELEASE=$(date -u +%Y%m%dT%H%M%SZ)
SF_BACKUP="$SF_BACKUP_ROOT/silentflow-$SF_RELEASE"
mkdir -m 700 "$SF_BACKUP"
SF_PREVIOUS_IMAGE="silentflow:rollback-$SF_RELEASE"
docker image tag "$(docker inspect -f '{{.Image}}' silentflow_backend)" "$SF_PREVIOUS_IMAGE"
printf '%s\n' "$SF_PREVIOUS_IMAGE" > "$SF_BACKUP/image-tag"
printf '%s\n' "$SF_PROJECT" > "$SF_BACKUP/compose-project"
cp docker-compose.yml docker-config.env "$SF_BACKUP/"
docker image save "$SF_PREVIOUS_IMAGE" > "$SF_BACKUP/application-image.tar"
docker exec pgdb pg_dump -U postgres -d silentflow -Fc > "$SF_BACKUP/database.dump"
docker exec -i pgdb pg_restore --list < "$SF_BACKUP/database.dump" > "$SF_BACKUP/database-contents.txt"
tar -C media -cpf "$SF_BACKUP/media.tar" .
docker run --rm --network none --volumes-from silentflow_backend:ro \
  --entrypoint tar "$SF_PREVIOUS_IMAGE" -C /home/app/staticfiles -cf - . > "$SF_BACKUP/static.tar"
tar -tf "$SF_BACKUP/media.tar" > /dev/null
tar -tf "$SF_BACKUP/static.tar" > /dev/null
```

Use the actual database owner if it is not `postgres`. Listing the dump checks
readability, not full restorability; retain a separately verified backup. Keep
the backup off the public media/static mounts. Retain the old `django/` source
too if it has changes not included in the running image.

**2. Copy the reviewed application files and prepare the candidate.** Transfer the
updated `django/` tree, including new files such as `sf/seo.py` and the social PNG.
The current development tree includes uncommitted files, so `git pull` alone will
not transfer all the work. Exclude `artifacts`, `media`, `staticfiles`, local
settings, and local credentials. Preserve the server's parent `docker-compose.yml`
and merge the settings from `django/.env.example` into `docker-config.env`.
Keep existing database values and `DJANGO_PORT=8000`; use production
`config.settings`, `DEBUG=0`, `SITE_INDEXABLE=1`, and a new private secret.

```bash
export SILENTFLOW_IMAGE="silentflow:release-$SF_RELEASE"
chmod 600 docker-config.env
docker build -t "$SILENTFLOW_IMAGE" django
sf_compose() {
  docker compose -p "$SF_PROJECT" -f docker-compose.yml -f django/compose.release.yml "$@"
}
sf_compose config --quiet
sf_compose run --rm --no-deps backend python manage.py check --deploy
```

Only the documented HSTS subdomain/preload warnings are expected. Resolve any
other errors before continuing. The following one-time ownership adjustment is
limited to the two public Silent Flow mounts inspected above. It allows UID 10001
to generate thumbnails and collect static files while nginx retains read access.
It does not follow symlink directories or change any nginx/pgdb/certbot storage.

```bash
docker run --rm --network none --user 0 --volumes-from silentflow_backend \
  --entrypoint sh "$SILENTFLOW_IMAGE" -c '
    set -eu
    for root in /home/app/media /home/app/staticfiles; do
      test -d "$root"
      find "$root" -xdev -type d -exec chown 10001:10001 {} +
      find "$root" -xdev -type f -exec chown 10001:10001 {} +
      find "$root" -xdev -type d -exec chmod 755 {} +
      find "$root" -xdev -type f -exec chmod 644 {} +
    done
  '
sf_compose run --rm --no-deps backend python manage.py migrate --plan
```

Review that plan before continuing. Only the documented `auth.0012` migration
is expected on the old database (or no pending migrations if already applied).
Stop if the plan differs; do not apply an unexpected plan automatically.

```bash
docker exec -i pgdb psql -X -v ON_ERROR_STOP=1 -U postgres -d silentflow \
  < django/scripts/migrate_django_6_1.sql
sf_compose run --rm --no-deps backend python manage.py migrate --check
sf_compose run --rm --no-deps backend python manage.py prepare_images --profile card
sf_compose run --rm --no-deps backend python manage.py prepare_images --profile landscape
```

Image preparation is sequential and may take time on two CPUs. Watch free disk
space; it retains originals and existing cache files. It can be rerun safely.

**3. Replace only Silent Flow, then verify through the public proxy.** Allow a
brief interruption while the container is replaced and static files are copied.

```bash
sf_compose up -d --no-deps --no-build backend
sf_compose logs --tail=80 backend
sf_compose exec -T backend python manage.py migrate --check
curl --fail --silent --show-error --max-time 30 https://silentflow.org/about/ > /dev/null
curl --fail --silent --show-error --max-time 30 https://silentflow.org/robots.txt
curl --fail --silent --show-error --max-time 30 https://silentflow.org/sitemap.xml > /dev/null
curl --fail --silent --show-error --head --max-time 30 https://silentflow.org/static/images/social-default.png
curl --silent --show-error --head --max-time 30 https://silentflow.org/catalogue/
```

Expect robots to advertise the sitemap (not `Disallow: /`), the preview to return
200 with `image/png`, and `/catalogue/` to redirect permanently to `/releases/`.
Open a release, check an AVIF request returns `image/avif`, test playback and seek
to the middle of an MP3 (a range request should return 206). Check admin login and
an image upload, both download buttons, and mobile navigation. Inspect page source
for production canonical URLs and absence of `noindex` on public pages. Submit
`https://silentflow.org/sitemap.xml` in Search Console after those checks.

If the app is running but the proxy returns 502 after replacement, its upstream
may still refer to the old container IP. Coordinate that with the proxy owner;
these commands do not reload or recreate the shared nginx container.

**4. Roll back the application if verification fails.** In the same shell, the
variables remain set. For a later session, set `SF_BACKUP` to the retained backup
directory, reload `SF_PROJECT` from `compose-project`, and redefine `sf_compose`
as above. The old image contains the old source; never rebuild it using new code.

```bash
sf_compose stop backend
cp "$SF_BACKUP/docker-config.env" docker-config.env
export SILENTFLOW_IMAGE=$(cat "$SF_BACKUP/image-tag")
docker image inspect "$SILENTFLOW_IMAGE" > /dev/null
docker run --rm -i --network none --user 0 --volumes-from silentflow_backend \
  --entrypoint tar "$SILENTFLOW_IMAGE" -C /home/app/staticfiles -xf - < "$SF_BACKUP/static.tar"
sf_compose up -d --no-deps --no-build backend
sf_compose logs --tail=80 backend
```

If the tagged image was removed, load `application-image.tar` with `docker image
load -i` before rolling back. Do not automatically restore the database or shrink
`first_name`: the field widening remains compatible with the old application,
and restoring a dump would discard subsequent data. Retain new media and caches.
This procedure has been checked locally; it has not been run on the production VM.

## Frontend and images completed (2026-10-03)

The revised visual pass uses the #131313 background with neutral grays and
subtle cool accents. Archivo is hosted locally, with weight 900 for headings.
Its font files and SIL Open Font License are in `static/fonts/archivo` (source:
[Google Fonts Archivo](https://github.com/google/fonts/tree/main/ofl/archivo)).
The floating logo opens the original horizontal navigation style, using native
HTML details with keyboard access, Escape, and outside-click handling.
The homepage introduction pairs the circular logo with two overlapping muted
slate-blue and gray circles, with broad translucent bands like the submissions
panel, and a
subtle gray-blue panel, followed by the latest 25 active releases. Release titles,
descriptions and links are rendered in HTML; the first release image loads eagerly
and the remaining responsive images are lazy-loaded. Local checks at 320, 390,
1440 and 3840 px loaded only 3-5 release images initially; warm rendering used one
database query (about 220 ms locally, not a production benchmark). This keeps the
extra releases crawlable while limiting initial image traffic, following
[Google's lazy-loading guidance](https://developers.google.com/search/docs/crawling-indexing/javascript/lazy-loading).
Artwork stays fixed to the viewport as its banner scrolls past. Reduced-motion mode uses normal
scrolling images. Website-image derivatives preserve their
original proportions, avoiding the earlier extra crop. Release pages use that
artwork as a background, with a cover fallback when no website image exists.
Releases have searchable cover cards and MP3/lossless download links. Artists
have readable biographies and linked artwork, including artists without a bio.
About introduces the label and gives submissions a dedicated email invitation.

The public catalogue now lives at `/releases/`; `/catalogue/` permanently
redirects there. Page titles, descriptions, canonical URLs, and social metadata
are present. Set `SITE_URL` to the public origin (default:
`https://silentflow.org`). Local debug pages request no indexing. The licensing
copy asks visitors to check release terms and enquire about video use.

Local CSS and small vanilla-JS files replace jQuery, Materialize, remote font
requests, and the obsolete Universal Analytics snippet. No analytics replacement
or frontend build system was added.

### Custom player

The desktop/mobile reference images are implemented as a compact glass-style
player fixed to the bottom center. A track's play/pause button opens it. There is
one shared audio element, no audio download before the visitor presses play, and
no separate native player in each row. Controls include play/pause, previous,
next, elapsed/remaining time, artist/title, track number, a clickable and
keyboard-accessible seek bar, shuffle, repeat off/all/one, and close. Shuffle
visits each playable track before repeating. Close stops audio and returns focus
to the initiating track. Browser Media Session controls are supported where
available; device volume controls remain available. Without JavaScript, track
links open the audio directly. Playback is scoped to the current release page;
ordinary page navigation stops it.

Local media responses now support single byte ranges for real seeking tests,
through `config/media_docker_local.py`. The handler is restricted to debug mode
and the local URL configuration. Production media delivery remains with nginx.

Optional browser checks live in `scripts/test_player.cjs`. Install Playwright
as a development tool (no runtime frontend dependency), then run against the
local app with a release containing at least three playable tracks:

```powershell
npm install --prefix artifacts/browser --no-save --package-lock=false playwright
node scripts/test_player.cjs
```

The script uses installed Microsoft Edge by default; `SF_TEST_BROWSER` selects
another installed Chromium channel, `SF_TEST_URL` selects the app origin, and
`SF_TEST_RELEASE` selects the release path. It checks actual browser audio events
using a local fixture, plus real catalogue MP3 playback and seeking. Coverage
includes track changes, all repeat modes, shuffle without duplicates, slider
mouse/keyboard input, close, rapid switching, failed audio/retry, and no-JS links
at 1440, 390, and 320 px.

### Prepare responsive images before rollout

Pillow generates AVIF derivatives with JPEG fallbacks; originals are unchanged.
Cards offer 320/640/960 px variants; homepage and release backgrounds offer
960/1920/2880 px at their original aspect ratio. AVIF quality is 55, and JPEG
fallback quality is 85. The optional square `cover` profile retains 600/960 px
variants. Background `sizes` values account for the height as well as width of
the area filled by `object-fit: cover`; release backgrounds adjust when their
container changes size. This avoids mobile browsers picking a small image and
stretching it over a tall section. Small originals are never enlarged. Encoding
uses one thread per image. Sizes and quality settings live in `sf/images.py`.

The initial benchmark across all 165 active covers used 600 px AVIF at quality 35:
it totalled 2,265,139 bytes versus 2,587,031 bytes for the old 300 px JPEG at quality
75: **12.4% smaller overall at twice the width**. 146 of 165 covers were individually
no larger. Additional responsive sizes and retained JPEGs do consume cache space;
this comparison describes a single delivered variant, not total disk savings.
The current, sharper quality-55 profiles trade some of those savings for detail;
the initial 12.4% figure does not describe the current profiles.

Generation runs on first use, so prepare the cache before serving traffic on the
small VM. This sequential command reuses existing derivatives and does not clear
old files. Run it inside the updated Silent Flow application container; locally:

```powershell
docker compose -f compose.local.yml exec backend python manage.py prepare_images --profile card
docker compose -f compose.local.yml exec backend python manage.py prepare_images --profile landscape
```

Use `--limit N` to process the latest N releases in a smaller batch (0 means all).
The current local card cache and the latest 25 landscape images are prepared.
Older landscape derivatives remain cached at the previous quality; prepare the
new landscape profile for all releases before deployment. New releases generate missing
variants on demand, or can be prepared with the same commands. Verify AVIF media responses on
production during rollout; shared nginx configuration was not changed.

### SEO completed

`/sitemap.xml` lists the five public sections and all active releases with valid
slugs (170 URLs in the restored catalogue). It uses one database query and excludes
admin pages, unpublished releases, and redirect URLs. No modification dates are
invented: the catalogue has no reliable updated-at field. Canonical URLs use
`SITE_URL`, encode Unicode paths, and omit query parameters. See
[Google's sitemap guidance](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap).

Production `/robots.txt` advertises the sitemap and excludes `/control/`.
`DEBUG=True` or `SITE_INDEXABLE=0` disables indexing through robots.txt, page
metadata, and an `X-Robots-Tag` header. Use the latter setting for staging even
with debug disabled. Admin and error responses always request no indexing;
these directives are crawler instructions, not access controls.

Pages include Organization/WebSite JSON-LD; release pages also include
[MusicAlbum](https://schema.org/MusicAlbum), artists, ordered recordings,
durations, genres, catalogue identifiers, and audio URLs from the visible
catalogue. Serialization escapes script delimiters. No ratings or per-release
licences are assumed. The existing five-query release rendering is preserved.

Open Graph and Twitter metadata share the page title and description. Releases
reuse the cached 960 px JPEG cover fallback, including dimensions and alt text.
Other pages use `static/images/social-default.png`, a 1200 x 630 card made from
the existing logo and Archivo font (about 84 KiB). The optional development
script `node scripts/render_social.cjs` regenerates it using the same Playwright
setup as the player checks; production serves the static PNG directly.
See the [Open Graph specification](https://ogp.me/).

Local browser checks passed for home, releases, artists, About, and a release:
valid JSON-LD, matching canonical/social metadata, available PNG/JPEG previews,
no mobile overflow, and no browser/HTTP errors. Local robots blocks indexing.
After deployment, verify the public robots/sitemap and preview image URLs
through the existing proxy, then submit the sitemap in Search Console. Public
crawler validation and search indexing cannot be checked on localhost.
The updated production image also built successfully. A temporary container with
no network access verified non-root static collection (including the social card),
production robots, and indexable page metadata with a simulated HTTPS proxy
header. Deployment checks retained only the two documented HSTS warnings.

### Frontend verification and remaining work

Edge checks at 1440, 390, and 320 px covered home, releases, artists, About, and
a release page: no horizontal overflow, missing visible images, local HTTP errors,
or JavaScript errors. Menu keyboard interaction, release search, audio playback,
single-track playback, and navigation without JavaScript passed. Automated axe
checks reported no WCAG A/AA violations on those pages at 1440 and 390 px; these
checks are not a substitute for a full accessibility review. Screenshots and
browser scripts are under ignored `artifacts/browser`.

No database schema changes are needed for the frontend or SEO passes. No deployment was
performed. Next: verification on the actual server and the documented backup/rollout
steps. The owner changed the initial visual
plan to restore the floating logo menu, neutral gray palette, Archivo, and parallax;
the current implementation follows that revision.

[![CC BY 4.0][cc-by-shield]][cc-by]

[cc-by]: http://creativecommons.org/licenses/by/4.0/
[cc-by-shield]: https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg
