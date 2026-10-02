from django.db import connection
from django.test.runner import DiscoverRunner


class CatalogueTestRunner(DiscoverRunner):
    """Create unmanaged legacy tables only inside Django's disposable test DB."""

    def setup_databases(self, **kwargs):
        config = super().setup_databases(**kwargs)
        if connection.settings_dict['NAME'] != 'test_silentflow_test':
            raise RuntimeError('Refusing to create catalogue tables outside the test database.')
        from .models import Artist, Release, ReleaseArtists, ReleaseTags, Tag, Track
        with connection.cursor() as cursor:
            cursor.execute('CREATE SCHEMA label')
        with connection.schema_editor() as editor:
            for model in (Artist, Release, Tag, ReleaseArtists, ReleaseTags, Track):
                editor.create_model(model)
        return config
