-- Run as postgres while connected to the local silentflow database.
-- Restore application access after a dump was restored as postgres.
-- Does not change ownership, data, role passwords, or server configuration.
BEGIN;

DO $$
BEGIN
    IF current_database() <> 'silentflow' THEN
        RAISE EXCEPTION 'Connect to the silentflow database before running this script';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE silentflow TO silentflow;
GRANT USAGE ON SCHEMA label, public TO silentflow;

GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE
    label.artist, label.release, label.release_artists,
    label.release_tags, label.tag, label.track,
    public.auth_group, public.auth_group_permissions, public.auth_permission,
    public.auth_user, public.auth_user_groups, public.auth_user_user_permissions,
    public.django_admin_log, public.django_content_type, public.django_session,
    public.thumbnail_kvstore
TO silentflow;

GRANT SELECT ON TABLE public.django_migrations TO silentflow;

GRANT USAGE, SELECT ON SEQUENCE
    label.artist_id_seq, label.release_id_seq, label.release_artists_id_seq,
    label.release_tags_id_seq, label.tag_id_seq, label.track_id_seq,
    public.auth_group_id_seq, public.auth_group_permissions_id_seq,
    public.auth_permission_id_seq, public.auth_user_id_seq,
    public.auth_user_groups_id_seq, public.auth_user_user_permissions_id_seq,
    public.django_admin_log_id_seq, public.django_content_type_id_seq
TO silentflow;

COMMIT;
