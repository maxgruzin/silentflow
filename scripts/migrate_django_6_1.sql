-- Production equivalent of the SQL migration applied locally on 2026-10-03.
-- Run the entire file as the table owner, connected to database "silentflow".
-- Back up the database first. With psql, use -X -v ON_ERROR_STOP=1.
-- Compatible with the existing PostgreSQL 13 schema as well as newer servers;
-- this script does not upgrade PostgreSQL itself.
--
-- Only schema change: auth_user.first_name varchar(30) -> varchar(150).
-- Records auth.0012 so a later Django migrate will not repeat it.
-- Existing sf migration history and all catalogue tables are left untouched.

BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';
SET LOCAL search_path = public, pg_catalog;

DO $migration$
BEGIN
    IF current_database() <> 'silentflow' THEN
        RAISE EXCEPTION 'Connect to the silentflow database before running this script';
    END IF;
END
$migration$;

-- Prevent concurrent migration record inserts during the check and update.
LOCK TABLE public.django_migrations IN SHARE ROW EXCLUSIVE MODE;

DO $migration$
DECLARE
    field_type text;
    field_length integer;
    already_applied boolean;
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM public.django_migrations
        WHERE app = 'auth' AND name = '0011_update_proxy_permissions'
    ) THEN
        RAISE EXCEPTION 'Expected auth.0011 to be applied; use Django migrate to resolve earlier migrations first';
    END IF;

    SELECT data_type, character_maximum_length
    INTO field_type, field_length
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'auth_user'
      AND column_name = 'first_name';

    IF field_type IS DISTINCT FROM 'character varying'
       OR field_length IS NULL OR field_length NOT IN (30, 150) THEN
        RAISE EXCEPTION 'Unexpected auth_user.first_name definition: type=%, length=%. No changes applied.', field_type, field_length;
    END IF;

    SELECT EXISTS (
        SELECT 1 FROM public.django_migrations
        WHERE app = 'auth' AND name = '0012_alter_user_first_name_max_length'
    ) INTO already_applied;

    IF already_applied AND field_length <> 150 THEN
        RAISE EXCEPTION 'Migration history says auth.0012 is applied, but first_name is not varchar(150)';
    END IF;

    IF field_length = 30 THEN
        ALTER TABLE public.auth_user ALTER COLUMN first_name TYPE varchar(150);
    END IF;

    IF NOT already_applied THEN
        INSERT INTO public.django_migrations (app, name, applied)
        VALUES ('auth', '0012_alter_user_first_name_max_length', CURRENT_TIMESTAMP);
    END IF;
END
$migration$;

COMMIT;

-- Expected results: character varying / 150, followed by one auth.0012 row.
SELECT data_type, character_maximum_length
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'auth_user'
  AND column_name = 'first_name';

SELECT app, name, applied
FROM public.django_migrations
WHERE app = 'auth' AND name = '0012_alter_user_first_name_max_length';
