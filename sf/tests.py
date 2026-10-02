import datetime
import tempfile
from pathlib import Path

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from sorl.thumbnail import get_thumbnail

from .models import Artist, Release, ReleaseArtists, Track


class PublicPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.artist = Artist.objects.create(id=10, name='Test Artist', bio='An ambient artist.', websites=[], is_active=True)
        cls.release = Release.objects.create(name='Visible release', catalogue_number='SF001', slug='visible-release', released_at=timezone.now(), is_active=True)
        cls.hidden = Release.objects.create(name='Hidden release', catalogue_number='SF002', slug='hidden-release', released_at=timezone.now(), is_active=False)
        cls.related = Release.objects.create(name='Related release', catalogue_number='SF003', slug='related-release', released_at=timezone.now(), is_active=True)
        for release in (cls.release, cls.hidden, cls.related):
            ReleaseArtists.objects.create(release=release, artist=cls.artist)
        Track.objects.create(release=cls.release, title='First track', slug='first-track', pos=1, duration=datetime.time(0, 3, 20), track_mp3='track_mp3/example.mp3')

    def test_public_pages_render_and_hide_unpublished_releases(self):
        for path in ('/', '/catalogue/', '/artists/', '/release/visible-release/', '/about/', '/contact/'):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, 'Hidden release')

    def test_release_contains_playable_track_and_active_recommendation(self):
        response = self.client.get('/release/visible-release/')
        self.assertContains(response, '/media/track_mp3/example.mp3')
        self.assertContains(response, 'Related release')
        self.assertNotContains(response, 'Hidden release')
        self.assertEqual(list(response.context['recommended_releases']), [self.related])

    def test_hidden_and_missing_releases_are_404(self):
        for path in ('/release/hidden-release/', '/release/missing/', '/hidden-release/', '/missing/', '/artists/unexpected/'):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_old_release_link_redirects_to_matching_release(self):
        self.assertRedirects(self.client.get('/visible-release/'), reverse('release', args=['visible-release']), status_code=301)

    def test_unicode_release_slugs_still_resolve(self):
        self.release.slug = 'angstrom-\u00e9cho'
        self.release.save()
        self.assertEqual(self.client.get(reverse('release', args=[self.release.slug])).status_code, 200)

    def test_safe_methods_and_unsupported_methods(self):
        for path in ('/', '/catalogue/', '/artists/', '/release/visible-release/', '/about/', '/contact/'):
            with self.subTest(path=path):
                response = self.client.head(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, b'')
                self.assertEqual(self.client.post(path).status_code, 405)

    def test_artist_queries_do_not_grow_with_artist_count(self):
        for number in range(20, 30):
            artist = Artist.objects.create(id=number, name=f'Artist {number}', bio='Bio', websites=[], is_active=True)
            ReleaseArtists.objects.create(artist=artist, release=self.release)
        with self.assertNumQueries(2):
            response = self.client.get('/artists/')
        self.assertContains(response, '/release/visible-release/')
        self.assertNotContains(response, 'https://silentflow.org/release/')

    def test_security_headers_and_admin_login(self):
        response = self.client.get('/about/')
        self.assertEqual(response.headers['X-Frame-Options'], 'DENY')
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(self.client.get('/control/login/').status_code, 200)

    def test_admin_can_open_catalogue_lists_and_edit_forms(self):
        user = get_user_model().objects.create_superuser('test-admin', 'admin@example.com', 'test-password')
        self.client.force_login(user)
        for model in ('artist', 'release', 'releaseartists', 'releasetags', 'tag', 'track'):
            with self.subTest(model=model):
                self.assertEqual(self.client.get(f'/control/sf/{model}/').status_code, 200)
        self.assertEqual(self.client.get(f'/control/sf/release/{self.release.pk}/change/').status_code, 200)


class ThumbnailTests(TestCase):
    def test_missing_cached_file_is_regenerated_without_removing_source(self):
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            cache.clear()
            source = Path(directory) / 'cover.jpg'
            Image.new('RGB', (900, 900), 'navy').save(source)
            thumbnail = get_thumbnail('cover.jpg', '300x300', quality=75)
            destination = Path(thumbnail.storage.path(thumbnail.name))
            self.assertTrue(destination.exists())
            destination.unlink()
            repaired = get_thumbnail('cover.jpg', '300x300', quality=75)
            self.assertEqual(thumbnail.name, repaired.name)
            self.assertTrue(destination.exists())
            self.assertTrue(source.exists())
            with Image.open(destination) as image:
                self.assertEqual(image.size, (300, 300))
            cache.clear()
