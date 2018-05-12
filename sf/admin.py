from django.contrib import admin

from .models import Tag, Artist, Release, ReleaseTags, ReleaseArtists, Track


class TagAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


class ReleaseTagsAdmin(admin.ModelAdmin):
    list_display = ['release', 'tag']


class ArtistAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'bio', 'email', 'websites', 'is_active']

    class Meta:
        ordering = 'name'

class ReleaseArtistsAdmin(admin.ModelAdmin):
    list_display = ['id', 'release', 'artist']


class ReleaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'catalogue_number', 'name', 'released_at', 'slug', 'is_active', 'download_link']


class TrackAdmin(admin.ModelAdmin):
    list_display = ['id', 'release', 'title', 'slug', 'pos', 'duration']

    class Meta:
        ordering = '-id'

admin.site.register(Tag, TagAdmin)
admin.site.register(Artist, ArtistAdmin)
admin.site.register(Release, ReleaseAdmin)
admin.site.register(ReleaseTags, ReleaseTagsAdmin)
admin.site.register(ReleaseArtists, ReleaseArtistsAdmin)
admin.site.register(Track, TrackAdmin)
