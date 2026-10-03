"""Public metadata derived from the catalogue, without extra database queries."""
from urllib.parse import urljoin

from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse
from django.utils.encoding import iri_to_uri
from sorl.thumbnail import get_thumbnail


DEFAULT_TITLE = 'Silent Flow — ambient, experimental & jazz label'
DEFAULT_DESCRIPTION = (
    'Discover ambient, experimental and jazz music on Silent Flow, an independent '
    'netlabel. Listen, meet the artists and download releases for free.'
)


def public_url(path):
    return iri_to_uri(urljoin(settings.SITE_URL + '/', path))


def indexable():
    return settings.SITE_INDEXABLE and not settings.DEBUG


def social_image(release=None):
    if release and release.cover_image:
        # Reuse the card JPEG: social crawlers need a widely supported format.
        image = get_thumbnail(release.cover_image, '960x960', crop='center',
                              upscale=False, format='JPEG', quality=85)
        return {'url': public_url(image.url), 'width': image.width,
                'height': image.height, 'alt': f'Cover artwork for {release.name}'}
    return {'url': public_url(static('images/social-default.png')),
            'width': 1200, 'height': 630,
            'alt': 'Silent Flow — ambient, experimental and jazz netlabel'}


def site_schema():
    home = public_url(reverse('index'))
    return [
        {'@type': 'Organization', '@id': home + '#label', 'name': 'Silent Flow',
         'url': home, 'logo': public_url(static('images/sf/logo.png'))},
        {'@type': 'WebSite', '@id': home + '#website', 'name': 'Silent Flow',
         'url': home, 'publisher': {'@id': home + '#label'}},
    ]


def release_schema(release, tracks, artists, tags, image):
    url = public_url(reverse('release', args=[release.slug]))
    musicians = [
        {'@type': 'MusicGroup', 'name': artist.name,
         'url': public_url(reverse('artists')) + f'#artist-{artist.pk}'}
        for artist in artists
    ]
    items = []
    for position, track in enumerate(tracks, 1):
        seconds = track.duration.hour * 3600 + track.duration.minute * 60 + track.duration.second
        recording = {'@type': 'MusicRecording', '@id': url + f'#track-{track.pk}',
                     'name': track.title, 'duration': f'PT{seconds}S',
                     'inAlbum': {'@id': url + '#album'}}
        if track.track_mp3:
            recording['audio'] = {'@type': 'AudioObject',
                                  'contentUrl': public_url(track.track_mp3.url),
                                  'encodingFormat': 'audio/mpeg'}
        items.append({'@type': 'ListItem', 'position': position, 'item': recording})
    album = {'@type': 'MusicAlbum', '@id': url + '#album', 'url': url,
             'name': release.name, 'identifier': release.catalogue_number,
             'datePublished': release.released_at.date().isoformat(),
             'image': image['url'], 'numTracks': len(tracks),
             'publisher': {'@id': public_url(reverse('index')) + '#label'},
             'track': {'@type': 'ItemList', 'numberOfItems': len(items), 'itemListElement': items}}
    if musicians:
        album['byArtist'] = musicians
    if tags:
        album['genre'] = tags
    return album
