from sorl.thumbnail import default
from sorl.thumbnail.base import ThumbnailBackend


class RepairingThumbnailBackend(ThumbnailBackend):
    """Repair stale metadata after a restore without clearing other thumbnails."""

    def get_thumbnail(self, file_, geometry_string, **options):
        thumbnail = super().get_thumbnail(file_, geometry_string, **options)
        if not thumbnail.storage.exists(thumbnail.name):
            default.kvstore.delete(thumbnail, delete_thumbnails=False)
            thumbnail = super().get_thumbnail(file_, geometry_string, **options)
        return thumbnail
