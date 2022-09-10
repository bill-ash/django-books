from django.conf import settings

DEFAULTS = {
    'HELLO': 'WORLD',
}

settings.configure(default_settings=DEFAULTS)
