from django.contrib import admin

from .models import Tag, Artist, Release, ReleaseTags, Track


class TagAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


class ArtistAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'bio', 'email', 'website', 'is_active']


class ReleaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'catalogue_number', 'artist', 'name', 'released_at', 'slug', 'is_active']

admin.site.register(Tag, TagAdmin)
admin.site.register(Artist, ArtistAdmin)
admin.site.register(Release, ReleaseAdmin)
admin.site.register(ReleaseTags)
admin.site.register(Track)
