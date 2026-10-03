from collections import defaultdict
import re

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_safe

from config import __version__
from .models import Artist, Release, ReleaseArtists, ReleaseTags, Track
from . import seo


@require_safe
def robots(request):
    if not seo.indexable():
        text = 'User-agent: *\nDisallow: /\n'
    else:
        text = 'User-agent: *\nDisallow: /control/\n\nSitemap: ' + seo.public_url(reverse('sitemap')) + '\n'
    return HttpResponse(text, content_type='text/plain; charset=utf-8')


@require_safe
def sitemap(request):
    urls = [seo.public_url(reverse(name)) for name in ('index', 'catalogue', 'artists', 'about', 'contact')]
    for slug in Release.objects.filter(is_active=True).order_by('id').values_list('slug', flat=True):
        if slug and re.fullmatch(r'[-\w]+', slug):
            urls.append(seo.public_url(reverse('release', args=[slug])))
    return render(request, 'sitemap.xml', {'urls': urls}, content_type='application/xml; charset=utf-8')


@require_safe
def index(request):
    releases = Release.objects.filter(is_active=True).order_by('-released_at', '-id')[:25]
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
    return render(request, 'artists.html', {'artists': artist_list, 'version': __version__,
        'page_title': 'Artists | Silent Flow',
        'page_description': 'Meet the independent artists behind Silent Flow: ambient, experimental and jazz musicians sharing their music freely.'})


@require_safe
def catalogue(request):
    releases = Release.objects.filter(is_active=True).order_by('-released_at', '-id')
    return render(request, 'catalogue.html', {'releases': releases, 'version': __version__,
        'page_title': 'Free music releases | Silent Flow',
        'page_description': 'Explore the Silent Flow catalogue of ambient, experimental and jazz music. Listen to tracks and download complete releases for free.'})


@require_safe
def about(request):
    return render(request, 'about.html', {'version': __version__,
        'page_title': 'About the label & music submissions | Silent Flow',
        'page_description': 'Silent Flow is a non-commercial ambient, experimental and jazz netlabel. Discover our approach, meet the artists, and send us your music.'})


@require_safe
def release(request, slug):
    release_obj = get_object_or_404(Release, slug=slug, is_active=True)
    artist_ids = ReleaseArtists.objects.filter(release=release_obj).values_list('artist_id', flat=True)
    related_ids = ReleaseArtists.objects.filter(artist_id__in=artist_ids).values_list('release_id', flat=True)
    recommendations = Release.objects.filter(is_active=True, id__in=related_ids).exclude(pk=release_obj.pk).order_by('-released_at', '-id')[:6]
    tracks = list(Track.objects.filter(release=release_obj).order_by('pos', 'id'))
    tags = list(ReleaseTags.objects.filter(release=release_obj).values_list('tag__name', flat=True))
    musicians = list(Artist.objects.filter(id__in=artist_ids, is_active=True).order_by('name'))
    image = seo.social_image(release_obj)
    return render(request, 'release.html', {
        'release': release_obj,
        'tracklist': tracks,
        'tags': tags,
        'artists': musicians,
        'social_image': image,
        'release_schema': seo.release_schema(release_obj, tracks, musicians, tags, image),
        'recommended_releases': recommendations,
        'version': __version__,
        'page_title': f'{release_obj.name} [{release_obj.catalogue_number}] | Silent Flow',
        'page_description': f'Listen to {release_obj.name} [{release_obj.catalogue_number}] on Silent Flow. Explore the tracks, discover the artist and download the complete release.',
    })


@require_safe
def contact(request):
    return render(request, 'contact.html', {'version': __version__,
        'page_title': 'Contact Silent Flow',
        'page_description': 'Contact Silent Flow about music submissions, releases and music-use enquiries.'})


@require_safe
def legacy_release(request, slug):
    release_obj = get_object_or_404(Release, slug=slug, is_active=True)
    return redirect('release', slug=release_obj.slug, permanent=True)
