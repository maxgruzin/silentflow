from django.shortcuts import render
from .models import Release, Track
# from django.http import HttpResponse


def index(request):

    if request.method == 'GET':
        releases = Release.objects.filter(is_active=True).order_by('-released_at').values()[:200]
        # for release in releases:
        #     tracklist_values = list(Track.objects.filter(release_id=release['id']).order_by('pos').values(
        #         'pos', 'title', 'slug', 'duration'))
        #     release['tracks'] = tracklist_values

        return render(request, 'index.html', {'releases': releases})


def release(request):

    return render(request, 'index.html')


def contact(request):

    return render(request, 'contact.html')