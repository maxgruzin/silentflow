from io import BytesIO

from sorl.thumbnail.engines.pil_engine import Engine as PillowEngine


class Engine(PillowEngine):
    """Limit AVIF encoding to one thread on the shared VM."""

    def _get_raw_data(self, image, format_, quality, image_info=None, progressive=False):
        if format_ != 'AVIF':
            return super()._get_raw_data(image, format_, quality, image_info or {}, progressive)
        with BytesIO() as output:
            image.save(output, format='AVIF', quality=quality, speed=6, max_threads=1,
                       icc_profile=(image_info or {}).get('icc_profile', b''))
            return output.getvalue()
