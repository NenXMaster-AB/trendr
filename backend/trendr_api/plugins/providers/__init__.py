from .openai_text import register as register_openai_text
from .openai_text_stub import register as register_openai_text_stub
from .nanobanana_image_stub import register as register_nanobanana_image
from .openai_image import register as register_openai_image


def register_all():
    register_openai_text()
    register_openai_text_stub()
    register_nanobanana_image()
    register_openai_image()
