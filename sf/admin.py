from django.contrib import admin

from .models import Tag, Artist, Release, ReleaseTags, ReleaseArtists, Track


class TagAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


class ReleaseTagsAdmin(admin.ModelAdmin):
    list_display = ['release', 'tag']
    list_select_related = ['release', 'tag']


class ArtistAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'bio', 'email', 'websites', 'is_active']

    ordering = ['name']
    search_fields = ['name']

class ReleaseArtistsAdmin(admin.ModelAdmin):
    list_display = ['id', 'release', 'artist']
    list_select_related = ['release', 'artist']


class ReleaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'catalogue_number', 'name', 'released_at', 'slug', 'is_active', 'download_link']
    search_fields = ['name', 'catalogue_number']
    list_filter = ['is_active']


class TrackAdmin(admin.ModelAdmin):
    list_display = ['id', 'release', 'title', 'slug', 'pos', 'duration']

    ordering = ['-id']
    list_select_related = ['release']
    search_fields = ['title', 'release__name']

admin.site.register(Tag, TagAdmin)
admin.site.register(Artist, ArtistAdmin)
admin.site.register(Release, ReleaseAdmin)
admin.site.register(ReleaseTags, ReleaseTagsAdmin)
admin.site.register(ReleaseArtists, ReleaseArtistsAdmin)
admin.site.register(Track, TrackAdmin)
