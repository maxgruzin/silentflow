from django.shortcuts import render
from .models import *
# from django.http import HttpResponse


def index(request):

    if request.method == 'GET':
        releases = Release.objects.filter(is_active=True).order_by('-released_at').values()
        # for release in releases:
        #     tracklist_values = list(Track.objects.filter(release_id=release['id']).order_by('pos').values(
        #         'pos', 'title', 'slug', 'duration'))
        #     release['tracks'] = tracklist_values

        return render(request, 'index.html', {'releases': releases})


def artists(request):

    if request.method == 'GET':
        artists = Artist.objects.filter(is_active=True).order_by('name').values().exclude(id__in=[0, 1])
        # for release in releases:
        #     tracklist_values = list(Track.objects.filter(release_id=release['id']).order_by('pos').values(
        #         'pos', 'title', 'slug', 'duration'))
        #     release['tracks'] = tracklist_values

        return render(request, 'artists.html', {'artists': artists})


def catalogue(request):

    if request.method == 'GET':
        releases = Release.objects.filter(is_active=True).order_by('-released_at').values('catalogue_number', 'name', 'slug')

        return render(request, 'catalogue.html', {'releases': releases})


def about(request):

    return render(request, 'about.html')


def release(request, slug):

    if request.method == 'GET':
        release_qset = Release.objects.get(is_active=True, slug=slug)

        tracklist = list(Track.objects.filter(release_id=release_qset).order_by('pos').values(
            'id', 'pos', 'title', 'slug', 'duration', 'track_mp3'))

        return render(request, 'release.html', {'release': release_qset,
                                                'tracklist': tracklist})


def contact(request):

    return render(request, 'contact.html')
