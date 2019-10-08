from django.shortcuts import render
from .models import *
from django.http import HttpResponseNotFound

from config import __version__



def index(request):

    if request.method == 'GET':
        releases = Release.objects.filter(is_active=True).order_by('-released_at').values()[0:15]
        # for release in releases:
        #     tracklist_values = list(Track.objects.filter(release_id=release['id']).order_by('pos').values(
        #         'pos', 'title', 'slug', 'duration'))
        #     release['tracks'] = tracklist_values

        return render(request, 'index.html', {'releases': releases,
                                              'version': __version__})


def artists(request):

    if request.method == 'GET':
        artists = Artist.objects.filter(is_active=True).order_by('name').values().exclude(id__in=[0, 1]).values()
        for artist in artists:
            artists_release_ids = ReleaseArtists.objects.filter(artist=artist['id']).values_list('release__id', flat=True)
            releases = list(Release.objects.filter(id__in=artists_release_ids, is_active=True).order_by('-id').values(
                  'catalogue_number', 'name', 'slug', 'cover_image'))
            artist['releases'] = releases

        return render(request, 'artists.html', {'artists': artists,
                                                'version': __version__})


def catalogue(request):

    if request.method == 'GET':
        releases = Release.objects.filter(is_active=True).order_by('-released_at')
        tags = Tag.objects.all()

        return render(request, 'catalogue.html', {'releases': releases,
                                                  'tags': tags,
                                                  'version': __version__})


def about(request):

    return render(request, 'about.html', {'version': __version__})


def release(request, slug):

    if request.method == 'GET':
        release_qset = Release.objects.filter(slug=slug, is_active=True).first()

        if release_qset is None:
            return HttpResponseNotFound('<h1>Page not found</h1>')

        tags = ReleaseTags.objects.filter(release=release_qset).values_list('tag__name', flat=True)

        tracklist = list(Track.objects.filter(release_id=release_qset).order_by('pos').values(
            'id', 'pos', 'title', 'slug', 'duration', 'track_mp3'))

        release_artist_ids = ReleaseArtists.objects.filter(release=release_qset).values_list('artist', flat=True)
        recommended_release_ids = ReleaseArtists.objects.filter(artist__in=release_artist_ids).exclude(release=release_qset).values_list('release', flat=True)
        recommended_releases = Release.objects.filter(id__in=recommended_release_ids)
        artists = Artist.objects.filter(id__in=release_artist_ids)

        return render(request, 'release.html', {'release': release_qset,
                                                'tracklist': tracklist,
                                                'tags': tags,
                                                'recommended_releases': recommended_releases,
                                                'artists': artists,
                                                'version': __version__})


def contact(request):

    return render(request, 'contact.html', {'version': __version__})
