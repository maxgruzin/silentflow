from collections import defaultdict

from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_safe

from config import __version__
from .models import Artist, Release, ReleaseArtists, ReleaseTags, Track


@require_safe
def index(request):
    releases = Release.objects.filter(is_active=True).order_by('-released_at', '-id')[:15]
    return render(request, 'index.html', {'releases': releases, 'version': __version__})


@require_safe
def artists(request):
    artist_list = list(Artist.objects.filter(is_active=True).exclude(id__in=[0, 1]).order_by('name').values())
    by_artist = defaultdict(list)
    links = ReleaseArtists.objects.filter(
        artist_id__in=[artist['id'] for artist in artist_list], release__is_active=True,
    ).select_related('release').order_by('-release__released_at', '-release_id')
    for link in links:
        by_artist[link.artist_id].append(link.release)
    for artist in artist_list:
        artist['releases'] = by_artist[artist['id']]
    return render(request, 'artists.html', {'artists': artist_list, 'version': __version__})


@require_safe
def catalogue(request):
    releases = Release.objects.filter(is_active=True).order_by('-released_at', '-id')
    return render(request, 'catalogue.html', {'releases': releases, 'version': __version__})


@require_safe
def about(request):
    return render(request, 'about.html', {'version': __version__})


@require_safe
def release(request, slug):
    release_obj = get_object_or_404(Release, slug=slug, is_active=True)
    artist_ids = ReleaseArtists.objects.filter(release=release_obj).values_list('artist_id', flat=True)
    related_ids = ReleaseArtists.objects.filter(artist_id__in=artist_ids).values_list('release_id', flat=True)
    recommendations = Release.objects.filter(is_active=True, id__in=related_ids).exclude(pk=release_obj.pk).order_by('-released_at', '-id')[:6]
    return render(request, 'release.html', {
        'release': release_obj,
        'tracklist': Track.objects.filter(release=release_obj).order_by('pos', 'id'),
        'tags': ReleaseTags.objects.filter(release=release_obj).values_list('tag__name', flat=True),
        'artists': Artist.objects.filter(id__in=artist_ids, is_active=True).order_by('name'),
        'recommended_releases': recommendations,
        'version': __version__,
    })


@require_safe
def contact(request):
    return render(request, 'contact.html', {'version': __version__})


@require_safe
def legacy_release(request, slug):
    release_obj = get_object_or_404(Release, slug=slug, is_active=True)
    return redirect('release', slug=release_obj.slug, permanent=True)
