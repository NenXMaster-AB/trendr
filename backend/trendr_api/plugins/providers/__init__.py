from .openai_text import register as register_openai_text
from .openai_text_stub import register as register_openai_text_stub
from .nanobanana_image_stub import register as register_nanobanana_image


def register_all():
    register_openai_text()
    register_openai_text_stub()
    register_nanobanana_image()
