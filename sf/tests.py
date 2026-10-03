import datetime
import json
import os
import re
import stat
import tempfile
from unittest import skipUnless
from xml.etree import ElementTree
from pathlib import Path

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from sorl.thumbnail import get_thumbnail

from .models import Artist, Release, ReleaseArtists, Track


@override_settings(DEBUG=True)
class LocalMediaTests(SimpleTestCase):
    def test_audio_ranges_and_invalid_ranges(self):
        from config.media_docker_local import serve_media
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, 'sample.mp3').write_bytes(b'0123456789')
            for header, expected, body in (
                ('bytes=2-5', 206, b'2345'),
                ('bytes=7-', 206, b'789'),
                ('bytes=-3', 206, b'789'),
                ('bytes=8-99', 206, b'89'),
                ('bytes=99-', 416, b''),
                ('bytes=6-2', 416, b''),
                ('bytes=-0', 416, b''),
                ('bytes=0-1,4-5', 200, b'0123456789'),
            ):
                with self.subTest(header=header):
                    request = RequestFactory().get('/media/sample.mp3', HTTP_RANGE=header)
                    response = serve_media(request, 'sample.mp3', document_root=directory)
                    try:
                        self.assertEqual(response.status_code, expected)
                        actual = b''.join(response.streaming_content) if response.streaming else response.content
                        self.assertEqual(actual, body)
                        if expected == 206:
                            self.assertEqual(int(response['Content-Length']), len(body))
                            self.assertIn('/10', response['Content-Range'])
                    finally:
                        response.close()

    def test_local_media_view_is_disabled_outside_debug(self):
        from config.media_docker_local import serve_media
        from django.http import Http404
        with override_settings(DEBUG=False), self.assertRaises(Http404):
            serve_media(RequestFactory().get('/media/sample.mp3'), 'sample.mp3')


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
        for path in ('/', '/releases/', '/artists/', '/release/visible-release/', '/about/', '/contact/'):
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
        self.assertContains(response, '<audio ', count=1)
        self.assertNotContains(response, '<audio controls')
        self.assertContains(response, 'data-track-url="/media/track_mp3/example.mp3"')
        self.assertContains(response, 'aria-label="Seek within track"')
        self.assertContains(response, '<noscript>')

    def test_lossless_download_is_available_on_catalogue_and_release(self):
        self.release.download_link_lossless = 'https://example.com/music.zip'
        self.release.save()
        for path in ('/releases/', '/release/visible-release/'):
            self.assertContains(self.client.get(path), 'href="https://example.com/music.zip"')
        self.release.download_link_lossless = 'javascript:alert(1)'
        self.release.save()
        for path in ('/releases/', '/release/visible-release/'):
            self.assertNotContains(self.client.get(path), 'javascript:')

    def test_hidden_and_missing_releases_are_404(self):
        for path in ('/release/hidden-release/', '/release/missing/', '/hidden-release/', '/missing/', '/artists/unexpected/'):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_catalogue_redirect_preserves_existing_links(self):
        self.assertRedirects(self.client.get('/catalogue/'), '/releases/', status_code=301)
        self.assertEqual(self.client.get('/catalogue/?source=bookmark')['Location'], '/releases/?source=bookmark')

    def test_artists_without_biographies_are_visible(self):
        Artist.objects.create(id=40, name='New artist', websites=[], is_active=True)
        self.assertContains(self.client.get('/artists/'), 'New artist')

    def test_external_links_reject_unsafe_schemes(self):
        self.artist.websites = ['javascript:alert(1)']
        self.artist.save()
        self.release.download_link = 'javascript:alert(2)'
        self.release.save()
        self.assertNotContains(self.client.get('/artists/'), 'javascript:')
        self.assertNotContains(self.client.get('/release/visible-release/'), 'javascript:')
        self.assertNotContains(self.client.get('/releases/'), 'javascript:')

    def test_metadata_and_frontend_dependencies(self):
        response = self.client.get('/release/visible-release/')
        self.assertContains(response, '<link rel="canonical" href="https://silentflow.org/release/visible-release/">', html=True)
        self.assertContains(response, 'Visible release [SF001] | Silent Flow')
        for obsolete in ('jquery', 'materialize', 'google-analytics', 'fonts.googleapis.com'):
            self.assertNotContains(response, obsolete)

    @override_settings(SITE_URL='https://silentflow.org')
    def test_sitemap_lists_only_canonical_published_urls(self):
        self.related.slug = 'été'
        self.related.save()
        with self.assertNumQueries(1):
            response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        urls = [element.text for element in ElementTree.fromstring(response.content).iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
        self.assertEqual(len(urls), 7)
        self.assertIn('https://silentflow.org/release/%C3%A9t%C3%A9/', urls)
        self.assertIn('https://silentflow.org/releases/', urls)
        self.assertNotIn('https://silentflow.org/catalogue/', urls)
        self.assertFalse(any('hidden-release' in url or '/control/' in url for url in urls))
        self.assertNotContains(response, 'lastmod')

    def test_robots_and_headers_distinguish_public_local_and_staging(self):
        for debug, enabled, expected in ((False, True, True), (True, True, False), (False, False, False)):
            with self.subTest(debug=debug, enabled=enabled), override_settings(DEBUG=debug, SITE_INDEXABLE=enabled):
                robots = self.client.get('/robots.txt')
                page = self.client.get('/about/')
                if expected:
                    self.assertContains(robots, 'Disallow: /control/\n')
                    self.assertContains(robots, 'Sitemap: https://silentflow.org/sitemap.xml')
                    self.assertNotIn('X-Robots-Tag', page)
                    self.assertNotContains(page, 'noindex')
                else:
                    self.assertContains(robots, 'Disallow: /\n')
                    self.assertEqual(page['X-Robots-Tag'], 'noindex, nofollow')
                    self.assertContains(page, 'name="robots" content="noindex, nofollow"')
                self.assertEqual(self.client.get('/control/login/')['X-Robots-Tag'], 'noindex, nofollow')
                self.assertEqual(self.client.get('/release/missing/')['X-Robots-Tag'], 'noindex, nofollow')

    def test_release_schema_matches_visible_tracks_without_more_queries(self):
        with self.assertNumQueries(5):
            response = self.client.get('/release/visible-release/?tracking=test')
        payload = re.search(r'<script type="application/ld\+json">(.*?)</script>', response.content.decode(), re.S).group(1)
        graph = json.loads(payload)['@graph']
        album = next(item for item in graph if item['@type'] == 'MusicAlbum')
        self.assertEqual(album['url'], 'https://silentflow.org/release/visible-release/')
        self.assertEqual(album['name'], self.release.name)
        self.assertEqual(album['identifier'], 'SF001')
        self.assertEqual(album['numTracks'], 1)
        self.assertEqual(album['byArtist'][0]['name'], self.artist.name)
        recording = album['track']['itemListElement'][0]['item']
        self.assertEqual(recording['duration'], 'PT200S')
        self.assertEqual(recording['audio']['contentUrl'], 'https://silentflow.org/media/track_mp3/example.mp3')
        self.assertContains(response, 'id="' + recording['@id'].split('#')[1] + '"')
        self.assertNotIn('license', payload)
        self.assertNotIn('email', payload)

    def test_catalogue_text_cannot_break_out_of_structured_data(self):
        self.release.name = '</script><script>alert("x")</script> & music'
        self.release.save()
        response = self.client.get('/release/visible-release/')
        payload = re.search(r'<script type="application/ld\+json">(.*?)</script>', response.content.decode(), re.S).group(1)
        self.assertNotContains(response, '<script>alert(')
        self.assertNotIn('<', payload)
        album = json.loads(payload)['@graph'][-1]
        self.assertEqual(album['name'], self.release.name)

    def test_unicode_canonical_and_social_metadata_are_consistent(self):
        self.release.slug = 'été'
        self.release.save()
        response = self.client.get('/release/%C3%A9t%C3%A9/?ref=share')
        self.assertContains(response, '<link rel="canonical" href="https://silentflow.org/release/%C3%A9t%C3%A9/">', html=True)
        for key in ('og:title', 'twitter:title'):
            self.assertContains(response, f'{key}" content="Visible release [SF001] | Silent Flow"')
        self.assertContains(response, 'https://silentflow.org/static/images/social-default.png')

    def test_crawler_endpoints_support_head_but_not_post(self):
        for path in ('/robots.txt', '/sitemap.xml'):
            self.assertEqual(self.client.head(path).status_code, 200)
            self.assertEqual(self.client.head(path).content, b'')
            self.assertEqual(self.client.post(path).status_code, 405)

    def test_old_release_link_redirects_to_matching_release(self):
        self.assertRedirects(self.client.get('/visible-release/'), reverse('release', args=['visible-release']), status_code=301)

    def test_unicode_release_slugs_still_resolve(self):
        self.release.slug = 'angstrom-\u00e9cho'
        self.release.save()
        self.assertEqual(self.client.get(reverse('release', args=[self.release.slug])).status_code, 200)

    def test_safe_methods_and_unsupported_methods(self):
        for path in ('/', '/releases/', '/artists/', '/release/visible-release/', '/about/', '/contact/'):
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
    @skipUnless(os.name == 'posix', 'Public asset permissions are enforced on the Linux server')
    def test_public_assets_remain_readable_under_gunicorn_umask(self):
        from django.core.files.base import ContentFile
        from django.core.files.storage import FileSystemStorage
        from django.contrib.staticfiles.storage import StaticFilesStorage
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            cache.clear()
            previous_umask = os.umask(0o027)
            try:
                for storage_class in (FileSystemStorage, StaticFilesStorage):
                    root = Path(directory, storage_class.__name__)
                    storage = storage_class(location=root)
                    name = storage.save('nested/public.txt', ContentFile(b'public asset'))
                    self.assertEqual(stat.S_IMODE(Path(storage.path(name)).stat().st_mode), 0o644)
                    self.assertEqual(stat.S_IMODE((root / 'nested').stat().st_mode), 0o755)
                source = Path(directory, 'cover.jpg')
                Image.new('RGB', (100, 100), 'navy').save(source)
                thumbnail = get_thumbnail('cover.jpg', '50x50', format='AVIF', quality=55)
                path = Path(thumbnail.storage.path(thumbnail.name))
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o644)
                for parent in path.parents:
                    if parent == Path(directory):
                        break
                    self.assertEqual(stat.S_IMODE(parent.stat().st_mode), 0o755)
            finally:
                os.umask(previous_umask)
                cache.clear()

    def test_website_images_keep_the_full_landscape_composition(self):
        from .images import responsive_image
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            cache.clear()
            source = Path(directory) / 'website.jpg'
            Image.new('RGB', (1200, 500), 'navy').save(source)
            result = responsive_image('website.jpg', 'landscape')
            self.assertEqual((result['fallback'].width, result['fallback'].height), (1200, 500))
            self.assertIn('1200w', result['srcset'])
            self.assertNotIn('1920w', result['srcset'])
            with Image.open(source) as original:
                self.assertEqual(original.size, (1200, 500))
            cache.clear()

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

    def test_responsive_images_are_avif_with_jpeg_fallback_and_no_upscaling(self):
        from .images import responsive_image
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            cache.clear()
            source = Path(directory) / 'small.jpg'
            Image.new('RGB', (200, 200), 'navy').save(source)
            original = source.read_bytes()
            result = responsive_image('small.jpg')
            self.assertTrue(result['fallback'].name.endswith('.jpg'))
            self.assertEqual(result['fallback'].width, 200)
            self.assertEqual(len(result['srcset'].split(', ')), 1)
            self.assertTrue(result['srcset'].endswith(' 200w'))
            avif = next(Path(directory).rglob('*.avif'))
            with Image.open(avif) as image:
                self.assertEqual(image.format, 'AVIF')
                self.assertEqual(image.size, (200, 200))
            self.assertEqual(original, source.read_bytes())
            cache.clear()
