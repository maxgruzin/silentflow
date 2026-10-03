from django.core.management.base import BaseCommand, CommandError
from sf.images import PROFILES, responsive_image
from sf.models import Release


class Command(BaseCommand):
    help = 'Pre-generate responsive images sequentially; originals and existing thumbnails are retained.'

    def add_arguments(self, parser):
        parser.add_argument('--profile', choices=PROFILES, default='card')
        parser.add_argument('--limit', type=int, default=0, help='Latest N active releases; 0 means all.')

    def handle(self, *args, **options):
        if options['limit'] < 0:
            raise CommandError('--limit must be zero or positive')
        releases = Release.objects.filter(is_active=True).order_by('-released_at', '-id')
        if options['limit']:
            releases = releases[:options['limit']]
        failures = 0
        count = 0
        for release in releases:
            source = release.cover_image
            if options['profile'] == 'landscape':
                source = release.website_image or release.cover_image
            if not source:
                continue
            try:
                responsive_image(source, options['profile'])
                count += 1
                if count % 20 == 0:
                    self.stdout.write(f'Prepared {count} releases…')
            except (OSError, ValueError) as exc:
                failures += 1
                self.stderr.write(f'{release.catalogue_number}: {exc}')
        self.stdout.write(f'Prepared {count} releases ({options["profile"]}). Originals unchanged.')
        if failures:
            raise CommandError(f'{failures} image(s) could not be prepared.')
