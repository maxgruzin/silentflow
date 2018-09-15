from django.db import models
from django.contrib.postgres.fields import ArrayField


class Tag(models.Model):
    """
    Tags 
    """
    name = models.TextField()

    class Meta:
        managed = False
        db_table = '"label"."tag"'

    def __str__(self):
        return self.name


class Artist(models.Model):
    """
    Artists 
    """
    name = models.TextField()
    bio = models.TextField(null=True, blank=True)
    email = models.TextField(null=True, blank=True)
    websites = ArrayField(models.TextField(null=True, blank=True))
    is_active = models.BooleanField()
    country = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = '"label"."artist"'

    def __str__(self):
        return self.name


class Release(models.Model):
    """
    Releases 
    """
    catalogue_number = models.TextField()
    name = models.TextField()
    released_at = models.DateTimeField()
    headline = models.TextField(null=True, blank=True)
    review = models.TextField(null=True, blank=True)
    slug = models.TextField(null=True, blank=True)
    is_active = models.BooleanField()
    cover_image = models.ImageField(upload_to='cover_image', null=True, blank=True)
    website_image = models.ImageField(upload_to='website_image', null=True, blank=True)
    download_link = models.TextField(null=True, blank=True)
    mentions = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        ordering = ['-released_at']
        db_table = '"label"."release"'

    def __str__(self):
        return self.name


class ReleaseTags(models.Model):
    """
    Release tags: many to many table
    """
    release = models.ForeignKey(Release, on_delete=models.PROTECT)
    tag = models.ForeignKey(Tag, on_delete=models.PROTECT)

    class Meta:
        managed = False
        db_table = '"label"."release_tags"'


class ReleaseArtists(models.Model):
    """
    Release artists: many to many table
    """
    release = models.ForeignKey(Release, on_delete=models.PROTECT)
    artist = models.ForeignKey(Artist, on_delete=models.PROTECT)

    class Meta:
        managed = False
        db_table = '"label"."release_artists"'


class Track(models.Model):
    """
    Tracks 
    """
    release = models.ForeignKey(Release, on_delete=models.PROTECT)
    title = models.TextField()
    slug = models.TextField(null=True, blank=True)
    pos = models.IntegerField()
    duration = models.TimeField()
    track_mp3 = models.FileField(upload_to='track_mp3', null=True, blank=True)

    class Meta:
        managed = False
        db_table = '"label"."track"'

    def __str__(self):
        return self.title
